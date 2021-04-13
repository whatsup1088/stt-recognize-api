import uuid
from typing import List
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from misc import save_upload_file
import redis
from pathlib import Path
from models.Recognition import RecognitionModel
import os

router = APIRouter()
r = redis.Redis(host='localhost', port=6379, password='')

@router.on_event("startup")
async def starup_event():
    pass 

@router.post("/stt/upload_wav")
async def upload_wav_api(
    background_tasks: BackgroundTasks,
    upload_files: List[UploadFile] = File(...),
    save_file: bool = True,
):
    response = dict()
    q = list()
    for upload_file in upload_files:
        mime_type, media_type = upload_file.content_type.split("/")
        if "audio" != mime_type:
            response[upload_file.filename] = RecognitionModel(
                error=True,
                error_msg=f"type '{mime_type}' not supported",
            )
            continue

        uniqid = str(uuid.uuid1())
        # 存進硬碟
        if save_file:
            # run saving file job async
            save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'data/{uniqid}.wav')
            background_tasks.add_task(
                save_upload_file,
                upload_file,
                Path(save_path),
            )
        # 寫 redis
        q.append(save_path)
        r.rpush('saved_wav_path', save_path)
        # rec = Recognizer(router._model)

        # contents = rec.format_normalize(upload_file.file, media_type)
        # # sentences = rec.recognize(contents)
        # print
        # sentences = rec.recognize_wav_from_path('contents')

        response[upload_file.filename] = RecognitionModel(
            data=dict(
                uniqid=uniqid,
                result=dict(),
                text='test',
            ),
        )
    return response
