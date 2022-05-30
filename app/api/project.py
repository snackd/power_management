import json
import datetime

from flask import jsonify, request
from flask import session
from sqlalchemy import func, and_, or_, between, exists

from . import api
from .. import db
from ..models import *

from . import mqtt_talker as mqtttalker

from config import role, G_CONTROL_VALUE_TYPE_LIST
from config import DELIVER_WAY
from config import R

from .log import log_info

from .gateway_use.device import switch_api as switch
# from .gateway_use.device.config.gateway_setting import *
# from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.setting import *

from datetime import datetime


@api.route('/gateway_setting/query', methods=['POST', 'GET'])
def gateway_setting():
    req_p_id = request.args.get('p_id', default="dae", type=str)
    gateway_info = []
    Gateway_data = db.session.query(Gateway).filter(
        Gateway.project_id == req_p_id).all()
    db.session.close()

    for data in Gateway_data:
        gateway_info.append({'gateway_id': data.id, 'uid': data.uid, 'country': data.country,
                             'city': data.city, 'physical_address': data.physical_address, 'gateway_name': data.gateway_name})

    return jsonify(gateway_info), 201


@api.route('/node_control', methods=['POST', 'GET'])
def node_control():
    # web_start_time = datetime.now()
    # print("-"*10)

    node_id = request.form.get('item_id', default=0, type=int)
    # node_state = request.form.get('state', default="", type=str)

    # Server
    node_state = request.form.get('state', default=0, type=int)

    # gateway_uid = request.form.get('gateway_uid', default="", type=str)

    update_node = []
    for_log = ""

    #　選取對應點位資訊
    node_list_sql = "SELECT `nl`.`node_id`, `nl`.`gateway_id`, `nl`.`device_id`, `nl`.`type_id`, `nl`.`name`, " \
                    "`nl`.`device_address`, `nl`.`num`, `nl`.`state`, `gl`.`mac_address` " \
                    "FROM `node_list` AS `nl` " \
                    "INNER JOIN `gateway_list` AS `gl` ON(`nl`.`gateway_id` = `gl`.`id`)" \
                    "WHERE `nl`.`node_id` = {} LIMIT 1".format(node_id)
    node_list_result = db.engine.execute(node_list_sql).fetchall()

    node_type = node_list_result[0][3]
    node_device_address = node_list_result[0][5]
    node_num = node_list_result[0][6]
    # node_gateway_mac = node_list_result[0][8]
    gateway_mac = node_list_result[0][8]

    # node_switch_change = 0 if node_state == "ON" else 100

    # Server
    node_switch_change = 0 if node_state == 100 else 100

    node_value_change = node_state
    update_value = node_value_change if int(
        node_type) in G_CONTROL_VALUE_TYPE_LIST else node_switch_change


    if role == "Gateway":
        if int(node_type) in G_CONTROL_VALUE_TYPE_LIST:
            switch.switch_dimmer(int(node_device_address),
                            int(node_num), update_value)
        else:
            switch.switch_node(int(node_device_address),
                                 int(node_num), update_value)

        payload_dic = {
            'node_id': 1,
            'state': update_value
        }
        # 更新資料庫點位資訊 (點位狀態、ID) [B]
        update_node_sql = "UPDATE `node_list` SET `state` = '{}' WHERE `node_id` = {}".format(
            update_value, node_id)
        update_node_result = db.engine.execute(update_node_sql)
        # 更新資料庫點位資訊 (點位狀態、ID) [E]

    elif role == "Cloud":
        payload_dic = {
            'device_address': node_device_address,
            'num': node_num,
            'state': update_value
        }

    topic = "control/node"

    payload = json.dumps(payload_dic)

    web_start_time = datetime.now()

    if DELIVER_WAY == "Ethernet":
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_mac, topic, payload)
        response = mqtt_talker.start()
    elif DELIVER_WAY == "NB-IoT":
        task_segment = '/'
        method = "request"
        message_segment = '|'
        publish_redis = "publish"
        composition = topic + task_segment + method + message_segment + payload
        R.rpush(publish_redis, composition)
        response = nbiot_talker.message_check_monitor()

    # web_end_time = datetime.now()
    # web_response_time = web_end_time - web_start_time
    # print("Web Response Time:", web_response_time)
    # print("-"*10)

    if response:
        # log_info(node_gateway_mac, "update", "realtime change node state", str(
        #     payload), json.loads(response)['state'], "Cloud")
        response = json.loads(response)
        if role == 'Cloud':
            # 更新資料庫點位資訊 (點位狀態、ID) [B]
            update_node_sql = "UPDATE `node_list` SET `state` = '{}' WHERE `node_id` = {}".format(
                update_value, node_id)
            update_node_result = db.engine.execute(update_node_sql)
            # 更新資料庫點位資訊 (點位狀態、ID) [E]

        return jsonify(response), 201
    else:
        return "Request Timeout", 500


    db.session.commit()
    db.session.close()


@api.route('/group_control', methods=['POST', 'GET'])
def group_control():
    group_id = request.form.get('item_id', default=0, type=int)
    # group_state = request.form.get('state', default="", type=str)
    group_state = request.form.get('state', default=0, type=int)
    # gateway_uid = request.form.get('gateway_uid', default="", type=str)

    switch_type_list = [1, 2]

    update_node = []
    for_log = ""

    # 選取對應群組資訊
    group_list_sql = "SELECT `grl`.`group_id`, `grl`.`gateway_id`, `grl`.`name`, `grl`.`num`, `gl`.`mac_address` " \
                     "FROM `group_list` AS `grl` " \
                     "INNER JOIN `gateway_list` AS `gl` ON(`grl`.`gateway_id` = `gl`.`id`) " \
                     "WHERE `grl`.`group_id` = {} LIMIT 1".format(group_id)

    group_list_result = db.engine.execute(group_list_sql).fetchall()
    gateway_mac = group_list_result[0][4]
    group_num = group_list_result[0][3]

    # group_state_change = 0 if group_state == "ON" else 100

    # Server
    group_state_change = 0 if group_state == 100 else 100

    if role == "Gateway":

        switch.switch_group(int(group_num), group_state_change)
        payload_dic = {
            "group_id": group_id,
            "state": group_state_change
        }
        #  更新資料庫資料 [B]
        update_group_sql = "UPDATE `group_list` SET `state` = '{}' WHERE `group_id` = {}".format(
            group_state_change, group_id)
        update_group_result = db.engine.execute(update_group_sql)

        group_node_list_sql = "SELECT `nl`.`node_id`, `nl`.`gateway_id`, `nl`.`type_id`, `nl`.`name`, `nl`.`device_address`, `nl`.`num` " \
                              "FROM `node_list` AS `nl` " \
                              "INNER JOIN `group_node_list` AS `gnl` ON(`nl`.`node_id` = `gnl`.`node_id` AND `nl`.`gateway_id` = `gnl`.`gateway_id`) " \
                              "WHERE `gnl`.`group_id` = {}".format(group_id)
        group_node_list = db.engine.execute(group_node_list_sql)

        for data in group_node_list:
            node_id = data[0]
            node_type = data[2]
            update_value = group_state_change
            node_update_state_sql = "UPDATE node_list SET state='{}' WHERE node_id={}".format(
                update_value, node_id)
            node_update_state = db.engine.execute(node_update_state_sql)
        #  更新資料庫資料 [E]

    elif role == "Cloud":
        payload_dic = {
            "num": group_num,
            "state": group_state_change
        }

    topic = "control/group"

    payload = json.dumps(payload_dic)

    if DELIVER_WAY == "Ethernet":
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_mac, topic, payload)
        response = mqtt_talker.start()
    elif DELIVER_WAY == "NB-IoT":
        task_segment = '/'
        method = "request"
        message_segment = '|'
        publish_redis = "publish"
        composition = topic + task_segment + method + message_segment + payload
        R.rpush(publish_redis, composition)
        response = nbiot_talker.message_check_monitor()

    if response:
        # log_info(gateway_mac, "update", 'realtime change group state', str(
        #     payload), json.loads(response)['state'], "Cloud")
        if role == "Cloud":
            #  更新資料庫資料 [B]
            update_group_sql = "UPDATE `group_list` SET `state` = '{}' WHERE `group_id` = {}".format(
                group_state_change, group_id)
            update_group_result = db.engine.execute(update_group_sql)

            group_node_list_sql = "SELECT `nl`.`node_id`, `nl`.`gateway_id`, `nl`.`type_id`, `nl`.`name`, `nl`.`device_address`, `nl`.`num` " \
                                  "FROM `node_list` AS `nl` " \
                                  "INNER JOIN `group_node_list` AS `gnl` ON(`nl`.`node_id` = `gnl`.`node_id` AND `nl`.`gateway_id` = `gnl`.`gateway_id`) " \
                                  "WHERE `gnl`.`group_id` = {}".format(group_id)
            group_node_list = db.engine.execute(group_node_list_sql)

            for data in group_node_list:
                node_id = data[0]
                node_type = data[2]
                update_value = group_state_change
                node_update_state_sql = "UPDATE node_list SET state='{}' WHERE node_id={}".format(
                    update_value, node_id)
                node_update_state = db.engine.execute(node_update_state_sql)
            #  更新資料庫資料 [E]
        response = json.loads(response)
        return jsonify(response), 201
    else:
        return "Request Timeout", 500

    db.session.commit()
    db.session.close()


@api.route('/scene_control', methods=['POST', 'GET'])
def scene_control():
    scene_id = request.form.get('item_id', default=0, type=int)
    # 先抓取此場景下的點位資料

    scene_list_sql = "SELECT `sl`.`scene_id`, `sl`.`name`, `sl`.`num`, `gl`.`mac_address` " \
                     "FROM `scene_list` AS `sl` " \
                     "INNER JOIN `gateway_list` AS `gl` ON(`sl`.`gateway_id` = `gl`.`id`) " \
                     "WHERE `sl`.`scene_id` = {} LIMIT 1".format(scene_id)
    scene_list_result = db.engine.execute(scene_list_sql).fetchall()

    scene_number = scene_list_result[0][2]
    gateway_mac = scene_list_result[0][3]

    # snl.node_state
    scene_node_list_sql = "SELECT `nl`.`node_id`, `nl`.`type_id`, `nl`.`name`, `nl`.`device_address`, " \
                          "`nl`.`num`, `snl`.`node_state` " \
                          "FROM `node_list` AS `nl` " \
                          "INNER JOIN `scene_node_list` AS `snl` ON(`nl`.`node_id` = `snl`.`node_id` AND `nl`.`gateway_id` = `snl`.`gateway_id`) " \
                          "WHERE `snl`.`scene_id` = {}".format(scene_id)
    scene_node_list = db.engine.execute(scene_node_list_sql)



    if role == "Gateway":
        switch.switch_scene(int(scene_number))
        payload_dic = {
            "scene_id": scene_id
        }
        #  更新資料庫資料 [B]
        for data in scene_node_list:
            node_id = data[0]
            node_type = data[1]
            update_value = data[5]
            node_update_state_sql = "UPDATE node_list SET state={} WHERE node_id={}".format(
                update_value, node_id)
            node_update_state = db.engine.execute(node_update_state_sql)
        #  更新資料庫資料 [E]

    elif role == "Cloud":
        payload_dic = {
            "num": scene_number
        }

    topic = "control/scene"

    payload = json.dumps(payload_dic)

    if DELIVER_WAY == "Ethernet":
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_mac, topic, payload)
        response = mqtt_talker.start()
    elif DELIVER_WAY == "NB-IoT":
        task_segment = '/'
        method = "request"
        message_segment = '|'
        publish_redis = "publish"
        composition = topic + task_segment + method + message_segment + payload
        R.rpush(publish_redis, composition)
        response = nbiot_talker.message_check_monitor()

    if response:
        # log_info(gateway_mac[0], "update", "realtime change scene setting", str(payload),
        #          json.loads(response)['state'], "Cloud")
        response = json.loads(response)
        if role == 'Cloud':
            #  更新資料庫資料 [B]
            for data in scene_node_list:
                node_id = data[0]
                node_type = data[1]
                update_value = data[5]
                node_update_state_sql = "UPDATE node_list SET state={} WHERE node_id={}".format(
                    update_value, node_id)
                node_update_state = db.engine.execute(node_update_state_sql)
            #  更新資料庫資料 [E]
        return jsonify(response), 201
    else:
        return "Request Timeout", 500


@api.route('/load_area', methods=['POST', 'GET'])
def load_area():
    result = False
    message = ''
    data_array = {}

    try:
        area_id = request.form.get('area_id', default=0, type=int)
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        node_list_sql = "SELECT `dl`.`type_id`, `n`.`node_id`, `n`.`name`, `n`.`num`, `n`.`state` " \
                        "FROM `area_node_list` AS `anl` " \
                        "INNER JOIN `node_list` AS `n` ON(`n`.`node_id` = `anl`.`node_id` AND `n`.`gateway_id` = `anl`.`gateway_id`) " \
                        "INNER JOIN `device_list` AS `dl` ON(`n`.`device_id` = `dl`.`device_id` AND `n`.`gateway_id` = `dl`.`gateway_id`)" \
                        "WHERE `anl`.`area_id` = {} AND `n`.`gateway_id` = {}".format(area_id, gateway_id)
        node_list_object = db.engine.execute(node_list_sql)
        node_list = [{column: value for column, value in rowproxy.items()}
                     for rowproxy in node_list_object]

        group_list_sql = "SELECT `group_id`, `name`, `num`, `state` " \
                         "FROM  `group_list` " \
                         "WHERE `area_id` = {} AND `gateway_id` = {}".format(area_id, gateway_id)

        group_list_object = db.engine.execute(group_list_sql)
        group_list = [{column: value for column, value in rowproxy.items()}
                      for rowproxy in group_list_object]

        scene_list_sql = "SELECT `scene_id`, `name`, `num` " \
                          "FROM `scene_list` " \
                          "WHERE `area_id` = {} AND `gateway_id` = {}".format(area_id, gateway_id)

        scene_list_object = db.engine.execute(scene_list_sql)
        scene_list = [{column: value for column, value in rowproxy.items()}
                       for rowproxy in scene_list_object]

        data_array = {
            'node_list': node_list,
            'group_list': group_list,
            'scene_list': scene_list
        }
        result = True
    except Exception as e:
        message = str(e)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)

@api.route('/update_node_state', methods=['POST', 'GET'])
def update_node_state():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        item_id = request.form.get('item_id', default=0, type=int)
        control_type = request.form.get('control_type', default='', type=str)
        item_node_list_field = '`nl`.`type_id`, `il`.`node_id`, `il`.`node_state`' if control_type == 'scene' else '`nl`.`type_id`, `il`.`node_id`'
        item_node_list_table = "`{}_node_list` AS `il` " \
                               "INNER JOIN `node_list` AS `nl` " \
                               "ON(`il`.`node_id` = `nl`.`node_id` AND `il`.`gateway_id` = `nl`.`gateway_id`)".format(control_type)
        item_node_list_sql = "SELECT {} FROM {} WHERE `il`.`gateway_id` = {} AND `il`.`{}_id` = {}".format(
            item_node_list_field, item_node_list_table, gateway_id, control_type, item_id)
        item_node_list_object = db.engine.execute(item_node_list_sql).fetchall()
        item_node_list = [[value for value in rowproxy] for rowproxy in item_node_list_object]
        data_array = item_node_list
        result = True
    except Exception as e:
        message = str(e)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)