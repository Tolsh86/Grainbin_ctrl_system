"""路由聚合器 — 将所有子路由挂载到 /api/v1"""

from fastapi import APIRouter

from app.routers import auth, projects, users, ingest, dicts, upload, mapping, batch, contracts, reviews

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(ingest.router)
api_router.include_router(dicts.router)
api_router.include_router(upload.router)
api_router.include_router(mapping.router)
api_router.include_router(batch.router)
api_router.include_router(contracts.router)
api_router.include_router(reviews.router)

__all__ = ["api_router"]
