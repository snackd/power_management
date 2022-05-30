import json
import datetime

from flask import jsonify, request

# from flask import session

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

from .gateway_use.device import switch_api as switch
# from .gateway_use.device.config.gateway_setting import *
# from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.setting import *


@api.route('/demand_setting_update', methods=['POST', 'GET'])
def demand_setting_update():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway-id', default=0, type=int)
        max_value = request.form.get('max-value', default=0, type=int) # 契約需量
        upper = request.form.get('upper', default=0, type=int) # 需量上限
        lower = request.form.get('lower', default=0, type=int) # 需量下限
        reload_gap = request.form.get('reload-gap', default=0, type=int) # 復歸間隔時間
        unload_mode = request.form.get('unload-mode', default=0, type=int) # 卸載模式


        # demand_setting_update_sql = "UPDATE `demand_setting` SET `max_value` = {}, `upper` = {}, `lower` = {}, `reload_gap` = {}, `mode` = {}  WHERE `gateway_id`={}".format(max_value, upper, lower, reload_gap, unload_mode, gateway_id)
        demand_setting_update_sql = "UPDATE `demand_setting_list` SET `max_value` = {}, `upper` = {}, `lower` = {}, `reload_gap` = {}, `mode` = {}  WHERE `gateway_id`={}".format(max_value, upper, lower, reload_gap, unload_mode, gateway_id)
        demand_setting_update_result = db.engine.execute(demand_setting_update_sql)

        payload_dic = {
            "column": {
                "upper": upper,
                "lower": lower,
                # "reload_off_gap": reload_off_gap,
                # "reload_delay": reload_delay,
                "reload_gap": reload_gap,
                # "cycle": cycle,
                "mode": unload_mode,
            },
            "where": {
                # "example:": example,
            }
        }

        payload = json.dumps(payload_dic)
        topic = "update/demand_setting"
        gateway_mac = "09ea6335-d2bd-4678-9ca9-647b5574a09e"

        # print("Gateway_Mac:", session['gateway-mac-address'])

        if DELIVER_WAY == "Ethernet":
            # mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic, payload)
            mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_mac, topic, payload)
            response = mqtt_talker.start()
        elif DELIVER_WAY == "NB-IoT":
            method = "request"
            message_segment = '|'
            publish_redis = "publish"
            composition = topic + method + message_segment + payload
            R.rpush(publish_redis, composition)
            response = nbiot_talker.message_check_monitor()

        if not response:
            raise BaseException("Request Timeout")

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
