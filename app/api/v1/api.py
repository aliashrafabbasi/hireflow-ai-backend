from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    health,
    users,
    resume,
    jobs,
    match,
    rpa,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(users.router)
api_router.include_router(resume.router)
api_router.include_router(jobs.router)
api_router.include_router(match.router)
api_router.include_router(rpa.router)