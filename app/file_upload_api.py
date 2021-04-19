import uuid
from typing import List
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from misc import save_upload_file
# import redis
from pathlib import Path
from configobj import ConfigObj
import os
import datetime
import json

router = APIRouter()

@router.on_event("startup")
async def starup_event():
    router._cfg = ConfigObj(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini'))

    # router._redis = redis.Redis(host='localhost', port=6379, password='')

@router.post("/stt/upload_wav")
async def upload_wav_api(
    background_tasks: BackgroundTasks,
    upload_files: List[UploadFile] = File(...),
    # save_file: bool = True,
    id: str = 'id_test',
    project: str = '客服質檢',
    source_unit: str = '客服中心',
    c_p_num: str = 'c_p_num',
    c_id: str = 'c_id',
    a_p_num: str = 'a_p_num',
    a_id: str = 'a_id',
    port_id: str = '8616',
):
    # 設定參數
    storage_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), router._cfg['upload']['wav_storage_path'])
    metadata_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), router._cfg['upload']['metadata_path'])
    # 初始化
    response = dict()
    metadata = dict()
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
        # if save_file:
        if True:
            # run saving file job async
            # metadata = dict()
            # with open(f'{metadata_path}/{uniqid}.json', 'w') as f:
                
            save_path = os.path.join(storage_dir_path, f'{uniqid}.wav')
            background_tasks.add_task(
                save_upload_file,
                upload_file,
                Path(save_path),
            )
            metadata['id'] = uniqid
            metadata['source_file_name'] = upload_file.filename
            metadata['project'] = project
            metadata['source_unit'] = source_unit
            metadata['c_p_num'] = c_p_num
            metadata['c_id'] = c_id
            metadata['a_p_num']= a_p_num
            metadata['a_id']= a_id
            metadata['port_id'] = port_id
            metadata['api_version']= '200'
            with open(f'{metadata_path}/{uniqid}.json', 'w') as f:
                f.write(json.dumps(metadata))

        response[upload_file.filename] = uniqid
        # log <filename> <uuid>
    return response
