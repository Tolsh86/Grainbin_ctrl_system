"""路由聚合器 — 将所有子路由挂载到 /api/v1"""

from fastapi import APIRouter

from app.routers import auth, projects, users, ingest, dicts

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(ingest.router)
api_router.include_router(dicts.router)

__all__ = ["api_router"]
