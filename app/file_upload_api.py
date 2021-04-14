import uuid
from typing import List
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from misc import save_upload_file
# import redis
from pathlib import Path
from configobj import ConfigObj
import os

router = APIRouter()

@router.on_event("startup")
async def starup_event():
    router._cfg = ConfigObj('./config.ini')
    # router._redis = redis.Redis(host='localhost', port=6379, password='')

@router.post("/stt/upload_wav")
async def upload_wav_api(
    background_tasks: BackgroundTasks,
    upload_files: List[UploadFile] = File(...),
    save_file: bool = True,
):
    # 設定參數
    # queue_name = router._cfg['upload']['queue_name']
    storage_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), router._cfg['upload']['wav_storage_path'])
    # 初始化
    response = dict()
    # 正式流程開始
    for upload_file in upload_files:
        mime_type, media_type = upload_file.content_type.split("/")
        if "audio" != mime_type:
            response[upload_file.filename] = dict(
                error=True,
                error_msg=f"type '{mime_type}' not supported",
            )
            # log error: not support <mime_type>
            continue

        uniqid = str(uuid.uuid1())
        # 存進硬碟
        if save_file:
            # run saving file job async
            save_path = os.path.join(storage_dir_path, f'{uniqid}.wav')
            background_tasks.add_task(
                save_upload_file,
                upload_file,
                Path(save_path),
            )
        response[uniqid] = upload_file.filename
        # log <filename> <uuid>
    return response
