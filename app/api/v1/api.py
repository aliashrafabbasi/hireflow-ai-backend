from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    health,
    users,
    resume,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(resume.router)