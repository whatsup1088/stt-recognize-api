#!/usr/bin/env python3

import asyncio
import concurrent.futures
import json
import os
from urllib.parse import parse_qs, urlparse

import websockets
from vosk import KaldiRecognizer, Model

from NLU import nlu

vosk_interface = "0.0.0.0"
vosk_port = 2702
vosk_model_path = "../model"

model = Model(vosk_model_path)
pool = concurrent.futures.ThreadPoolExecutor((os.cpu_count() or 1))
loop = asyncio.get_event_loop()


def process_chunk(rec, message):
    if rec.AcceptWaveform(message):
        return rec.Result()

    return rec.PartialResult()

async def recognize(websocket, path):

    rec = None
    phrase_list = None
    sample_rate = 8000
    state = 0

    request_id = parse_qs(urlparse(path).query).get('unique_id', 'unknow')

    if isinstance(request_id, list):
        request_id = request_id[0]

    print(f"request id: {request_id}")

    while True:

        message = await websocket.recv()

        if isinstance(message, str):
            print(f"copy that: {message}")
            continue

        if not rec:
            rec = KaldiRecognizer(model, sample_rate)

        response = await loop.run_in_executor(pool, process_chunk, rec, message)
        res = json.loads(response)

        if res.get("text", False):
            state = nlu.send_action(res.get("text"), state, request_id)
            print(f"{state}, {response}")

        await websocket.send(response)

start_server = websockets.serve(recognize, vosk_interface, vosk_port)

loop.run_until_complete(start_server)
loop.run_forever()
