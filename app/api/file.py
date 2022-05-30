import json

from flask import jsonify, request, Response
from sqlalchemy import func, and_, or_, between, exists

from . import api
from .. import db
from ..models import *

from . import mqtt_talker as mqtttalker

from config import role, G_CONTROL_VALUE_TYPE_LIST
from ..api import lib_read_file as read_file
from .log import log_info

@api.route('/export_all', methods=['POST', 'GET'])
def export_all():
    result = False
    message = ''
    data_array = {}

    try:
        download_dict = {}
        gateway_id = request.args.get('gateway_id', default=0, type=int)

        table_name_array = ['device_list', 'area_list', 'area_node_list', 'demand_setting', 'group_list',
                            'group_node_list', 'scene_list', 'scene_node_list', 'unload_group_list',
                            'unload_group_node_list', 'node_list'];
        for table_name in table_name_array:
            get_table_list_sql = 'SELECT * FROM {} WHERE `gateway_id` = {}'.format(table_name, gateway_id)
            get_table_list = db.engine.execute(get_table_list_sql).fetchall()
            download_dict[table_name] = [[(value if isinstance(value, int) else str(value)) for value in rowproxy] for rowproxy in get_table_list]

        download_json = json.dumps(download_dict)
        return Response(download_json,
                        mimetype='application/json',
                        headers={'Content-Disposition': 'attachment;filename=export-all.json'})
    except Exception as e:
        message = str(e)
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)

@api.route('/upload_file', methods=['POST', 'GET'])
def upload_file():
    result = False
    message = ''
    data_array = {}

    try:
        file = request.files['upload_file']
        if file and read_file.is_allowed_file(file):
            filename = file.filename
            file_data = json.load(file)
            for table_name, data in file_data.items():
                insert_data = ''
                for each_data in data:
                    data_string = ','.join([(str(value) if isinstance(value, int) else ('NULL' if str(value) == 'None' else '\''+str(value)+'\'')) for value in each_data])
                    insert_data += ', ({})'.format(data_string) if len(insert_data) >0 else '({})'.format(data_string)
                insert_data_sql = 'INSERT INTO {} VALUES {}'.format(table_name, insert_data)
                insert_data_result = db.engine.execute(insert_data_sql)
            result = True
        else:
            message = '檔案不支援!'
            result = False

    except Exception as e:
        message = str(e)
    finally:
        data = {
            'result': result,
            'message': message,
            'data': data_array
        }
        return jsonify(data)