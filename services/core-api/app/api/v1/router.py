from fastapi import APIRouter

from app.modules.resumes.router import router as resumes_router
from app.modules.jd.router import router as jd_router

api_router = APIRouter()
api_router.include_router(resumes_router)
api_router.include_router(jd_router)
