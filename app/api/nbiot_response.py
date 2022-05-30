# coding=utf-8
import json
import time

from sqlalchemy import func, and_, or_, between, exists

from config import role
from config import DELIVER_WAY
from config import R

from . import api
from .. import db

from datetime import datetime

# 解析器，取出要的資訊
def parser(message):
    # 去除 \r
    message = message.replace('\r', '')

    length = len(message)

    print("len:", length)
    print("content:", message)

    # 依照 topic 來切分， SMSUB: host_uuid/to/gw_id/action/table, "payload"
    message_list = message.split('/')

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
    print("Type:", type(payload))

    return gateway_id, action, table, method, payload

# 主函式
def message_check_monitor():
    # 設定好 redis
    redis_response = "web_response"
    coding = "utf-8"
    print("NB-IoT Monitor Start")

    # 不斷監聽
    while True:
        # print("1")
        time.sleep(0.5)

        # 檢查有幾封接收的訊息(任務)
        receive_queue = R.llen('receive')

        # 若有訊息(任務)要執行
        if receive_queue:
            print("-" * 10)
            print("receive Queue:", redis_response)
            print("-" * 10)

            # 從 Redis 的 Queue 取出第一筆訊息
            message = R.lpop(redis_response).decode(coding)

            # 使用解析器得到資訊
            gateway_id, action, table, method, payload = parser(message)

            record(method="receive", action=action, table=table)

            # 讓無窮迴圈休息，減緩機器負擔、避免過熱
            # (sec.)
            time.sleep(0.2)
            break

    return payload

def record(method, action, table):
    sql_start_time = datetime.now()

    ROLE = "Server"

    try:
        sql = (
            "INSERT INTO `log_list` "
            "(`role`, `type`, `deliver_way`, `action`, `table`, `result`) "
            "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}') "
        ).format(ROLE, method, DELIVER_WAY, action, table, "ok")
        log_result = db.engine.execute(sql)
    except BaseException as n:
        print("Log Fail:", n)

    sql_end_time = datetime.now()
    write_sql_time = sql_end_time - sql_start_time

    # print("Role:", ROLE," Delivery:", DELIVER_WAY)
    print("Method:", method, " Action:", action, " Table:", table)
    print("Write SQL Time:", write_sql_time)

# 當這隻程式為主程式執行時
if __name__ == '__main__':
    message_check_monitor()
