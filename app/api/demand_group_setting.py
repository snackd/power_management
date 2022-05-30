import json
import datetime

from flask import jsonify, request
from sqlalchemy import func, and_, or_, between, exists

from . import api
from .. import db
from ..models import *

from . import mqtt_talker as mqtttalker
from . import nbiot_response as nbiot_talker

from config import role, G_CONTROL_VALUE_TYPE_LIST
from config import DELIVER_WAY

from .log import log_info

from .gateway_use.device import switch_api as switch
# from .gateway_use.device.config.gateway_setting import *
# from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.setting import *
from ..api import lib_get_gateway_info as gateway_info


@api.route('/get_demand_group_node', methods=['POST', 'GET'])
def get_demand_group_node():
    result = False
    message = ''
    data_array = {}

    try:
        unload_group_id = request.form.get('group_id', default=0, type=int)
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        demand_group_node_list_sql = "SELECT `nl`.`node_id`, `nl`.`type_id`, `nl`.`name`, `nl`.`device_address`, `nl`.`num`, `nl`.`state`, `nl`.`demand_state`, `ugnl`.`unload_group_id` AS `node_group_state` " \
                                     "FROM `node_list` AS `nl` " \
                                     "LEFT JOIN `unload_group_node_list` AS `ugnl` ON(`ugnl`.`node_id` = `nl`.`node_id` AND `ugnl`.`gateway_id` = `nl`.`gateway_id`) " \
                                     "WHERE (`ugnl`.`unload_group_id` = {} AND `ugnl`.`gateway_id` = {}) OR (`nl`.`gateway_id` = {} AND `ugnl`.`unload_group_id` IS NULL )".format(unload_group_id, gateway_id, gateway_id)
        demand_group_node_list_object = db.engine.execute(demand_group_node_list_sql)
        demand_group_node_list = {str(rowproxy[0]): {column: value for column, value in rowproxy.items()} for rowproxy in demand_group_node_list_object}
        data_array = demand_group_node_list
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


@api.route('/change_demand_group_sort', methods=['POST', 'GET'])
def change_demand_group_sort():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        demand_group_id = request.form.get('demand_group_id', default=0, type=int)
        demand_group_sort = request.form.get('demand_group_sort', default=0, type=int)

        get_gateway_mac_result = gateway_info.get_gateway_info(gateway_id)
        get_gateway_mac = get_gateway_mac_result[0][1]


        update_demand_group_list_sql = "UPDATE `unload_group_list` SET `sort` = {} " \
                                     "WHERE `unload_group_id` = {} AND `gateway_id` = {} ".format(demand_group_sort,
                                                                                                  demand_group_id, gateway_id)
        update_demand_group_list_result = db.engine.execute(update_demand_group_list_sql)

        payload_dic = {
                "column": {
                    "sort": demand_group_sort
                },
                "where": {
                    "unload_group_id": demand_group_id,
                },
        }

        payload = json.dumps(payload_dic)

        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, get_gateway_mac, "update/unload_group", payload)

        response = mqtt_talker.start()

        result = True
    except Exception as e:
        message = str(e)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)\


@api.route('/demand_group_info_setting', methods=['POST', 'GET'])
def demand_group_info_setting():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        demand_group_id = request.form.get('demand-group-id', default=0, type=int)
        demand_group_sort = request.form.get('demand-group-sort', default=0, type=int)
        demand_group_number = request.form.get('demand-group-number', default=0, type=int)
        demand_group_name = request.form.get('demand-group-name', default='', type=str)

        get_gateway_mac_result = gateway_info.get_gateway_info(gateway_id)
        get_gateway_mac = get_gateway_mac_result[0][1]

        if role == "Gateway":
            update_demand_group_list_sql = "UPDATE `unload_group_list` SET `name` = '{}', `num` = {}, `sort` = {}  " \
                                         "WHERE `unload_group_id` = {} AND `gateway_id` = {} ".format(demand_group_name, demand_group_number, demand_group_sort, demand_group_id, gateway_id)
            update_demand_group_list_result = db.engine.execute(update_demand_group_list_sql)
            payload_dic = {
                "column": {
                    "name ": demand_group_name,
                    "num": demand_group_number,
                    "sort": demand_group_sort
                },
                "where": {
                    "unload_group_id": demand_group_id,
                },
            }
        payload = json.dumps(payload_dic)

        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, get_gateway_mac, "update/unload_group", payload)

        response = mqtt_talker.start()

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


@api.route('/demand_group_node_change', methods=['POST', 'GET'])
def demand_group_node_change():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        demand_group_id = request.form.get('demand_group_id', default=0, type=int)
        node_id = request.form.get('node_id', default=0, type=int)
        change_type = request.form.get('change_type', default='', type=str)

        get_gateway_mac_result = gateway_info.get_gateway_info(gateway_id)
        get_gateway_mac = get_gateway_mac_result[0][1]


        if role == "Gateway":
            if change_type == 'selected':
                delete_group_node_sql = "DELETE FROM `unload_group_node_list` " \
                                        "WHERE `gateway_id` = {} AND `unload_group_id` = {} " \
                                        "AND `node_id` = {}".format(gateway_id, demand_group_id, node_id)
                delete_group_node_result = db.engine.execute(delete_group_node_sql)

                topic = "deleted/unload_group_node"

            else:
                insert_group_node_sql = "INSERT INTO `unload_group_node_list`(`gateway_id`, `unload_group_id`, `node_id`) " \
                                        "VALUES ({}, {}, {})".format(gateway_id, demand_group_id, node_id)
                insert_group_node_result = db.engine.execute(insert_group_node_sql)

                topic = "insert/unload_group_node"

            payload_dic = {
                "unload_group_id": demand_group_id,
                "node_id": node_id,
            }

        elif role == "Cloud":
            if change_type == 'selected':
                delete_group_node_sql = "DELETE FROM `unload_group_node_list` " \
                                        "WHERE `gateway_id` = {} AND `unload_group_id` = {} " \
                                        "AND `node_id` = {}".format(gateway_id, demand_group_id, node_id)
                topic = "deleted/unload_group_node"
                delete_group_node_result = db.engine.execute(delete_group_node_sql)
            else:
                insert_group_node_sql = "INSERT INTO `unload_group_node_list`(`gateway_id`, `unload_group_id`, `node_id`) " \
                                        "VALUES ({}, {}, {})".format(gateway_id, demand_group_id, node_id)
                insert_group_node_result = db.engine.execute(insert_group_node_sql)

                topic = "insert/unload_group_node"

            payload_dic = {
                "unload_group_id": demand_group_id,
                "node_id": node_id,
            }

        payload = json.dumps(payload_dic)

        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, get_gateway_mac, topic, payload)

        response = mqtt_talker.start()

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
