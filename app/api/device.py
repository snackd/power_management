import os
import json
import time
import datetime
from datetime import timedelta

from flask import json, jsonify, request
from sqlalchemy import and_, between, exists, func, or_

from . import api
from .. import db
from ..models import *

from . import mqtt_talker as mqtttalker

from config import role
from .log import log_info


from .schedule import today_check

from .gateway_use.device import group as switch
from .gateway_use.device import group as switch
from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.gateway_setting import *


@api.route('/role', methods=['POST', 'GET'])
def role_method():
    return jsonify(role), 201

# 裝置設定頁面
@api.route('/node/setting', methods=['POST', 'GET'])
def node_setting():
    if request.method == "POST":
            gateway_uid = request.form.get('gateway_uid', default="", type=str)
            node_id = request.form.get('id', default="", type=str)
    elif request.method =="GET":
            gateway_uid = request.args.get('gateway_uid', default="", type=str)
            node_id = request.args.get('id', default="", type=str)

    if role == "Gateway":
        if request.method == "GET":
            Node_data = db.session.query(Node).order_by(Node.node_name).all()
            node_data = []
            for data in Node_data:
                node_data.append({
                    'id': data.id,
                    'gateway': data.gateway,
                    'gateway_address': data.gateway_address,
                    'model': data.model,
                    'node_name': data.node_name,
                    'node': data.node,
                    'group_id': data.group_id,
                    'model_type': data.model_type,
                    'node_state': data.node_state

                })
            return jsonify(node_data), 201
        elif request.method == "POST":
            Node_data = db.session.query(Node).filter(Node.id == node_id).order_by(Node.id == node_id).all()
            node_data = []
            for data in Node_data:
                message={
                    'id': data.id,
                    'gateway': data.gateway,
                    'gateway_address': data.gateway_address,
                    'model': data.model,
                    'group_id': data.group_id,
                    'node_name': data.node_name,
                    'node': data.node
                }
            node_data.append(message)
            return jsonify(node_data), 201


    elif role =="Cloud":
        message = json.dumps({
            'methods': request.method,
            'node_id': node_id
        })
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_uid, "node/setting", message)
        response = mqtt_talker.start()
        if response:
            return jsonify(response), 201
        else:
            return "Request Timeout", 500


@api.route('/group/setting', methods=['POST', 'GET'])
def group_setting():
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    if role == "Gateway":
        Group_data = db.session.query(Group).all()
        group_data = []
        for data in Group_data:
            group_data.append({
                'id': data.id,
                'group_num': data.group_num,
                'group_name': data.group_name,
                'group_state': data.group_state,
                'created_at': data.created_at,
                'updated_at': data.updated_at
            })
        return jsonify(group_data), 201
    elif role =="Cloud":
        message = json.dumps({})
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "group/setting", message)
        response = mqtt_talker.start()
        if response:
            return jsonify(response), 201
        else:
            return "Request Timeout", 500
    # elif role=="Cloud":


@api.route('/scene/setting', methods=['POST', 'GET'])
def scenes_setting():
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    if role == "Gateway":
        Scenes_data = db.session.query(Scenes.scene_name,Scenes.scene_number).distinct(Scenes.scene_number).group_by(
            Scenes.scene_number,Scenes.scene_name).order_by(Scenes.scene_number)
        scenes_data = []
        for data in Scenes_data:
            scenes_data.append({
                'scene_name': data.scene_name,
                'scene_number': data.scene_number
            })
        return jsonify(scenes_data), 201
    elif role =="Cloud":
        message = json.dumps({})
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "scene/setting", message)
        response = mqtt_talker.start()
        if response:
            return jsonify(response), 201
        else:
            return "Request Timeout", 500


@api.route('/device/realtime_group_state', methods=['POST', 'GET'])
def realtime_group_state():
    group_id = request.args.get('group_id', default="", type=str)
    group_state = request.args.get('group_state', default="", type=str)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)

    if role == "Gateway":
        update_node=[]
        for_log = ""
        node_of_group = db.session.query(Group).filter(Group.id == group_id)
        for data in node_of_group:
            group_numb = data.group_num
        # 如果傳進來的為開代表我要將此群組的NODE設為關
        if(group_state == "ON"):
            state_change = "OFF"
            switch.switch_group(int(group_numb), state_change)
            db.session.query(Group).filter(Group.id == group_id).update({Group.group_state: "OFF"})
            state = "UPDATE `group` SET group_state='OFF' WHERE id='%s'"%(group_id)
            for_log = for_log + '\n' + state
            node_of_data = db.session.query(Node).filter(Node.group_id == group_id)

            for data in node_of_data:
                node_num = data.id
                if data.model_type == 1:
                    db.session.query(Node).filter(
                        Node.id == node_num).update({Node.node_state: "OFF"})
                    state = "UPDATE node SET node_state='OFF' WHERE id='%s'"%(node_num)
                    for_log = for_log + '\n' + state
                elif data.model_type == 0:
                    db.session.query(Node).filter(Node.id == node_num).update({Node.node_state: "0"})
                    state = "UPDATE node SET node_state='0' WHERE id='%s'"%(node_num)
                    for_log = for_log + '\n' + state

                update_node.append({
                    'id': data.id,
                    'gateway': data.gateway,
                    'gateway_address': data.gateway_address,
                    'model': data.model,
                    'node_name': data.node_name,
                    'node': data.node,
                    'group_id': data.group_id,
                    'model_type': data.model_type,
                    'node_state': data.node_state
                })

        # 如果傳進來的為關代表我要將此群組的NODE設為開
        elif(group_state == "OFF"):
            state_change = "ON"
            switch.switch_group(int(group_numb),state_change)
            db.session.query(Group).filter(Group.id == group_id).update({Group.group_state: "ON"})
            state = "UPDATE `group` SET group_state='ON' WHERE id='%s'"%(group_id)
            for_log = for_log + '\n' + state
            node_of_data = db.session.query(Node).filter(Node.group_id == group_id).filter(Node.group_id == group_id)

            for data in node_of_data:
                node_num = data.id
                if data.model_type == 1:
                    db.session.query(Node).filter(Node.id == node_num).update({Node.node_state: "ON"})
                    state = "UPDATE node SET node_state='ON' WHERE id='%s'"%(node_num)
                    for_log = for_log + '\n' + state
                elif data.model_type == 0:
                    db.session.query(Node).filter(Node.id == node_num).update({Node.node_state: "100"})
                    state = "UPDATE node SET node_state='100' WHERE id='%s'"%(node_num)
                    for_log = for_log + '\n' + state

                update_node.append({
                    'id': data.id,
                    'gateway': data.gateway,
                    'gateway_address': data.gateway_address,
                    'model': data.model,
                    'node_name': data.node_name,
                    'node': data.node,
                    # 'group_num': data.group_num,
                    'group_id': data.group_id,
                    'model_type': data.model_type,
                    'node_state': data.node_state
                })

        print('UUID:',gateway_uid)
        message =json.dumps(update_node)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "node/update", message)
        response = mqtt_talker.start()

        query_group = db.session.query( Group).filter( Group.id == group_id).all()
        group_data = []
        for data in query_group:
            group_data.append({
                'id': group_id,
                'group_num': data.group_num,
                'group_name': data.group_name,
                'group_state': data.group_state
            })
        message = json.dumps(group_data)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "group/update", message)
        response = mqtt_talker.start()
        log_info(gateway_uid, "update", "realtime change group state", for_log, "ok", "Gateway")
        db.session.commit()
        db.session.close()
        return jsonify({'state': "ok", 'state_change': state_change}), 201
    elif role =="Cloud":

        message = json.dumps({
            "group_id": group_id,
            "group_state": group_state
        })

        print('UUID:',gateway_uid)
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "device/realtime_group_state", message)
        response = mqtt_talker.start()

        if response:
            log_info(gateway_uid, "update", 'realtime change group state', str(message), json.loads(response)['state'],"Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500


@api.route('/device/realtime_node_state', methods=['POST', 'GET'])
def realtime_node_state():
    node_id = request.args.get('node_id', default="", type=str)
    node_state = request.args.get('node_state', default="", type=str)
    node_state_value = request.args.get('node_state_value', default="", type=str)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    if role == "Gateway":
        query_nodes = db.session.query(Node).filter(Node.id == node_id)
        for data in query_nodes:
            node_gateway_address = int(data.gateway_address)
            node_node = int(data.node)
        if(node_state == "ON"):
            state_change = "OFF"
            switch.switch_power(node_gateway_address, node_node, state_change)
            db.session.query(Node).filter(Node.id == node_id).update({Node.node_state: "OFF"})
            state = "\nUPDATE node SET node_state='OFF' WHERE id='%s'"%(node_id)
        elif(node_state == "OFF"):
            state_change = "ON"
            switch.switch_power(node_gateway_address, node_node, state_change)
            db.session.query(Node).filter(Node.id == node_id).update({Node.node_state: "ON"})
            state = "\nUPDATE node SET node_state='ON' WHERE id='%s'"%(node_id)
        elif(node_state >= str(0)):
            state_change = node_state_value
            switch.switch_power(node_gateway_address, node_node, state_change)
            db.session.query(Node).filter(Node.id == node_id).update({Node.node_state: node_state_value})
            state="\nUPDATE node SET node_state='%s' WHERE id='%s'"%(node_state_value,node_id)

        db.session.commit()
        update_node=[]
        query_node = db.session.query(Node).filter(Node.id == node_id)
        for data in query_node:
            update_node.append({
                    'id': data.id,
                    'gateway': data.gateway,
                    'gateway_address': data.gateway_address,
                    'model': data.model,
                    'node_name': data.node_name,
                    'node': data.node,
                    'group_id': data.group_id,
                    'model_type': data.model_type,
                    'node_state': data.node_state
            })
        message =json.dumps(update_node)

        print('UUID:',gateway_uid)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "node/update", message)
        response = mqtt_talker.start()
        log_info(gateway_uid, "update", "realtime change node state", state, "ok", "Gateway")
        state = {}
        state['state'] = "ok"
        db.session.commit()
        db.session.close()
        return jsonify({'state': "ok", 'state_change': state_change}), 201
    elif role=="Cloud":
        message = json.dumps({
            "node_id":node_id,
            "node_state":node_state,
            "node_state_value": node_state_value
            })

        print('UUID:',gateway_uid)
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "device/realtime_node_state", message)
        response = mqtt_talker.start()
        if response:
            log_info(gateway_uid, "update", "realtime change node state", str(
                message), json.loads(response)['state'], "Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500

@api.route('/device/realtime_scene_state', methods=['POST', 'GET'])
def realtime_scene_state():
    scene_number = request.args.get('scene_number', default="", type=str)
    # 先抓取此場景下的點位資料
    gateway_uid = request.args.get('gateway_uid', default="", type=str)

    if role == "Gateway":
        update_node=[]
        for_log = ""
        switch.switch_scene(int(scene_number),"ON")
        scene_nodedata = db.session.query(Scenes).filter(Scenes.scene_number == scene_number)
        for data in scene_nodedata:

            db.session.query(Node).filter(Node.id == data.node).update({Node.node_state: data.node_state})
            query_node = db.session.query(Node).filter(Node.id == data.node)
            for_log = for_log +"\nUPDATE node SET node_state='%s' WHERE id='%s'"%(data.node_state,data.node)
            for datas in query_node:
                update_node.append({
                    'id': datas.id,
                    'gateway': datas.gateway,
                    'gateway_address': datas.gateway_address,
                    'model': datas.model,
                    'node_name': datas.node_name,
                    'node': datas.node,
                    'group_id': datas.group_id,
                    'model_type': datas.model_type,
                    'node_state': datas.node_state
                })
        log_info(gateway_uid, "update", "realtime change scene setting", for_log, "ok", "Gateway")

        print('UUID:',gateway_uid)
        message =json.dumps(update_node)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "node/update", message)
        response = mqtt_talker.start()
        db.session.commit()
        db.session.close()
        return jsonify({'state': "ok"}), 201
    elif role =="Cloud":
        message = json.dumps({
            "scene_number":scene_number
            })
        print('UUID:',gateway_uid)
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "device/realtime_scene_state", message)
        response = mqtt_talker.start()
        if response:
            log_info( gateway_uid, "update", "realtime change scene setting", str(message), json.loads(response)['state'],"Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500

# 點位設定頁面


@api.route('/node_setting/insert', methods=['POST', 'GET'])
def node_setting_insert():
    id = request.args.get('id', default="", type=str)
    node_gateway = request.args.get('node_gateway', default="", type=str)
    node_model = request.args.get('node_model', default="", type=str)
    gateway_address = request.args.get('node_gateway_address', default="", type=str)
    node_name = request.args.get('node_name', default="", type=str)
    node = request.args.get('node', default="", type=str)
    created_at = request.args.get('created_at_insert', default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), type=str)
    updated_at = request.args.get('updated_at_insert', default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), type=str)
    group_id = request.args.get('group_id', default=None, type=str)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    state = {}

    if role == "Gateway":
        # 檢查有無超過256筆資料
        data_counts = db.session.query(func.count(Node.node)).all()[0][0]
        if data_counts >= 256:
            state["state"] = "failed"
            log_info(gateway_uid, "insert", "node", None, "overcount", "Gateway")
            db.session.commit()
            db.session.close()
            return jsonify({'status':'overcount'}, state), 201
        # 重複檢查先確定有無重複的點位，無則新增點位
        data_repeat = db.session.query(Node.gateway_address, Node.node).filter(or_(and_(Node.gateway_address == gateway_address, Node.node == node),Node.node_name==node_name)).first()
        if data_repeat is None:
            if node_model in model_percent:
                insert_data = Node(
                    None,
                    node_gateway,
                    node_model,
                    node_name,
                    node,
                    gateway_address,
                    created_at,
                    updated_at,
                    "0",
                    "0",
                    group_id,
                )
                insert_sql = "\nINSERT INTO node(gateway,gateway_address,model,node_name,node,created_at,updated_at,model_type,node_state)VALUES('%s','%s','%s','%s','%s','%s','%s','0','0')"%(node_gateway,gateway_address,node_model,node_name,node,created_at,updated_at)
            else:
                insert_data = Node(
                    None,
                    node_gateway,
                    node_model,
                    node_name,
                    node,
                    gateway_address,
                    created_at,
                    updated_at,
                    "1",
                    "OFF",
                    group_id,
                )
                insert_sql = "\nINSERT INTO node(gateway,gateway_address,model,node_name,node,created_at,updated_at,model_type,node_state)VALUES('%s','%s','%s','%s','%s','%s','%s','1','OFF')"%(node_gateway,gateway_address,node_model,node_name,node,created_at,updated_at)

            db.session.add(insert_data)
            # 存取所有的點位並回傳
            Node_data = db.session.query(Node).filter(
                and_(Node.gateway_address == gateway_address, Node.node == node)).all()
            node_data = []
            for data in Node_data:
                node_data.append({
                    'id': data.id,
                    'gateway': data.gateway,
                    'gateway_address': data.gateway_address,
                    'model': data.model,
                    'node_name': data.node_name,
                    'node': data.node,
                    "node_state": data.node_state
                })

            message =json.dumps(node_data)
            mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "node/insert", message)
            response = mqtt_talker.start()
            log_info(gateway_uid, "insert", "node", insert_sql, "ok", "Gateway")
            db.session.commit()
            db.session.close()
            return jsonify({'status': 'ok'}, node_data), 201
        else:
            state["status"] = "failed"
            log_info(gateway_uid, "insert", "node",None, "repeat error", "Gateway")
            return jsonify({'status': 'repeat error'}, state), 201
    elif role =="Cloud":
        message = json.dumps({
            "node_gateway": node_gateway,
            "node_model": node_model,
            "gateway_address": gateway_address,
            "node_name": node_name,
            "node": node,
            "created_at": created_at,
            "updated_at": updated_at,
            "group_id": group_id
        })
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_uid, "node_setting/insert", message)
        response = mqtt_talker.start()
        if response:
            log_info(gateway_uid, "insert", 'node', str(message),json.loads(response)[0]['status'],"Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500


@api.route('/node_setting/update', methods=['POST', 'GET'])
def node_setting_update():
    # Get the identification of the device, and the time to check
    node_id = request.args.get('node_id', default="1", type=str)
    node_update_gateway = request.args.get('node_gateway', default="1", type=str)
    node_update_gateway_address = request.args.get('node_gateway_address', default="950", type=str)
    node_update_model = request.args.get('node_model', default="LT2014", type=str)
    node_update_node_name = request.args.get('node_name', default="15", type=str)
    node_update_node = request.args.get('node', default="15", type=str)
    node_origin_gateway = request.args.get('node_origin_gateway', default="15", type=str)
    node_origin_node = request.args.get('node_origin_node', default="15", type=str)
    # node_group_state_update = request.args.get('group_state', default="1", type=int)
    node_updated_at = request.args.get('updated_at', default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), type=str)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    state={}
    if role == "Gateway":
        # 先更新原本的點位與位址為空
        db.session.query(Node).filter(Node.id == node_id).update(
            {Node.gateway_address: None, Node.node: None, Node.node_name: None})
        # 去判斷有無相同的點位
        data_repeat = db.session.query(Node.gateway_address, Node.node).filter(or_(and_(
            Node.gateway_address == node_update_gateway_address, Node.node == node_update_node), Node.node_name == node_update_node_name)).first()
        if data_repeat is not None:
            state['state'] = "repeat error"
            log_info(gateway_uid, "update", "node", None, "repeat error", "Gateway")
            return jsonify(state), 201
        if(node_update_model in model_percent):
            db.session.query(Node).filter(Node.id == node_id).update({
                Node.gateway: node_update_gateway,
                Node.gateway_address: node_update_gateway_address,
                Node.model: node_update_model,
                Node.node_name: node_update_node_name,
                Node.node: node_update_node,
                Node.updated_at: node_updated_at,
                Node.node_state: "0",
                Node.model_type: "0"
            })
            sql="\nUPDATE node SET gateway= '%s',gateway_address= '%s',model= '%s',node_name= '%s',node= '%s',updated_at= '%s',model_type = '0',node_state= '0' WHERE id='%s'"%(node_update_gateway,node_update_gateway_address,node_update_model,node_update_node_name,node_update_node,node_updated_at,node_id)

        else:
            db.session.query(Node).filter(Node.id == node_id).update({
                Node.gateway: node_update_gateway,
                Node.gateway_address: node_update_gateway_address,
                Node.model: node_update_model,
                Node.node_name: node_update_node_name,
                Node.node: node_update_node,
                Node.updated_at: node_updated_at,
                Node.model_type: "1"
            })
            sql="\nUPDATE node SET gateway= '%s',gateway_address= '%s',model= '%s',node_name= '%s',node= '%s',updated_at= '%s',model_type = '1',node_state= 'OFF' WHERE id='%s'"%(node_update_gateway,node_update_gateway_address,node_update_model,node_update_node_name,node_update_node,node_updated_at,node_id)
        update_node=[]
        query_node = db.session.query(Node).filter(Node.id == node_id)
        for datas in query_node:
            update_node.append({
                    'id': datas.id,
                    'gateway': datas.gateway,
                    'gateway_address': datas.gateway_address,
                    'model': datas.model,
                    'node_name': datas.node_name,
                    'node': datas.node,
                    # 'group_num': data.group_num,
                    'group_id': datas.group_id,
                    'model_type': datas.model_type,
                    'node_state': datas.node_state
            })
        message =json.dumps(update_node)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "node/update", message)
        response = mqtt_talker.start()
        state['state'] = "ok"
        log_info(gateway_uid, "update", "node", sql, "ok", "Gateway")
        db.session.commit()
        db.session.close()
        return jsonify(state), 201
    elif role =="Cloud":
        message = json.dumps({
            "node_id" :node_id,
            "node_update_gateway":node_update_gateway,
            "node_update_gateway_address": node_update_gateway_address,
            "node_update_model": node_update_model,
            "node_update_node_name": node_update_node_name,
            "node_update_node":node_update_node,
            "node_updated_at": node_updated_at
        })
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_uid, "node_setting/update", message)
        response = mqtt_talker.start()
        if response:
            log_info( gateway_uid, "update", 'node', str(message), json.loads(response)['state'],'Cloud')
            return jsonify(response), 201
        else:
            return "Request Timeout", 500


@api.route('/node_setting/delete', methods=['POST', 'GET'])
def node_setting_delete():
    node_id = request.args.get('id', default="", type=str)
    node = request.args.get('node', default="255", type=str)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    state = {}

    if role == "Gateway":
        for_log = ""
        node_data = db.session.query(Node).filter(Node.id == node_id).first()
        nodedata_delete = db.session.query(Scenes).filter(Scenes.node == node).all()
        db.session.delete(node_data)
        for_log =for_log +'\n'+"DELETE FROM node WHERE id='%s'"%(node_id)
        if nodedata_delete:
            for data in nodedata_delete:
                db.session.delete(data)
                for_log =for_log +'\n'+"DELETE FROM scenes WHERE node='%s'"%(data.node)
        state['state'] = "ok"
        delete_node_data=[]
        delete_node_data.append({
            'id': node_id
        })
        message =json.dumps(delete_node_data)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "node/delete", message)
        response = mqtt_talker.start()
        log_info(gateway_uid, "delete", "node", for_log, "ok", "Gateway")
        db.session.commit()
        db.session.close()
        return jsonify(state), 201
    elif role =="Cloud":
        message = json.dumps({

            "gateway_uid": gateway_uid,
            "node": node,
            "node_id": node_id
        })
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "node_setting/delete", message)
        response = mqtt_talker.start()
        if response:
            log_info(gateway_uid, "delete", "node", str(message), json.loads(response)['state'],'Cloud')
            return jsonify(response), 201
        else:
            return "Request Timeout", 500

# 群組設定頁面


@api.route('/group_setting/insert', methods=['POST', 'GET'])
def group_setting_insert():
    node = []
    group_name = request.args.get('group_name', default="", type=str)
    group_num = request.args.get('group_num', default="", type=str)
    length = request.args.get('length', default="", type=int)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    state = {}

    for i in range(0, length, 1):
        node.append(request.args.get('check_node[' + str(i) + ']', default="", type=str))
    if role == "Gateway":
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        data_repeat = db.session.query(Group.group_num).filter(or_(Group.group_num == group_num,Group.group_name == group_name)).first()
        id = ""
        for_log = ""
        # 檢查有無超過60筆資料
        data_counts = db.session.query(func.count(Group.id)).all()[0][0]
        if data_counts >= 32:
            state["state"] = "failed"
            log_info(gateway_uid, "insert", "group", None, "overcount", "Gateway")
            return jsonify({"status":"overcount"}, state), 201
        elif data_repeat is None:
            insert_data = Group(
                None,
                group_num,
                group_name,
                "OFF",
                current_time,
                current_time
            )
            for_log = for_log+"\n"+"INSERT INTO `group`(group_num,group_name,group_state,created_at,updated_at)VALUES('%s','%s','OFF','%s','%s')"%(group_num,group_name,current_time,current_time)
            db.session.add(insert_data)
            state["state"] = "ok"
            # 新增資料後取出資料並回傳
            Group_data = db.session.query(Group).filter(and_(Group.group_num == group_num, Group.group_name == group_name)).all()
            group_data = []
            for data in Group_data:
                group_data.append({
                    'id': data.id,
                    'group_num': data.group_num,
                    'group_name': data.group_name,
                    'group_state': data.group_state,
                    'created_at': data.created_at,
                    'updated_at': data.updated_at
                })
            message =json.dumps(group_data)
            mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "group/insert", message)
            response = mqtt_talker.start()
            # 新增此群組到各個排程中(首先取出該群組ID在取出所有排程的星期與時間並新增此群組至排程中)
            newgroup_id = db.session.query(Group.id).filter(Group.group_num == group_num).first()[0]
            Schedule_data = db.session.query(Schedule.control_time, Schedule.control_time_of_sun, Schedule.schedule_table).distinct(
            Schedule.control_time, Schedule.schedule_table)
            schedule_group_state = "OFF"
            new_group_data = []
            for d in Schedule_data:
                new_group_data = Schedule(None, d.schedule_table, newgroup_id, schedule_group_state, d.control_time, d.control_time_of_sun,"false")
                db.session.add(new_group_data)
                ct = d.control_time_of_sun
                sql = "INSERT INTO schedule(schedule_table,group_id,schedule_group_state,control_time,control_time_of_sun,setting)VALUES('%s','%s','%s','%s','%s','false')" % (
                    d.schedule_table, newgroup_id, schedule_group_state, d.control_time, d.control_time_of_sun)
                for_log = for_log+"\n"+sql
            # 更新此點位綁定的群組ID
            for i in range(0, length, 1):
                db.session.query(Node).filter(Node.id == node[i]).update({Node.group_id: group_data[0]['id']})
                sql="UPDATE node SET group_id= '%s' WHERE id='%s'"%(node[i],group_data[0]['id'])
                for_log = for_log+"\n"+sql
            db.session.commit()
            switch.set_group(group_data[0]["id"])
            log_info(gateway_uid, "insert", "group", for_log, "ok", "Gateway")

            db.session.close()
            return jsonify(group_data, state), 201
        # 有重複
        else:
            state["state"] = "failed"
            log_info(gateway_uid, "insert", "group", None, "repeat error", "Gateway")
            return jsonify({"status":"repeat error"}, state), 201
    elif role == "Cloud":
        message = json.dumps({
            "group_name": group_name,
            "group_num": group_num,
            "length": length,
            "node": node
        })
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_uid, "group_setting/insert", message)
        response = mqtt_talker.start()
        if response:
            log_info(gateway_uid, 'insert','the node bind group', str(message),json.loads(response)[1]['state'],"Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500
@api.route('/group_setting/delete', methods=['POST', 'GET'])
def group_setting_delete():
    group_id = request.args.get('group_id', default="", type=str)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    state = {}
    if role == "Gateway":
        for_log = ""
        switch.delete_group(group_id)
        data_repaet = db.session.query(Group).filter(
            Group.id == group_id).first()
        db.session.query(Node).filter(Node.group_id == group_id).update({Node.group_id: None})
        group_data = db.session.query(Schedule).filter(Schedule.group_id == group_id).all()
        db.session.delete(data_repaet)
        for_log = for_log+"\n"+"UPDATE node SET group_id=NULL WHERE group_id='%s'"%(group_id)
        for_log = for_log+"\n"+"DELETE FROM `group` WHERE id='%s'"%(group_id)
        for_log = for_log+"\n"+"DELETE FROM schedule WHERE group_id='%s'"%(group_id)
        for data in group_data:
            db.session.delete(data)
        log_info(gateway_uid, "delete", "group", for_log, "ok", "Gateway")
        state['state'] = "ok"
        group_data = []
        group_data.append({'id': group_id})
        message =json.dumps(group_data)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "group/delete", message)
        response = mqtt_talker.start()
        db.session.commit()
        db.session.close()
        return jsonify(state), 201
    elif role == "Cloud":
        message = json.dumps({
            "group_id": group_id,
        })
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "group_setting/delete", message)
        response = mqtt_talker.start()
        if response:
            log_info(gateway_uid, "delete", "group",str(message),json.loads(response)['state'],"Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500


@api.route('/group_setting/update', methods=['POST', 'GET'])
def group_setting_update():
    node = []
    group_id = request.args.get('group_id', default="", type=str)
    group_name = request.args.get('group_name', default="", type=str)
    group_num = request.args.get('group_num', default="", type=str)
    length = request.args.get('length', default="", type=int)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    state = {}

    for i in range(0, length, 1):
        node.append(request.args.get('check_node[' + str(i) + ']', default="", type=str))
    if role == "Gateway":
        updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if db.session.query(Group.group_num).filter(and_(or_(Group.group_num == group_num,Group.group_name == group_name), Group.id != group_id)).first() is not None:
            state['state'] = "name_number_repeat"
            log_info(gateway_uid, "update", "group", None, "repeat error", "Gateway")
            return jsonify({'status': 'repeat error'}, state), 201
        for_log = ""
        switch.delete_group(group_id)
        # 更新群組名稱
        db.session.query(Group).filter(Group.id == group_id).update({Group.group_num: group_num, Group.group_name: group_name})
        for_log = for_log + "\n" +"UPDATE `group` SET group_num='%s',group_name='%s' WHERE id='%s'"%(group_num,group_name,group_id)
        # log_info(gateway_uid, "update group ", "group_id: " + str(group_id) + "\ngroup number: " +str(group_num) + "\ngroup_name: " + str(group_name) + "\nnode_id: " + str(node))
        db.session.query(Node).filter(Node.group_id == group_id).update({Node.group_id: None, Node.updated_at: current_time})
        for_log = for_log + "\n" +"UPDATE node SET group_id=NULL,updated_at='%s' WHERE group_id='%s'"%(updated_at,group_id)
        for i in range(0, length, 1):
            db.session.query(Node).filter(Node.id == node[i]).update({Node.group_id: group_id, Node.updated_at: current_time})
            for_log = for_log + "\n" +"UPDATE node SET group_id='%s',updated_at='%s' WHERE id='%s'"%(group_id,updated_at,node[i])
            # log_info(gateway_uid,"update group bind node","group number: "+str(group_num)+"\ngroup_name: "+str(group_name)+"\nnode_id: "+str(node[i]))
        state["state"] = "ok"
        # 回傳資訊
        Group_data = db.session.query(Group).filter(and_(Group.id == group_id, Group.group_name == group_name)).all()
        group_data = []
        for data in Group_data:
            group_data.append({
                'id': data.id,
                'group_num': data.group_num,
                'group_name': data.group_name,
                'group_state': data.group_state,
                'created_at': data.created_at,
                'updated_at': data.updated_at
            })
        message =json.dumps(group_data)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "group/update", message)
        response = mqtt_talker.start()
        db.session.commit()
        switch.set_group(group_id)
        log_info(gateway_uid, "update", "group", for_log, "ok", "Gateway")

        db.session.close()
        return jsonify(group_data, state), 201
    elif role == "Cloud":
        message = json.dumps({
                'group_id': group_id,
                'group_num': group_num,
                'group_name': group_name,
                # 'group_state': group_state,
                'length': length,
                'node': node
        })
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "group_setting/update", message)
        response = mqtt_talker.start()
        if response:
            log_info(gateway_uid, "update",  "group", str(message),json.loads(response)[1]['state'], "Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500



# 場景設定頁面

@api.route('/scene_setting/setting', methods=['POST', 'GET'])
def scene_setting_setting():
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    state = {}

    if role == "Gateway":
        Node_data = db.session.query(Node).all()
        scenes_node_data = []
        for data in Node_data:
            if data.model in model_percent:
                scenes_node_data.append({
                    'id': data.id,
                    'model': data.model,
                    'node_name': data.node_name,
                    'scene_node_state': "0",
                })
            else:
                scenes_node_data.append({
                    'id': data.id,
                    'model': data.model,
                    'node_name': data.node_name,
                    'scene_node_state': "1",
                })
        state['state'] = "ok"
        db.session.close()
        return jsonify(state, scenes_node_data), 201
    elif role == "Cloud":
        message = json.dumps({})
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_uid, "scene_setting/setting", message)
        response = mqtt_talker.start()
        if response:
            return jsonify(response), 201
        else:
            return "Request Timeout", 500

@api.route('/scene_setting/insert', methods=['POST', 'GET'])
def scene_setting_insert():
    scene_name = request.args.get('scene_name', default="", type=str)
    scene_number = request.args.get('scene_number', default="", type=str)
    length = request.args.get('length', default="", type=int)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    node_id = []
    node_state = []
    node_value = []
    state={}
    for i in range(0, length, 1):
        node_id.append(request.args.get(
            'check_node_id[' + str(i) + ']', default="", type=str))
        node_state.append(request.args.get(
            'scene_node_state[' + str(i) + ']', default="", type=str))
        node_value.append(request.args.get(
            'nodevalue[' + str(i) + ']', default="", type=str))

    if role == "Gateway":
        created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for_log = ""
        # (1)場景有無超過60筆(2)場景編號有無重複(3)無重複則插入場景
        if db.session.query(func.count(Scenes.scene_number)).distinct()[0][0] >= 60:
            state['state'] = "failed"
            log_info(gateway_uid, "insert", "scene", None, "overcount", "Gateway")
            return jsonify({'state':'overcount'},state), 201
        elif db.session.query(Scenes).filter(or_(Scenes.scene_number == scene_number,Scenes.scene_name == scene_name )).first():
            state['state'] = "failed"
            log_info(gateway_uid, "insert", "scene", None, "repeat error", "Gateway")
            return jsonify({'state':'repeat error'},state), 201
        else:
            id = ""
            for i in range(0, length, 1):
                    insert_data = Scenes(None, node_id[i], node_value[i], scene_name, scene_number, created_at, created_at)
                    db.session.add(insert_data)
                    for_log = for_log + "\n" +"INSERT INTO scenes(node,node_state,scene_name,scene_number,created_at)VALUES('%s','%s','%s','%s','%s')"%(node_id[i], node_value[i], scene_name, scene_number, created_at)
            scene_data = db.session.query(Scenes).filter(Scenes.scene_number == scene_number).all()
            scene_node_data_output = []
            for data in scene_data:
                scene_node_data_output.append({
                    'id': data.id,
                    'node': data.node,
                    'node_state': data.node_state,
                    'scene_name': data.scene_name,
                    'scene_number': data.scene_number,
                    'created_at': data.created_at,
                    'updates_at': data.updated_at,
                })
            db.session.commit()
            switch.set_scene(int(scene_number))
            message =json.dumps(scene_node_data_output)
            mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "scene/insert", message)
            response = mqtt_talker.start()
            state['state'] = "ok"
            log_info(gateway_uid, "insert", "scene", for_log, "ok", "Gateway")

            db.session.close()
            return jsonify(state,scene_node_data_output), 201
    elif role == "Cloud":
        message = json.dumps({
            'node_id': node_id,
                'node_state': node_state,
                'node_value':node_value,
                'scene_name': scene_name,
                'scene_number': scene_number,
                'length':length
        })
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_uid, "scene_setting/insert", message)
        response = mqtt_talker.start()
        if response:
            log_info(gateway_uid, "insert", "scene", str(message),json.loads(response)[0]['state'],"Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500


@api.route('/scene_setting/delete', methods=['POST', 'GET'])
def scene_setting_delete():
    scene_number = request.args.get('scene_num', default="", type=str)
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    state = {}

    if role == "Gateway":
        switch.delete_scene(int(scene_number))
        db.session.query(Scenes).filter(Scenes.scene_number == scene_number).delete()
        sql="\nDELETE FROM scenes WHERE scene_number='%s'"%(scene_number)
        log_info(gateway_uid, "delete", "scene", sql, "ok", "Gateway")
        scene_data = []
        scene_data.append({'scene_number': scene_number})
        message =json.dumps(scene_data)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "scene/delete", message)
        response = mqtt_talker.start()
        state['state'] = "ok"
        db.session.commit()
        db.session.close()
        return jsonify(state), 201
    elif role == "Cloud":
        message = json.dumps({
                'scene_number': scene_number,
        })
        mqtt_talker = mqtttalker.MqttTalker(cloud_mqtt_host, gateway_uid, "scene_setting/delete", message)
        response = mqtt_talker.start()
        if response:
            log_info(gateway_uid, "delete", "scene", str(message),json.loads(response)['state'],"Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500

@api.route('/scene_setting/update_information', methods=['POST', 'GET'])
def scene_setting_update_information():
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    if role == "Gateway":
        Scenes_data = Scenes.query.join(Node, Scenes.node == Node.id).add_columns(Scenes.scene_number, Scenes.scene_name, Scenes.node, Scenes.node_state,  Node.id, Node.node_name, Node.model, Node.model_type).filter(Scenes.node == Node.id).filter(Node.id == Scenes.node)
        Node_node = db.session.query(Node).all()
        Node_model = db.session.query(Node.model).distinct()
        scene_record = db.session.query(Scenes.scene_number).distinct()
        scene_record_number = []
        for data in scene_record:
            scene_record_number.append(data.scene_number)
        node_storage = []
        node_data = []
        scenes_data = []
        model_type = []
        for model_data in Node_model:
            model_type.append(model_data.model)
        for data in Scenes_data:
            scenes_data.append({
                'scene_number': data.scene_number,
                'scene_name': data.scene_name,
                'node': data.Scenes.node,
                'node_state': data.node_state,
                'node_name': data.node_name,
                'node_model': data.model,
                'model_type': data.model_type
            })
        for data in Node_node:
            node_data.append({
                'id': data.id,
                'node_name': data.node_name,
                'node_model': data.model,
                'model_type': data.model_type
            })
        scene_information = {}
        node_record = {}
        node_not_record = {}
        for scene_number in scene_record_number:
            scene_information[str(scene_number)] = []
        for scene_number in scene_record_number:
            node_record[str(scene_number)] = []
            node_not_record[str(scene_number)] = []

        for scene_number in scene_record_number:
            for data in scenes_data:
                if(data['scene_number'] == scene_number):
                    node_record[str(scene_number)].append(data['node'])
            for data in node_data:
                if(data['id'] not in node_record[str(scene_number)]):
                    node_not_record[str(scene_number)].append(data['id'])

        for scene_number in scene_record_number:
            for data in scenes_data:
                if(data['scene_number'] == scene_number):
                    scene_information[str(scene_number)].append({
                        'scene_number': data['scene_number'],
                        'scene_name': data['scene_name'],
                        'node': data['node'],
                        'node_state': data['node_state'],
                        'node_name': data['node_name'],
                        'node_model': data['node_model'],
                        'model_type': data['model_type']
                    })
            # 為每個場景加上沒有的點位資訊
            for data in node_not_record[str(scene_number)]:
                for node_datas in node_data:
                    if data == node_datas['id']:
                        scene_information[str(scene_number)].append({
                            'scene_number': scene_number,
                            'scene_name': "",
                            'node': node_datas['id'],
                            'node_name': node_datas['node_name'],
                            'node_model': node_datas['node_model'],
                            'model_type': node_datas['model_type']
                        })
        db.session.commit()
        db.session.close()
        return jsonify(scenes_data, node_data, scene_information, model_type), 201
    elif role == "Cloud":
        message = json.dumps({})
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "scene_setting/update_information", message)
        response = mqtt_talker.start()
        if response:
            return jsonify(response), 201
        else:
            return "Request Timeout", 500


@api.route('/scene_setting/update', methods=['POST', 'GET'])
def scene_setting_update():
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    origin_scene_number = request.args.get('origin_scene_number', default="", type=str)
    origin_scene_name = request.args.get('origin_scene_name', default="", type=str)
    scene_name = request.args.get('scene_name', default="", type=str)
    scene_number = request.args.get('scene_number', default="", type=str)
    length = request.args.get('length', default="", type=int)
    created_at = request.args.get('created_at', default="", type=datetime)
    node_id = []
    node_value = []
    model_type = []
    state = {}
    for_log = ""
    for i in range(0, length, 1):
        node_id.append(request.args.get('check_node[' + str(i) + ']', default="", type=int))  # 要插入已經要更改的node
        node_value.append(request.args.get('value[' + str(i) + ']', default="", type=str))
        model_type.append(request.args.get('model_type[' + str(i) + ']', default="", type=str))

    if role == "Gateway":
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        exists_scene_number = []

        # 判斷名稱、編號是否有無重複情形
        if(origin_scene_number == scene_number) and (origin_scene_name != scene_name):
            data_repeat = Scenes.query.filter(Scenes.scene_name == scene_name,Scenes.scene_number != scene_number).first()
            if data_repeat is not None:
                log_info(gateway_uid, "update", "scene", None, "repeat error", "Gateway")
                return jsonify({'state':'repeat error'})
        elif(origin_scene_number != scene_number) and (origin_scene_name == scene_name):
            data_repeat = Scenes.query.filter(Scenes.scene_number == scene_number).first()
            if data_repeat is not None:
                log_info(gateway_uid, "update", "scene", None, "repeat error", "Gateway")
                return jsonify({'state':'repeat error'})
        elif(origin_scene_number != scene_number) and (origin_scene_name != scene_name):
            data_repeat = Scenes.query.filter(or_(Scenes.scene_number == scene_number,Scenes.scene_name == scene_name)).first()
            if data_repeat is not None:
                log_info(gateway_uid, "update", "scene", None, "repeat error", "Gateway")
                return jsonify({'state':'repeat error'})
        switch.delete_scene(int(origin_scene_number))
        exists_number = db.session.query(Scenes).filter(Scenes.scene_number == origin_scene_number).all()
        # 取出該場景所擁有的點位
        for data in exists_number:
            exists_scene_number.append(data.node)
        # 先取出該場景所有點位、並將現在將要更改的點位比較，不再裡面則先刪除
        for delete_number in exists_scene_number:
            if delete_number not in node_id:
                Scenes.query.filter(and_(Scenes.scene_number == origin_scene_number, Scenes.node == delete_number)).delete()
                for_log = for_log + "\n" +"DELETE FROM scenes WHERE scene_number='%s' AND node='%s'"%(origin_scene_number,delete_number)

        # 更新場景點位的狀態
        for i in range(0, length, 1):
            if node_id[i] in exists_scene_number:
                Scenes.query.filter(and_(Scenes.node == node_id[i], Scenes.scene_number == origin_scene_number)).update({'node_state': node_value[i], 'scene_name': scene_name, 'scene_number': scene_number, 'updated_at': updated_at})
                for_log = for_log + "\n" +"UPDATE scenes SET node_state='%s',scene_name='%s',scene_number='%s',updated_at='%s' WHERE node='%s' AND scene_number='%s'"%( node_value[i],scene_name,scene_number,updated_at,node_id[i],origin_scene_number)
            elif node_id[i] not in exists_scene_number:
                insert_data = Scenes(None, node_id[i], node_value[i], scene_name, scene_number, created_at, updated_at)
                for_log = for_log + "\n" +"INSERT INTO scenes(node,node_state,scene_name,scene_number,created_at,updated_at)VALUES('%s','%s','%s','%s','%s','%s')"%( node_id[i], node_value[i], scene_name, scene_number, created_at, updated_at)
                db.session.add(insert_data)
        db.session.commit()
        switch.set_scene(int(scene_number))
        scene_data = []
        scene_data.append({
            'origin_scene_number':origin_scene_number,
            'scene_number':scene_number,
            'scene_name':scene_name
        })
        message =json.dumps(scene_data)
        mqtt_talker = mqtttalker_client.MqttTalker(mqtt_host, gateway_uid, "scene/update", message)
        response = mqtt_talker.start()
        state['state'] = "ok"
        log_info(gateway_uid, "update", "scene", for_log, "ok", "Gateway")

        db.session.close()
        return jsonify(state), 201
    elif role == "Cloud":
        message = json.dumps({
            'origin_scene_number':origin_scene_number,
            'origin_scene_name': origin_scene_name,
            'scene_name':scene_name,
            'scene_number':scene_number,
            'length':length,
             'node_id':node_id,
             'node_value':node_value,
        })
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "scene_setting/update", message)
        response = mqtt_talker.start()
        if response:
            log_info(gateway_uid, "update", "scene ",str(message),json.loads(response)['state'],"Cloud")
            return jsonify(response), 201
        else:
            return "Request Timeout", 500







