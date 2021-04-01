#!/usr/bin/python
# -*- coding: UTF-8 -*-

import argparse
import ast
import copy
from collections import Counter
from datetime import datetime
import logging
import operator
import os
import time

from configobj import ConfigObj
import jieba
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import confusion_matrix

# from if_stt.code.text_processing.tokenizer import Tokenizer
# 先不斷詞，因為 stt 結果為已斷過詞
# 實作算分的機制

logging.basicConfig(filename='./log/nlu_'+str(datetime.now().strftime('%Y%m%d'))+'.log',
                    datefmt='%Y%m%d %H:%M:%S',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO)

log_record = {}


class Selector:
    def __init__(self, cfg_path: str):
        self.cfg = ConfigObj(cfg_path)
        self.process_cfg()
        self.keyword_mapping_dict = self.build_keyword_count()

    def eval_performance(self):
        # tok = Tokenizer('lm_config.ini')
        jieba_main_dict_path = os.path.join(os.path.dirname(__file__), 'jieba.5.txt')
        jieba_user_dict_path = os.path.join(os.path.dirname(__file__), '__UserDict.txt')
        jieba.set_dictionary(jieba_main_dict_path)
        jieba.load_userdict(jieba_user_dict_path)

        testing_data = self.load_pkl()

        test_q_list = list()
        test_ans_list = list()

        for i in testing_data:
            if len(str(i[0])) <= 0:
                continue
            test_q_list.append(str(i[0]))
            test_ans_list.append(str(i[1]))
        # 測試部分資料
        # test_q_list = test_q_list[-3:-2]
        # test_ans_list = test_ans_list[-3:-2]
        # print(test_q_list)
        # print(test_ans_list)

        selector_ans_list = list()
        tok_record = list()
        for i in test_q_list:
            try:
                ii = list(jieba.cut(i.lower(), HMM=False))
                tok_record.append(ii)
            except:
                print('====', i)
                input('????')
            res = self.run_selector(' '.join(ii), display=False)
            selector_ans_list.append(res)
        
        # 比較結果，記錄結果
        right_list = list()
        wrong_list = list()
        reask_list = list()
        legacy_ivr_list = list()

        for i in range(len(test_ans_list)):
            if not isinstance(selector_ans_list[i], list):
                print(f'{i}, {test_ans_list[i]} {test_q_list[i]} {tok_record[i]}')
                print('----------', selector_ans_list[i])
                input('>>>>>')
            elif len(selector_ans_list[i]) > 1:
                # 追問
                log = [' '.join(tok_record[i]), f'{test_ans_list[i]}', f'{selector_ans_list[i]}']
                reask_list.append(log)
            elif selector_ans_list[i][0][0].split('_', -1)[1] == '-1':
                # 傳統 ivr
                log = [' '.join(tok_record[i]), f'{test_ans_list[i]}', f'{selector_ans_list[i]}']
                legacy_ivr_list.append(log)
            elif test_ans_list[i] == selector_ans_list[i][0][0].split('_', -1)[1]:
                # 答對
                log = [' '.join(tok_record[i]), f'{test_ans_list[i]}', f'{selector_ans_list[i]}']
                right_list.append(log)
            else:
                # 答錯
                log = [' '.join(tok_record[i]), f'{test_ans_list[i]}', f'{selector_ans_list[i]}']
                wrong_list.append(log)
            # 比較是否包含在最高分項
        # 統計 True False
        print(f'準確度：{len(right_list)/float(len(right_list) + len(wrong_list))} 問題、答對 {len(right_list)} 題、答錯 {len(wrong_list)} 題、需追問 {len(reask_list)} 題 (需追問的不列入準確度計算)')
        print(f'覆蓋率：{(len(right_list) + len(wrong_list) + len(reask_list))/float(len(test_ans_list))} = {(len(right_list) + len(wrong_list) + len(reask_list))}/{len(test_ans_list)} = (答對題數+答錯題數+追問題數)/總題數')

        with open(os.path.join(os.path.dirname(__file__), 'right_list.txt'), 'w', encoding='utf8') as f:
            f.write('\n'.join([','.join(i) for i in right_list]))
        with open(os.path.join(os.path.dirname(__file__), 'wrong_list.txt'), 'w', encoding='utf8') as f:
            f.write('\n'.join([','.join(i) for i in wrong_list]))
        with open(os.path.join(os.path.dirname(__file__), 'reask_list.txt'), 'w', encoding='utf8') as f:
            f.write('\n'.join([','.join(i) for i in reask_list]))
        with open(os.path.join(os.path.dirname(__file__), 'legacy_ivr_list.txt'), 'w', encoding='utf8') as f:
            f.write('\n'.join([','.join(i) for i in legacy_ivr_list]))

        self.make_confusion_matrix(right_list, wrong_list, reask_list, legacy_ivr_list)

    def make_confusion_matrix(self, right_list: list, wrong_list: list, reask_list: list, legacy_ivr_list: list):
        # 這邊實作更詳細的 report，分析 wrong_list，先統計各 ivr 分錯的
        # to-do 畫出 confusion matrix
        # 每個 list 裡面的元素長這樣 ['消費 限額', '111', "[('ivr_1121_5', 0.6666666666666666)]"]
        y_true = [ x[1] for x in right_list ] + [ x[1] for x in wrong_list ] + [ x[1] for x in legacy_ivr_list ]
        y_pred = [ ast.literal_eval(x[2])[0][0].split('_')[1] for x in right_list ] +[ ast.literal_eval(x[2])[0][0].split('_')[1] for x in wrong_list ] +[ ast.literal_eval(x[2])[0][0].split('_')[1] for x in legacy_ivr_list ]
        labels = list(set(y_true))
        cf_matrix = confusion_matrix(y_true, y_pred, labels=labels)

        plt.figure(figsize=(16, 16))
        sns.heatmap(cf_matrix, annot=True, xticklabels=labels, yticklabels=labels)
        plt.xlabel("y pred")
        plt.ylabel("y true") 
        plt.savefig("cf_matrix.png")
        plt.show()
        pass

    def load_pkl(self):
        self.data = pd.read_pickle(os.path.join(os.path.dirname(__file__), 'ivr_cust_q.pkl'))
        tmp = self.data[['cust_q', 'ivr_no']]
        tmp_list = tmp.values.tolist()
        return tmp_list
        # with open('testing_data.txt', 'w', encoding='utf8') as f:
        #     for i in tmp_list:
        #         for j in i:
        #             f.write(str(j))
        #             f.write(',')
        #         f.write('\n')

    def process_cfg(self):
        self.end_point_map_tag = dict()
        self.end_point_content = dict()
        for k, v in self.cfg['end_point'].items():
            self.end_point_map_tag[k] = set(v[1:])
            self.end_point_content[k] = v[0]
            # self.cfg['end_point'][k] = set(v[1:])

    # 把關鍵字建分數字典，先 count 每個詞出現在幾個 end_point 裡面
    def build_keyword_count(self):
        tag_dict = self.cfg['tag']
        # print(tag_dict['doubt'])
        # input('sssss')
        keyword_mapping_dict = dict()
        # for k, v in tag_dict.items():
        #     if not isinstance(v, list):
        #         print(v)
        #         tag_dict[k] = list(v)
        for k, v in tag_dict.items():
            for vv in v:
                if vv not in keyword_mapping_dict.keys():
                    keyword_mapping_dict[vv] = list()
                keyword_mapping_dict[vv].append(k)
        for k, v in keyword_mapping_dict.items():
            keyword_mapping_dict[k] = [1.0/len(set(v)), set(v)]
            # keyword_mapping_dict[k] = [1.0, set(v)]
        # print(keyword_mapping_dict['卡'])
        return keyword_mapping_dict


    def match_end_point(self, sentence_tag_score: list):
        s_tag_score = sentence_tag_score
        end_point_dict = self.end_point_map_tag
        res = dict()
        for k, v in end_point_dict.items():
            res[k] = 0
            for vv in v:
                if vv in s_tag_score.keys():
                    res[k] += s_tag_score[vv]/len(end_point_dict[k])
        return res

    # 關鍵字對應到哪個 tag 的分數
    def get_all_tag_score_in_sentence(self, sentence: str):
        tag_score = dict()
        keyword_mapping_dict = self.keyword_mapping_dict
        for i in sentence.strip().split(' '):
            if i in keyword_mapping_dict.keys():
                for tag in keyword_mapping_dict[i][1]:
                    if tag not in tag_score.keys():
                        tag_score[tag] = 0
                    tmp = max([keyword_mapping_dict[i][0] for j in keyword_mapping_dict[i][1]])
                    if tmp > tag_score[tag]:
                        tag_score[tag] = tmp
        return tag_score

    def decide_which_end_point(self, end_point_dict: dict):
        end_point_sort = sorted(end_point_dict.items(), key=lambda x:x[1], reverse=True)
        res = list()
        best_score = end_point_sort[0][1]
        if best_score == 0:
            return res
        res.append(end_point_sort[0])
        for i in end_point_sort[1:]:
            if i[1] == best_score:
                res.append(i)
        return res

    def refine_decision(self, sentence: str, end_point_candidate: list):
        # end_point 命名為 ivr_xxx_yyy
        # 這裡得把 xxx 歸類到同一項，確認多個 xxx 是不同的才進行追問

        # 完全沒有關鍵字的，就把 end_point 代號設為 -1
        if len(end_point_candidate) == 0:
            return [('ivr_-1', 1.0)]
        # 表示答案唯一，直接回傳
        elif len(end_point_candidate) == 1:
            return end_point_candidate
        # 到這裡表示 end_point_candidate 的內容有多個
        # 檢查 xxx 是不是全部都同一個

        # print(end_point_candidate, 'ttttt')
        candidate_set = set([i[0].split('_', -1)[1] for i in end_point_candidate])
        # print(candidate_set, 'ttttt')
        # candidate_list = [i[0].split('_', -1)[1] for i in end_point_candidate]
        # counter = Counter(candidate_list)
        # counter_res = sorted(counter.items(), key=lambda item: item[1], reverse=True)
        # print(counter)
        # print(counter_res)
        # input()

        # if len(counter) == 1:
        if len(candidate_set) == 1:
            return [(f'ivr_{list(candidate_set)[0]}', 1.0)]
        
        # elif counter_res[0][1] > counter_res[1][1]:
        #     return [(f'ivr_{counter_res[0][0]}', 1.0)] 

        # 多個 end_point 同時完全滿足的才進行檢查，沒滿的就去追問吧
        if end_point_candidate[0][1] < 1:
            return end_point_candidate

        res = copy.deepcopy(end_point_candidate)
        final_res = dict()
        dist_dict = dict()

        # 到這邊表示有多個 xxx 了
        for k in end_point_candidate:
            dist_dict[k[0]] = list()
        end_point_dict = self.end_point_map_tag
        keyword_score = self.keyword_mapping_dict
        # 只要處理複數個 1 的狀況就好
        if len(res) > 1 and res[0][1] >= 1:
            # tag 多的 end_point 優先，其實可以不用排序，懶得改
            tag_count_list = sorted([(i, len(self.end_point_map_tag[i[0]])) for i in end_point_candidate], key=lambda item: item[1], reverse=True)
            # prune 掉比較短的
            pruned_candidate_list = [tag_count_list[0]]
            for i in tag_count_list[1:]:
                if i[1] == tag_count_list[0][1]:
                    pruned_candidate_list.append(i)
            # 檢查是不是同一個分機
            pruned_candidate_set = set([i[0][0].split('_', -1)[1] for i in pruned_candidate_list])
            if len(pruned_candidate_set) == 1:
                return [(f'ivr_{list(pruned_candidate_set)[0]}', 1.0)]
            count = 0
            for i in sentence.strip().split(' '):
                if i in keyword_score.keys() and len(keyword_score[i][1]) == 1:
                    for j in dist_dict.keys():
                        if len(keyword_score[i][1].intersection(end_point_dict[j])) > 0:
                            dist_dict[j].append(count)
                    # 計算 tag 間的平均距離
                count += 1
            for k, v in dist_dict.items():
                if len(v) == 1:
                    final_res[k] = len(end_point_dict[k])
                elif len(v) == 0:
                    final_res[k] = 10
                else:
                    final_res[k] = (v[-1]-v[0])/float(len(v))
            try:
                res = [min(final_res.items(), key=lambda x:x[1])]
            except:
                print(dist_dict)
                print(sentence, end_point_candidate)
                input(',,,,')
        return res

    def run_selector(self, sentence: str, meta: dict={}, display: bool=True):
        try:
            print('||||||| debug ||||||||') if display else None
            log_record['nlu_start'] = time.ctime()
            s_tag = self.get_all_tag_score_in_sentence(sentence)
            print('s_tag: ', s_tag) if display else None
            self.tag_score = s_tag
            sorted_end_point_dict = self.match_end_point(s_tag)
            print('sorted_end_point_dict: ', sorted_end_point_dict) if display else None

            end_point_candidate = self.decide_which_end_point(sorted_end_point_dict)
            print('end_point_candidate: ', end_point_candidate) if display else None

            res = self.refine_decision(sentence, end_point_candidate)
            print('res:', res) if display else None
            log_record['nlu_end'] = time.ctime()
            log_record['nlu_result'] = res
            log_record['nlu_time_diff'] = (datetime.strptime(log_record['nlu_end'], "%c") - 
                                           datetime.strptime(log_record['nlu_start'], "%c")).seconds 

            return res
        except Exception as e:
            logging.error(e) 
        finally:
            log_record['unique_id'] = meta.get('unique_id', 'unknow')
            log_record['voice_id'] = meta.get('voice_id', 'unknow')
            logging.info(log_record)  
            

    def response_action(self, end_point_list):
        end_point_content = self.end_point_content
        if 'reask_content_max_count' in self.cfg.keys():
            reask_content_max_count = self.cfg['reask_content_max_count']
        else:
            reask_content_max_count = 2
        # 這裡要處理 end_point_list 是類似 [(ivr_111_1, 0.8), (ivr_111_2, 0.8), (ivr_118, 0.8)] 的情況
        # 原則上 111 挑一個講就好，另外一個要講 118 的服務內容
        if len(end_point_list) > 1:
            ivr_code_set = set()
            reask_item = list()
            for i in end_point_list:
                if len(reask_item) >= reask_content_max_count:
                    break
                ivr_code = i[0].split('_', -1)[1]
                if ivr_code in ivr_code_set:
                    continue
                else:
                    ivr_code_set.add(ivr_code)
                    reask_item.append(i[0])
            msg_to_user = f'iIVR：不好意思，請問要 '
            for i in list(reask_item):
                new_msg = f'{end_point_content[i]} 還是要 '
                # msg = f'iIVR：不好意思，請問要 {end_point_content[end_point_list[0][0]]} 還是 {end_point_content[end_point_list[1][0]]} 還是什麼服務呢？\n顧客：'
                msg_to_user = ''.join([msg_to_user, new_msg])
            msg_to_user = ''.join([msg_to_user, '其他服務呢？\n顧客：'])
            state = 'multiple'
            msg_to_redis = ','.join( 'F_{}'.format(ext[0].split('_', -1)[1]) for ext in end_point_list)
        # elif len(end_point_list) == 0:
        elif end_point_list[0][0] == 'ivr_-1':
            msg_to_user = f'iIVR：抱歉，系統無法辨識您的需求，將用傳統 IVR 繼續為您服務'
            msg_to_redis = f'F_-1'
            state = 'unknown'
        else:
            if end_point_list[0][0] in end_point_content.keys():
                msg_to_user = f'立刻為您導航至 {end_point_content[end_point_list[0][0]]}'
            else:
                msg_to_user = f'立刻為您導航至 {end_point_list[0][0]} (滿足多重子項目)'
            msg_to_redis = 'E_{}'.format(end_point_list[0][0].split('_')[1])
            state = 'complete'
        return msg_to_user, state, msg_to_redis

    def run_keyword_main_procedure(self, max_re_ask_count: int = -1):
        if max_re_ask_count == -1:
            max_re_ask_count = int(self.cfg['parameters']['retry_count'])
        state = 'start'
        count = 0
        sentence = input('=====================\n==== new session ====\n=====================\niIVR：玉山銀行您好，請問有什麼能為您服務呢？\n顧客：')
        while True:
            if count > max_re_ask_count:
                print('iIVR：抱歉，系統仍無法確認您的需求，將為您轉接專人，請稍候')
            res = self.run_selector(sentence, display=True)
            msg, state, msg_to_redis = slct.response_action(res)
            if state == 'complete':
                print(msg)
                break
            elif state == 'unknown':
                print(msg)
                break
            else:
                sentence = input(msg)
            count += 1
            

if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument("config_path", help="please input an abs path to your config file")
    # args = parser.parse_args()
    # print("Config 檔案路徑：", args.config_path)
    # slct = Selector(args.config_path)
    slct = Selector(os.path.join(os.path.dirname(__file__), 'keyword_tag_v2.txt'))
    '''
    小資料測試模式
    '''
    # test_sentence = ['我 的 信用卡 丟了 怎麼辦', 
    #                  '我 的 金融卡 掉了 怎麼辦', 
    #                  '我 卡片 丟了 怎麼辦', 
    #                  '我 的 卡 不見 了 怎麼辦', 
    #                  '我 的 ubear 卡 昨天就 找不到 了 怎麼辦', 
    #                  '我 是 醫師卡 的 客戶 目前 卡片 找不到 ㄟ', 
    #                  '我 有 申辦 玉山 的 信用卡 請問 怎麼 預約 去 桃機 阿 網路上 找不到 耶',
    #                  '我 昨天 買 衣服 刷卡 完 之後 黑 那個 我 回家 就 找不到 了',
    #                  '你 有 名字 嗎',
    #                  '我 可以 跟 你 約會 嗎', 
    #                  '想 請問 信用 額度']
    # for i in test_sentence:
    #     print('顧客：', i)
    #     res = slct.run_selector(i)
    #     msg = slct.response_action(res)
    #     print('iIVR：', msg)

    '''
    無限問答模式
    '''
    # while True:
    #     slct.run_keyword_main_procedure()

    '''
    完整測試模式
    '''
    slct.eval_performance()
    