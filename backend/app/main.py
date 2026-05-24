"""
FastAPI application entry point.
Configures CORS, lifespan events, and route registration.
"""

from contextlib import contextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.api import api_router

# Import all models so Base.metadata knows about them
import app.models  # noqa: F401


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="CortexMCP — AI Research Agent",
        description="Autonomous async research & report generation system",
        version="1.0.0",
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

    # ─── Startup: Create tables (dev convenience, Alembic for production) ───
    @app.on_event("startup")
    def on_startup():
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()
