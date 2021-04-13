from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from routers import docs, stt
import file_upload_api

router = APIRouter()

router.include_router(docs.router)
router.include_router(stt.router)
router.include_router(file_upload_api.router)
