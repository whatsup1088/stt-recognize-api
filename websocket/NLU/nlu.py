import redis


textbook = ''
state = 0
request_id = 'ivr'


def save_to_redis(request_id, nlu_rslt):
    r = redis.StrictRedis(host="192.168.8.166", port=6379, db=0, password='crv1313')
    r.rpush(request_id, nlu_rslt)
    r.expire(request_id, 2*3600)


def in_sentence(keywords, sentence):
    sentence = sentence.replace(' ','')
    for keyword in keywords:
        if keyword in sentence:
            return True
    return False


def send_action(textbook, state):
    if state == -1:
        next_action = 'close'
    
    elif state == 0:
        if in_sentence(['信用卡', '卡', '卡片'], textbook):
            state = 1
            next_action = 'F01'
        if in_sentence(['存款', '貸款', '轉帳'], textbook):
            state = 2
            next_action = 'F02'
        else:
            next_action = 'retry'

    elif state == 1:
        if in_sentence(['帳單', '繳費'], textbook):
            state = 0
            next_action = 'A01'
        if in_sentence(['停卡', '掛失', '開卡'], textbook):
            state = 0
            next_action = 'A02'
        if in_sentence(['卡友貸', '貸款' '刷卡分期'], textbook):
            state = 0
            next_action = 'A03'
        if in_sentence(['紅利', '機場服務兌換', '機場接送', '旅遊保險'], textbook):
            state = 0
            next_action = 'A04'
        if in_sentence(['機場接送'], textbook):
            state = 0
            next_action = 'A05'
        else:
            next_action = 'retry'

    elif state == 2:
        if in_sentence(['帳戶查詢', '傳真'], textbook):
            state = 0
            next_action = 'A06'
        if in_sentence(['轉帳', '定存'], textbook):
            state = 0
            next_action = 'A07'
        if in_sentence(['掛失', '密碼變更'], textbook):
            state = 0
            next_action = 'A08'
        if in_sentence(['貸款'], textbook):
            state = 0
            next_action = 'A09'
        if in_sentence(['簽帳'], textbook):
            state = 0
            next_action = 'A10'
        if in_sentence(['外匯'], textbook):
            state = 0
            next_action = 'A11'
        else:
            next_action = 'retry'
    
    else:
        next_action = 'retry'

    save_to_redis(request_id, next_action)

    return state


if __name__ == "__main__":
    state = 2
    textbook = '我要買外匯'
    rslt = send_action(textbook, state)
    print(rslt)
