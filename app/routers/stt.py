import time
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from misc import save_upload_file
from models.Recognition import RecognitionModel
from settings import File as file_setting
from vosk import Model

from libs.recognizer import Recognizer

router = APIRouter()


@router.on_event("startup")
async def starup_event():
    router._model = Model("speech_model/esun")


@router.post("/stt/recognize")
async def create_upload_files(
    background_tasks: BackgroundTasks,
    upload_files: List[UploadFile] = File(...),
    save_file: bool = False,
):
    response = dict()
    add.delayfsfd()

    for upload_file in upload_files:
        mime_type, media_type = upload_file.content_type.split("/")
        if "audio" != mime_type:
            response[upload_file.filename] = RecognitionModel(
                error=True,
                error_msg=f"type '{mime_type}' not supported",
            )
            continue

        uniqid = str(uuid.uuid1())

        if save_file:
            # run saving file job async
            background_tasks.add_task(
                save_upload_file,
                upload_file,
                Path(f"{file_setting.upload_file_path_prefix}/{uniqid}.wav"),
            )

        rec = Recognizer(router._model)

        contents = rec.format_normalize(upload_file.file, media_type)
        sentences = rec.recognize(contents)

        response[upload_file.filename] = RecognitionModel(
            data=dict(
                uniqid=uniqid,
                result=sentences.get("result"),
                text=sentences.get("text"),
            ),
        )
    return response
