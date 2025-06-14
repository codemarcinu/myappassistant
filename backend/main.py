from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import settings
from .api import chat, agents, food, upload, pantry
from .core.database import engine, Base, AsyncSessionLocal
from .models import shopping
from .core.migrations import run_migrations

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
    version=settings.APP_VERSION
)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(agents.router, prefix="/api", tags=["Agents"])
app.include_router(food.router, prefix="/api")
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(pantry.router, prefix="/api", tags=["Pantry"])

@app.get("/")
async def read_root():
    return {"message": f"Witaj w backendzie aplikacji {settings.APP_NAME}!"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
