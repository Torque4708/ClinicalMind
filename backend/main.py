import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.database import init_db
from backend.routers import auth, profile, match, chat, trials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init db + trigger initial trial sync."""
    logger.info("Starting ClinicalMind backend...")
    await init_db()
    logger.info("Database initialized.")
    # Trigger initial ETL sync on startup (non-blocking)
    try:
        from backend.tasks.etl_tasks import sync_trials_task
        sync_trials_task.delay()
        logger.info("Initial trial sync task dispatched to Celery.")
    except Exception as e:
        logger.warning(f"Could not dispatch initial sync (Celery may be unavailable): {e}")
    yield
    logger.info("ClinicalMind backend shutting down.")


app = FastAPI(
    title="ClinicalMind API",
    description="AI Clinical Trial Intelligence & Patient Matching Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(match.router)
app.include_router(chat.router)
app.include_router(trials.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ClinicalMind API", "version": "1.0.0"}
