# coding: utf-8
import os
import sys
import time
import json
import signal

from flask import jsonify
from datetime import datetime, timedelta

# mqtt paho
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
# import paho.mqtt.subscribe as subscribe


class MqttOnEthernet():

    # create instance
    def __init__(self):
        # Defaults 0
        self._qos = 0

    # TODO Broker setting label
    # setting Broker IP/port
    def set_broker_info(self, host, port):
        # Broker IP or URL
        self._host = host

        # Port 1883 or 8883(TLS) / Default 1883
        self._port = port

    def set_qos(self, qos):
        # Defaults 0
        self._qos = qos

    # 當 Client 接收到來自 Broker 的確認連線請求時
    def on_connect(self, mq, userdata, rc, _):
        print("Connection returned result:", rc)

        # instance subscribe example
        mq.subscribe(self._topic, qos=self._qos)
        print("Subscribe:", self._topic)

    # 當接收到訂閱的主題訊息時，輸出訊息連線狀況及內容
    def on_message(self, mq, userdata, msg):
        print("Received message Topic:", msg.topic)
        print("Received message Qos:", msg.qos)
        # payload are bytes types, convert to str type
        print("Received message Payload:", msg.payload.decode("utf-8"))

    # TODO subscribe label
    def subscribe(self, topic):
        self._topic = topic

        # create Client instance
        client = mqtt.Client()

        client.on_connect = self.on_connect
        client.on_message = self.on_message

        try:
            # connect to broker (IP/URL)
            client.connect(self._host)
        except:
            print("MQTT Broker is not online. Connect later.")

        # nonblocking function
        client.loop_forever()

    # TODO publish label
    def publish(self, topic, payload):
        # publish example
        publish.single(topic, payload, qos=self._qos,
                       hostname=self._host, port=self._port)
        print("Publish:", topic)

        #   Publish full
        # single(topic, payload=None, qos=0, retain=False, hostname="localhost",
        # port=1883, client_id="", keepalive=60, will=None, auth=None, tls=None,
        # protocol=mqtt.MQTTv311, transport="tcp")

    def multiple_publish(self, msgs):
        publish.multiple(msgs, hostname=self._host)


def test():
    # Broker
    mqtt_host = '140.116.39.212'

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/festival'
    # message = json.dumps({
    #     "id": 5,
    #     "gateway_id": 1,
    #     "date": "2020-11-25",
    #     "statement": "5",
    #     "bind": "weekday",
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/schedule_list_test'
    # message = json.dumps({
    #     "id": 5,
    #     "gateway_id": 1,
    #     "bind": "weekday",
    #     "group_id": 2,
    #     "group_state": "ON",
    #     "control_time": "07:00:00",
    #     "control_time_of_sun": "sun",
    #     "available": 0
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/sunset'
    # message = json.dumps({
    #     "id": 5,
    #     "gateway_id": 1,
    #     "calendar": "weekday",
    #     "group_id": 2,
    #     "group_state": "ON",
    #     "control_time": "08:00:00",
    #     "control_time_of_sun": "sunset",
    #     "available": 0
    # })


    topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/control/node'
    message = json.dumps({
        "device_address": 2,
        "state": 0,
        "num": 1,
    })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/control/group'
    # message = json.dumps({
    #     "num": 1,
    #     "state": "ON"
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/control/scene'
    # message = json.dumps({
    #     "num": 1,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/area_list'
    # message = json.dumps({
    #         "id": 3,
    #         "gateway_id": 1,
    #         "name": 'area3',
    #     })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/update/area_list'
    # message = json.dumps({
    #         "id": 3,
    #         "name": 'area3-1',
    #     })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/delete/area_list'
    # message = json.dumps({
    #         "id": 3,
    #     })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/area_node'
    # message = json.dumps({
    #     "id": 1,
    #     "area_id": 1,
    #     "node_id": 2,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/delete/area_node'
    # message = json.dumps({
    #     "id": 1,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/area_group'
    # message = json.dumps({
    #     "id": 1,
    #     "area_id": 1,
    #     "group_id": 2,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/delete/area_group'
    # message = json.dumps({
    #     "id": 1,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/area_scene'
    # message = json.dumps({
    #     "id": 1,
    #     "area_id": 1,
    #     "scene_id": 2,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/delete/area_scene'
    # message = json.dumps({
    #    "id": 1,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/group'
    # message = json.dumps({
    #     "id": 5,
    #     "area_id": 1,
    #     "group_num": 1,
    #     "group_name": "window",
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/update/group'
    # message = json.dumps({
    #     "id": 5,
    #     "group_name": "window_new",
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/delete/group'
    # message = json.dumps({
    #     "id": 5,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/group_node'
    # message = json.dumps({
    #     "id":1,
    #     "group_id": 1,
    #     "node_id": 2,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/delete/group_node'
    # message = json.dumps({
    #     "id":1,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/scene'
    # message = json.dumps({
    #     "id": 5,
    #     "area_id": 1,
    #     "scene_num": 1,
    #     "scene_name": "night",
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/update/scene'
    # message = json.dumps({
    #     "id": 5,
    #     "scene_name": "night_new",
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/delete/scene'
    # message = json.dumps({
    #     "scene_id": 5,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/scene_node'
    # message = json.dumps({
    #     "id": 1,
    #     "scene_id": 1,
    #     "node_id": 2,
    #     "node_state": "ON"
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/delete/scene_node'
    # message = json.dumps({
    #     "id":1
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/device'
    # message = json.dumps({
    #     'id':10,
    #     'gw_id':1,
    #     'name': 'LB3000',
    #     'type_id':2,
    #     'address':1,
    #     'channel':8,
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/update/device'
    # message = json.dumps({
    #     'Field':{
    #     'device_name': 'LC3000',
    #     'type_id':2,
    #     'address':3,
    #     'channel':8,
    # }
    #     'WHERE': {
    #         'id': 10,
    #     }
    # })

    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/delete/device'
    # message = json.dumps({
    #     'id': 10,
    # })


    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/update/node'
    # message = json.dumps({
    #     "name": 2,
    #     "num": 1,
    #     'WHERE': {
    #         'device_address': 2,
    #         'num': 1,
    #     }
    # })

    # TODO 與思嘉討論
    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/setting'
    # message = json.dumps({
    #     'model': 'PM210-4-STD',
    #     'address': 1,
    #     'ch':1,
    #     'speed':9600,
    #     'circuit':1,
    #     'pt':1,
    #     'ct':1,
    #     'meter_type':3,
    # })


    # topic = '140.116.39.172/to/09ea6335-d2bd-4678-9ca9-647b5574a09e/update/demand_setting'
    # message = json.dumps({
    #     'value': 100,
    #     'value_max': 1,
    #     'value_min':1,
    #     'load_off_gap':9600,
    #     'reload_delay':1,
    #     'reload_gap':1,
    #     'cycle':1,
    # })


    # 512 bytes
    # message = json.dumps([
    #     {'id': '1',
    #      'group_num': '1',
    #      'group_name': '1 floor',
    #      'group_state': 'on'},
    #     {'id': '2',
    #      'group_num': '2',
    #      'group_name': '2 floor',
    #      'group_state': 'off'}
    # ])

    # topic = '140.116.39.172/from/09ea6335-d2bd-4678-9ca9-647b5574a09e/insert/festival'
    # message = json.dumps({
    #     "id": 5,
    #     "gateway_id": 1,
    #     "date": "2020-11-25",
    #     "statement": "5",
    #     "bind": "weekday",
    # })

    instance1 = MqttOnEthernet()

    try:
        instance1.set_broker_info(host=mqtt_host, port=1883)
        instance1.set_qos(qos=2)    # can be omitted
        instance1.publish(topic=topic, payload=message)
    except:
        print("Missing step")



if __name__ == "__main__":
    test()
    # print("Result:\n", test())
