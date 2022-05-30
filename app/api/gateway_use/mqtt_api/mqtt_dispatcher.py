# coding=utf-8
# import json
# from datetime import datetime, timedelta

# 顯示 action/target
import mqtt_api.mqtt_topic_display as mqtt_topic_display

# 開關點位
import device.switch_api as switch_api

# 選擇傳輸方式
# import messenger
from messenger import deliver


import device.meter as meter
import device.condition as condition

# import device.config.setting as setting
from device.config.setting import *

# ROLE = setting.ROLE
# DELIVER_WAY = setting.DELIVER_WAY

def control_function(action, target, payload):
    if target == 'node':

        if ROLE == "Gateway":

            device_address = int(payload["device_address"])
            node_num = int(payload["num"])
            node_state = int(payload["state"])

            # 開關點位並回傳狀態
            switch_status = switch_api.switch_node(device_address=device_address,
                                                   node_num=node_num, state=node_state)

            sql = (
                "UPDATE `node_list` SET `state`='{}' "
                "WHERE `device_address`='{}' AND `num`='{}' "
            ).format(node_state, device_address, node_num)
            result = dbh.execute(sql)

        elif ROLE == "Server":

            node_id = int(payload["node_id"])
            node_state = int(payload["state"])

            sql = (
                "UPDATE `node_list` SET `state`='{}' "
                "WHERE `node_id`='{}'"
            ).format(node_state, node_id)
            result = dbh.execute(sql)

    elif target == 'group':

        if ROLE == "Gateway":
            group_num = int(payload["num"])
            group_state = int(payload["state"])

            # 開關群組
            switch_status = switch_api.switch_group(
                group_num=group_num, state=group_state)

            # print("Switch Status:", switch_status)

            # 選取對應群組資訊
            sql = (
                "SELECT `group_id` FROM `group_list` "
                "WHERE `num`='{}' "
            ).format(group_num)
            query_results = dbh.query(sql)

            # 為了提取 group_id
            for data in query_results:
                group_id = data["group_id"]

            # 更新群組資訊
            sql = (
                "UPDATE `group_list` SET `state`='{}' "
                "WHERE `num`='{}' "
            ).format(group_state, group_num)
            result = dbh.execute(sql)

            # 從 group_node_list 抓取對應 group_id 底下的 node_id & node_state
            # 更新 node_list 對應 node_id 的 node_state
            sql = (
                "UPDATE node_list NL, "
                "(SELECT node_id "
                "FROM group_node_list "
                "WHERE group_id = '{}' ) AS GNL "
                "SET NL.state = '{}' "
                "WHERE GNL.node_id = NL.id "
            ).format(group_id, group_state)
            result = dbh.execute(sql)

        elif ROLE == "Server":
            group_id = int(payload["group_id"])
            group_state = int(payload["state"])

            sql = (
                "UPDATE `group_list` SET `state`='{}' "
                "WHERE `group_id`='{}' "
            ).format(group_state, group_id)
            result = dbh.execute(sql)

            # 從 group_node_list 抓取對應 group_id 底下的 node_id & node_state
            # 更新 node_list 對應 node_id 的 node_state
            sql = (
                "UPDATE node_list NL, "
                "(SELECT node_id "
                "FROM group_node_list "
                "WHERE group_id = '{}' ) AS GNL "
                "SET NL.state = '{}' "
                "WHERE GNL.node_id = NL.id "
            ).format(group_id, group_state)
            result = dbh.execute(sql)

    elif target == 'scene':

        if ROLE == "Gateway":
            scene_num = int(payload["num"])

            # 開關場景
            switch_status = switch_api.switch_scene(scene_num=scene_num)

            # 取出 scene_id
            sql = (
                "SELECT `scene_id` FROM `scene_list` "
                "WHERE `num`='{}' "
            ).format(scene_num)
            query_results = dbh.query(sql)

            for data in query_results:
                scene_id = data["scene_id"]

            # 從 scene_node_list 抓取對應 scene_id 底下的 node_id & tate
            # 更新 node_list 對應 node_id 的 state
            sql = (
                "UPDATE node_list NL, "
                "(SELECT node_id, node_state "
                "FROM scene_node_list "
                "WHERE scene_id = '{}' ) AS SNL "
                "SET NL.state = SNL.node_state "
                "WHERE SNL.node_id = NL.id "
            ).format(scene_id)
            result = dbh.execute(sql)

        elif ROLE == "Server":
            scene_id = int(payload["scene_id"])

            # 從 scene_node_list 抓取對應 scene_id 底下的 node_id & tate
            # 更新 node_list 對應 node_id 的 state
            sql = (
                "UPDATE node_list NL, "
                "(SELECT node_id, node_state "
                "FROM scene_node_list "
                "WHERE scene_id = '{}' ) AS SNL "
                "SET NL.state = SNL.node_state "
                "WHERE SNL.node_id = NL.id "
            ).format(scene_id)
            result = dbh.execute(sql)

    # SQL execute result: "ok"/"fail"
    return result


def insert_function(action, target, payload):
    target += "_list"
    sql = "INSERT INTO `{}`(".format(target)
    i = 0
    for key in payload.keys():
        i += 1
        sql += " `{}`".format(key)
        if i != len(payload):
            sql += ","
    sql += ") VALUES ("
    i = 0
    for value in payload.values():
        i += 1
        sql += " '{}'".format(value)
        if i != len(payload):
            sql += ","
    sql += ")"

    print(sql)
    result = dbh.execute(sql)

    return result


def update_function(action, target, payload):

    if ROLE == "Gateway" and target == "unload_group":
        result = unload_exception(payload)
    else:
        target += "_list"
        sql = "UPDATE `{}` SET ".format(target)
        i = 0

        column = payload.get("column")

        for key, value in column.items():
            i += 1
            # 判別是 None 寫入 NULL
            if value == None:
                sql += " `{}`= NULL".format(key)
            else:
                sql += " `{}`= '{}'".format(key, value)

            if i == (len(column)):
                break
            elif i != (len(column)):
                sql += ","

        sql += " WHERE "
        where = payload.get("where")
        i = 0
        for key, value in where.items():
            sql += " `{}`= '{}'".format(key, value)
            i += 1
            if i != len(where):
                sql += " AND "

        print(sql)
        result = dbh.execute(sql)
    return result


def unload_exception(payload):

    unload_group_state = payload["column"].get("unload_group_state")
    state = payload["column"].get("state")
    unload_group_id = payload["where"].get("unload_group_id")

    if unload_group_id > 0:
        switch_group_num = unload_group_id - 1

    cond = condition.Condition()

    # 手動賦歸
    if unload_group_state == 1:
        result = meter.Meter(cond).switch_group(
            group_num=switch_group_num, status=state)
    # 手動卸載
    elif unload_group_state == 2:
        result = meter.Meter(cond).switch_group(
            group_num=switch_group_num, status=state)
    # 自動模式
    else:
        result = "ok"

    if result:
        command_result = "ok"
    else:
        command_result = "fail"

    return command_result


def delete_function(action, target, payload):
    target += "_list"
    sql = "DELETE FROM `{}` WHERE".format(target)
    i = 0
    for key, value in payload.items():
        sql += " `{}`= '{}'".format(key, value)
        i += 1
        if i != len(payload):
            sql += " AND "

    print(sql)
    result = dbh.execute(sql)

    return result


# 分配任務
def dispatch(action, target, payload, gateway_id):

    payload = add_gateway_id(action=action, gateway_id=gateway_id, payload=payload)

    try:

        if action == "control":
            result = control_function(action, target, payload)
        elif action == "insert":
            result = insert_function(action, target, payload)
        elif action == "update":
            result = update_function(action, target, payload)
        elif action == "delete":
            result = delete_function(action, target, payload)

    except BaseException as n:
        result = "fail"
        print("Fail:", n)

    return result


def main_processing(gateway_id, action, target, payload, method):
    # 處理訊息，開始時間點
    start_time = datetime.now()

    # 顯示主題
    mqtt_topic_display.display(action, target)

    # 新增 gateway_id 到 payload
    gateway_id = read_gateway_id(mac_address=gateway_id)

    # 從 str 型態轉 dict 型態(loads)
    payload = json.loads(payload)


    if method == "request":
        # 分配任務，回傳執行 SQL 語法結果
        result = dispatch(action=action, target=target,
                          payload=payload, gateway_id=gateway_id)

        # 回傳訊息，從 dict 型態轉 str 型態
        payload = json.dumps({
            "state": result,
        })

        # 將訊息交付給郵差
        deliver(deliver_way=DELIVER_WAY, action=action,
                target=target, payload=payload)

    elif method == "response":

        # 接收到 response 不做處理，避免回傳
        if DELIVER_WAY == "NB-IoT":
            pass
        else:
            pass

    else:
        result = "ok"
        payload = json.dumps({
            "state": result,
        })
        deliver(deliver_way=DELIVER_WAY, action=action,
                target=target, payload=payload)

    # 處理訊息，結束時間點
    end_time = datetime.now()
    spend_time = end_time - start_time
    print("Spend Time:", spend_time)


def add_gateway_id(action, gateway_id, payload):
    if action == "update":
        payload["where"].setdefault('gateway_id', gateway_id)
    else:
        payload.setdefault("gateway_id", gateway_id)

    return payload


def read_gateway_id(mac_address):
    sql = (
        "SELECT `id` "
        "FROM `gateway_list` "
        " WHERE `mac_address` = '{}' "
    ).format(mac_address)

    query_results = dbh.query(sql)

    for data in query_results:
        gateway_id = data['id']

    return gateway_id


def log_record(method, action, target, result):
    try:
        sql = (
            "INSERT INTO `log_list` "
            "(`role`, `type`, `deliver_way`, `action`, `target`, `result`) "
            "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}') "
        ).format(ROLE, method, DELIVER_WAY, action, target, result)
        log_result = dbh.execute(sql)
    except BaseException as n:
        print("Log Fail:", n)

    return log_result