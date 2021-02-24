#!/usr/bin/env python3

import asyncio
import concurrent.futures
import json
import os

import websockets
from vosk import KaldiRecognizer, Model

vosk_interface = "0.0.0.0"
vosk_port = 2700
vosk_model_path = "model/esun"

model = Model(vosk_model_path)
pool = concurrent.futures.ThreadPoolExecutor((os.cpu_count() or 1))
loop = asyncio.get_event_loop()


def process_chunk(rec, message):
    if message == '{"eof" : 1}':
        return rec.FinalResult(), True
    elif rec.AcceptWaveform(message):
        return rec.Result(), False

    return rec.PartialResult(), False


async def recognize(websocket, path):

    rec = None
    phrase_list = None
    sample_rate = 16000

    while True:

        message = await websocket.recv()

        if not rec:
            rec = KaldiRecognizer(model, sample_rate)

        response, stop = await loop.run_in_executor(pool, process_chunk, rec, message)
        await websocket.send(response)
        if stop:
            break


start_server = websockets.serve(recognize, vosk_interface, vosk_port)

loop.run_until_complete(start_server)
loop.run_forever()
