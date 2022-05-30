import json
import datetime

from flask import jsonify, request, session
from sqlalchemy import func, and_, or_, between, exists

from . import api, lib_generate_id
from .. import db
from ..models import *

from . import mqtt_talker as mqtttalker
from . import nbiot_response as nbiot_talker

from config import role
from config import DELIVER_WAY
from config import R

from .log import log_info


from .gateway_use.device import group as switch
# from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.setting import *


@api.route('/load_project_group', methods=['POST', 'GET'])
def load_project_group():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)

        node_list_sql = "SELECT `n`.`id`, `n`.`node`, `n`.`node_name`, `gnl`.`group_id` FROM " \
                        "`node_list` AS `n` " \
                        "LEFT JOIN `group_node_list` AS `gnl` ON(`n`.`id` = `gnl`.`channel_id`)" \
                        "WHERE `gateway_id` = {}".format(gateway_id)
        node_list_object = db.engine.execute(node_list_sql)
        node_list = {str(rowproxy[0]): {column: value for column, value in rowproxy.items()} for rowproxy in
                     node_list_object}
        data_array['node_list'] = node_list
        group_list_sql = "SELECT `gl`.`group_id`, `gl`.`num`, `gl`.`name` AS `group_name`, " \
                         "`nl`.`node_id`, `nl`.`num` AS `node_number`, `nl`.`name` AS `node_name`" \
                         "FROM `group_list` AS `gl` " \
                         "INNER JOIN `group_node_list` AS `gnl` ON(`gl`.`group_id` = `gnl`.`group_id` AND `gl`.`gateway_id` = `gnl`.`gateway_id`) " \
                         "INNER JOIN `node_list` AS `nl` ON(`nl`.`node_id` = `gnl`.`node_id` AND `nl`.`gateway_id` = `gnl`.`gateway_id`) " \
                         "WHERE `g`.`gateway_id` = {}".format(gateway_id)
        group_list_object = db.engine.execute(group_list_sql)
        group_list = {}
        for each_node in group_list_object:
            if each_node[0] not in group_list:
                group_list[each_node[0]] = {
                    'group-name': each_node[2],
                    'node-data': {}
                }
            group_list[each_node[0]]['node-data'][each_node[3]] = list(each_node)
        data_array['group_list'] = group_list
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


@api.route('/group_node_check', methods=['POST', 'GET'])
def group_node_check():
    result = False
    message = ''
    data_array = {}

    try:
        node_id = request.form.get('node_id', default=0, type=int)
        group_id = request.form.get('group_id', default=0, type=int)
        group_number = request.form.get('group_number', default=0, type=int)
        checked = request.form.get('checked', default=0, type=int)

        if checked == 0:
            delete_group_node_sql = "DELETE FROM `group_node_list` " \
                                    "WHERE `gateway_id` = {} AND `node_id` = {} AND `group_id` = {}".format(session['gateway-id'], node_id, group_id)
            delete_group_node = db.engine.execute(delete_group_node_sql)
            topic = 'delete/group_node'
        else:
            insert_group_node_sql = "INSERT INTO group_node_list(`gateway_id`, `group_id`, `node_id`) " \
                                    "VALUES({}, {}, {})".format(session['gateway-id'], group_id, node_id)
            insert_group_node = db.engine.execute(insert_group_node_sql)
            topic = 'insert/group_node'

        db.session.close()

        # TODO Switch.set_group
        if role == "Gateway":
            switch.set_group(session['gateway-id'], group_id, group_number)

        payload_dic = {
            'group_id': group_id,
            'node_id': node_id
        }
        payload = json.dumps(payload_dic)

        # TODO group_node_check
        if DELIVER_WAY == "Ethernet":
            mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic, payload)
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
        result = True

    except BaseException as e:
        message = str(e)
    except Exception as e:
        message = str(e)
        print('HI!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(message)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/save_group_info', methods=['POST', 'GET'])
def save_group_info():
    result = False
    message = ''
    data_array = {}

    try:
        group_id = request.form.get('group_id', default=0, type=int)
        group_name = request.form.get('group_name', default='', type=str)
        group_number = request.form.get('group_number', type=int)

        update_group_sql = "UPDATE `group_list` SET `name` = '{}', `num` = {} WHERE `group_id` = {} AND `gateway_id` = {}".format(group_name, group_number, group_id, session['gateway-id'])
        update_group = db.engine.execute(update_group_sql)
        db.session.close()

        # payload_dic = {
        #     'group_id': group_id,
        #     'name': group_name,
        #     'num': group_number
        # }

        payload_dic = {
            "column": {
                "name": group_name,
                "num": group_number,
            },
            "where": {
                "group_id": group_id,
            }
        }
        payload = json.dumps(payload_dic)

        topic = "update/group"

        # TODO save_group_info
        if DELIVER_WAY == "Ethernet":
            mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic, payload)
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
        result = True

    except BaseException as e:
        message = str(e)
    except Exception as e:
        message = str(e)
        print('HI!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(message)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/add_group', methods=['POST', 'GET'])
def add_group():
    result = False
    message = ''
    data_array = {}

    try:
        group_name = request.form.get('group_name', default='', type=str)
        group_number = request.form.get('group_number', type=int)
        node_list = request.form.getlist('node_list[]')
        if len(node_list) == 0:
            raise BaseException("請選擇群組所包含的點位!")

        group_id = lib_generate_id.generate_id(3, session['gateway-id'])

        add_group_sql = "INSERT INTO `group_list`(`group_id`, `gateway_id`, `name`, `num`) " \
                        "VALUES({}, {}, '{}', {})".format(group_id, session['gateway-id'], group_name, group_number)
        add_group_result = db.engine.execute(add_group_sql)

        payload_dic = {
            'group_id': group_id,
            'name': group_name,
            'num': group_number
        }
        payload = json.dumps(payload_dic)

        topic = "insert/group"

        # TODO add group
        if DELIVER_WAY == "Ethernet":
            mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic, payload)
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

        i = 0
        for node_id in node_list:
            if i == 0:
                add_group_nodes = '({}, {}, {})'.format(session['gateway-id'], group_id, node_id)
            else:
                add_group_nodes += ', ({}, {}, {})'.format(session['gateway-id'], group_id, node_id)
            i += 1
            payload_dic = {
                'group_id': group_id,
                'node_id': node_id
            }
            payload = json.dumps(payload_dic)

            topic = "insert/group_node"

            # TODO add group
            if DELIVER_WAY == "Ethernet":
                mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic, payload)
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

        add_group_nodes_sql = "INSERT INTO `group_node_list`(`gateway_id`, `group_id`, `node_id`) VALUES {}".format(add_group_nodes)
        add_group_nodes = db.engine.execute(add_group_nodes_sql)
        db.session.close()

        # TODO Switch.set_group
        if role == "Gateway":
            switch.set_group(session['gateway-id'], group_id, group_number)
            result = True

    except BaseException as e:
        message = str(e)
    except Exception as e:
        message = str(e)
        print('HI!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(message)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/delete_group', methods=['POST', 'GET'])
def delete_group():
    result = False
    message = ''
    data_array = {}

    try:
        group_id = request.form.get('group_id', default=0, type=int)
        group_number = request.form.get('group_number', default=0, type=int)

        delete_group_node_sql = "DELETE FROM `group_node_list` WHERE `gateway_id` = {} AND `group_id` = {}".format(
            session['gateway-id'], group_id)
        delete_group_node = db.engine.execute(delete_group_node_sql)

        delete_group_sql = "DELETE FROM `group_list` " \
                           "WHERE `gateway_id` = {} AND `group_id` = {}".format(session['gateway-id'], group_id)
        delete_group = db.engine.execute(delete_group_sql)
        db.session.close()

        # TODO Switch.delete_group
        if role == "Gateway":
            switch.delete_group(session['gateway-id'], group_id, group_number)

        payload_dic = {
            'group_id': group_id
        }
        payload = json.dumps(payload_dic)

        topic = "delete/group"

        # TODO delete_group
        if DELIVER_WAY == "Ethernet":
            mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic, payload)
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
        result = True

    except BaseException as e:
        message = str(e)
    except Exception as e:
        message = str(e)
        print('HI!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(message)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)

@api.route('/delete_group_node', methods=['POST', 'GET'])
def delete_group_node():
    result = False
    message = ''
    data_array = {}

    try:
        group_id = request.form.get('group_id', default=0, type=int)
        group_number = request.form.get('group_number', default=0, type=int)
        node_id = request.form.get('node_id', type=int)

        delete_group_node_sql = "DELETE FROM `group_node_list` WHERE `gateway_id` = {} AND `group_id` = {} AND `node_id` = {}".format(session['gateway-id'], group_id, node_id)
        delete_group_node = db.engine.execute(delete_group_node_sql)
        db.session.close()

        # TODO Switch.set_group_delete
        if role == "Gateway":
            switch.set_group(session['gateway-id'], group_id, group_number)

        payload_dic = {
            'group_id': group_id,
            'node_id': node_id
        }
        payload = json.dumps(payload_dic)

        topic = "delete/group_node"

        # TODO delete_group_node
        if DELIVER_WAY == "Ethernet":
            mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic, payload)
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
        result = True

    except BaseException as e:
        message = str(e)
    except Exception as e:
        message = str(e)
        print('HI!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(message)
        log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)