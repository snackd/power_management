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

# from .log import log_info

from .gateway_use.device import group as switch
# from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.setting import *


@api.route('/load_project_scene', methods=['POST', 'GET'])
def load_project_scene():
    result = False
    message = ''
    data_array = {}

    try:
        project_id = request.form.get('project_id', default=0, type=int)

        node_list_sql = "SELECT `n`.`id`, `n`.`node`, `n`.`node_name`, `dl`.`type_id` FROM `node_list` AS `n` " \
                        "INNER JOIN `device_list` AS `dl` ON(`n`.`device_id` = `dl`.`id`)" \
                        "WHERE `project_id` = {}".format(project_id)
        node_list_object = db.engine.execute(node_list_sql)
        node_list = {str(rowproxy[0]): {column: value for column, value in rowproxy.items()} for rowproxy in
                     node_list_object}
        data_array['node_list'] = node_list
        scene_list_sql = "SELECT `sl`.`id` AS `scene_id`, `sl`.`scene_number`, `sl`.`scene_name`, " \
                         "`n`.`id` AS `node_id`, `n`.`node_name`, `snl`.`node_state` " \
                         "FROM `scene_list` AS `sl` " \
                         "INNER JOIN `scene_node_list` AS `snl` ON(`s`.`id` = `snl`.`scene_id`) " \
                         "INNER JOIN `node_list` AS `n` ON(`n`.`id` = `snl`.`channel_id`) " \
                         "WHERE `s`.`project_id` = {}".format(project_id)
        scene_list_object = db.engine.execute(scene_list_sql)
        scene_list = {}
        for each_node in scene_list_object:
            if each_node[0] not in scene_list:
                scene_list[each_node[0]] = {
                    'scene-name': each_node[2],
                    'scene-number': each_node[1],
                    'node-data': {}
                }
            scene_list[each_node[0]]['node-data'][each_node[3]] = list(each_node)
        data_array['scene_list'] = scene_list
        db.session.close()
        result = True
    except Exception as e:
        message = str(e)
        print('HI!!!!!!!!!!!!!!!!!')
        print(message)
        # log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/scene_enabled_change', methods=['POST', 'GET'])
def scene_enabled_change():
    result = False
    message = ''
    data_array = {}

    try:
        node_id = request.form.get('node_id', default=0, type=int)
        scene_id = request.form.get('scene_id', default=0, type=int)
        node_state = request.form.get('node_state', default=0, type=int)

        scene_list_sql = "SELECT `scene_id`, `num`, `name` FROM `scene_list` WHERE `scene_id` = {} AND `gateway_id` = {} LIMIT 1".format(scene_id, session['gateway-id'])
        scene_list = db.engine.execute(scene_list_sql).fetchall()

        scene_number = scene_list[0][1]

        insert_scene_node_sql = "UPDATE scene_node_list SET `node_state` = {} WHERE `node_id` = {} AND `scene_id`={} AND `gateway_id` = {}"\
                                 .format(node_state, node_id, scene_id, session['gateway-id'])

        insert_scene_node = db.engine.execute(insert_scene_node_sql)
        db.session.close()
        # TODO Switch.set_scene
        if role == "Gateway":
            switch.set_scene(session['gateway-id'], scene_id, scene_number)

        payload_dic = {
            'scene_id': scene_id,
            'node_id': node_id,
            'node_state': node_state
        }
        payload = json.dumps(payload_dic)

        topic = "update/scene_node"

        # TODO scene_enabled_change
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
        # log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/scene_unselected_node', methods=['POST', 'GET'])
def scene_unselected_node():
    result = False
    message = ''
    data_array = {}

    try:
        node_id_list = request.form.getlist('node_id_list[]')
        node_state_list = request.form.getlist('node_state_list[]')
        scene_id = request.form.get('scene_id', default=0, type=int)
        scene_number = request.form.get('scene_number', default=0, type=int)

        for i in range(len(node_id_list)):
            node_id = node_id_list[i]

            node_state = node_state_list[i]
            insert_scene_node_sql = "INSERT INTO scene_node_list(`gateway_id`, `scene_id`, `node_id`, `node_state`) " \
                                    "VALUES({}, {}, {}, '{}')".format(session['gateway-id'], scene_id, node_id, node_state)
            insert_scene_node = db.engine.execute(insert_scene_node_sql)
        db.session.close()

        # TODO Switch.set_scene
        if role == "Gateway":
            switch.set_scene(session['gateway-id'], scene_id, scene_number)

        payload_dic = {
            'scene_id': scene_id,
            'node_id': node_id,
            'node_state': node_state
        }
        payload = json.dumps(payload_dic)

        topic = "insert/scene_node"

        # TODO scene_unselected_node
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
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/scene_selected_node', methods=['POST', 'GET'])
def scene_selected_node():
    result = False
    message = ''
    data_array = {}

    try:
        node_id_list = request.form.getlist('node_id_list[]')
        scene_id = request.form.get('scene_id', default=0, type=int)
        scene_number = request.form.get('scene_number', default=0, type=int)

        for i in range(len(node_id_list)):
            node_id = node_id_list[i]
            delete_scene_node_sql = "DELETE FROM `scene_node_list` " \
                                     "WHERE `gateway_id` = {} AND `node_id` = {} AND `scene_id` = {}".format(session['gateway-id'], node_id, scene_id)

            delete_scene_node = db.engine.execute(delete_scene_node_sql)
        db.session.close()

        # TODO Switch.set_scene
        if role == "Gateway":
            switch.set_scene(session['gateway-id'], scene_id, scene_number)

        payload_dic = {
            'scene_id': scene_id,
            'node_id': node_id
        }
        payload = json.dumps(payload_dic)

        topic = "delete/scene_node"

        # TODO scene_selected_node
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
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/save_scene_info', methods=['POST', 'GET'])
def save_scene_info():
    result = False
    message = ''
    data_array = {}

    try:
        scene_id = request.form.get('scene_id', default=0, type=int)
        scene_name = request.form.get('scene_name', default='', type=str)
        scene_number = request.form.get('scene_number', type=int)

        update_scene_sql = "UPDATE `scene_list` SET `name` = '{}', `num` = {} WHERE `gateway_id` = {} AND `scene_id` = {}".format(scene_name, scene_number, session['gateway-id'], scene_id)
        update_scene = db.engine.execute(update_scene_sql)
        db.session.close()

        # payload_dic = {
        #     'scene_id': scene_id,
        #     'name': scene_name,
        #     'num': scene_number
        # }
        payload_dic = {
            "column": {
                "name": scene_name,
                "num": scene_number,
            },
            "where": {
                "scene_id": scene_id,
            }
        }

        payload = json.dumps(payload_dic)

        topic = "update/scene"

        # TODO save_scene_info
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
        # log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


# FIXME
@api.route('/add_scene', methods=['POST', 'GET'])
def add_scene():
    result = False
    message = ''
    data_array = {}

    try:
        scene_name = request.form.get('scene_name', default='', type=str)
        scene_number = request.form.get('scene_number', type=int)
        node_list = request.form.getlist('node_list[]')
        node_state_list = request.form.getlist('node_state_list[]')
        scene_id = lib_generate_id.generate_id(4, session['gateway-id'])

        if len(node_list) == 0:
            raise BaseException("請選擇場景所包含的點位!")

        add_scene_sql = "INSERT INTO `scene_list`(`scene_id`, `gateway_id`, `name`, `num`) " \
                        "VALUES({}, {}, '{}', {})".format(scene_id, session['gateway-id'], scene_name, scene_number)

        add_scene_result = db.engine.execute(add_scene_sql)
        payload_dic = {
            'scene_id': scene_id,
            'name': scene_name,
            'num': scene_number
        }
        payload = json.dumps(payload_dic)

        topic = "insert/scene"

        # TODO add_scene
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

        add_scene_nodes = ''
        i = 0
        for node_id in node_list:
            if i == 0:
                add_scene_nodes += '({}, {}, {}, {})'.format(session['gateway-id'], scene_id, node_id, node_state_list[i])
            else:
                add_scene_nodes += ', ({}, {}, {}, {})'.format(session['gateway-id'], scene_id, node_id, node_state_list[i])

            payload_dic = {
                'scene_id': scene_id,
                'node_id': node_id,
                'node_state': node_state_list[i]
            }
            payload = json.dumps(payload_dic)

            topic = "insert/scene_node"

            # TODO add_scene
            if DELIVER_WAY == "Ethernet":
                mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic,
                                                    payload)
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
            i += 1
        add_scene_nodes_sql = "INSERT INTO `scene_node_list`(`gateway_id`, `scene_id`, `node_id`, `node_state`) VALUES {}".format(add_scene_nodes)
        add_scene_nodes_result = db.engine.execute(add_scene_nodes_sql)
        db.session.close()

        # TODO Switch.set_scene
        if role == "Gateway":
            switch.set_scene(session['gateway-id'], scene_id, scene_number)

        result = True
    except BaseException as e:
        message = str(e)
        print('HI!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(message)
    except Exception as e:
        message = str(e)
        print('HI!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(message)
        # log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)

@api.route('/delete_scene', methods=['POST', 'GET'])
def delete_scene():
    result = False
    message = ''
    data_array = {}

    try:
        scene_id = request.form.get('scene_id', default=0, type=int)
        scene_number = request.form.get('scene_number', default=0, type=int)

        delete_scene_node_sql = "DELETE FROM `scene_node_list` WHERE `gateway_id` = {} AND `scene_id` = {}".format(
            session['gateway-id'], scene_id)
        delete_scene_node = db.engine.execute(delete_scene_node_sql)

        delete_scene_sql = "DELETE FROM `scene_list` WHERE `gateway_id` = {} AND `scene_id` = {}".format(session['gateway-id'], scene_id)
        delete_scene = db.engine.execute(delete_scene_sql)
        db.session.close()

        # TODO Switch.delete_scene
        if role == "Gateway":
            switch.delete_scene(session['gateway-id'], scene_id, scene_number)

        payload_dic = {
            'scene_id': scene_id
        }
        payload = json.dumps(payload_dic)

        topic = "delete/scene"

        # TODO delete_scene
        if DELIVER_WAY == "Ethernet":
            mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic, payload)
            response = mqtt_talker.start()
        elif DELIVER_WAY == "NB-IoT":
            method = "request"
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
        # log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/delete_scene_node', methods=['POST', 'GET'])
def delete_scene_node():
    result = False
    message = ''
    data_array = {}

    try:
        scene_id = request.form.get('scene_id', default=0, type=int)
        scene_number = request.form.get('scene_number', default=0, type=int)
        node_id = request.form.get('node_id', default='', type=str)

        delete_scene_node_sql = "DELETE FROM `scene_node_list` WHERE `gateway_id` = {} AND `scene_id` = {} AND `node_id` = {}".format(session['gateway-id'], scene_id, node_id)
        delete_scene_node = db.engine.execute(delete_scene_node_sql)
        db.session.close()

        # TODO Switch.set_scene
        if role == "Gateway":
            switch.set_scene(session['gateway-id'], scene_id, scene_number)

        payload_dic = {
            'scene_id': scene_id,
            'node_id': node_id
        }
        payload = json.dumps(payload_dic)

        topic = "delete/scene_node"

        # TODO delete_scene_node
        if DELIVER_WAY == "Ethernet":
            mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, session['gateway-mac-address'], topic, payload)
            response = mqtt_talker.start()
        elif DELIVER_WAY == "NB-IoT":
            method = "request"
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
        # log_info(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)