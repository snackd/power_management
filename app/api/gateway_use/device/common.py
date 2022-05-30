# encoding=utf-8
#! /usr/bin/python

import json
import time
import requests
import os.path
import socket
import datetime
import sys

from . import mysql as daesql
from .config import database_setting as dbconfig
from .config.path import *

encoding = "utf-8"

# 取得伺服器設定的參數
def get_server_settings():
    try:
        dbh = daesql.MySQL(dbconfig.mysql_config)
        table_name = "link_list"
        column = "id"
        sql = (
            "SELECT * "
            "FROM `{}` "
            "ORDER BY `{}`"
            "LIMIT 1"
        ).format(table_name, column)
        my_setting = dbh.query(sql)[0]
    except:
        print("Un excepted Error: {0}".format(sys.exc_info()[0]))
        raise

    # try:
    #     sqlobj = daesql.MySQL(dbconfig.mysql_config)
    #     table_name = 'links'
    #     state = "SELECT * FROM {0} ORDER BY id DESC LIMIT 1".format(table_name)
    #     my_setting = sqlobj.query(state)[0]
    # except:
    #     print("Un excepted Error: {0}".format(sys.exc_info()[0]))
    #     raise

    return my_setting


# # 將資料傳送給指定API伺服器
# def post_data_to_server(data):
#     try:
#         settings = get_server_settings()
#         server_ip = settings['ip']
#         server_domain = settings['domain']
#         server_port = settings['port']
#         server_path = settings['path']
#         key = settings['key']
#         ethernet = "eth0"
#         json_data = json.dumps(data)
#    #     url = "{0}:{1}/{2}/{3}?mac={4}".format(server_ip, server_port, server_path,key, get_mac(ethernet))
#         url = "http://{0}:{1}/{2}/{3}".format(server_ip,
#                                               server_port, server_path, key)
#         time.sleep(.5)
#         response = requests.post(url, json_data, timeout=3)
#         time.sleep(1)
#         return response

#     except requests.exceptions.ConnectTimeout:
#         rewrite_connection_times()

#     except:
#         print("Unexcepted error: {0}".format(sys.exc_info()[0]))
#         raise

# 傳資料到 Server
def post_data_to_server(data):
    try:
        settings = get_server_settings()
        server_ip = settings['ip']
        # server_domain = settings['domain']
        server_port = settings['port']
        server_path = settings['path']
        key = settings['key']
        # ethernet = "eth0"
        json_data = json.dumps(data)
        url = "http://{0}:{1}/{2}/{3}".format(server_ip,
                                              server_port, server_path, key)

        print("http://{0}:{1}/{2}/{3}", server_ip,
              server_port, server_path, key)

        url = bytes(url, encoding="utf8")
        time.sleep(.5)

        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        time.sleep(1)
        ser.write(b'at+sapbr=1,1\r')
        time.sleep(1)
        ser.write(b'at+httpinit\r')
        time.sleep(1)
        ser.write(b'at+httppara="cid",1\r')
        time.sleep(1)
        ser.write(b'at+httppara="url","%s"\r' % (url))
        time.sleep(1)
        ser.write(b'at+httpdata=500,5000\r')
        time.sleep(1)
        ser.write(json_data.encode() + b'\r')
        time.sleep(10)
        ser.write(b'at+httpaction=1\r')
        time.sleep(2)

        response = 201
        return response

    except requests.exceptions.ConnectTimeout:
        rewrite_connection_times()

    except:
        print("Unexcepted error: {0}".format(sys.exc_info()[0]))
        raise

    finally:
        ser.close()

# 取得 boot 設定
def get_boot_settings():
    try:
        filename = BOOT_CONFIG_PATH

        if not os.path.exists(filename):
            obj = {}
            obj['boot_code'] = 'M'
            obj['connect_times'] = 0

            file = open(filename, 'w', encoding=encoding)
            file.write(json.dumps(obj))
            file.close()

        file = open(filename, 'r', encoding=encoding)
        settings = file.read()
        my_settings = json.loads(settings)
        file.close()

        return my_settings

    except:
        print("Unexcepted error: {0}".format(sys.exc_info()[0]))
        raise

# 寫入 boot 設定
def write_boot_settings(key, value):
    try:
        my_settings = get_boot_settings()
        my_settings[key] = value

        file = open(BOOT_CONFIG_PATH, 'w', encoding=encoding)
        file.write(json.dumps(my_settings))
        file.close()

    except:
        print("Unexcepted error: {0}".format(sys.exc_info()[0]))
        raise

# 寫 boot Code
def write_boot_code(code):
    my_settings = get_boot_settings()
    write_boot_settings('boot_code', code)

# 取 boot code
def get_boot_code():
    my_settings = get_boot_settings()

    return my_settings['boot_code']


# 重新連線一百次後重新開機
def rewrite_connection_times(code=''):
    if not code == '':
        write_boot_settings('connect_times', 0)

        return 0

    is_reboot = False
    my_settings = get_boot_settings()
    times = my_settings['connect_times']

    times = int(times) + 1
    log('requests failed', times)

    if times == 100:
        is_reboot = True
        times = 0

    write_boot_settings('connect_times', times)

    if is_reboot:
        write_boot_settings('W')
        os.system('reboot')


# 取現在時間
def get_now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# 取現在秒數
def get_now_sec():
    return datetime.datetime.now().strftime('%S')


# 取 mac
def get_mac(interface):
    try:
        mac = open('/sys/class/net/' + interface + '/address').readline()

    except:
        mac = "00:00:00:00:00:00"

    return mac[0:17]


# 取 ip 位置
def get_ip_address():
    return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]


# Log
def log(title, s):
    print("{0} {1} {0}".format("*" * 10, title))
    print(s)
    print("-" * 10)


