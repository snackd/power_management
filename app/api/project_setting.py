import json
import datetime

from flask import jsonify, request, session
from sqlalchemy import func, and_, or_, between, exists

from . import api
from .. import db
from config import role
from ..models import *

from . import mqtt_talker as mqtttalker

from config import role
from .log import log_info

# from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.setting import *


@api.route('/project_change', methods=['POST', 'GET'])
def project_change():
    result = False
    message = ''
    data_array = {}

    try:
        node_id = request.form.get('node_id', default=0, type=int)
        project_id = request.form.get('project_id', default=0, type=int)
        update_node_project = "UPDATE `node_list` SET `project_id`={} WHERE `id`={}".format(project_id, node_id)
        update_node_project_result = db.engine.execute(update_node_project)
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


@api.route('/project_add', methods=['POST', 'GET'])
def project_add():
    result = False
    message = ''
    data_array = {}

    try:
        project_name = request.form.get('project_name', default='', type=str)
        insert_project_sql = "INSERT INTO `project_list` (`user_id`, `name`) VALUES ({}, '{}')".format(session['user-id'], project_name)
        insert_project_result = db.engine.execute(insert_project_sql)
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


@api.route('/project_modify', methods=['POST', 'GET'])
def project_modify():
    result = False
    message = ''
    data_array = {}

    try:
        project_id = request.form.get('project_id', default=0, type=int)
        project_name = request.form.get('project_name', default='', type=str)
        update_project_sql = "UPDATE `project_list` SET `name`='{}' WHERE `id`={}".format(project_name, project_id)
        update_project = db.engine.execute(update_project_sql)
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


@api.route('/project_delete', methods=['POST', 'GET'])
def project_delete():
    result = False
    message = ''
    data_array = {}

    try:
        delete_project_id = request.form.get('delete_project_id', default=0, type=int)
        replace_project_id = request.form.get('replace_project_id', default=0, type=int)

        replace_project_sql = "UPDATE `node_list` SET `project_id`='{}' WHERE `project_id`={}".format(replace_project_id, delete_project_id)
        replace_project = db.engine.execute(replace_project_sql)

        delete_project_sql = "DELETE FROM `project_list` WHERE `id` = {}".format(delete_project_id)
        delete_project = db.engine.execute(delete_project_sql)
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
