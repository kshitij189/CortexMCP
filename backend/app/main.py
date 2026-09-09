"""
FastAPI application entry point.
Configures CORS, lifespan events, and route registration.
"""

import logging
import traceback
from contextlib import contextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.api import api_router

logger = logging.getLogger("cortexmcp")

# Import all models so Base.metadata knows about them
import app.models  # noqa: F401


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="CortexMCP — AI Research Agent",
        description="Autonomous async research & report generation system",
        version="1.0.0",
    )

    # ─── Unhandled error handling ───
    # Starlette's default 500 handler sits *outside* every user middleware, so a
    # crash produces a bare "Internal Server Error" with no CORS headers. The
    # browser then reports it as "blocked by CORS policy" and the real cause is
    # invisible. Registering this before CORSMiddleware puts it *inside* the CORS
    # layer (add_middleware prepends, so the last one added is outermost), which
    # means the JSON response below still gets Access-Control-Allow-Origin.
    @app.middleware("http")
    async def catch_unhandled_errors(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(
                "Unhandled error on %s %s\n%s",
                request.method,
                request.url.path,
                traceback.format_exc(),
            )
            return JSONResponse(
                status_code=500,
                content={"detail": f"{type(exc).__name__}: {exc}"},
            )

    # ─── CORS ───
    origins = settings.cors_origins_list
    allow_credentials = True
    if "*" in origins:
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Routes ───
    app.include_router(api_router)

    # ─── Health Check ───
    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "healthy", "service": "cortexmcp-backend"}

    @app.get("/health/ready", tags=["Health"])
    def health_ready():
        """Readiness check — verifies DB connectivity."""
        from app.database import SessionLocal
        try:
            db = SessionLocal()
            db.execute(Base.metadata.tables["users"].select().limit(1)) if "users" in Base.metadata.tables else None
            db.close()
            return {"status": "ready", "database": "connected"}
        except Exception as e:
            return {"status": "not_ready", "database": str(e)}

    @app.get("/health/redis", tags=["Health"])
    def health_redis():
        """Readiness check — verifies Redis and the Celery broker separately.

        The two use different clients (redis-py directly for pub/sub, kombu for
        the queue), so they can fail independently — most often when Upstash's
        free daily command quota runs out.
        """
        result = {}

        try:
            from app.pubsub.progress import progress_pubsub
            progress_pubsub.redis_client.ping()
            result["redis"] = "connected"
        except Exception as e:
            result["redis"] = f"{type(e).__name__}: {e}"

        try:
            from app.workers.celery_app import celery_app
            conn = celery_app.connection_for_write()
            conn.ensure_connection(max_retries=0, timeout=5)
            conn.release()
            result["celery_broker"] = "connected"
        except Exception as e:
            result["celery_broker"] = f"{type(e).__name__}: {e}"

        healthy = result["redis"] == "connected" and result["celery_broker"] == "connected"
        result["status"] = "ready" if healthy else "not_ready"
        return result

    @app.get("/health/llm", tags=["Health"])
    def health_llm():
        """Reports which models each configured LLM provider actually serves.

        Model ids get retired by providers without notice, which is how report
        generation started failing; this shows the live catalogue so a stale
        GEMINI_MODEL/GROQ_MODEL override is obvious. Never returns key material.
        """
        from app.services.llm_service import llm_service

        result = {"active_provider": llm_service.provider}

        try:
            result["gemini_models"] = llm_service.available_gemini_models()
        except Exception as e:
            result["gemini_models"] = f"{type(e).__name__}: {e}"

        try:
            result["groq_models"] = llm_service.available_groq_models()
        except Exception as e:
            result["groq_models"] = f"{type(e).__name__}: {e}"

        result["configured_overrides"] = {
            "GEMINI_MODEL": llm_service.gemini_model or None,
            "GROQ_MODEL": llm_service.groq_model or None,
        }
        return result

    # ─── Startup: Create tables (dev convenience, Alembic for production) ───
    @app.on_event("startup")
    def on_startup():
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()
