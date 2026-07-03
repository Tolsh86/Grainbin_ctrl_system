"""路由聚合器 — 将所有子路由挂载到 /api/v1"""

from fastapi import APIRouter

from app.routers import auth, projects, users, ingest

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(ingest.router)

__all__ = ["api_router"]
