from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.config import settings
from backend.api import chat, agents, food, upload
from backend.core.database import engine, Base, AsyncSessionLocal
from backend.models import shopping
from backend.core.migrations import run_migrations
from backend.core.seed_data import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Run migrations
    await run_migrations()
    
    # Seed database
    async with AsyncSessionLocal() as session:
        await seed_database(session)
    
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

@app.get("/")
async def read_root():
    return {"message": f"Witaj w backendzie aplikacji {settings.APP_NAME}!"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
