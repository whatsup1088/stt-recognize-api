import io
import json
from typing import List

import fleep
from fastapi import File, UploadFile
from pydub import AudioSegment
from vosk import KaldiRecognizer, Model


class Recognizer:
    def __init__(self, model: Model):
        self._rec = KaldiRecognizer(model, 16000)
        self._tpye_mappimg = {"wav": "wav", "mpeg": "mp3"}

    def __del__(self):
        self._rec = None

    def recognize(self, file: UploadFile, type: str) -> str:
        contents = self.format_normalize(file.file, type)

        if self._rec.AcceptWaveform(contents):
            pass

        return json.loads(self._rec.Result())

    def format_normalize(self, file: File, type: str = "wav") -> List:
        audio = AudioSegment.from_file(file, self._tpye_mappimg[type])
        audio = audio.set_frame_rate(16000)

        buf = buf = io.BytesIO()
        audio.export(buf, format="wav")

        return buf.getvalue()
