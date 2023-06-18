from fastapi import APIRouter

from .auth import router as auth_router

routers = APIRouter()
routers.include_router(auth_router)
