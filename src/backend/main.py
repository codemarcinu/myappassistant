import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.sql import text
from starlette.middleware.base import BaseHTTPMiddleware

from backend.api import agents, chat, food, pantry, upload
from backend.api.v1.endpoints import receipts
from backend.config import settings
from backend.core.database import AsyncSessionLocal, Base, engine
from backend.core.migrations import run_migrations
from backend.core.seed_data import seed_database

# --- Rate limiting ---
limiter = Limiter(key_func=get_remote_address)


# --- Middleware: Logging ---
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logging.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logging.info(f"Response: {response.status_code}")
        return response


# --- Middleware: Auth (szkielet) ---
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Tu można dodać logikę JWT lub innej autoryzacji
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Run migrations
    await run_migrations()
    # Seed the database
    logging.info("Seeding database with initial data...")
    db = AsyncSessionLocal()
    try:
        await seed_database(db)
    finally:
        await db.close()
    logging.info("Database seeding finished.")
    yield  # Cleanup code here if needed


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    description="Backend dla modułowej aplikacji agentowej.",
    version=settings.APP_VERSION,
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    # UWAGA: W środowisku produkcyjnym te wartości powinny pochodzić ze zmiennych środowiskowych!
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
# app.add_middleware(AuthMiddleware)  # Odkomentuj, gdy AuthMiddleware będzie gotowe
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


# --- Exception Handlers ---
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})


# --- API Versioning ---
api_v1 = APIRouter()
api_v1.include_router(chat.router, tags=["Chat"])
api_v1.include_router(agents.router, tags=["Agents"])
api_v1.include_router(food.router)
api_v1.include_router(upload.router, tags=["Upload"])
api_v1.include_router(pantry.router, tags=["Pantry"])
api_v1.include_router(receipts.router)

app.include_router(api_v1, prefix="/api/v1")


# --- Health check ---
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/ready", tags=["Health"])
async def ready_check():
    """Readiness check (np. sprawdzenie połączenia z bazą)."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            status_code=503, content={"status": "not ready", "error": str(e)}
        )


# --- Background task example ---
@app.post("/api/v1/long-task")
async def long_task(background_tasks: BackgroundTasks):
    """Przykład endpointu z background taskiem."""

    def do_long_work():
        import time

        time.sleep(5)
        logging.info("Long task finished!")

    background_tasks.add_task(do_long_work)
    return {"status": "started"}


@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint."""
    return {"message": f"Witaj w backendzie aplikacji {settings.APP_NAME}!"}
