#!/usr/bin/python
# -*- coding: UTF-8 -*-

from configobj import ConfigObj
import argparse
import operator
import copy
import pandas as pd
import jieba
import os
# from if_stt.code.text_processing.tokenizer import Tokenizer
# 先不斷詞，因為 stt 結果為已斷過詞
# 實作算分的機制

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
            res = self.run_selector(' '.join(ii), display=True)
            selector_ans_list.append(res)
        
        # 比較結果，記錄結果
        right_list = list()
        wrong_list = list()
        reask_list = list()
        legacy_ivr_list = list()

        for i in range(len(test_ans_list)):
            try:
                if len(selector_ans_list[i]) > 1:
                    # 追問
                    log = [' '.join(tok_record[i]), f'{test_ans_list[i]}', f'{selector_ans_list[i]}']
                    reask_list.append(','.join(log))
                elif selector_ans_list[i][0][0].split('_', -1)[1] == '-1':
                    # 傳統 ivr
                    log = [' '.join(tok_record[i]), f'{test_ans_list[i]}', f'{selector_ans_list[i]}']
                    legacy_ivr_list.append(','.join(log))
                elif test_ans_list[i] == selector_ans_list[i][0][0].split('_', -1)[1]:
                    # 答對
                    log = [' '.join(tok_record[i]), f'{test_ans_list[i]}', f'{selector_ans_list[i]}']
                    right_list.append(','.join(log))
                else:
                    # 答錯
                    log = [' '.join(tok_record[i]), f'{test_ans_list[i]}', f'{selector_ans_list[i]}']
                    wrong_list.append(','.join(log))
            except:
                print(selector_ans_list[i])
            # 比較是否包含在最高分項
        # 統計 True False
        print(f'準確度：{len(right_list)/float(len(right_list) + len(wrong_list))} 問題、答對 {len(right_list)} 題、答錯 {len(wrong_list)} 題、需追問 {len(reask_list)} 題 (需追問的不列入準確度計算)')
        print(f'覆蓋率：{(len(right_list) + len(wrong_list) + len(reask_list))/float(len(test_ans_list))}，共 {len(test_ans_list)} 題，等於 (答對題數+答錯題數+追問題數)/總題數')

        with open(os.path.join(os.path.dirname(__file__), 'right_list.txt'), 'w', encoding='utf8') as f:
            f.write('\n'.join(right_list))
        with open(os.path.join(os.path.dirname(__file__), 'wrong_list.txt'), 'w', encoding='utf8') as f:
            f.write('\n'.join(wrong_list))
        with open(os.path.join(os.path.dirname(__file__), 'reask_list.txt'), 'w', encoding='utf8') as f:
            f.write('\n'.join(reask_list))
        with open(os.path.join(os.path.dirname(__file__), 'legacy_ivr_list.txt'), 'w', encoding='utf8') as f:
            f.write('\n'.join(legacy_ivr_list))


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

    # 把關鍵字建分數字典，先 count 每個詞出現在
    def build_keyword_count(self):
        tag_dict = self.cfg['tag']
        keyword_mapping_dict = dict()
        for k, v in tag_dict.items():
            for vv in v:
                if vv not in keyword_mapping_dict.keys():
                    keyword_mapping_dict[vv] = list()
                keyword_mapping_dict[vv].append(k)
        for k, v in keyword_mapping_dict.items():
            keyword_mapping_dict[k] = [1.0/len(set(v)), set(v)]
        return keyword_mapping_dict


    def match_end_point(self, sentence_tag_score: list):
        s_tag_score = sentence_tag_score
        # print(s_tag_score)
        end_point_dict = self.end_point_map_tag
        res = dict()
        for k, v in end_point_dict.items():
            res[k] = 0
            for vv in v:
                # print('vv', vv)
                if vv in s_tag_score.keys():
                    res[k] += s_tag_score[vv]/len(end_point_dict[k])

        # print(res)
        # print('>>>>>')
        return res

    # 關鍵字對應到哪個 tag 的分數
    def get_all_tag_score_in_sentence(self, sentence: str):
        tag_score = dict()
        keyword_mapping_dict = self.keyword_mapping_dict
        # print('0000000', sentence)
        for i in sentence.strip().split(' '):
            # print(i, '......')
            if i in keyword_mapping_dict.keys():
                for tag in keyword_mapping_dict[i][1]:
                    if tag not in tag_score.keys():
                        tag_score[tag] = 0
                    tmp = max([keyword_mapping_dict[i][0] for j in keyword_mapping_dict[i][1]])
                    if tmp > tag_score[tag]:
                        tag_score[tag] = tmp
        # tmp = list()
        # tmp.append(sentence)
        # print(tag_score, ',,,,,,,,,')
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

    def refine_decision(self, sentence, end_point_candidate):
        res = copy.deepcopy(end_point_candidate)
        final_res = dict()
        # print(end_point_candidate)
        # input()
        dist_dict = dict()
        if len(end_point_candidate) == 0:
            return [('ivr_-1', 1.0)]
        for k in end_point_candidate:
            dist_dict[k[0]] = list()
        end_point_dict = self.end_point_map_tag
        keyword_score = self.keyword_mapping_dict
        # print('~~~', res)
        # 只要處理複數個 1 的狀況就好
        if len(res) > 1 and res[0][1] == 1:
        # if len(res) > 1:
            count = 0
            for i in sentence.strip().split(' '):
                if i in keyword_score.keys() and len(keyword_score[i][1]) == 1:
                    for j in dist_dict.keys():
                        # print(end_point_dict[j])
                        # print(keyword_score[i])
                        # input('[[[[[[[')
                        if len(keyword_score[i][1].intersection(end_point_dict[j])) > 0:
                            dist_dict[j].append(count)
                    # 計算 tag 間的平均距離
                count += 1
            for k, v in dist_dict.items():
                if len(v) == 1:
                    # print(f'有問題: {k} {v}\n{sentence}\n{end_point_candidate}')
                    final_res[k] = len(end_point_dict[k])
                    # print(final_res[k])
                    # input('uuuuuu')
                else:
                    final_res[k] = (v[-1]-v[0])/float(len(v))
            # print(final_res)
            # print(']]]]]]]]]]')
            try:
                res = [min(final_res.items(), key=lambda x:x[1])]
            except:
                print(dist_dict)
                print(sentence, end_point_candidate)
                input(',,,,')
            # print(res, '.....')
        return res

    def run_selector(self, sentence: str, display: bool=True):
        s_tag = self.get_all_tag_score_in_sentence(sentence)
        self.tag_score = s_tag
        sorted_end_point_dict = self.match_end_point(s_tag)
        end_point_candidate = self.decide_which_end_point(sorted_end_point_dict)
        res = self.refine_decision(sentence, end_point_candidate)
        if display:
            # print(s_tag)
            # print(sorted_end_point_dict)
            # print(end_point_candidate)
            print(res)
        return res 

    def response_action(self, end_point_list):
        if len(end_point_list) > 1:
            msg = ','.join( 'F_{}'.format(ext[0].split('_')[-1]) for ext in end_point_list) 
        elif len(end_point_list) == 0:
            msg = 'F_-1'
        else:
            msg = 'E_{}'.format(end_point_list[0][0].split('_')[-1]) 
        return msg

    def run_keyword_main_procedure(self, max_re_ask_count: int = -1):
        if max_re_ask_count == -1:
            max_re_ask_count = int(self.cfg['parameters']['retry_count'])
        state = 'start'
        count = 0
        sentence = input('=====================\n==== new session ====\n=====================\niIVR：玉山銀行您好，請問有什麼能為您服務呢？\n顧客：')
        while True:
            if count > max_re_ask_count:
                print('iIVR：抱歉，系統仍無法確認您的需求，將為您轉接專人，請稍候')
            res = self.run_selector(sentence)
            msg, state = slct.response_action(res)
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
    slct = Selector(os.path.join(os.path.dirname(__file__), 'keyword_tag_prototype.txt'))
    slct.eval_performance()
    exit()

    test_sentence = ['我 的 信用卡 丟了 怎麼辦', 
    #                  '我 的 金融卡 掉了 怎麼辦', 
    #                  '我 卡片 丟了 怎麼辦', 
    #                  '我 的 卡 不見 了 怎麼辦', 
    #                  '我 的 ubear 卡 昨天就 找不到 了 怎麼辦', 
    #                  '我 是 醫師卡 的 客戶 目前 卡片 找不到 ㄟ', 
    #                  '我 有 申辦 玉山 的 信用卡 請問 怎麼 預約 去 桃機 阿 網路上 找不到 耶',
    #                  '我 昨天 買 衣服 刷卡 完 之後 黑 那個 我 回家 就 找不到 了',
    #                  '你 有 名字 嗎',
    #                  '我 可以 跟 你 約會 嗎', 
                     '想 請問 信用 額度']
    for i in test_sentence:
        print('顧客：', i)
        res = slct.run_selector(i)
        msg = slct.response_action(res)
        print('iIVR：', msg)
    # while True:
    #     slct.run_keyword_main_procedure()
