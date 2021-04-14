from fastapi import BackgroundTasks
import os
import redis
from libs.recognizer import Recognizer
import time
from models.Recognition import RecognitionModel
from vosk import Model
from configobj import ConfigObj
from utils import FileManager as fm

def recognize_from_redis():
    # 導入設定
    cfg = ConfigObj('./config.ini')
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['stt']['model_path'])
    wav_storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['upload']['wav_storage_path'])
    wav_path_after_stt = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['stt']['wav_path_after_stt'])
    # 初始化物件
    rec = Recognizer(Model(model_path))
    # 開始主程式囉
    while True:
        # 掃檔、逐一辨識、辨識完搬檔
        wav_list = fm.list_all_file_type_in_dir('\.wav$', wav_storage_path)
        if len(wav_list) <= 0:
            time.sleep(2)
            continue
        wav_list.sort(key=os.path.getctime)
        for i in wav_list:
            t_start = time.time()
            print(f'{t_start} 開始辨識：{i}')
            sentence = rec.recognize_wav_from_path(i)
            t_complete = time.time()
            print(sentence)
            print(f'{t_complete} 辨識完成：{sentence["text"]}，共花費 {t_complete - t_start} 秒')
            # 辨識完的就搬擋
            os.rename(i, os.path.join(wav_path_after_stt, i.rsplit("/", 1)[-1]))

if __name__ == '__main__':
    recognize_from_redis()
