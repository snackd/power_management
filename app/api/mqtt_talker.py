# coding=utf-8
import os
import sys
import time
import json
import signal

from flask import jsonify

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from datetime import datetime, timedelta

from config import role as ROLE
from config import server_id as SERVER_ID

from sqlalchemy import func, and_, or_, between, exists
from config import DELIVER_WAY
from config import R

from . import api
from .. import db

message_segment = "|"
end_segment = "~"

# print("---MQTT Talker---")
# print("Role:", ROLE)
# print("Server ID:", SERVER_ID)
# print("---MQTT Talker---")

class MqttTalker():

    # 初始化設定，當類別生成時即有的屬性
    def __init__(self, host, gateway_id, task, payload):
        self.host = host
        self.gateway_id = gateway_id
        self.task = task
        self.payload = payload

        self.action, self.target = self.task.split("/")
        # NB-IoT
        self.task_segment = '/'
        self.message_segment = '|'
        self.redis_publish = "publish"
        self.r = R
        self.redis_web_response = "web_response"
        self.coding = "utf-8"
        self.method = "request"
        # self.action = ""
        # self.target = ""

        # ROLE
        if ROLE == "Cloud":
            # self.publish_topic = SERVER_ID + "/to/" + self.gateway_id + "/" + task
            self.publish_topic = SERVER_ID + "/to/" + self.gateway_id + "/" + task + "/request"
            self.subscribe_topic = SERVER_ID + "/from/#"
        elif ROLE == "Gateway":
            self.publish_topic = SERVER_ID + "/from/" + self.gateway_id + "/" + task
            self.publish_topic = SERVER_ID + "/from/" + self.gateway_id + "/" + task + "/request"
            self.subscribe_topic = SERVER_ID + "/to/#"

        # 連線品質
        self.qos = 1

        # 回傳訊息
        self.response = ""

        # MQTT 是否保持連線
        self.mqtt_looping = True

    # 當有 MQTT 連上的時候，(不須與 broker 保持連線)
    def on_connect(self, mq, userdata, rc, _):

        # Publish
        print(ROLE," Publish:", self.publish_topic)
        publish.single(self.publish_topic, self.payload, qos=self.qos, hostname=self.host)

        # Subscribe
        print(ROLE," Subscribe:", self.subscribe_topic)
        mq.subscribe(self.subscribe_topic)

    # 當 MQTT 有訂閱的訊息進來時
    def on_message(self, mq, userdata, msg):

        print("Receiving messages from {} (qos={})...".format(msg.topic, msg.qos))
        print("LEN:", len(msg.payload))
        print("Content:\n{}".format(msg.payload))
        self.mqtt_looping = False
        self.response = msg.payload.decode("utf-8")

    def record(self, method, action, target):
        sql_start_time = datetime.now()

        try:
            sql = (
                "INSERT INTO `log_list` "
                "(`role`, `type`, `deliver_way`, `action`, `target`, `result`) "
                "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}') "
            ).format(ROLE, method, DELIVER_WAY, action, target, "ok")
            log_result = db.engine.execute(sql)
        except BaseException as n:
            print("Log Fail:", n)

        sql_end_time = datetime.now()
        write_sql_time = sql_end_time - sql_start_time

        # print("Role:", ROLE," Delivery:", DELIVER_WAY)
        print("Method:", method, " Action:", action, " Target:", target)
        print("Write SQL Time:", write_sql_time)

    def ethernet_response(self):
        self.mqtt_looping = True
        client = mqtt.Client()

        action, target = self.task.split("/")

        # FIXME Case:1-1，Ethernet，發送端(Server)，發送訊息
        # FIXME Case:3-1，Ethernet，發送端(Gateway)，發送訊息
        self.record(method="publish", action=action, target=target)

        client.on_connect = self.on_connect
        client.on_message = self.on_message

        try:
            client.connect(self.host)
        except:
            print("MQTT Broker is not online. Connect later.")
            return ""

        print("Sending message:\n{}".format(self.payload))

        wait_until = datetime.now() + timedelta(seconds=30)

        while self.mqtt_looping:
            client.loop()
            if self.mqtt_looping == False:
                break
            elif wait_until < datetime.now():
                if not self.response:

                    # FIXME Case:1-1，Ethernet，發送端(Server)，發送訊息
                    # FIXME Case:3-1，Ethernet，發送端(Gateway)，發送訊息
                    self.record(method="publish", action=action, target=target)

                    publish.single(self.publish_topic, self.payload, qos=self.qos, hostname=self.host)
                    print("publish again")
                    time.sleep(5)
                else:
                    wait_until = datetime.now() + timedelta(seconds=10)

        if not self.response:
            print("timeout")
            return None

        client.disconnect()

        print("TYPE:", type(self.response))
        print("FULL:", self.response)

        return self.response

    # TODO:可更精簡，把 payload 改為 self.payload
    def nbiot_message_parser(self, message):
        message = message.replace('\r', '')

        length = len(message)

        print("len:", length)
        print("content:", message)

        # 依照 topic 來切分， SMSUB: host_uuid/to/gw_id/action/target, "payload"
        message_list = message.split('/')

        # get gateway_id
        gateway_id = message_list[-4]

        # get action
        self.action = message_list[-3]

        # get target
        self.target = message_list[-2]

        print("Gateway id:", gateway_id)
        print("action:", self.action)
        print("target:", self.target)

        # resquest,"payload"
        last_list = message_list[-1].split('"', 1)

        # method，request/response，此收到皆為 response
        self.method = last_list[0]
        payload = last_list[-1]

        # 去除 ,"  最後 "
        payload = payload[2:-1]
        print("Payload:", payload)
        print("Type:", type(payload))

        return payload

    def nbiot_deliver(self):
        print("NB-IoT Deliver")
        self.composition = self.task + self.task_segment + self.method + self.message_segment + self.payload
        print("Compostion:",self.composition)
        self.r.rpush(self.redis_publish, self.composition)

    def nbiot_response(self):
        print("NB-IoT Monitor Start")
        # 不斷監聽
        while True:
            time.sleep(0.5)

            # 檢查有幾封接收的訊息(任務)
            response_queue = R.llen(self.redis_web_response)

            # 若有訊息(任務)要執行
            if response_queue:
                print("-" * 10)
                print("Web Response Queue:", self.redis_web_response)
                print("-" * 10)

                # 從 Redis 的 Queue 取出第一筆訊息
                message = R.lpop(self.redis_web_response).decode(self.coding)

                # 使用解析器得到資訊
                self.payload = self.nbiot_message_parser(message)

                # FIXME Case:3-4，NB-IoT，發送端(Gateway)，接收回傳
                self.record(method="receive", action=self.action, target=self.target)

                # 讓無窮迴圈休息，減緩機器負擔、避免過熱
                # (sec.)
                time.sleep(0.2)
                break

        return self.payload

    # 主函式
    def start(self):
        if DELIVER_WAY == "Ethernet":
            response = self.ethernet_response()
        elif DELIVER_WAY == "NB-IoT":
            self.nbiot_deliver()
            response = self.nbiot_response()

        return response


def test():
    # MQTT Broker
    mqtt_host = "140.116.39.212"

    # Server_id
    server_id = "140.116.39.172"

    # Gateway_id
    gateway_id = "09ea6335-d2bd-4678-9ca9-647b5574a09e"

    # Task
    task = "control/node"

    # Payload
    payload = json.dumps({})

    mqtt_talker = MqttTalker(mqtt_host, gateway_id, task, payload)

    response = mqtt_talker.start()

    if response:
        return response, 201
    else:
        return "Failure", 201


if __name__ == "__main__":
    print("Result:\n", test())
