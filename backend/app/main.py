from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import dashboard
from app.api import engines
from app.api import performance
from app.api import telegram
from app.api.administrators import (
    router as administrators_router,
)
from app.api.auth import (
    router as auth_router,
)
from app.api.models import (
    router as models_router,
)
from app.api.results import (
    router as results_router,
)
from app.api.signals import (
    router as signals_router,
)
from app.api.telegram_auto_posts import (
    router as telegram_auto_posts_router,
)
from app.core.config import settings
from app.db.session import engine
from app.services.telegram_auto_publisher import (
    start_auto_publisher,
    stop_auto_publisher,
)

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.

    Starts the Telegram Auto Publisher when FastAPI starts
    and stops it gracefully when FastAPI shuts down.
    """

    await start_auto_publisher()

    try:
        yield

    finally:
        await stop_auto_publisher()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Backend API for the Mines Signal System"
    ),
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://mines-signal-eight.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTES
# ============================================================

# Authentication
app.include_router(
    auth_router,
)


# Administrators
app.include_router(
    administrators_router,
)


# Signals
app.include_router(
    signals_router,
)


# Results
app.include_router(
    results_router,
)


# Models
app.include_router(
    models_router,
)


# Engines
app.include_router(
    engines.router,
)


# Performance
app.include_router(
    performance.router,
)


# Dashboard
app.include_router(
    dashboard.router,
)


# Telegram
app.include_router(
    telegram.router,
)


# Telegram Auto Publisher
app.include_router(
    telegram_auto_posts_router,
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "online",
        "environment": settings.app_env,
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "mines-signal-api",
    }


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

@app.get("/api/health/database")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as exc:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc),
        }
 
