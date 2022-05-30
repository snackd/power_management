# coding=utf-8
# import time
# import json
# import redis
# from datetime import datetime

import mqtt_api.mqtt_dispatcher as mqtt_dispatcher

from device.config.setting import *

# import device.config.setting as setting
# from .device.config.setting import *

# 連接資料庫
# dbh = setting.sql_connect

# ROLE = setting.ROLE
# DELIVER_WAY = setting.DELIVER_WAY

# 主函式
def message_check_monitor():
    # 設定好 redis
    # r = redis.Redis('localhost')
    # redis_receive = "receive"
    # redis_response = "response"
    # coding = "utf-8"
    print("NB-IoT Monitor Start")

    # 不斷監聽
    while True:

        # 減少負荷、避免過熱
        time.sleep(0.2) # (sec.)

        # 檢查有幾封接收的訊息(任務)
        receive_queue = R.llen(redis_receive)
        response_queue = R.llen(redis_response)

        # 若有訊息(任務)要執行
        if receive_queue:
            print("-" * 10)
            print("receive Queue:", receive_queue)
            print("-" * 10)

            # 從 Redis 的 Queue 取出第一筆訊息
            message = R.lpop(redis_receive).decode(coding)

            # 使用解析器得到資訊
            gateway_id, action, table, method, payload = parser(message)

            record(method="receive", action=action, table=table)

            # 分配任務
            mqtt_dispatcher.main_processing(gateway_id=gateway_id, action=action, table=table, payload=payload, method=method)

        elif response_queue:
            print("response Queue:", response_queue)
            message = R.lpop(redis_response).decode(coding)

            #  使用解析器得到資訊
            action, table, method, payload = parser_response(message)

            # record(method="receive", action=action, table=table)

            # redis_record(method="receive", action=action, table=table)

# def redis_record(method, action, table):
#     redis_time = time.time()
#     str_time = str(redis_time)
#     redis_content = action + '/' + table + '/' + str_time
#     R.rpush("transmit_receive", redis_content)

def record(method, action, table):
    sql_start_time = datetime.now()

    try:
        sql = (
            "INSERT INTO `log_list` "
            "(`role`, `type`, `deliver_way`, `action`, `table`, `result`) "
            "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}') "
        ).format(ROLE, method, DELIVER_WAY, action, table, "ok")
        log_result = dbh.execute(sql)
    except BaseException as n:
        print("Log Fail:", n)

    sql_end_time = datetime.now()
    write_sql_time = sql_end_time - sql_start_time

    # print("Role:", ROLE," Delivery:", DELIVER_WAY)
    print("Method:", method, " Action:", action, " Table:", table)
    print("Write SQL Time:", write_sql_time)


# 解析器，取出要的資訊
def parser(message):
    # 去除 \r
    message = message.replace('\r', '')

    length = len(message)

    print("len:", length)
    print("content:", message)

    # 依照 topic 來切分， SMSUB: host_uuid/to/gw_id/action/table, "payload"
    message_list = message.split('/')

    print("Message List:", message_list)
    print("Message List Len:", len(message_list))

    # get gateway_id
    gateway_id = message_list[-4]

    # get action
    action = message_list[-3]

    # get table
    table = message_list[-2]

    print("Gateway id:", gateway_id)
    print("action:", action)
    print("table:", table)

    # resquest,"payload"
    last_list = message_list[-1].split('"', 1)

    # method，request/response
    method = last_list[0]
    payload = last_list[-1]

    # 去除 ,"  最後 "
    payload = payload[2:-1]
    print("Payload:", payload)
    print("Type:",type(payload))

    return gateway_id, action, table, method, payload


# 解析器，取出要的資訊
def parser_response(message):
    # 去除 \r
    message = message.replace('\r', '')

    length = len(message)

    print("len:", length)
    print("content:", message)

    # 依照 topic 來切分， SMSUB: host_uuid/to/gw_id/action/table, "payload"
    message_list = message.split('/')

    print("Message List:", message_list)
    print("Message List Len:", len(message_list))

    # get action
    action = message_list[-3]

    # get table
    table = message_list[-2]

    print("action:", action)
    print("table:", table)

    # resquest,"payload"
    last_list = message_list[-1].split('"', 1)

    # method，request/response
    method = last_list[0]
    payload = last_list[-1]

    # 去除 ,"  最後 "
    payload = payload[2:-1]
    print("Payload:", payload)
    print("Type:", type(payload))

    return action, table, method, payload


# 從 str 型態轉 dict 型態(loads)
# payload = json.loads(payload)

# 回傳訊息，從 dict 型態轉 str 型態
# payload = json.dumps(payload)


# 當這隻程式為主程式執行時
if __name__ == '__main__':
    message_check_monitor()
