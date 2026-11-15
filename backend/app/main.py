"""FastAPI application entrypoint with CORS and database lifecycle management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.config import settings
from backend.app.db.models import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing database table initialization."""
    init_db()
    yield


app = FastAPI(
    title="TalentCouncil HRMS API",
    description="Multi-agent hiring council evaluation and audit API",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS strictly honoring FRONTEND_ORIGIN
allowed_origins = [settings.FRONTEND_ORIGIN]
if "http://localhost:3000" not in allowed_origins:
    allowed_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

