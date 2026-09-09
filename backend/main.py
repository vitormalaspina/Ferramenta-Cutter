from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from utils.logger import get_logger
from utils.config import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("YouTube Cutter backend starting...")

    # Initialize database tables
    from models.database import Base, engine
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")

    # Ensure storage directories exist
    for d in [settings.temp_dir, settings.output_dir, settings.jobs_dir, Path("logs")]:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Storage directories ready.")

    yield

    # Shutdown
    logger.info("YouTube Cutter backend stopping.")


app = FastAPI(
    title="YouTube Cutter",
    version="1.0.0",
    description="API local para cortar vídeos do YouTube",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import analyze, jobs, health

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(analyze.router, prefix="/api", tags=["Analyze"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])


@app.get("/")
async def root():
    return {"status": "ok", "message": "YouTube Cutter API"}
