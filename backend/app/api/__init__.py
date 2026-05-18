"""Router aggregation — registers all API route modules."""

from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.research import router as research_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(research_router)
