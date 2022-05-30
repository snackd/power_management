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

# from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.setting import *


@api.route('/load_project', methods=['POST', 'GET'])
def load_project():
    result = False
    message = ''
    data_array = {}

    try:
        project_id = request.form.get('project_id', default=0, type=int)
        area_list_sql = "SELECT `id`, `area_name` FROM `area_list` WHERE `project_id` = {}".format(
            project_id)
        area_list_object = db.engine.execute(area_list_sql)
        area_list = [{column: value for column, value in rowproxy.items()} for rowproxy in area_list_object]

        area_node_sql = "SELECT `a`.`id` AS `area_id`, `n`.`node_name` " \
                        "FROM `area_list` AS `a` " \
                        "INNER JOIN `area_node_list` AS `anl` ON(`a`.`id` = `anl`.`area_id`) " \
                        "INNER JOIN `node_list` AS `n` ON (`n`.`id` = `anl`.`channel_id`) " \
                        "WHERE `a`.`project_id` = {}".format(project_id)
        area_node_object = db.engine.execute(area_node_sql)
        area_node_list = {}
        for each_node in area_node_object:
            if each_node[0] in area_node_list:
                area_node_list[each_node[0]].append(list(each_node))
            else:
                area_node_list[each_node[0]] = [list(each_node)]

        area_group_sql = "SELECT `a`.`id` AS `area_id`, `g`.`group_name` " \
                         "FROM `area_list` AS `a` " \
                         "INNER JOIN `area_group_list` AS `agl` ON(`a`.`id` = `agl`.`area_id`) " \
                         "INNER JOIN `group` AS `g` ON (`g`.`id` = `agl`.`group_id`) " \
                         "WHERE `a`.`project_id` = {}".format(project_id)
        area_group_object = db.engine.execute(area_group_sql)
        area_group_list = {}
        for each_group in area_group_object:
            if each_group[0] in area_group_list:
                area_group_list[each_group[0]].append(list(each_group))
            else:
                area_group_list[each_group[0]] = [list(each_group)]

        area_scene_sql = "SELECT `a`.`id` AS `area_id`, `s`.`scene_name` " \
                          "FROM `area_list` AS `a` " \
                          "INNER JOIN `area_scene_list` AS `asl` ON(`a`.`id` = `asl`.`area_id`) " \
                          "INNER JOIN `scene` AS `s` ON (`s`.`id` = `asl`.`scene_id`) " \
                          "WHERE `a`.`project_id` = {}".format(project_id)
        area_scene_object = db.engine.execute(area_scene_sql)
        area_scene_list = {}
        for each_scene in area_scene_object:
            if each_scene[0] in area_scene_list:
                area_scene_list[each_scene[0]].append(list(each_scene))
            else:
                area_scene_list[each_scene[0]] = [list(each_scene)]

        data_array = {
            'area_list': area_list,
            'node_list': area_node_list,
            'group_list': area_group_list,
            'scene_list': area_scene_list
        }
        result = True
    except Exception as e:
        message = str(e)
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/area_modify', methods=['POST', 'GET'])
def area_modify():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        area_id = request.form.get('area_id', default=0, type=int)
        area_name = request.form.get('area_name', default='', type=str)
        update_area_sql = "UPDATE `area_list` SET `name`='{}' WHERE `gateway_id` = {} AND `area_id`={}".format(area_name, gateway_id, area_id)
        update_area = db.engine.execute(update_area_sql)
        result = True
    except Exception as e:
        message = str(e)
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/area_add', methods=['POST', 'GET'])
def area_add():
    result = False
    message = ''
    data_array = {}

    try:
        area_name = request.form.get('area_name', default='', type=str)
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        area_id = lib_generate_id.generate_id(5, gateway_id)

        insert_area_sql = "INSERT INTO `area_list` (`gateway_id`, `area_id`, `name`) VALUES ({}, {}, '{}')".format(gateway_id, area_id, area_name)
        insert_area_result = db.engine.execute(insert_area_sql)
        result = True

        payload_dic = {
            'area_id': area_id,
            'name': area_name
        }
        payload = json.dumps(payload_dic)

        topic = "insert/area"

        # TODO area_add
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

    except Exception as e:
        message = str(e)
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/load_area_node', methods=['POST', 'GET'])
def load_area_node():
    result = False
    message = ''
    data_array = {}

    try:
        area_id = request.form.get('area_id', default=0, type=int)
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        load_node_sql = "SELECT `node_id`, `name` AS `node_name` FROM `node_list` WHERE `gateway_id` = {}".format(gateway_id)
        load_node_result = db.engine.execute(load_node_sql)
        node_list = [{column: value for column, value in rowproxy.items()} for rowproxy in load_node_result]
        load_area_node_sql = "SELECT `node_id` FROM `area_node_list` WHERE `area_id` = {} AND `gateway_id` = {}".format(area_id, gateway_id)
        load_area_node_result = db.engine.execute(load_area_node_sql)
        area_node_list = [value[0] for value in load_area_node_result]
        data_array = {
            'node_list': node_list,
            'area_items_list': area_node_list
        }
        result = True
    except Exception as e:
        message = str(e)
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/load_area_group', methods=['POST', 'GET'])
def load_area_group():
    result = False
    message = ''
    data_array = {}

    try:
        area_id = request.form.get('area_id', default=0, type=int)
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        load_group_sql = "SELECT `group_id`, `name` AS `group_name`, `area_id` FROM `group_list` " \
                         "WHERE `gateway_id` = {} AND (`area_id` IS NULL OR `area_id` = {})".format(gateway_id, area_id)
        load_group_result = db.engine.execute(load_group_sql)
        group_list = [{column: value for column, value in rowproxy.items()} for rowproxy in load_group_result]
        # load_area_group_sql = "SELECT `group_id` FROM `area_group_list` WHERE `area_id` = {}".format(area_id)
        # load_area_group_result = db.engine.execute(load_area_group_sql)
        # area_group_list = [value[0] for value in load_area_group_result]
        data_array = {
            'group_list': group_list
        }
        result = True
    except Exception as e:
        message = str(e)
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/load_area_scene', methods=['POST', 'GET'])
def load_area_scene():
    result = False
    message = ''
    data_array = {}

    try:
        area_id = request.form.get('area_id', default=0, type=int)
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        load_scene_sql = "SELECT `scene_id`, `name` AS `scene_name`, `area_id` " \
                          "FROM `scene_list` WHERE `gateway_id` = {} AND  (`area_id` IS NULL OR `area_id` = {})".format(gateway_id, area_id)
        load_scene_result = db.engine.execute(load_scene_sql)
        scene_list = [{column: value for column, value in rowproxy.items()} for rowproxy in load_scene_result]

        data_array = {
            'scene_list': scene_list
        }
        result = True
    except Exception as e:
        message = str(e)
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/change_area_node', methods=['POST', 'GET'])
def change_area_node():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        area_id = request.form.get('area_id', default=0, type=int)
        node_id = request.form.get('item_id', default=0, type=int)
        node_include = request.form.get('check_state', default=2, type=int)

        print("----change_area_node----")
        # print("----123456----")
        print("Gateway Mac:", session['gateway-mac-address'])
        # print("----123456----")

        if node_include == 1:
            area_insert_node_sql = "REPLACE INTO `area_node_list` (`gateway_id`, `area_id`, `node_id`) " \
                                   "VALUES ({}, {}, {})".format(gateway_id, area_id, node_id)
            area_insert_node = db.engine.execute(area_insert_node_sql)
            topic = 'insert/area_node'
        else:
            area_delete_node_sql = "DELETE FROM `area_node_list` " \
                                   "WHERE `gateway_id`={} AND `area_id`={} AND `node_id`={}".format(gateway_id, area_id, node_id)
            area_delete_node = db.engine.execute(area_delete_node_sql)
            topic = 'delete/area_node'


        payload_dic = {
            'area_id': area_id,
            'node_id': node_id
        }
        payload = json.dumps(payload_dic)

        # TODO change_area_node
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
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/change_area_group', methods=['POST', 'GET'])
def change_area_group():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        area_id = request.form.get('area_id', default=0, type=int)
        group_id = request.form.get('item_id', default=0, type=int)
        group_include = request.form.get('check_state', default=2, type=int)

        print("----change_area_group----")
        print("Gateway Mac:", session['gateway-mac-address'])

        update_group_table = "`group_list` "
        update_group_field = " `area_id` = {} ".format(area_id) if group_include == 1 else " `area_id` = NULL"
        update_group_where = "`gateway_id` = {} AND `group_id` = {}".format(gateway_id, group_id)
        update_group_sql = "UPDATE {} SET {} WHERE {} ".format(update_group_table, update_group_field, update_group_where)
        update_group_result = db.engine.execute(update_group_sql)

        # payload_dic = {
        #     'area_id': area_id if group_include == 1 else "NULL",
        #     'group_id': group_id
        # }
        payload_dic = {
            "column":{
                "area_id":area_id if group_include == 1 else None,
            },
            "where":{
                "group_id":group_id,
            },
        }
        payload = json.dumps(payload_dic)

        topic = "update/group"

        # TODO change_area_group
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
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/change_area_scene', methods=['POST', 'GET'])
def change_area_scene():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        area_id = request.form.get('area_id', default=0, type=int)
        scene_id = request.form.get('item_id', default=0, type=int)
        scene_include = request.form.get('check_state', default=2, type=int)

        print("----change_area_scene----")
        print("Gateway Mac:", session['gateway-mac-address'])

        update_scene_table = "`scene_list` "
        update_scene_field = " `area_id` = {} ".format(area_id) if scene_include == 1 else " `area_id` = NULL"
        update_scene_where = "`gateway_id` = {} AND `scene_id` = {}".format(gateway_id, scene_id)
        update_scene_sql = "UPDATE {} SET {} WHERE {} ".format(update_scene_table, update_scene_field,
                                                               update_scene_where)
        update_scene_result = db.engine.execute(update_scene_sql)

        # payload_dic = {
        #     'area_id': area_id if scene_include == 1 else "NULL",
        #     'scene_id': scene_id
        # }
        payload_dic = {
            "column":{
                "area_id": area_id if scene_include == 1 else None,
            },
            "where":{
                "scene_id": scene_id,
            },
        }
        payload = json.dumps(payload_dic)

        topic = "update/scene"

        # TODO change_area_scene
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
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)


@api.route('/area_delete', methods=['POST', 'GET'])
def area_delete():
    result = False
    message = ''
    data_array = {}

    try:
        gateway_id = request.form.get('gateway_id', default=0, type=int)
        area_id = request.form.get('area_id', default=0, type=int)

        delete_area_node_sql = "DELETE FROM `area_node_list` WHERE `gateway_id` = {} AND `area_id` = {}".format(gateway_id, area_id)
        delete_area_node = db.engine.execute(delete_area_node_sql)

        delete_area_group_sql = "UPDATE `group_list` SET `area_id` = NULL WHERE `gateway_id` = {} AND `area_id` = {}".format(gateway_id, area_id)
        delete_area_group = db.engine.execute(delete_area_group_sql)

        delete_area_scene_sql = "UPDATE `scene_list` SET `area_id` = NULL WHERE `gateway_id` = {} AND  `area_id` = {}".format(gateway_id, area_id)
        delete_area_scene = db.engine.execute(delete_area_scene_sql)

        delete_area_sql = "DELETE FROM `area_list` WHERE `gateway_id` = {} AND `area_id` = {}".format(gateway_id, area_id)
        delete_area = db.engine.execute(delete_area_sql)

        payload_dic = {
            'area_id': area_id
        }
        payload = json.dumps(payload_dic)

        topic = "delete/area"

        # TODO area_delete
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
        print('Hi!!!!!!!!!!!!!')
        print(message)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)
