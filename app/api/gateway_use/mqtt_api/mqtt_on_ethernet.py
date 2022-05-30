# coding=utf-8
# import time

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

# import mqtt_dispatcher
import mqtt_api.mqtt_dispatcher as mqtt_dispatcher

# from datetime import datetime
# import device.config.setting as setting
from device.config.setting import *

# ROLE = dbconfig.ROLE
# DELIVER_WAY = dwconfig.DELIVER_WAY

# ROLE = setting.ROLE
# DELIVER_WAY = setting.DELIVER_WAY

class MqttOnEthernet:

    def __init__(self, host, server_id, gateway_id, topic):

        self.host = host
        self.gateway_id = gateway_id
        self.topic = topic
        self.response = ""
        self.qos = 1

        self.mqtt_client = mqtt.Client()
        self._init_mqtt()

        self.server_id = server_id
        self.redis_time = time.time()

        # redis
        self.r = R



    def _init_mqtt(self):
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message

        try:
            self.mqtt_client.connect_async(self.host, 1883, 30)
            self.mqtt_client.loop_start()
        except:
            print('MQTT Broker is not online. Connect later.')

    # 當與 broker 使用 MQTT 連線上的時候，(不須與 broker 保持連線)
    def on_mqtt_connect(self, mq, userdata, flags, rc):
        print(mq)
        print(userdata)
        print(flags)
        print(rc)

        if ROLE == "Server":
            self.mqtt_client.subscribe("{}/from/{}/{}".format(self.server_id, self.gateway_id, self.topic), qos=self.qos)
            print('Subscribe:\n{}/from/{}/{}\n'.format(self.server_id, self.gateway_id, self.topic))

        elif ROLE == "Gateway":
            self.mqtt_client.subscribe("{}/to/{}/{}".format(self.server_id, self.gateway_id, self.topic), qos=self.qos)
            print('Subscribe:\n{}/to/{}/{}\n'.format(self.server_id, self.gateway_id, self.topic))

    # 當有訂閱的主題，收到訊息時
    def on_mqtt_message(self, mq, userdata, msg):
        try:
            print("-----")
            print("Receiving messages from {} (qos={})...".format(msg.topic, msg.qos))
            print("LEN:", len(msg.payload))
            print("Content:\n{}".format(msg.payload))

            host_uuid, direct, gateway_id, action, target, method = msg.topic.split("/")

            # self.record(method="receive", action=action, target=target)

            self.redis_record(method="receive", action=action, target=target)

            # 分配任務
            mqtt_dispatcher.main_processing(gateway_id=gateway_id, action=action, target=target, method=method, payload=msg.payload.decode("utf-8"))

        except:
            print("--on_mqtt_message Error!--")

    def publish(self, topic, payload):

        if ROLE == "Server":
            publish.single("{}/to/{}/{}/{}/response".format(self.server_id, self.gateway_id, action, target), payload, qos=publish_qos, hostname=mqtt_host)

        if ROLE == "Gateway":
            publish.single("{}/from/{}/{}/{}/response".format(self.server_id, self.gateway_id, action, target), payload, qos=publish_qos, hostname=mqtt_host)


    # 原始
    # def run(self):
    #     while True:
    #         pass

    # 檢查 redis 有無欲發送的訊息，再發送
    def run(self):
        redis_publish = "publish"
        coding = "utf-8"

        while True:

            # 檢查有幾封訊息待發送
            publish_queue = self.r.llen(redis_publish)

            # 若有訊息待發
            if publish_queue and self.can_publish_flag:
                print('-' * 10)
                print('task Queue:', publish_queue)

                # 取出 Queue 中第一筆訊息
                message = self.r.lpop(redis_publish).decode(coding)
                message_list = message.split('|')

                # action/target/method
                action, target, method = message_list[0].split("/")

                # self.record(method="publish", action=action, target=target)

                # topic = publish_topic + action/target/method
                # payload = payload
                self.publish(topic=self.publish_topic + message_list[0],
                                payload=message_list[1])

            # 減少負荷、避免過熱
            time.sleep(0.2) # (sec.)


    def record(self, method, action, target):
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
        print("Method:", method, " Action:", action, " Target:", target)
        print("Write SQL Time:", write_sql_time)

    def redis_record(self, method, action, target):
        self.redis_time = time.time()
        str_time = str(self.redis_time)
        redis_content = action + '/' + target + '/' + str_time
        R.rpush("transmit_receive", redis_content)