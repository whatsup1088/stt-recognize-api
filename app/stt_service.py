from fastapi import BackgroundTasks
import os
import redis
from libs.recognizer import Recognizer
import time
from models.Recognition import RecognitionModel
from vosk import Model
from configobj import ConfigObj
from utils import FileManager as fm
from utils import UtcTime
import json
from datetime import timezone

def recognize_pooling_srv():
    # 導入設定
    cfg = ConfigObj(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'offline_stt_api_config.ini'))
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['stt']['model_path'])
    wav_storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['upload']['wav_storage_path'])
    wav_path_after_stt = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['stt']['wav_path_after_stt'])
    metadata_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['upload']['metadata_path'])
    op_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['log']['log_storage_path'])
    stt_result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cfg['stt']['stt_res_storage_path'])
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
            log_name = i.split('/', -1)[-1].rsplit('.', 1)[0]
            i_metadata_path = f'{metadata_path}/{log_name}.json'
            if not os.path.isfile(i_metadata_path):
                print(f'[請檢查] metadata 檔案不存在，wav 路徑為 {i}，忽略此檔辨識')
                continue
            t_start = UtcTime.get_current_utc_time()
            print(f'[開始辨識] 於 {t_start} 辨識 {i}')
            sentence = rec.recognize_wav_from_path(i)
            t_end = UtcTime.get_current_utc_time()
            with open(i_metadata_path, 'r') as f:
                metadata = json.load(f)
            # 寫結果，metadata 部份塞進來
            sentence.update(metadata)
            # 寫結果，辨識結果部份
            sentence['key'] = log_name
            sentence['recog_start_time'] = t_start
            sentence['recog_end_time'] = t_end
            sentence['recog_time'] = t_end - t_start
            sentence['time_zone'] = str(timezone.utc)
            sentence['am_version'] = model_path.rsplit('/', 1)[-1]
            sentence['lm_version'] = model_path.rsplit('/', 1)[-1]
            sentence['hostname'] = 'stt_test'
            with open(f'{stt_result_path}/{log_name}.json', 'w') as f:
                f.write(json.dumps(sentence))
            # print(sentence)
            print(f'[辨識完成] {t_end} ：{sentence["text"]}，共花費 {t_end - t_start} 秒')
            # 刪掉 metadata 檔案
            os.remove(i_metadata_path)
            # 辨識完的 wav 要搬家
            os.rename(i, os.path.join(wav_path_after_stt, i.rsplit("/", 1)[-1]))

if __name__ == '__main__':
    recognize_pooling_srv()
