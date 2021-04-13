import io
import json
from typing import List

import fleep
from fastapi import File, UploadFile
from pydub import AudioSegment
from vosk import KaldiRecognizer, Model
import aiofiles
import time
import os


class Recognizer:
    def __init__(self, model: Model):
        self._rec = KaldiRecognizer(model, 16000)
        self._type_mapping = {"x-wav": "wav", "mpeg": "mp3", "wav": "wav", "wave": "wav"}

    def __del__(self):
        self._rec = None

    def recognize(self, contents: bytes) -> str:

        if self._rec.AcceptWaveform(contents):
            pass

        return json.loads(self._rec.Result())

    def recognize_wav_from_path(self, wav_path: str) -> str:
        # wav_path = '/home/hans/Downloads/chao-16k-16bit.wav'
        while not os.path.exists(wav_path):
            time.sleep(1)
        # async with aiofiles.open(wav_path, 'rb') as f:
        #     wav = await f.read()
        with open(wav_path, 'rb') as f:
            wav = f.read()
        if self._rec.AcceptWaveform(wav):
            pass
        log_name = wav_path.split('/', -1)[-1].rsplit('.', 1)[0]
        recog_res = json.loads(self._rec.Result())
        with open(f'{os.path.dirname(wav_path)}/{log_name}.json', 'w') as f:
            f.write(json.dumps(recog_res))
        return recog_res

    def format_normalize(self, file: File, type: str = "wav") -> bytes:
        audio = AudioSegment.from_file(file, self._type_mapping[type])
        audio = audio.set_frame_rate(16000)

        buf = io.BytesIO()
        audio.export(buf, format="wav")

        return buf.getvalue()
