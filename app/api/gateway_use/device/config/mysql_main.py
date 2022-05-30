# encoding=utf-8
#! /usr/bin/python

# import time
# import sqlite3
# import sys
import pymysql.cursors
# import json
# from .config.path import *


class MySQL:
    def __init__(self, dbconfig):
        super(MySQL, self).__init__()
        self.connection = pymysql.connect(host=dbconfig['host'],
                                          user=dbconfig['user'],
                                          password=dbconfig['password'],
                                          db=dbconfig['db'],
                                          charset='utf8mb4',
                                          cursorclass=pymysql.cursors.DictCursor)

    def execute(self, sql):
        connection = self.connection
        cursor = connection.cursor()
        result = cursor.execute(sql)
        connection.commit()
        response = {
            'result': result,
            'last_id': cursor.lastrowid
        }
        if response:
            response = "ok"

        return response
        # return result

    def query(self, state):
        connection = self.connection
        with connection.cursor() as cursor:
            cursor.execute(state)
            result = cursor.fetchall()

        return result

    def query_machine_setting(self, model):
        # time.sleep(0.05)
        conn = self.connection
        cursor = conn.cursor()

        table_name = "gateway_list"
        mac_address = '09ea6335-d2bd-4678-9ca9-647b5574a09e'

        sql = (
            "SELECT `id` "
            "FROM `gateway_list` "
            "WHERE `mac_address`= '{}' "
        ).format(mac_address)

        cursor.execute(sql)
        result = cursor.fetchone()
        gateway_id = result['id']

        # 查詢機器代碼
        result = self.query_code(model)

        code_h = result['code_h']
        code_l = result['code_l']

        table_name = "device_list"
        table2_name = "device_type_list"
        sql = (
            "SELECT D.`device_id`, D_T.`name`, D_T.`class`, D_T.`point`, D_T.`channels`, D.`address`, D.`baud_rate` "
            "FROM `{}` as D, `{}` as D_T "
            "WHERE D_T.`name` = '{}' "
            "AND D_T.`id` = D.`device_id` "
            "AND D.`gateway_id` = '{}' "
        ).format(table_name, table2_name, model, gateway_id)

        cursor.execute(sql)
        result = cursor.fetchone()

        # device_information = []
        # for i in result:
        #     device_information.append(i)

        # 打包為 dict，方便觀看取什麼值，照舊有的改法
        device_setting = []
        setting_dict = {
            "mac_address": mac_address,
            "gateway_id": gateway_id,
            "device_id": result['device_id'],
            "model": result['name'],
            "class": result['class'],
            "point": result['point'],
            "channel": result['channels'],
            "address": result['address'],
            "baud_rate": result['baud_rate'],
            "code_h": code_h,
            "code_l": code_l,
        }
        # setting_dict = {
        #     "mac_address": mac_address,
        #     "gateway_id": gateway_id,
        #     "device_id": device_information[0],
        #     "model": device_information[1],
        #     "class": device_information[2],
        #     "point": device_information[3],
        #     "channel": device_information[4],
        #     "address": device_information[5],
        #     "baud_rate": device_information[6],
        #     "code_h": code_h,
        #     "code_l": code_l,
        # }
        device_setting.append(setting_dict)

        return device_setting


    # 將 baudrate 轉換成台科電的規定格式 1-1200, 2-2400, 3-4800, 4-9600
    def convert_speed_to_number(self, speed):
        if speed == '1200':
            return 1

        elif speed == '2400':
            return 2

        elif speed == '4800':
            return 3

        elif speed == '9600':
            return 4

    # 查詢電表型號的代碼
    def query_code(self, model):
        conn = self.connection
        cursor = conn.cursor()
        table_name = "code_list"
        sql = (
            "SELECT `code_h`, `code_l` "
            "FROM `{}` "
            "WHERE `model` = '{}' "
        ).format(table_name, model)
        cursor.execute(sql)
        result = cursor.fetchone()

        return result


    def close(self):
        self.connection.close()
