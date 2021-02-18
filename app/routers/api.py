from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from routers import docs, stt

router = APIRouter()

router.include_router(docs.router)
router.include_router(stt.router)
