#!/usr/bin/env python3

import asyncio
import concurrent.futures
from datetime import datetime
import json
import logging
import os
import time
from urllib.parse import parse_qs, urlparse
import uuid

import redis
from vosk import KaldiRecognizer, Model
import websockets

from NLU import ivr_selector

vosk_interface = "0.0.0.0"
vosk_port = 2702
vosk_model_path = "data/model"

model = Model(vosk_model_path)
pool = concurrent.futures.ThreadPoolExecutor((os.cpu_count() or 1))
loop = asyncio.get_event_loop()

slct = ivr_selector.Selector('./NLU/keyword_tag_prototype.txt')


def save_to_redis(request_id, nlu_rslt):
    r = redis.StrictRedis(host="192.168.8.166", port=6379, db=0, password='crv1313', decode_responses=True)
    r.rpush(request_id, nlu_rslt)
    r.expire(request_id, 2*3600)


def set_log():
    logging.basicConfig(filename='./log/stt_'+str(datetime.now().strftime('%Y%m%d'))+'.log',
                        datefmt='%Y%m%d %H:%M:%S',
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO)


def process_chunk(rec, message):
    if rec.AcceptWaveform(message):
        return rec.Result()

    return rec.PartialResult()

async def recognize(websocket, path):

    msg_time_list = []
    log_record = {}

    rec = None
    sample_rate = 16000

    request_id = parse_qs(urlparse(path).query).get('unique_id', 'unknow')

    if isinstance(request_id, list):
        request_id = request_id[0]
    
    print(f"request id: {request_id}")
    log_record['unique_id'] = request_id

    while True:
        try:
            message = await websocket.recv()
            msg_time_list.append(time.time())
            if isinstance(message, str):
                print(f"copy that: {message}")
                continue

            if not rec:
                rec = KaldiRecognizer(model, sample_rate)

            response = await loop.run_in_executor(pool, process_chunk, rec, message)
            res = json.loads(response)
            
            if res.get("text", False):
                recognize_end_time = time.time()
                log_record['recognize_end'] = time.ctime(recognize_end_time)
                log_record['sentence_start'] = time.ctime(msg_time_list[0])
                log_record['sentence_end'] = time.ctime(msg_time_list[-1])
                log_record['sentence_time_duration'] = msg_time_list[-1] - msg_time_list[0]
                log_record['recognize_time_duration'] = recognize_end_time - msg_time_list[-1]         
                log_record['stt_result'] = res.get("text")
                log_record['audio_file_id'] = '{}_{}_{}'.format(time.strftime("%Y-%m-%d", time.gmtime()), 
                                                                request_id, str(uuid.uuid1()))
                logging.info(log_record)
                msg_time_list = []
                
                meta = {'unique_id':request_id, 'voice_id':''}
                nlu_rslt = slct.run_selector(res.get("text"), meta)
                msg = slct.response_action(nlu_rslt)
                # save_to_redis(request_id, msg)
                print(f"{msg}, {response}")

            await websocket.send(response)
        except Exception as e:
            logging.error(e) 

if __name__=='__main__':      
    set_log()
    start_server = websockets.serve(recognize, vosk_interface, vosk_port)

    loop.run_until_complete(start_server)
    loop.run_forever()
