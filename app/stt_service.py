from fastapi import BackgroundTasks
import os
import redis
from libs.recognizer import Recognizer
import time
from models.Recognition import RecognitionModel
from vosk import Model
from configobj import ConfigObj


def recognize_from_redis():
    # 導入設定
    cfg = ConfigObj('./config.ini')
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['stt']['model_path'])
    redis_queue_name = cfg['upload']['queue_name']
    redis_host = cfg['redis']['host']
    redis_port = int(cfg['redis']['port'])
    # 初始化物件
    redis_server = redis.Redis(host=redis_host, port=redis_port, password='')
    rec = Recognizer(Model(model_path))
    # 開始主程式囉
    while True:
        wav_path = redis_server.blpop(redis_queue_name)
        wav_path = wav_path[1].decode()
        t_start = time.time()
        print(f'{t_start} 開始辨識：{wav_path}')
        sentence = rec.recognize_wav_from_path(wav_path)
        t_complete = time.time()
        print(f'{t_complete} 辨識完成：{sentence["text"]}，共花費 {t_complete - t_start} 秒')


if __name__ == '__main__':
    recognize_from_redis()
