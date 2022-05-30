# coding=utf-8

# import sys
# import redis
# from datetime import datetime

# import device.config.setting as setting
from device.config.setting import *

# MQTT
# import paho.mqtt.publish as publish

# ROLE = setting.ROLE
# DELIVER_WAY = setting.DELIVER_WAY

# 分隔符號
# task_segment = '/'
# message_segment = '|'
# end_segement = '~'

# Redis
# r = redis.Redis('localhost')
# R = setting.R
# redis_publish = setting.redis_publish
# redis_response = setting.redis_response

# MQTT need
mqtt_host = cloud_mqtt_host  # Broker
server_id = server_host  # Server ip address
gateway_id = mac_address  # Gateway Mac_address
# mqtt_host = setting.cloud_mqtt_host  # Broker
# server_id = setting.server_host  # Server ip address
# gateway_id = setting.mac_address  # Gateway Mac_address
publish_qos = 1  # Qos


# 連接資料庫
# dbh = setting.dbh

def record(method, action, target):
    sql_start_time = datetime.now()

    try:
        sql = (
            "INSERT INTO `log_list` "
            "(`role`, `type`, `deliver_way`, `action`, `target`, `result`) "
            "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}') "
        ).format(ROLE, method, DELIVER_WAY, action, target, "ok")
        log_result = dbh.execute(sql)
    except BaseException as n:
        print("Log Fail:", n)

    sql_end_time = datetime.now()
    write_sql_time = sql_end_time - sql_start_time

    # print("Role:", ROLE," Delivery:", DELIVER_WAY)
    print("Method:", method, " Action:", action, " target:", target)
    print("Write SQL Time:", write_sql_time)

def redis_record(method, action, target):
    redis_time = time.time()
    str_time = str(redis_time)
    redis_content = action + '/' + target + '/' + str_time
    R.rpush("transmit_publish", redis_content)

def deliver(deliver_way, action, target, payload):
    deliver_dict.get(deliver_way)(action, target, payload)

def ethernet_publish(action, target, payload):

    # record(method="publish", action=action, target=target)

    # DONE:
    redis_record(method="publish", action=action, target=target)

    if ROLE == "Gateway":
        publish.single("{}/from/{}/{}/{}/response".format(server_id, gateway_id, action, target), payload, qos=publish_qos, hostname=mqtt_host)
        # print("Ethernet Return:{}/from/{}/{}/{}/response".format(server_id, gateway_id, action, target))
    elif ROLE == "Server":
        publish.single("{}/to/{}/{}/{}/response".format(server_id, gateway_id, action, target), payload, qos=publish_qos, hostname=mqtt_host)
        # print("Ethernet Return:{}/to/{}/{}/{}/response".format(server_id, gateway_id, action, target))


# Gateway 回傳給 Server 時
def nbiot_publish(action, target, payload):

    if ROLE == "Gateway":
        print("---")
        print("NB-IoT publish redis")
        # 當訊息是串列時去除 []
        if type(payload) == list:
            print("Type:", type(payload))
            payload = payload[1:-1]

        # 訊息在 redis = action/target/method|payload
        method = "response"

        composition = action + '/' + target + '/' + method + '|' + payload
        # print("Compoosition:", composition)
        R.rpush(redis_publish, composition)


# 字典判別使用 Ethernet 或 NB-IoT (key - value)
deliver_dict = {
    # Ethernet
    'Ethernet': ethernet_publish,

    # NB-IoT
    'NB-IoT': nbiot_publish,
}
