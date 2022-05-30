import json
import datetime

from flask import jsonify, request, session
from sqlalchemy import func, and_, or_, between, exists

from . import api
from .. import db
from ..models import *

# from . import mqtt_talker as mqtttalker

from config import role
from .log import log_info

# from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.setting import *

# mqtt_test
from . import mqtt_talker as mqtttalker

@api.route('/mqtt_api_test', methods=['POST', 'GET'])
def mqtt_test():

    # 依照 MQTT 參考文件上填入的欄位
    payload = json.dumps({
        "device_address": 2,
        "num": 1,
        "state": 100
    })

    # 放入 MQTT Broker，Gateway_id，Task，Payload
    mqtt_talker = mqtttalker.MqttTalker(
                "140.116.39.212", "09ea6335-d2bd-4678-9ca9-647b5574a09e", "control/node", payload)

    # 呼叫此函式，等待回傳訊息
    response = mqtt_talker.start()

    # 回傳的訊息( AJAX 到網頁上)
    if response:
        return jsonify(response), 201
    else:
        return "Request Timeout", 500

@api.route('/gateway_add', methods=['POST', 'GET'])
def gateway_add():
    result = False
    message = ''
    data_array = {}

    class gatewayInsertException(Exception):
        def __init__(self, error):
            self.message = error

        def __str__(self):
            return self.message

    try:
        gateway_uid = request.form.get('gateway_uid', default="", type=str)
        gateway_name = request.form.get('gateway_name', default="", type=str)
        gateway_city = request.form.get('gateway_city', default=135, type=int)
        gateway_address = request.form.get('gateway_address', default="", type=str)

        city_info_sql = "SELECT `id`, `country_name`, `city_name` FROM `city_list` WHERE `id` = {}".format(gateway_city)
        city_info_result = db.engine.execute(city_info_sql)
        db.session.close()
        city_info = [{column: value for column, value in rowproxy.items()} for rowproxy in city_info_result]

        gateway_check_duplicate_sql = "SELECT * FROM `gateway_list` WHERE `uid` = '{}'".format(gateway_uid)
        gateway_check_duplicate_result = db.engine.execute(gateway_check_duplicate_sql)
        gateway_check_duplicate = gateway_check_duplicate_result.fetchone()
        db.session.close()

        if gateway_check_duplicate is not None:
            raise gatewayInsertException('UID 重複!')

        message = json.dumps({
            'gateway_uid': gateway_uid,
            'name': gateway_name,
            'country': city_info[0]['country_name'],
            'city': city_info[0]['city_name'],
            'physical_address': str(gateway_address)
        })

        # TODO gateway_add
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_uid, "gateway_setting/insert", message)
        response = mqtt_talker.start()


        if json.loads(response['status']) != "ok":
            raise gatewayInsertException('Request Timeout!')
        insert_gateway_sql = "INSERT INTO gateway_list" \
                             "(`user_id`, `uid`, `city_id`, `physical_address`, `gateway_name`) " \
                             "VALUES ({}, '{}', {}, '{}', '{}')".format(session['user-id'], gateway_uid, gateway_city,
                                                                        gateway_address, gateway_name)
        insert_gateway = db.engine.execute(insert_gateway_sql)
        insert_project_sql = "INSERT INTO `project_list`(`user_id`, `name`) " \
                             "VALUES({}, '{}')".format(session['user-id'], gateway_name)
        insert_project = db.engine.execute(insert_project_sql)
        db.session.close()

        result = True
    except gatewayInsertException as e:
        message = str(e)
        log_info(message)
    except Exception as e:
        message = str(e)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/gateway_modify', methods=['POST', 'GET'])
def gateway_modify():
    result = False
    message = ''
    data_array = {}

    class gatewayInsertException(Exception):
        def __init__(self, error):
            self.message = error

        def __str__(self):
            return self.message

    try:
        gateway_uid = request.form.get('gateway_uid', default="", type=str)
        gateway_name = request.form.get('gateway_name', default="", type=str)
        gateway_city = request.form.get('gateway_city', default=135, type=int)
        gateway_address = request.form.get('gateway_address', default="", type=str)
        gateway_id = request.form.get('gateway_id', default=0, type=int)

        gateway_update_sql = "UPDATE `gateway_list` SET `gateway_name`='{}', `city_id`={}, physical_address='{}' " \
                             "WHERE `id`={}".format(gateway_name, gateway_city, gateway_address, gateway_id)
        gateway_update = db.engine.execute(gateway_update_sql)
        db.session.close()

        if gateway_uid != "":
            city_info_sql = "SELECT `id`, `country_name`, `city_name` FROM `city_list` WHERE `id` = {}".format(
                gateway_city)
            city_info_result = db.engine.execute(city_info_sql)
            db.session.close()
            city_info = [{column: value for column, value in rowproxy.items()} for rowproxy in city_info_result]

            gateway_check_duplicate_sql = "SELECT * FROM `gateway_list` WHERE `uid` = '{}'".format(gateway_uid)
            gateway_check_duplicate_result = db.engine.execute(gateway_check_duplicate_sql)
            gateway_check_duplicate = gateway_check_duplicate_result.fetchone()
            db.session.close()

            if gateway_check_duplicate is not None:
                raise gatewayInsertException('UID 重複!')

            message = json.dumps({
                'gateway_uid': gateway_uid,
                'name': gateway_name,
                'country': city_info[0]['country_name'],
                'city': city_info[0]['city_name'],
                'physical_address': str(gateway_address)
            })

             # TODO gateway_modify
            mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_uid, "gateway_setting/insert", message)
            response = mqtt_talker.start()

            if json.loads(response['status']) != "ok":
                raise gatewayInsertException('Request Timeout!')

            node_update_uid_sql = "UPDATE `gateway_list` AS `g` " \
                                  "LEFT JOIN `node_list` AS `n` ON(`g`.`uid` = `n`.`gateway`) " \
                                  "SET `n`.`gateway`='{}' WHERE `g`.`id`={}".format(gateway_uid, gateway_id)
            node_update_uid = db.engine.execute(node_update_uid_sql)

            gateway_update_uid_sql = "UPDATE `gateway_list` SET `uid`='{}' WHERE `id`={}".format(gateway_uid, gateway_id)
            gateway_update_uid = db.engine.execute(gateway_update_uid_sql)
            db.session.close()
        result = True
    except gatewayInsertException as e:
        message = str(e)
        log_info(message)
    except Exception as e:
        message = str(e)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/device_add', methods=['POST', 'GET'])
def device_add():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway-id', default=0, type=int)
        gateway_uid = request.form.get('gateway-uid', default=0, type=int)
        device_name = request.form.get('device-name', default="", type=str)
        device_address = request.form.get('device-address', default=-1, type=int)
        device_type = request.form.get('device-type', default=0, type=int)
        project_id = request.form.get('project-id', default=0, type=int)
        channel_name = request.form.getlist('channel-name[]')
        channel_point = request.form.getlist('channel-point[]')

        device_type_sql = "SELECT `id`, `class`, `name`, `channels` " \
                          "FROM `device_type_list` WHERE `id`={}".format(device_type)
        device_type_result = db.engine.execute(device_type_sql)
        device_type_list = device_type_result.fetchone()

        device_channels = device_type_list[3]
        device_name = device_name if device_name != "" else device_type_list[2]
        insert_device_sql = "INSERT `device_list`(`gateway_id`, `name`, `type_id`, `address`, `channels`) " \
                            "VALUES ({}, '{}', {}, {}, {})".format(gateway_id, device_name, device_type,
                                                                   device_address, device_channels)
        insert_device_result = db.engine.execute(insert_device_sql)
        device_id = insert_device_result.lastrowid

        for i in range(0, device_channels):
            if i == 0:
                insert_channel_value = "({}, {}, {}, {}, '{}', {}, '{}', {})".format(device_id, gateway_id, project_id, device_type, gateway_uid, device_address, channel_name[i], channel_point[i])
            else:
                insert_channel_value += ", ({}, {}, {}, {}, '{}', {}, '{}', {})".format(device_id, gateway_id, project_id, device_type, gateway_uid, device_address, channel_name[i], channel_point[i])

        channel_insert_sql = "INSERT `node_list`(`device_id`, `gateway_id`, `project_id`, `type_id`, `gateway`, `device_address`, `node_name`, `node`) " \
                             "VALUES {}".format(insert_channel_value)
        insert_device_result = db.engine.execute(channel_insert_sql)
        db.session.close()
        result = True
    except Exception as e:
        message = str(e)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/device_modify', methods=['POST', 'GET'])
def device_modify():
    result = False
    message = ''
    data_array = {}

    try:
        device_id = request.form.get('device-id', default=0, type=int)
        device_name = request.form.get('device-name', default="", type=str)
        device_address = request.form.get('device-address', default=0, type=int)

        device_update_sql = "UPDATE `device_list` AS `dl` " \
                            "LEFT JOIN `node_list` AS `n` ON(`dl`.`id` = `n`.`device_id`) " \
                            "SET `dl`.`name`='{0}', `dl`.`address`={1}, `n`.`device_address`={1} " \
                            "WHERE `dl`.`id`={2}".format(device_name, device_address, device_id)
        device_update_result = db.engine.execute(device_update_sql)
        db.session.close()
        result = True
    except Exception as e:
        message = str(e)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/node_modify', methods=['POST', 'GET'])
def node_modify():
    result = False
    message = ''
    data_array = {}

    try:
        node_id = request.form.get('node_id', default=0, type=int)
        node_name = request.form.get('node_name', default="", type=str)
        node_point = request.form.get('node_point', default=0, type=int)

        # node_update_sql = "UPDATE `node_list` SET `node_name`='{}', `node`={} " \
        #                   "WHERE `id`={}".format(node_name, node_point, node_id)

        node_update_sql = "UPDATE `node_list` SET `name`='{}', `num`={} " \
                          "WHERE `node_id`={}".format(node_name, node_point, node_id)
        node_update_result = db.engine.execute(node_update_sql)
        db.session.close()

        # payload_dic = {
        #     "column":{
        #         "device_address": 1,
        #         "num": 1,
        #         "name": "需量燈 1 號",
        #     },
        #     "where":{
        #         "node_id":1,
        #     },
        # }

        # payload = json.dumps(payload_dic)

        # if DELIVER_WAY == "Ethernet":
        #     mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], 'update/node', payload)
        #     response = mqtt_talker.start()
        # elif DELIVER_WAY == "NB-IoT":
        #     composition = 'update/scene_node' + '|' + payload
        #     R.rpush('publish', composition)

        #     response = nbiot_talker.monitor()

        # if not response:
        #     raise BaseException("Request Timeout")

        result = True
    except Exception as e:
        message = str(e)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)