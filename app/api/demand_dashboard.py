import json

from flask import jsonify, request
from sqlalchemy import func, and_, or_, between, exists

from . import api
from .. import db
from ..models import *

from . import mqtt_talker as mqtttalker
from . import nbiot_response as nbiot_talker

from config import role, G_CONTROL_VALUE_TYPE_LIST
from config import DELIVER_WAY
from config import R

from .log import log_info

# from .gateway_use.device.config.gateway_setting import *
# from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.setting import *
from ..api import lib_read_demand as demand
from ..api import lib_get_gateway_info as gateway_info
from datetime import datetime, date, time, timedelta

from .gateway_use.device import meter
from .gateway_use.device import condition

@api.route('/update_demand_value', methods=['POST', 'GET'])
def update_demand_value():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        now = datetime.now()  # current date and time
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        curr_date_temp = datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")
        month_first_day = now.strftime("%Y-%m-01 00:00:00")
        yesterday = curr_date_temp - timedelta(days=1)
        last_demand_value_result = demand.last_demand_value(gateway_id)
        last_demand_value = list(last_demand_value_result[0]) if len(last_demand_value_result) > 0 else []
        max_demand_result = demand.max_demand_value(gateway_id, month_first_day)
        max_demand = list(max_demand_result[0]) if len(max_demand_result) > 0 else []
        max_demand[3] = str(max_demand[3])
        demand_setting_list_result = demand.demand_setting_value(gateway_id)
        demand_setting_list = list(demand_setting_list_result[0]) if len(demand_setting_list_result) > 0 else []
        demand_record_list_result = demand.demand_record_value(gateway_id, yesterday)
        demand_record_list = [[str(value) for value in rowproxy] for rowproxy in
                              demand_record_list_result]
        data_array = {
            'last_demand_value': last_demand_value,
            'max_demand': max_demand,
            'demand_setting_list': demand_setting_list,
            'demand_record_list': demand_record_list
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

@api.route('/update_demand_group_value', methods=['POST', 'GET'])
def update_demand_group_value():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        demand_group_list_result = demand.demand_group_list(gateway_id)
        demand_group_list = [[value for value in rowproxy] for rowproxy in
                        demand_group_list_result]
        data_array = demand_group_list
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

@api.route('/change_unload_type', methods=['POST', 'GET'])
def change_unload_type():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        unload_group_number = request.form.get('gateway_id', default=0, type=int)
        unload_group_id = request.form.get('unload_group_id', default=0, type=int)
        unload_type = request.form.get('unload_type', default=0, type=int)

        demand_group_type_status = {
            0: 0,
            1: 100,
            2: 0,
        }
        get_gateway_mac_result = gateway_info.get_gateway_info(gateway_id)
        gateway_mac = get_gateway_mac_result[0][1]

        if unload_group_id > 0:
            switch_group_num = unload_group_id - 1

        if role == "Gateway":

            if unload_type != 0:
                cond = condition.Condition()
                data_array = meter.Meter(cond).switch_group(switch_group_num, demand_group_type_status[unload_type])
                payload_dic = {
                    "column":{
                        "state": demand_group_type_status[unload_type],
                        "unload_group_state": unload_type,
                    },
                    "where": {
                        "unload_group_id":unload_group_id,
                    },
                }
            else:
                payload_dic = {
                    "column":{
                        "unload_group_state": unload_type,
                    },
                    "where": {
                        "unload_group_id":unload_group_id,
                    },
                }

        elif role == "Cloud":
            if unload_type != 0:
                payload_dic = {
                    "column": {
                        "state": demand_group_type_status[unload_type],
                        "unload_group_state": unload_type,
                    },
                    "where": {
                        "unload_group_id": unload_group_id,
                    },
                }
            else:
                payload_dic = {
                    "column":{
                        "unload_group_state": unload_type,
                    },
                    "where": {
                        "unload_group_id":unload_group_id,
                    },
                }

        payload = json.dumps(payload_dic)

        topic = "update/unload_group"

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

        if not response:
            raise BaseException("Request Timeout")

        update_demand_group_status_sql = "UPDATE `unload_group_list` SET `state`={}, `unload_group_state`={} WHERE `gateway_id`={} AND `unload_group_id`={}".format(
            demand_group_type_status[unload_type], unload_type, gateway_id, unload_group_id)
        update_demand_group_status_result = db.engine.execute(update_demand_group_status_sql).fetchall()

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
