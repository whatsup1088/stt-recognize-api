import requests
from flask import Flask, request
from urllib.parse import quote

import redis


app = Flask(__name__)

textbook = ''
state = 0


def save_to_redis(request_id, nlu_rslt):
    r = redis.StrictRedis(host="192.168.8.166", port=6379, db=0, password='crv1313')
    r.set(request_id, nlu_rslt)


def in_sentence(keywords, sentence):
    sentence = sentence.replace(' ','')
    for keyword in keywords:
        if keyword in sentence:
            return True
    return False


def send_action(textbook, state):
    if state == -1:
        return 'close'
    
    if state == 0:
        if in_sentence(['信用卡', '卡', '卡片'], textbook):
            state = 1
            return 'F01'
        if in_sentence(['存款', '貸款', '轉帳'], textbook):
            state = 2
            return 'F02'
        return 'retry'

    if state == 1:
        if in_sentence(['帳單', '繳費'], textbook):
            return 'A01'
        if in_sentence(['停卡', '掛失', '開卡'], textbook):
            return 'A02'
        if in_sentence(['卡友貸', '貸款' '刷卡分期'], textbook):
            return 'A03'
        if in_sentence(['紅利', '機場服務兌換', '機場接送', '旅遊保險'], textbook):
            return 'A04'
        if in_sentence(['機場接送'], textbook):
            return 'A05'
        return 'retry'

    if state == 2:
        if in_sentence(['帳戶查詢', '傳真'], textbook):
            return 'A06'
        if in_sentence(['轉帳', '定存'], textbook):
            return 'A07'
        if in_sentence(['掛失', '密碼變更'], textbook):
            return 'A08'
        if in_sentence(['貸款'], textbook):
            return 'A09'
        if in_sentence(['簽帳'], textbook):
            return 'A10'
        if in_sentence(['外匯'], textbook):
            return 'A11'
        return 'retry'

    return 'retry'


if __name__ == "__main__":
    state = 2
    textbook = '我要買外匯'
    rslt = send_action(textbook, state)
    print(rslt)
