# coding=utf-8
# import os
import re
# import redis
# import time
# import json
# import signal
import serial

# from datetime import datetime, timedelta

# 資料庫資訊
# import device.config.database_setting as dbconfig

# 傳遞方式
# import device.config.deliver_way_setting as dwconfig

#
# import device.config.setting as setting
from device.config.setting import *

# ROLE = dbconfig.ROLE
# DELIVER_WAY = dwconfig.DELIVER_WAY

# ROLE = setting.ROLE
# DELIVER_WAY = setting.DELIVER_WAY

class MqttOnNbiot():

    # 初始化設定，當某實例生成時即有的類別屬性
    def __init__(self, host, server_id, gateway_id, topic):

        # self.r = redis.Redis("localhost")
        self.r = R

        self.qos = bytes(str(1), encoding="utf8")
        self.full_message = bytes("", encoding="utf-8")

        # Timer
        self.timer_flag = True
        self.composition_start_time = time.time()
        self.composition_end_time = time.time()
        self.composition_full_message_spend_time = time.time()

        # Timer Publish
        self.can_publish_flag = True
        self.publish_start_time = time.time()
        self.publish_end_time = time.time()
        self.at_cmd_publish_spend_time = time.time()

        # Publish 時間點
        self.publish_record_time = datetime.now()
        # Receive 時間點
        self.receive_record_time = datetime.now()

        # check
        self.smsub_received = bytes('SMSUB', encoding="utf-8")
        self.OK_received = bytes('OK', encoding="utf-8")

        # Regex
        self.regex_find_smsub = "SMSUB.*"
        # self.regex_find_smpub = "SMPUB.*"

        self.serial = "/dev/ttyUSB0" # default

        self.host = host
        self.broker_port = 1883
        self.qos = 1

        if ROLE == "Gateway":
            self.publish_topic = server_id + "/from/" + gateway_id + "/"
            self.subscribe_topic = server_id + "/to/" + gateway_id + "/#"
        # elif ROLE == "Server":
        #     self.publish_topic = server_id + "/to/" + gateway_id + "/"
        #     self.subscribe_topic = server_id + "/from/" + gateway_id + "/#"

        # TODO:最佳化 time (.sec)
        self.setting_time = 0.1
        self.publish_time = 0.1
        self.subscribe_time = 1.0

        # 連接資料庫
        # self.dbh = daesql.MySQL(dbconfig.mysql_config)
        self.dbh = dbh

    def set_broker_info(self, host, port="1883"):
        coding = "utf-8"
        port = str(port)
        # self.port = bytes("1883", encoding=coding)
        self.host = bytes(host, encoding=coding)
        self.port = bytes(port, encoding=coding)

    def set_qos(self, qos):
        self.qos = bytes(str(qos), encoding="utf-8")

    def set_serial(self, serial_port):
        # serial
        self.serial_time_out = 0.1
        self.serial_baudrate = 115200
        self.serial_port = serial_port
        self.ser = serial.Serial(
            self.serial_port, baudrate=self.serial_baudrate, timeout=self.serial_time_out)
        time.sleep(self.setting_time)

    def redis_receive_record(self):
        redis_time = time.time()
        str_time = str(redis_time)
        redis_content = "insert" + '/' + "electricity" + '/' + str_time
        R.rpush("transmit_receive", redis_content)

    def redis_publish_record(self):
        redis_time = time.time()
        str_time = str(redis_time)
        redis_content = "insert" + '/' + "electricity" + '/' + str_time
        R.rpush("transmit_publish", redis_content)

    def deal_received_message(self, message):

        # 當有收到訊息
        if message:
            coding = "utf-8"

            # print(message)

            # 設立一個變數，把訊息接在一起
            self.full_message += message

            # 計時發訊時間，當可以計時，重製初始紀錄時間
            if self.timer_flag:
                self.timer_flag = False
                self.composition_start_time = time.time()

            # 辨別內容是否有 publish 回傳的 OK ，有則可以進行下次推訊 (publish 回傳的 OK 會寫進 serial)
            if self.OK_received in self.full_message:

                self.can_publish_flag = True

                # 將 publish 回傳的 OK 取代掉
                self.check_message = re.sub(
                    "[OK]", "", self.full_message.decode(coding))
                self.check_message = bytes(self.check_message, encoding=coding)

                if self.check_message:
                    # 將資料寫回變數
                    self.full_message = self.check_message
                    self.publish_end_time = time.time()

                    # Publish OK Time
                    self.publish_record_time = datetime.now()
                    print("Publish Record Time", self.publish_record_time)
                    print("Publish Message:", self.full_message)

                    # 用 AT Command Publish 到成功，總花費時間
                    self.at_cmd_publish_spend_time = self.publish_end_time - self.publish_start_time
                    print("Publish OK Spend:", self.at_cmd_publish_spend_time, " s")

                    # 清空每次 Publish 訊息
                    # self.full_message = bytes("", encoding="utf-8")
                    # self.composition_start_time = time.time()

            # 確認訊息中有收到 SMSUB
            if self.smsub_received in self.full_message:

                # 再確認是否收到結尾訊息(\n)，"\x0a"，確保此為完整訊息
                if self.full_message[-1] == 10:
                    # self.receive_end_flag = True

                    # 收到訊息記錄時間點
                    self.receive_record_time = datetime.now()
                    print("-"*3)
                    print("Receive Record Time:", self.receive_record_time)

                    # 將確認為完整的一封訊息轉型
                    self.full_message = self.full_message.decode(coding)

                    print("Receive Full Message:", self.full_message)

                    # 找尋要的片段訊息
                    self.find_pattern = re.findall(
                        self.regex_find_smsub, self.full_message)

                    # 如果有找到的訊息
                    if self.find_pattern:

                        # 計算花費時間，由組成的訊息中找到要的片段
                        self.composition_end_time = time.time()
                        self.composition_full_message_spend = self.composition_end_time - self.composition_start_time

                        # DONE:
                        self.redis_receive_record()

                        # print("\n")
                        print("Composition Full Receive Message Spend:", self.composition_full_message_spend, " s")

                        for i in range(len(self.find_pattern)):

                            if '{"state": "ok"}' in self.find_pattern[i]:
                                # print("I find you")
                                self.r.rpush("response", self.find_pattern[i])
                                # print("Response Message:", self.find_pattern[i])
                            elif '{"state": "fail"}' in self.find_pattern[i]:
                                self.r.rpush("response", self.find_pattern[i])
                                # print("Response Message:", self.find_pattern[i])
                                # print(self.find_pattern[i])
                            else:
                                self.r.rpush("receive", self.find_pattern[i])
                                # print("Receive Message:", self.find_pattern[i])

                        # self.r.rpush(redis_receive, find_pattern)
                        # print("SUB:", find_pattern)

                        # 讓 timer_flag = True，可以進行下次計時
                        self.timer_flag = True

                        print("-")

                    # 清空變數中的訊息，重新儲存下一筆完整訊息
                    self.full_message = bytes("", encoding="utf-8")
        # 當沒有訊息
        elif not message:
            # 離開函式
            return None

    def wait_for_message_once(self):
        content = self.ser.read_until(
            b'\n', size=512)
        # 當有訊息來時
        if content:
            # 處理訊息
            self.deal_received_message(content)

    # 關閉 MQTT 連線
    def mqtt_close(self):
        # Disconnection MQTT
        self.ser.write(b'AT+SMDISC\r')
        time.sleep(self.setting_time)

        # Disconnect wireless
        self.ser.write(b'AT+CNACT=0\r')
        time.sleep(self.setting_time)

    # 檢查目前 MQTT 連線狀態
    def mqtt_status(self):
        self.ser.write(b'AT+SMSTATE?\r')
        time.sleep(self.setting_time)

        content = self.ser.read_until(b'OK\r\n', size=512)

        # TODO: 自動化
        print(content)

    def mqtt_setup(self):
        # Open wireless connection
        self.ser.write(b'AT+CNACT=1,"nbiot"\r')
        time.sleep(self.setting_time)

        # Config
        # (indispensable parameter) server URL address
        self.ser.write(b'AT+SMCONF="url","%s",%s\r' %(self.host, self.port))
        time.sleep(self.setting_time)

        # Hold connect time. default is 60s
        self.ser.write(b'AT+SMCONF="KEEPTIME",60\r')
        time.sleep(self.setting_time)

        # Send packet qos level. range of values（0~2）
        self.ser.write(b'AT+SMCONF="QOS","%s"\r' % (self.qos))
        time.sleep(self.setting_time)

        # MQTT Connection
        # TODO:判斷 MQTT 連線狀態
        self.ser.write(b'AT+SMCONN\r')
        time.sleep(self.setting_time)

        self.ser.flushInput()
        time.sleep(self.setting_time)

    def unsubscribe(self, topic):
        self.unsubscribe_topic = bytes(topic, encoding='utf8')

        # UnSubscribe Packet
        self.ser.write(b'AT+SMUNSUB="%s"\r' % (self.unsubscribe_topic))
        time.sleep(self.setting_time)

        # display unsubscribe topic
        print("unsubscribe:", topic)

        self.ser.flushInput()
        time.sleep(self.setting_time)

    def subscribe(self, topic):
        self.subscribe_topic = bytes(topic, encoding='utf8')
        self.ser.write(b'AT+SMSUB="%s",2\r' % (self.subscribe_topic))


        time.sleep(self.subscribe_time)

        print("NB-IoT Subscribe:", topic)
        self.ser.flushInput()
        time.sleep(self.setting_time)

    def publish(self, topic, payload):
        self.topic = bytes(topic, encoding="utf8")
        self.payload = bytes(payload, encoding="utf8")
        self.len = bytes(str(len(str(payload))), encoding="utf8")
        self.publish_start_time = time.time()

        self.ser.write(b'AT+SMPUB="%s","%s",%s,0\r' %(self.topic, self.len, self.qos))

        time.sleep(self.publish_time)

        # publish content
        self.ser.write(self.payload + b'\r')

        # display publish topic
        print("NB-IoT Publish:", topic)

        # DONE:
        self.redis_publish_record()

        # # 以 \n 做結尾符號，讀取 serial 資料
        # content = self.ser.read_until(
        #     b'\n', size=512)

        # # 當有訊息
        # if content:
        #     self.deal_received_message(content)

    # EDRX NB-IoT 收訊息是否會進入休眠狀態， 0 = 不會，1 = 會
    # TODO: Close_EDRX(self, EDRX)
    def Close_EDRX(self):
        self.ser.write(b'AT+CEDRXS=0\r')
        time.sleep(self.setting_time)

        content = self.ser.read_until(b'OK\r\n', size=5000)
        print(content)

    def mointor(self):
        redis_publish = "publish"
        coding = "utf-8"

        while True:

            # 檢查有幾封訊息待發送
            publish_queue = self.r.llen(redis_publish)

            # 若有訊息待發(給後端)
            if publish_queue and self.can_publish_flag:
                print('-' * 10)
                print('task Queue:', publish_queue)

                # 取出 Queue 中第一筆訊息
                message = self.r.lpop(redis_publish).decode(coding)
                message_list = message.split('|')

                # action/target/method
                action, target, method = message_list[0].split("/")

                # FIXME: Case:1-3，NB-IoT，接收端(Gateway)，發送訊息
                # FIXME: Case:2-1，NB-IoT，發送端(Gateway)，發送訊息
                # FIXME: Case:3-1，NB-IoT，發送端(Gateway)，發送訊息
                # self.record(method="publish", action=action, target=target)

                # topic = publish_topic + action/target/method
                # payload = payload
                self.publish(topic=self.publish_topic + message_list[0],
                                payload=message_list[1])

            # 若沒有發訊任務，則等待接收訊息
            else:
                self.wait_for_message_once()

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
            log_result = self.dbh.execute(sql)
        except BaseException as n:
            print("Log Fail:", n)

        sql_end_time = datetime.now()
        write_sql_time = sql_end_time - sql_start_time

        # print("Role:", ROLE," Delivery:", DELIVER_WAY)
        print("Method:", method, " Action:", action, " Target:", target)
        print("Write SQL Time:", write_sql_time)


    def init_set(self):
        self.set_serial(serial_port=self.serial)
        self.set_broker_info(host=self.host, port=self.broker_port)
        self.set_qos(qos=self.qos)  # can be omitted
        self.mqtt_setup()
        self.subscribe(topic=self.subscribe_topic)
        self.Close_EDRX()

    def run(self):
        # 開始計時，計算設置類別總花費時間
        start_time = time.time()

        self.init_set()

        # 結束計時，計算設置類別總花費時間
        end_time = time.time()

        # 設定功能等總花費時間
        spend = end_time - start_time
        print("Setting Spend:", spend, " s")

        # 等著收訊 & 發訊
        self.mointor()