# coding=utf-8
import json
import time
import redis
import threading
from . import mysql_main as my
from datetime import datetime

# MQTT
import paho.mqtt.publish as publish

# Schedule
from apscheduler.schedulers.blocking import BlockingScheduler
# from apscheduler.schedulers.background import BackgroundScheduler


# Redis
R = redis.Redis('localhost')
redis_publish = "publish"
redis_receive = "receive"
redis_response = "response"
coding = "utf-8"

# TODO Queue
# redis_serial_isOpen = "serial.isOpen"
# redis_modbus_queue = "modbus_queue"

# MQTT Broker
cloud_mqtt_host = "140.116.39.212"

# Server
server_host = "140.116.39.172"

# Gateway Mac Address
uid = "09ea6335-d2bd-4678-9ca9-647b5574a09e"
mac_address = "09ea6335-d2bd-4678-9ca9-647b5574a09e"

# 機型-數值與開關設定
model_percent = ['LT4500']

# ROLE = "Server"
ROLE = "Gateway"
DELIVER_WAY = "Ethernet"
# DELIVER_WAY = "NB-IoT"

# DB setting
if ROLE == "Gateway":
    mysql_config = {
        'host': 'localhost',
        'user': 'power_user1',
        'password': 'power_management',
        'db': 'lighting'
    }
elif ROLE == "Server":
    mysql_config = {
        'host': 'localhost',
        'user': 'power_user1',
        'password': 'power_management',
        'db': 'lighting'
    }
else:
    mysql_config = {
        'host': 'localhost',
        'user': 'power_user1',
        'password': 'power_management',
        'db': 'lighting'
    }

dbh = my.MySQL(mysql_config)