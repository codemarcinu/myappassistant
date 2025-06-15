import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from .api import agents, chat, food, pantry, upload
from .config import settings
from .core.database import Base, engine
from .core.migrations import run_migrations

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

    yield
    # Cleanup code here if needed


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    description="Backend dla modułowej aplikacji agentowej.",
    version=settings.APP_VERSION,
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- Exception Handlers ---
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})


# --- API Versioning ---
api_v1 = APIRouter(prefix="/api/v1")
api_v2 = APIRouter(prefix="/api/v2")

api_v1.include_router(chat.router, tags=["Chat"])
api_v1.include_router(agents.router, tags=["Agents"])
api_v1.include_router(food.router)
api_v1.include_router(upload.router, tags=["Upload"])
api_v1.include_router(pantry.router, tags=["Pantry"])


# Przykład endpointu v2 (możesz rozwinąć)
@api_v2.get("/hello")
async def hello_v2():
    """Przykładowy endpoint v2."""
    return {"message": "Hello from API v2!"}


app.include_router(api_v1)
app.include_router(api_v2)


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
            await conn.execute("SELECT 1")
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
