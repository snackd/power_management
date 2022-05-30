# encoding=utf-8
#! /usr/bin/python
# import sys
# import json
# import time
# import redis
# import threading
# from datetime import datetime

from . import common as common

# import serial_for_modbus as serial_api
from . import serial_for_modbus as serial_api

from . import condition as condition
# import condition as daesql

from . import parser as parser
from . import converter as converter

# from .config import setting as setting
from .config.setting import *

# MQTT
# import paho.mqtt.publish as publish

# Schedule
# from apscheduler.schedulers.blocking import BlockingScheduler

# ROLE = setting.ROLE
# DELIVER_WAY = setting.DELIVER_WAY

# print("Meter Role:", ROLE)
# print("Meter Deliver_way:", DELIVER_WAY)

class Meter(threading.Thread):

    # /dev/ttyS1 for Nanopi RS485, tr pin is 6
    def __init__(self, cond, port="/dev/ttyS1", tr_pin=6, baudrate=9600):
        super(Meter, self).__init__()
        # print("---Meter---")

        # redis
        self.r = R
        # self.r = redis.Redis('localhost')
        # self.r = setting.R

        # 使用 serial 接口下 Modbus
        self.serial = serial_api.Modbus()
        self.port = port
        self.baudrate = baudrate
        self.tr_pin = tr_pin
        self.serial.set_serial(port=self.port, baudrate=self.baudrate)
        # print("port:", self.port)
        # print("baud rate:", self.baudrate)

        # 高級鎖
        self.cond = cond

        # DB
        self.dbh = dbh
        # self.dbh = daesql.MySQL(dbconfig.mysql_config)
        # self.dbh = setting.sql_connect

        # 卸載用
        self.status = 0
        self.unloading_list = []
        self.last_number = 0

        # Gateway Setting
        self.mac_address = mac_address
        self.gateway_id = 1
        self.device_type_id = 4
        self.device_id = 10
        self.server_device_id = 10
        # self.mac_address = "09ea6335-d2bd-4678-9ca9-647b5574a09e"

        # Demand Value
        self.PD1 = 0    # 1 分鐘需量
        self.PD15 = 0   # 15 分鐘需量
        self.time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # MQTT
        self.mqtt_host = cloud_mqtt_host  # Broker
        self.server_id = server_host  # Server ip address
        self.publish_qos = 0

        # self.mqtt_host = setting.cloud_mqtt_host  # Broker
        # self.server_id = setting.server_host  # Server ip address

    # 從電錶讀資料
    def run(self):
        print("---Read Meter run---")

        # config = common.get_server_settings()

        self.read_gateway_id()
        self.read_device_id()

        temp = 30.000000

        scheduler = BlockingScheduler()
        scheduler.add_job(self.read_data_from_meter,
                            'interval', seconds=60.000000, max_instances=100)
        scheduler.start()

    # 讀取資料並作處理，由 4 個函式組成
    def read_data_from_meter(self):
        self.read_demand_setting()
        self.read_pm210()
        self.demand_control()
        self.mqtt_publish()

    # 讀取 gateway_id
    def read_gateway_id(self):
        column_name = "id"
        table_name = "gateway_list"
        condition_name = "mac_address"

        sql = (
            "SELECT `{0}` "
            "FROM `{1}` "
            "WHERE `{2}` = '{3}' "
        ).format(column_name, table_name, condition_name, self.mac_address)

        result = self.dbh.query(sql)

        if not result:
            print("Not found gateway_id!")
            sys.exit()

        result_list = result[0]
        self.gateway_id = result_list['id']

    # 讀取 device_type_id
    def read_device_type_id(self):
        column_name = "id"
        table_name = "device_type_list"
        condition_name = "name"

        sql = (
            "SELECT `{0}` "
            "FROM `{1}` "
            "WHERE `{2}`= '{3}' "
        ).format(column_name, table_name, condition_name, self.mac_address)

        result = self.dbh.query(sql)

        if not result:
            print("Not found device_type_id!")
            sys.exit()

        result_list = result[0]
        self.device_type_id = result_list['id']

    # 讀取 device_id
    def read_device_id(self):
        column_name = "id"  # Server device_id
        column_name2 = "device_id"   # Gateway device_id
        table_name = "device_list"
        condition_name = "gateway_id"
        condition_name2 = "type_id"

        sql = (
            "SELECT `{0}`, `{1}` "
            "FROM `{2}` "
            "WHERE `{3}` = '{4}' "
            "AND `{5}` = '{6}' "
        ).format(column_name, column_name2, table_name,
                 condition_name, self.gateway_id, condition_name2, self.device_type_id)

        result = self.dbh.query(sql)

        if not result:
            print("Not found device_id!")
            sys.exit()

        result_list = result[0]
        self.server_device_id = result_list['id']
        self.device_id = result_list['device_id']

    # 讀取需量設定
    def read_demand_setting(self):

        table_name = "demand_setting_list"
        column_name = "*"
        condition_name = "gateway_id"

        sql = (
            "SELECT `{0}` "
            "FROM `{1}` "
            "WHERE `{2}` = '{3}'"
        ).format(column_name, table_name, condition_name, self.gateway_id)
        # print("sql:", sql)

        demand_setting = self.dbh.query(sql)
        # print("demand_setting:", demand_setting)

        if not demand_setting:
            print("Not found demand setting!")
            sys.exit()

        # 讀取電錶設定，該列資料
        setting = demand_setting[0]

        self.max_demand = setting["max_value"]       # 需量契約容量
        self.upper_demand = setting["upper"]         # 需量上限
        self.lower_demand = setting["lower"]         # 需量下限
        self.load_off_gap = setting["load_off_gap"]  # 卸載間隔(延遲)時間
        self.reload_delay = setting["reload_delay"]  # 復歸延遲時間
        self.cycle = setting["cycle"]                # 計算週期，default (15 min)
        self.mode = setting["mode"]                  # 卸載模式

    # 開關點位 (LT3504) 接口為 dev/ttyS1，與電表一致
    def switch_group(self, group_num, status):

        if(status >= 1 and status <= 100):
            cmd = [1, 5, 1, group_num, 255, 0]
        elif status == 0:
            cmd = [1, 5, 1, group_num, 0, 0]
        else:
            raise Exception('status error')

        if group_num < 0 and group_num > 3:
            raise Exception('Num error')

        response = self.serial.write_command_to_modbus(cmd)

        return response

    # 讀取 PM210 型號的電錶
    def read_pm210(self):
        self.time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("---Read PM210---")

        self.serial.set_serial(port=self.port, baudrate=self.baudrate)

        cmd = [1, 3, 0, 20, 0, 36]

        response = self.serial.write_command_to_modbus(cmd)

        if response:
            # 解析、轉換計算 PM210 回傳的電力參數
            if response[0] == 1:
                response = parser.pm210_calculate_value(data_list=response)
                # print("Response:", len(response))
                response = converter.pm210_unit(data_list=response)
            else:
                print("Not PM210")
        else:
            print("No response")

        time.sleep(0.5)

        # print("Read Meter:", response)
        self.PD1 = response[-1]
        self.PD15 = response[-2]

        time.sleep(0.2)

        sql = (
            "INSERT INTO `electricity_list` "
            "(`gateway_id`, `device_id`, `demand_min`, `demand_quarter`, `recorded_at`) "
            "VALUES('{0}', '{1}', '{2}', '{3}', '{4}') "
        ).format(self.gateway_id, self.device_id, self.PD1, self.PD15, self.time_now)

        # print("SQL:", sql)
        result = self.dbh.execute(sql)

    # 需量控制，使需量使用在契約上、下限之間浮動
    def demand_control(self):
        print("-" * 10)
        print("value:", self.PD15)
        print("-" * 10)

        # 如果需量超過高限，則啟動卸載機制，保證需量不會超過
        if self.status == 0 or self.status == 2:
            if float(self.PD15) >= float(self.upper_demand):
                self.status = 1
                self.unload_device(gateway_id=self.gateway_id, mode=self.mode, upper_demand=self.upper_demand, delay=self.load_off_gap)
                reverting_flag = self.check_to_revert()
                print("Reverting Flag:", reverting_flag)

        # 如果需量已經低於低限，則復歸裝置
        if self.status == 1:
            if float(self.PD15) < float(self.lower_demand):
                self.status = 2
                self.revert_device(self.mode, self.reload_delay)

    def record(self, method, action, table):
        sql_start_time = datetime.now()

        try:
            sql = (
                "INSERT INTO `log_list` "
                "(`role`, `type`, `deliver_way`, `action`, `table`, `result`) "
                "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}') "
            ).format(ROLE, method, DELIVER_WAY, action, table, "ok")
            log_result = self.dbh.execute(sql)
        except BaseException as n:
            print("Log Fail:", n)

        sql_end_time = datetime.now()

        write_sql_time = sql_end_time - sql_start_time

        # print("Role:", ROLE," Delivery:", DELIVER_WAY)
        print("Method:", method, " Action:", action, " Table:", table)
        print("Write SQL Time:", write_sql_time)

    def redis_record(self, method, action, table):
        redis_time = time.time()
        str_time = str(redis_time)
        redis_content = action + '/' + table + '/' + str_time
        R.rpush("transmit_publish", redis_content)

    # 發 MQTT 訊息至 Server，中間透過 Broker
    def mqtt_publish(self):
        action = "insert"
        table = "electricity"

        payload_dic = {
            "device_id": self.server_device_id,
            "demand_min": self.PD1,
            "demand_quarter": self.PD15,
            "recorded_at": self.time_now,
        }
        payload = json.dumps(payload_dic)

        # FIXME:Case:2-1，Ethernet，發送端(Gateway)，發送訊息
        # FIXME:Case:2-1，NB-IoT，發送端(Gateway)，發送訊息
        # self.record(method="publish", action=action, table=table)

        # Ethernet
        if DELIVER_WAY == "Ethernet":
            # DONE:
            self.redis_record(method="publish", action=action, table=table)

            publish.single("{}/from/{}/{}/{}/request".format(self.server_id, self.mac_address, action, table), payload, qos=self.publish_qos, hostname=self.mqtt_host)
            print("Ethernet Publish:{}/from/{}/{}/{}/request".format(self.server_id, self.mac_address, action, table))
        elif DELIVER_WAY == "NB-IoT":
            redis_publish = "publish"
            method = "request"
            composition = action + "/" + table + "/" + method + "|" + payload
            self.r.rpush(redis_publish, composition)

    # 需量設定
    def demand_setting(self):

        table_name = "demand_setting_list"
        update_column_name = "max_value"
        condition_name = "gateway_id"
        value = 350

        sql = (
            "UPDATE `{0}` "
            "SET `{1}` = '{2}' "
            "WHERE `{3}` = '{4}' "
        ).format(table_name, update_column_name, value, condition_name, self.gateway_id)

        result = self.dbh.execute(sql)

    # 檢查還原
    def check_to_revert(self):
        if float(self.PD15) < float(self.upper_demand):
            self.status = 1
            return True
        else:
            return False

    # 卸載設備
    def unload_device(self, gateway_id, mode, upper_demand, delay):

        table_name = "unload_group_list"
        column_name = "unload_group_id"
        column_name2 = "unload_group_state"
        condition_name = "gateway_id"

        sql = (
            "SELECT `{0}`, `{1}` "
            "FROM `{2}` "
            "WHERE `{3}`  = '{4}'"
        ).format(column_name, column_name2, table_name, condition_name, self.gateway_id)
        print("sql:", sql)

        result = self.dbh.query(sql)

        unload_list = []
        for row in result:
            setting_state = row["unload_group_state"]
            unload_list.append(setting_state)

        print("UN:", unload_list)

        # 1:先卸載先復歸
        # 2: 先卸載後復歸
        # 3: 循環先卸載先復歸
        # 4: 循環先卸載後復歸
        # 先卸一起復歸
        # 循環先卸一起復歸
        print("Mode", mode)

        # 先卸_
        mode_first_list = [1, 2]

        # 循環_
        mode_cycle_list = [3, 4]

        if mode in mode_first_list:
            time.sleep(0.1)

            for i in range(0, 4):
                time.sleep(0.1)

                print("Un:", unload_list[i])
                if unload_list[i] == 0:
                    time.sleep(0.1)

                    self.switch_group(group_num=i, status=0)
                    self.unloading_list.append(i)

                    time.sleep(delay)

        elif mode in mode_cycle_list:
            time.sleep(0.1)

            for i in range(0, 4):
                time.sleep(0.1)

                print("INDEX:", index)
                # TODO Unknown，NEED READ
                index = 4 - self.last_number if (self.last_number + i + 1) >= 5 else self.last_number + i

                if unload_list[index] == 0:
                    time.sleep(0.1)

                    self.switch_group(group_num=index, status=0)
                    self.unloading_list.append(index)

                    time.sleep(delay)

    # 還原設備(復歸)
    def revert_device(self, mode, delay):
        # 1:先卸載先復歸
        # 2: 先卸載後復歸
        # 3: 循環先卸載先復歸
        # 4: 循環先卸載後復歸
        # 先卸一起復歸
        # 循環先卸一起復歸

        self.last_number = 0
        length = len(self.unloading_list)
        index = 0

        # 先卸
        mode_first_list = [1, 3]
        # 一起
        mode_together_list = [5, 6]
        # 後賦歸
        mode_later_list = [5, 6]

        if length == 0:
            print("Nothing!!")
            revert = False

        elif mode in mode_first_list:

            for i in range(0, length):
                index = self.unloading_list[0]

                self.switch_group(group_num=index, status=100)
                self.unloading_list.remove(index)
                time.sleep(delay)

            revert = True

        elif mode in mode_together_list:

            for i in range(0, length):
                index = self.unloading_list[0]

                self.switch_group(group_num=index, status=100)
                self.unloading_list.remove(index)

            revert = True

        elif mode in mode_later_list:

            for i in range(0, length):
                index = self.unloading_list[-1]

                self.switch_group(group_num=index, status=100)
                self.unloading_list.remove(index)
                time.sleep(delay)

            revert = True

        self.last_number = index
        self.status = 0

        return revert