"""
===============================================================================
NEXUS DASHBOARD BACKEND - MAIN APPLICATION
===============================================================================

File: dashboard/api/main.py
Created: 2024-12-15
Purpose: FastAPI application entry point for the Nexus Dashboard API

... (header unchanged) ...
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import our custom services
from services.sync_service import SyncService
from services.metrics_service import MetricsService
from cache.state import CacheState

# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application lifecycle:
    - STARTUP: Initialize services, run initial sync, start scheduler
    - SHUTDOWN: Stop scheduler, cleanup connections
    """
    print("=" * 60)
    print("NEXUS DASHBOARD BACKEND - STARTING")
    print("=" * 60)

    # Initialize the cache (stores our data in memory)
    app.state.cache = CacheState()

    # Initialize the sync service (handles Cosmos DB connections)
    app.state.sync_service = SyncService(app.state.cache)

    # Initialize the metrics service (calculates aggregations)
    app.state.metrics_service = MetricsService(app.state.cache)

    # Run initial sync to populate cache
    print("\n[STARTUP] Running initial data sync...")
    try:
        await app.state.sync_service.full_sync()
        print("[STARTUP] Initial sync complete!")
    except Exception as e:
        print(f"[STARTUP] Warning: Initial sync failed: {e}")
        print("[STARTUP] API will start but data may be unavailable")

    # Start background scheduler for periodic syncs
    app.state.sync_service.start_scheduler()

    print("\n[STARTUP] Backend ready!")
    print(f"[STARTUP] API available at http://localhost:8000")
    print("=" * 60)

    yield  # Application is running

    # Shutdown
    print("\n[SHUTDOWN] Stopping scheduler...")
    app.state.sync_service.stop_scheduler()
    print("[SHUTDOWN] Cleanup complete")


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Nexus Dashboard API",
    description="Backend API for the Nexus Query Optimizer Dashboard. Provides real-time metrics with incremental updates.",
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
cors_origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative React port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# Add origins from environment variable (for Azure production)
if cors_origins_env:
    cors_origins.extend([origin.strip() for origin in cors_origins_env.split(",") if origin.strip()])
    print(f"[CORS] Added origins from env: {cors_origins_env}")
else:
    # If no env var set, allow all origins (dev mode)
    cors_origins.append("*")
    print("[CORS] No CORS_ALLOWED_ORIGINS set, allowing all origins (dev mode)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# FRONTEND (REACT) STATIC HOSTING CONFIG
# ============================================================================
#
# During deployment, CI should build the Vite app (dashboard/web) and copy:
#   dashboard/web/dist/*  ->  dashboard/api/static/*
#
# That results in:
#   dashboard/api/static/index.html
#   dashboard/api/static/assets/...

STATIC_DIR = Path(__file__).parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    Serve the React app in production (index.html). If the frontend isn't present,
    fall back to API info so you can still verify the backend is running.
    """
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))

    return {
        "name": "Nexus Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "note": "Frontend not built/deployed (missing dashboard/api/static/index.html)",
    }


@app.get("/api/status")
async def get_status():
    cache = app.state.cache
    sync_service = app.state.sync_service

    return {
        "last_sync": cache.last_sync_timestamp.isoformat() if cache.last_sync_timestamp else None,
        "is_syncing": sync_service.is_syncing,
        "sync_interval_minutes": sync_service.sync_interval_minutes,
        "cache_stats": {
            "rewriter_records": len(cache.rewriter_data),
            "adoption_records": len(cache.adoption_data),
            "feedback_records": len(cache.feedback_data),
        },
        "errors": cache.sync_errors[-5:],
    }


@app.get("/api/rewriter")
async def get_rewriter_metrics():
    metrics_service = app.state.metrics_service
    cache = app.state.cache

    metrics = metrics_service.calculate_rewriter_metrics()

    metrics["metadata"] = {
        "generatedAt": datetime.now().isoformat(),
        "lastSync": cache.last_sync_timestamp.isoformat() if cache.last_sync_timestamp else None,
        "dataSource": "cosmos_staging",
        "recordCount": len(cache.rewriter_data),
    }

    return metrics


@app.get("/api/adoption")
async def get_adoption_metrics():
    metrics_service = app.state.metrics_service
    cache = app.state.cache

    metrics = metrics_service.calculate_adoption_metrics()

    metrics["metadata"] = {
        "generatedAt": datetime.now().isoformat(),
        "lastSync": cache.last_sync_timestamp.isoformat() if cache.last_sync_timestamp else None,
        "dataSource": "cosmos_production",
        "recordCount": len(cache.adoption_data),
    }

    return metrics


@app.get("/api/feedback")
async def get_feedback_metrics():
    metrics_service = app.state.metrics_service
    cache = app.state.cache

    metrics = metrics_service.calculate_feedback_metrics()

    metrics["metadata"] = {
        "generatedAt": datetime.now().isoformat(),
        "lastSync": cache.last_sync_timestamp.isoformat() if cache.last_sync_timestamp else None,
        "dataSource": "cosmos_production",
        "recordCount": len(cache.feedback_data),
    }

    return metrics


@app.post("/api/sync")
async def trigger_sync(full: bool = False):
    sync_service = app.state.sync_service

    if sync_service.is_syncing:
        raise HTTPException(status_code=409, detail="A sync is already in progress. Please wait.")

    try:
        if full:
            result = await sync_service.full_sync()
            sync_type = "full"
        else:
            result = await sync_service.incremental_sync()
            sync_type = "incremental"

        return {
            "success": True,
            "sync_type": sync_type,
            "records_added": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ============================================================================
# STATIC FILES MOUNT + SPA FALLBACK
# ============================================================================
# Must be defined AFTER /api routes so the fallback doesn't swallow them.

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """
    SPA fallback: serve index.html for any non-API route so React Router works
    on refresh/deep links.
    """
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    raise HTTPException(status_code=404, detail="Not Found")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
