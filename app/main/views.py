from flask import render_template, url_for
from flask import Flask, session, redirect, url_for, escape, request
from sqlalchemy import func, and_, or_, between, exists, extract
from . import main
# from . import UserCheck
from ..models import *
from ..models import User as user
from .. import db
# system role
from config import role, G_CONTROL_VALUE_TYPE_LIST
import json
import sys, os
from datetime import datetime, date, time, timedelta
from ..api import lib_read_demand as demand
# from datetime import timedelta

# 初始化一個Flask實例
app = Flask(__name__)

# 裝飾器設定路由

global message
message = None
global error
error = None
global authority
authority = None


@main.route('/')
def index():
    global authority
    global message
    global error
    session['role'] = role
    user_sql = "SELECT `id`, `account`, `password_hash`" \
               "FROM `user_list` LIMIT 1"
    user_sql_object = db.engine.execute(user_sql).fetchall()

    if role == "Gateway" and len(user_sql_object) == 0:
        return render_template('index.html', setting="setting")
    elif 'account' in session:
        if message == "Register Successful":
            register_message = message
            message = None
            return render_template("index.html", message=register_message, session_user_name=session['account'],
                                   authority=authority)
        user_sql = "SELECT `id`, `account`, `password_hash`, `authority`" \
                   "FROM `user_list` WHERE `account` = '{}' LIMIT 1".format(session['account'])
        user_sql_object = db.engine.execute(user_sql).fetchall()
        if user_sql_object[0][3] is None:
            return render_template('index.html')
        else:
            return render_template('index.html', session_user_name=session['account'], authority=user_sql_object[0][3])
    elif message:
        index_message = message
        message = None
        return render_template("index.html", message=index_message)
    elif error:
        index_error = error
        error = None
        return render_template("index.html", error=index_error)
    else:
        return render_template('index.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    global authority
    global message
    if request.method == 'POST':
        account = request.form['inputaccount']
        password = request.form['inputpassword']
        register_result = user.register_user(account, password)
        # 無此帳號創建帳號並存取權限
        if register_result is False:
            account_authority = db.session.query(
                User.authority).filter(User.account == account).first()
            session['account'] = account
            authority = account_authority.authority
            message = "Register Successful"
            return redirect(url_for('main.index'))
        # 相同帳號
        else:
            message = "Your account already exist"
            return redirect(url_for('main.index'))
    else:
        return render_template("index.html")


@main.route('/login', methods=['GET', 'POST'])
def login():
    global error
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        user_sql = "SELECT `id`, `account`, `password_hash`" \
                        "FROM `user_list` WHERE `account` = '{}' LIMIT 1".format(account)
        user_sql_object = db.engine.execute(user_sql).fetchall()
        if len(user_sql_object) > 0:
            rs = check_password_hash(user_sql_object[0][2], password)
            if rs:
                if role == 'Gateway':
                    gateway_sql = "SELECT `id`, `mac_address` FROM `gateway_list` LIMIT 1"
                    gateway_sql_object = db.engine.execute(gateway_sql).fetchall()
                    session['gateway-id'] = gateway_sql_object[0][0]
                    session['gateway-mac-address'] = gateway_sql_object[0][1]
                session['account'] = user_sql_object[0][1]
                session['user-id'] = user_sql_object[0][0]
                return redirect(url_for('main.index'))
            else:
                error = "Invalid Password"
                return redirect(url_for('main.index'))
        else:
            error = "Invalid Account"
        return redirect(url_for('main.index'))
    return redirect(url_for('main.index'))


@main.route('/setting', methods=['GET', 'POST'])
def setting():
    global error
    if request.method == 'POST':
        account = request.form['settingaccount']
        password = request.form['settingpassword']
        mqtt_host = request.form['setting_mqtt_host']
        gateway_UID = request.form['setting_gateway_UID']
        cloud_ip = request.form['setting_cloud_ip']
        cloud_port = request.form['setting_cloud_port']
        cloud_path = request.form['setting_cloud_path']
        cloud_key = request.form['setting_cloud_key']
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filex = open(
            "/var/www/dae-web/app/api_1_0/resident/method/config/gateway_setting.py", 'w', encoding='utf-8')
        filex.write('uid = "%s"\n' % (gateway_UID))
        filex.write('mqtt_host = "%s"' % (mqtt_host))
        filex.close()
        db.session.query(Links).delete()
        insert_data = Links(None, cloud_ip, cloud_path,
                            cloud_port, cloud_key, current_time, current_time)
        db.session.add(insert_data)
        insert_data = Gateway(None, gateway_UID, None,
                              None, None, "gateway", None, "06:00:00", "18:00:00")
        db.session.add(insert_data)
        insert_data = DemandSettings(100, 15, 10, 1, 2, 3, 15, None, None, current_time, current_time)
        db.session.add(insert_data)
        group_num = 1
        while group_num < 13:
            insert_data = Offloads(group_num, "false", "false", current_time, current_time)
            db.session.add(insert_data)
            group_num = group_num + 1
        insert_data = Setting(None, "PM210-4-STD", "1", "1", "9600", "1", "1", "1", "main_meter", current_time,
                              current_time, gateway_UID)
        db.session.add(insert_data)
        user.register_user(account, password)
        db.session.query(User).update({User.authority: "1"})
        db.session.commit()
        return redirect(url_for('main.index'))


# pop所有相關session


@main.route('/logout')
def logout():
    global authority
    global message
    global error
    authority = None
    message = None
    error = None
    session.pop('account', None)
    session.pop('p_id', None)
    session.pop('gateway_name', None)
    session.pop('gateway_uid', None)
    return redirect(url_for('main.index'))


@main.route('/project-setting', methods=['GET', 'POST'])
def project_setting():
    try:
        project_list_sql = 'SELECT `id`, `name` AS `project_name` FROM `project_list` WHERE `user_id` = {}'.format(session['user-id'])
        project_list_object = db.engine.execute(project_list_sql)
        project_list = {str(rowproxy[0]): {column: value for column, value in rowproxy.items()} for rowproxy in
                        project_list_object}

        node_list_sql = 'SELECT `n`.`id`, `n`.`project_id`, `n`.`node_name`, `d`.`name` AS `device_name`, `g`.`gateway_name` ' \
                        'FROM  `node_list` AS `n` ' \
                        'INNER JOIN `device_list` AS `d` ON(`n`.`device_id` = `d`.`id`) ' \
                        'INNER JOIN `gateway_list` AS `g` ON(`g`.`id` = `d`.`gateway_id`) ' \
                        'WHERE `g`.`user_id` = {}'.format(session['user-id'])
        node_list_object = db.engine.execute(node_list_sql)
        node_list = {}
        for each_node in node_list_object:
            if each_node[1] in node_list:
                node_list[each_node[1]].append(each_node)
            else:
                node_list[each_node[1]] = [each_node]
        return render_template('project_setting.html', project_list=project_list, node_list=node_list)
    except Exception as e:
        print('Hi!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(e)
        return render_template('project_setting.html', error=e)


@main.route('/area/<gateway_id>', methods=['GET', 'POST'])
def area(gateway_id):
    try:
        gateway_list_sql = "SELECT `id`, `mac_address`, `name` FROM `gateway_list` WHERE    `id` = {}".format(
            gateway_id)
        gateway_list_object = db.engine.execute(gateway_list_sql)
        gateway_list = [{column: value for column, value in rowproxy.items()} for rowproxy in gateway_list_object]
        area_list_sql = "SELECT `area_id`, `name` FROM `area_list` WHERE `gateway_id` = {}".format(gateway_id)
        area_list_object = db.engine.execute(area_list_sql)
        area_list = [{column: value for column, value in rowproxy.items()} for rowproxy in area_list_object]

        area_node_sql = "SELECT `anl`.`area_id`, `n`.`name` " \
                        "FROM `area_node_list` AS `anl`" \
                        "INNER JOIN `node_list` AS `n` ON (`n`.`node_id` = `anl`.`node_id` AND `n`.`gateway_id` = `anl`.`gateway_id`) " \
                        "WHERE `n`.`gateway_id` = {}".format(gateway_id)
        area_node_object = db.engine.execute(area_node_sql)
        area_node_list = {}
        for each_node in area_node_object:
            if each_node[0] in area_node_list:
                area_node_list[each_node[0]].append(each_node)
            else:
                area_node_list[each_node[0]] = [each_node]

        area_group_sql = "SELECT `area_id`, `name` FROM `group_list` " \
                         "WHERE `gateway_id` = {} ".format(gateway_id)
        area_group_object = db.engine.execute(area_group_sql)
        area_group_list = {}
        for each_group in area_group_object:
            if each_group[0] in area_group_list:
                area_group_list[each_group[0]].append(each_group)
            else:
                area_group_list[each_group[0]] = [each_group]

        area_scene_sql = "SELECT `area_id`, `name` " \
                          "FROM `scene_list`" \
                          "WHERE `gateway_id` = {}".format(gateway_id)
        area_scene_object = db.engine.execute(area_scene_sql)
        area_scene_list = {}
        for each_scene in area_scene_object:
            if each_scene[0] in area_scene_list:
                area_scene_list[each_scene[0]].append(each_scene)
            else:
                area_scene_list[each_scene[0]] = [each_scene]
        return render_template('area.html', gateway_id=gateway_id,
                               area_list=area_list, area_node_list=area_node_list, area_group_list=area_group_list, area_scene_list=area_scene_list, gateway_list=gateway_list)

    except Exception as e:
        print('Hi!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(e)
        return render_template('area.html', error=e)


@main.route('/node', methods=['GET', 'POST'])
def node():
    try:
        city_list_sql = "SELECT `id`, `country_name`, `city_name` FROM `city_list` WHERE `id` >= 135"
        city_list_object = db.engine.execute(city_list_sql)
        city_list = {str(rowproxy[0]): {column: value for column, value in rowproxy.items()} for rowproxy in city_list_object}

        device_type_sql = "SELECT `id`, `name`, `channels` FROM `device_type_list`"
        device_type_object = db.engine.execute(device_type_sql)
        device_type = {str(rowproxy[0]): {column: value for column, value in rowproxy.items()} for rowproxy in
                       device_type_object}

        node_list_sql = "SELECT `g`.`id` AS `gateway_id`, `g`.`mac_address`, `g`.`name`, `g`.`city_id`," \
                        " `g`.`physical_address`, `d`.`device_id`, `d`.`name` AS `device_name`, `d`.`type_id`," \
                        " `d`.`address`, `n`.`node_id`, `n`.`num`, `n`.`name`" \
                        " FROM `gateway_list` AS `g` " \
                        " LEFT JOIN `device_list` AS `d` ON(`g`.`id` = `d`.`gateway_id`) " \
                        " LEFT JOIN `node_list` AS `n` ON(`d`.`device_id` = `n`.`device_id`) " \
                        " WHERE `g`.`user_id` = {}".format(session['user-id'])
        node_list_object = db.engine.execute(node_list_sql)

        node_list = {}
        for each_node in node_list_object:
            if each_node[0] not in node_list:
                node_list[each_node[0]] = {
                    'gateway-name': each_node[2],
                    'gateway-uid': each_node[1],
                    'gateway-city-id': str(each_node[3]),
                    'gateway-address': each_node[4],
                    'device-data': {}
                }
            if each_node[5] not in node_list[each_node[0]]['device-data']:
                node_list[each_node[0]]['device-data'][each_node[5]] = {
                    'device-name': each_node[6],
                    'device-address': each_node[8],
                    'device-type-id': each_node[7],
                    'node-data': {}
                }
            node_list[each_node[0]]['device-data'][each_node[5]]['node-data'][each_node[9]] = each_node
        return render_template('node.html', node_list=node_list, city_list=city_list,
                               device_type=device_type)

    except Exception as e:
        print('Hi!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(e)
        return render_template('node.html', error=e)


@main.route('/group/<gateway_id>', methods=['GET', 'POST'])
def group(gateway_id):
    try:
        gateway_list_sql = "SELECT `id`, `mac_address`, `name` FROM `gateway_list` WHERE    `id` = {}".format(
            gateway_id)
        gateway_list_object = db.engine.execute(gateway_list_sql)
        gateway_list = [{column: value for column, value in rowproxy.items()} for rowproxy in gateway_list_object]

        node_list_sql = "SELECT `n`.`node_id`, `n`.`num`, `n`.`name`, `gnl`.`group_id` FROM " \
                        "`node_list` AS `n` " \
                        "LEFT JOIN `group_node_list` AS `gnl` ON(`n`.`node_id` = `gnl`.`node_id` AND `n`.`gateway_id` = `gnl`.`gateway_id`)" \
                        "WHERE `n`.`gateway_id` = {}".format(gateway_id)
        node_list_object = db.engine.execute(node_list_sql)
        node_list = {str(rowproxy[0]): {column: value for column, value in rowproxy.items()} for rowproxy in
                     node_list_object}
        group_list_sql = "SELECT `gl`.`group_id`, `gl`.`num` AS `group_num`, `gl`.`name` AS `group_name`, " \
                         "`n`.`node_id`, `n`.`name` AS `node_name` " \
                         "FROM `group_list` AS `gl` " \
                         "INNER JOIN `group_node_list` AS `gnl` ON(`gl`.`group_id` = `gnl`.`group_id` AND `gl`.`gateway_id` = `gnl`.`gateway_id`) " \
                         "INNER JOIN `node_list` AS `n` ON(`n`.`node_id` = `gnl`.`node_id` AND `n`.`gateway_id` = `gnl`.`gateway_id`) " \
                         "WHERE `gl`.`gateway_id` = {}".format(gateway_id)
        group_list_object = db.engine.execute(group_list_sql)
        group_list = {}
        for each_node in group_list_object:
            if each_node[0] not in group_list:
                group_list[each_node[0]] = {
                    'group-name': each_node[2],
                    'group-number': each_node[1],
                    'node-data': {}
                }
            group_list[each_node[0]]['node-data'][each_node[3]] = each_node
        return render_template('group.html', group_list=group_list, node_list=json.dumps(node_list), gateway_list=gateway_list)

    except Exception as e:
        print('Hi!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(e)
        return render_template('group.html', error=e)


@main.route('/scene/<gateway_id>', methods=['GET', 'POST'])
def scene(gateway_id):
    try:
        gateway_list_sql = "SELECT `id`, `mac_address`, `name` FROM `gateway_list` WHERE    `id` = {}".format(
            gateway_id)
        gateway_list_object = db.engine.execute(gateway_list_sql)
        gateway_list = [{column: value for column, value in rowproxy.items()} for rowproxy in gateway_list_object]

        node_list_sql = "SELECT `node_id`, `num`, `name`, `type_id` " \
                        "FROM `node_list` WHERE `gateway_id` = {}".format(gateway_id)
        node_list_object = db.engine.execute(node_list_sql)
        node_list = {str(rowproxy[0]): {column: value for column, value in rowproxy.items()} for rowproxy in
                     node_list_object}
        scene_list_sql = "SELECT `sl`.`scene_id`, `sl`.`num` AS `scene_number`, `sl`.`name` AS `scene_name`, " \
                          "`nl`.`node_id`, `nl`.`name` AS `node_name`, `nl`.`type_id`, `snl`.`node_state` " \
                          "FROM `scene_list` AS `sl` " \
                          "INNER JOIN `scene_node_list` AS `snl` ON(`sl`.`scene_id` = `snl`.`scene_id` AND `sl`.`gateway_id` = `snl`.`gateway_id`) " \
                          "INNER JOIN `node_list` AS `nl` ON(`nl`.`node_id` = `snl`.`node_id` AND `nl`.`gateway_id` = `snl`.`gateway_id`) " \
                          "WHERE `sl`.`gateway_id` = {}".format(gateway_id)
        scene_list_object = db.engine.execute(scene_list_sql)
        scene_list = {}
        for each_node in scene_list_object:
            if str(each_node[0]) not in scene_list:
                scene_list[str(each_node[0])] = {
                    'scene-name': each_node[2],
                    'scene-number': each_node[1],
                    'node-data': {}
                }
            scene_list[str(each_node[0])]['node-data'][str(each_node[3])] = list(each_node)

        return render_template('scene.html', scene_list=scene_list, node_list=json.dumps(node_list), gateway_list=gateway_list, gateway_id=gateway_id, G_CONTROL_VALUE_TYPE_LIST=G_CONTROL_VALUE_TYPE_LIST)

    except Exception as e:
        print('Hi!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(e)
        return render_template('scene.html', error=e)


@main.route('/gateway_setting', methods=['GET', 'POST'])
def gateway_setting():
    if 'account' in session:
        session.pop('uid', None)
        if request.method == 'POST':
            session['p_id'] = request.form['pid']
            session.pop('uid', None)
            p_name = project_page()
            return render_template('gateway_setting.html', p_name=p_name, p_id=session['p_id'])
        else:
            p_name = project_page()
            return render_template('gateway_setting.html', p_name=p_name, p_id=session['p_id'])

    else:
        return redirect(url_for('main.index'))


@main.route('/demand_dashboard/<gateway_id>', methods=['GET', 'POST'])
def demand_dashboard(gateway_id):
    if 'account' not in session:
        return redirect(url_for('main.index'))
    try:
        now = datetime.now()  # current date and time
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        curr_date_temp = datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")
        month_first_day = now.strftime("%Y-%m-01 00:00:00")
        yesterday = curr_date_temp - timedelta(days=1)
        last_demand_value = demand.last_demand_value(gateway_id)
        max_demand = demand.max_demand_value(gateway_id, month_first_day)
        demand_setting_list = demand.demand_setting_value(gateway_id)
        demand_group_list = demand.demand_group_list(gateway_id)
        demand_record_list_result = demand.demand_record_value(gateway_id, yesterday)
        demand_record_list = [[str(value) for value in rowproxy] for rowproxy in
                             demand_record_list_result]
        return render_template('demand_dashboard.html', max_demand=max_demand, last_demand_value=last_demand_value,
                               demand_setting_list=demand_setting_list, demand_group_list=demand_group_list,
                               demand_record_list=json.dumps(demand_record_list), gateway_id=gateway_id)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('HI!!!!!!!!!!!!!')
        print(str(e), exc_type, exc_tb.tb_lineno)
        return redirect(url_for('main.index'))\


@main.route('/demand_setting/<gateway_id>', methods=['GET', 'POST'])
def demand_setting(gateway_id):
    if 'account' not in session:
        return redirect(url_for('main.index'))
    try:
        # demand_setting_list_sql = "SELECT `max_value`, `upper`, `lower`, `load_off_gap`, `reload_delay`, `reload_gap`, `cycle`, `mode`" \
        #                           " FROM `demand_setting` WHERE `gateway_id` = {}".format(gateway_id)
        demand_setting_list_sql = "SELECT `max_value`, `upper`, `lower`, `load_off_gap`, `reload_delay`, `reload_gap`, `cycle`, `mode`" \
                                  " FROM `demand_setting_list` WHERE `gateway_id` = {}".format(gateway_id)
        demand_setting_list = db.engine.execute(demand_setting_list_sql).fetchall()
        return render_template('demand_setting.html', demand_setting_list=demand_setting_list, gateway_id=gateway_id)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('HI!!!!!!!!!!!!!')
        print(str(e), exc_type, exc_tb.tb_lineno)
        return redirect(url_for('main.index'))\


@main.route('/demand_group_setting/<gateway_id>', methods=['GET', 'POST'])
def demand_group_setting(gateway_id):
    if 'account' not in session:
        return redirect(url_for('main.index'))
    try:
        demand_group_setting_list_sql = "SELECT `unload_group_id`, `name`, `num`, `sort`, `unload_group_state`, `updated_at`" \
                                  " FROM `unload_group_list` WHERE `gateway_id` = {}".format(gateway_id)
        demand_group_setting_list_result = db.engine.execute(demand_group_setting_list_sql)
        demand_group_setting_list = {str(demand_group[0]) : {column: str(value) for column, value in demand_group.items()} for demand_group in demand_group_setting_list_result}

        return render_template('demand_group_setting.html', demand_group_setting_list=demand_group_setting_list, gateway_id=gateway_id)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('HI!!!!!!!!!!!!!')
        print(str(e), exc_type, exc_tb.tb_lineno)
        return redirect(url_for('main.index'))

@main.route('/gateway/<gateway_id>', methods=['GET', 'POST'])
def gateway(gateway_id):
    if 'account' in session:

        time_now = datetime.datetime.now()
        time_pass = time_now - datetime.timedelta(seconds=65)
        data_count_sql = "SELECT * FROM `electricity` WHERE `created_at` >= '{}' AND `created_at` <= '{}' AND `gateway_id` = {} ".format(time_pass, time_now, gateway_id)
        data_count_result = db.engine.execute(data_count_sql).fetchall()
        print(data_count_result)
        data_count = len(data_count_result)

        if data_count >= 3:
            reading_status = '定時讀錶中'
            fa_color = 'color: rgb(0, 236, 0)'
        elif data_count < 3 and data_count >= 1:
            reading_status = '讀錶功能不穩'
            fa_color = 'color: rgb(244, 167, 66)'
        else:
            reading_status = '讀錶功能暫停'
            fa_color = 'color: rgb(244, 66, 66)'

        return render_template('gateway.html', session_user_name=session['account'],
                               gateway_id=gateway_id,
                               reading_status=reading_status, fa_color=fa_color, role=session['role'])
    else:
        return redirect(url_for('main.index'))


@main.route('/control/<gateway_id>', methods=['GET', 'POST'])
def control(gateway_id):
    if 'account' not in session:
        return redirect(url_for('main.index'))
    try:
        area_list_sql = "SELECT `area_id`, `name` FROM `area_list` " \
                        "WHERE `gateway_id` = '{}'".format(gateway_id)
        area_list_object = db.engine.execute(area_list_sql).fetchall()

        if len(area_list_object) == 0 :
            return redirect(url_for('main.files', gateway_id=gateway_id))

        area_list = [{column: value for column, value in rowproxy.items()} for rowproxy in area_list_object]
        area_first_id = area_list[0]['area_id']
        node_list_sql = "SELECT `nl`.`type_id`, `nl`.`node_id`, `nl`.`name`, `nl`.`num`, `nl`.`state` " \
                        "FROM `area_node_list` AS `anl` " \
                        "INNER JOIN `node_list` AS `nl` ON(`nl`.`node_id` = `anl`.`node_id` " \
                        "AND `nl`.`gateway_id` = `anl`.`gateway_id`) " \
                        "WHERE `anl`.`area_id` = {} AND `nl`.`gateway_id` = {}".format(area_first_id, gateway_id)
        node_list = db.engine.execute(node_list_sql)

        group_list_sql = "SELECT `group_id`, `name`, `num`, `state` " \
                         "FROM  `group_list` " \
                         "WHERE `area_id` = {} AND `gateway_id` = {}".format(area_first_id, gateway_id)
        group_list = db.engine.execute(group_list_sql)

        scene_list_sql = "SELECT `scene_id`, `name`, `num` " \
                          "FROM `scene_list` " \
                          "WHERE `area_id` = {} AND `gateway_id` = {}".format(area_first_id, gateway_id)
        scene_list = db.engine.execute(scene_list_sql)
        return render_template('project.html', area_list=area_list,
                               node_list=node_list, group_list=group_list, scene_list=scene_list, gateway_id=gateway_id, G_CONTROL_VALUE_TYPE_LIST = G_CONTROL_VALUE_TYPE_LIST)
    except Exception as e:
        print('HI!!!!!!!!!!!!!')
        print(str(e))
        return redirect(url_for('main.index'))

@main.route('/schedule/<gateway_uid>', methods=['GET', 'POST'])
def schedule(gateway_uid):
    if 'account' in session:
        return render_template('schedule.html', session_user_name=session['account'],
                               gateway_uid=gateway_uid)
    else:
        return redirect(url_for('main.index'))


@main.route('/select_gateway')
def select_gateway():
    send_type = request.args.get('send_type')
    if 'account' in session:
        sql = "SELECT `id`, `name`, `mac_address` FROM `gateway_list` WHERE `user_id` = {} ".format(
            session['user-id'])
        gateway_list = db.engine.execute(sql)
        return render_template('select_gateway.html', gateway_list=gateway_list, send_type=send_type)
    else:
        return redirect(url_for('main.index'))


@main.route('/festival/<gateway_id>', methods=['GET', 'POST'])
def festival(gateway_uid):
    if 'account' in session:

        return render_template('festival.html', session_user_name=session['account'],
                               gateway_uid=gateway_uid)
    else:
        return redirect(url_for('main.index'))


@main.route('/files/<gateway_id>', methods=['GET', 'POST'])
def files(gateway_id):
    if 'account' not in session:
        return redirect(url_for('main.index'))

    try:
        return render_template('file.html', gateway_id=gateway_id)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('HI!!!!!!!!!!!!!')
        print(str(e), exc_type, exc_tb.tb_lineno)
        return redirect(url_for('main.index'))


def project_page():
    query_data = db.session.query(Project.project_name).filter(
        Project.id == session['p_id']).first()
    p_name = query_data.project_name
    return (p_name)


if __name__ == '__main__':
    app.run(debug=True)
