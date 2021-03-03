#!/usr/bin/env python3

import asyncio
import concurrent.futures
import json
import os

import websockets
from vosk import KaldiRecognizer, Model
from NLU import nlu

vosk_interface = "0.0.0.0"
vosk_port = 2700
vosk_model_path = "../model"

model = Model(vosk_model_path)
pool = concurrent.futures.ThreadPoolExecutor((os.cpu_count() or 1))
loop = asyncio.get_event_loop()


def process_chunk(rec, message):
    if rec.AcceptWaveform(message):
        return rec.Result(), False

    return rec.PartialResult(), False

async def recognize(websocket, path):

    rec = None
    phrase_list = None
    sample_rate = 16000
    state = 0

    while True:

        message = await websocket.recv()

        if not rec:
            rec = KaldiRecognizer(model, sample_rate)

        response, stop = await loop.run_in_executor(pool, process_chunk, rec, message)
        res = json.loads(response)

        if res.get("text", False):
            state = nlu.send_action(res.get("text"), state)
            print(state)

        await websocket.send(response)

        if stop:
            break

start_server = websockets.serve(recognize, vosk_interface, vosk_port)

loop.run_until_complete(start_server)
loop.run_forever()
