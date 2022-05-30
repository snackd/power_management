import json
import time
import datetime
from datetime import timedelta

from flask import jsonify, request
from sqlalchemy import func, and_, or_, between, exists

from . import api
from .. import db
from ..models import *

from . import mqtt_talker as mqtttalker

from config import role
from .log import log_info

from .gateway_use.device import cflag as cflag
from .gateway_use.device.config.cloud_setting import *
from .gateway_use.device.config.cloud_setting import *


@api.route('/festival_setting/rest_days', methods=['POST', 'GET'])
def rest_days():
    gateway_uid = ""
    if request.method == 'GET':
        gateway_uid = request.args.get('gateway_uid', default="", type=str)
        if role == "Gateway":
            result = db.session.query(festival.date).all()
            rest_days = [row[0] for row in result]
            return jsonify(rest_days)
        elif role == "Cloud":
            message = json.dumps({})
            mqtt_talker = mqtttalker.MqttTalker(
                cloud_mqtt_host, gateway_uid, "festival_setting/rest_days_get", message)
            response = mqtt_talker.start()
            if response:
                return jsonify(response), 201
            else:
                return "Request Timeout", 500
    elif request.method == 'POST':
        origin_date = []
        weekdate_dict = {}
        week_list = {}
        month_statement = {}
        everyMonthWeek_thisday = {}
        everyMonthWeek_statement = {}
        gateway_uid = request.form.get('gateway_uid', default="", type=str)
        rest_days = request.form.getlist('restDays[]')
        week_statement = json.loads(request.form.get('week_statement'))
        date_statement = json.loads(request.form.get('date_statement'))
        month_statement = json.loads(request.form.get('month_statement'))
        everyMonthWeek_thisday = json.loads(
            request.form.get('everyMonthWeek_thisday'))
        everyMonthWeek_statement = json.loads(
            request.form.get('everyMonthWeek_statement'))
        everyMonthWeek_number = json.loads(
            request.form.get('everyMonthWeek_number'))
        if role == "Gateway":
            for_log = ""
            origin = db.session.query(festival.date).all()
            # 原本資料庫日期
            for data in origin:
                origin_date.append(data.date)
            # 找出有無存在於原本資料庫的日期，如果沒有則加入
            # 每月的第一天
            for date in rest_days:
                (ret, ), = db.session.query(
                    exists().where(festival.date == date))
                # 需判斷是哪一種模式
                if ret is False:
                    weekday = datetime.datetime.strptime(
                        str(date), "%Y-%m-%d").weekday()
                    # 判斷星期幾
                    weekday = week_transform(weekday)
                    state = ""
                    if str(date) in week_statement:
                        db.session.add(
                            festival(None, date, week_statement[str(date)], 'holiday'))
                        state = "INSERT INTO festival(`date`,statement,bind_table)VALUES('%s','%s','%s')" % (
                            date, week_statement[str(date)], 'holiday')
                    elif str(date) in month_statement:
                        db.session.add(
                            festival(None, date, month_statement[str(date)], 'holiday'))
                        state = "INSERT INTO festival(`date`,statement,bind_table)VALUES('%s','%s','%s')" % (
                            date, month_statement[str(date)], 'holiday')
                    elif everyMonthWeek_thisday != {}:
                        for data in everyMonthWeek_number:
                            for key in data:
                                if str(date) in everyMonthWeek_thisday[str(key)][str(data[key])]:
                                    db.session.add(festival(
                                        None, date, everyMonthWeek_statement[str(key)][str(data[key])], 'holiday'))
                                    sql = "INSERT INTO festival(`date`,statement,bind_table)VALUES('%s','%s','%s')" % (
                                        date, everyMonthWeek_statement[str(key)][str(data[key])], 'holiday')
                                    state = state + '\n' + sql
                                else:
                                    db.session.add(
                                        festival(None, date, date_statement[str(date)], 'holiday'))
                                    sql = "INSERT INTO festival(`date`,statement,bind_table)VALUES('%s','%s','%s')" % (
                                        date, date_statement[str(date)], 'holiday')
                                    state = state + '\n' + sql
                    else:
                        db.session.add(
                            festival(None, date, date_statement[str(date)], 'holiday'))
                        sql = "INSERT INTO festival(`date`,statement,bind_table)VALUES('%s','%s','%s')" % (
                            date, date_statement[str(date)], 'holiday')
                        state = state + '\n' + sql
                    for_log = for_log + '\n' + state
            for date in origin_date:
                if(str(date) not in rest_days):
                    db.session.query(festival).filter(
                        festival.date == date).delete()
                    state = "DELETE FROM festival WHERE `date`='%s'" % (date)
                    for_log = for_log + '\n' + state
            db.session.commit()
            db.session.close()
            cflag.cflag()
            log_info(gateway_uid, 'insert', 'festival',
                     for_log, "ok", "Gateway")
            return jsonify({'status': 200})
        elif role == "Cloud":
            message = json.dumps({
                'rest_days': rest_days,
                'date_statement': date_statement,
                'week_statement': week_statement,
                'month_statement': month_statement,
                'everyMonthWeek_thisday': everyMonthWeek_thisday,
                'everyMonthWeek_statement': everyMonthWeek_statement,
                'everyMonthWeek_number': everyMonthWeek_number
            })
            mqtt_talker = mqtttalker.MqttTalker(
                cloud_mqtt_host, gateway_uid, "festival_setting/rest_days_post", message)
            response = mqtt_talker.start()
            if response:
                if(json.loads(response)['status'] == 200):
                    log_info(gateway_uid, "update", "festival",
                             'rest_days' + str(rest_days), "ok", "Cloud")
                return jsonify(response), 201
            else:
                return "Request Timeout", 500


def week_transform(weekday):
    print('type(weekday)', type(weekday))
    if(weekday) == 6:
        weekday == 0
    else:
        weekday += 1
    return weekday
# 特別節日


@api.route('/festival_setting/information', methods=['POST', 'GET'])
def festival_information_setting():
    gateway_uid = request.args.get('gateway_uid', default="", type=str)
    if role == "Gateway":
        festival_information = db.session.query(
            festival).order_by(festival.date).all()
        festival_list = []
        for data in festival_information:
            festival_list.append({
                'id': data.id,
                'date': data.date,
                'statement': data.statement,
                'bind_table': data.bind_table
            })
        db.session.commit()
        db.session.close()
        return jsonify(festival_list), 201
    elif role == "Cloud":
        message = json.dumps({})
        mqtt_talker = mqtttalker.MqttTalker(
            cloud_mqtt_host, gateway_uid, "festival_setting/information", message)
        response = mqtt_talker.start()
        if response:
            return jsonify(response), 201
        else:
            return "Request Timeout", 500
