# encoding=utf-8
#! /usr/bin/python

import threading
# import time
# import sys

from . import serial_for_modbus as serial_api
# import serial_for_modbus as serial_api

# from . import mysql as daesql
# from .config import database_setting as dbconfig
from .config import setting as setting

from apscheduler.schedulers.blocking import BlockingScheduler

# import datetime
# datetime.datetime.strptime("08:00:00", "%H:%M:%S")
# datetime.datetime.strptime("08:00:00", "%H:%M:%S").strftime("%H:%M")

# 日出、日落
time_region = ['sunset', 'sunrise']

class Schedule(threading.Thread):

    def __init__(self):
        super(Schedule, self).__init__()

        print("Schedule")

        self.serial = serial_api.Modbus()
        # self.dbh = daesql.MySQL(dbconfig.mysql_config)
        self.dbh = setting.sql_connect


    def run(self):
        print("---Schedule run---")

        # while True:
        #     pass
        self.read_sql()

        print("---DB Close---")

        self.dbh.close()

        print("---Serial Close---")
        self.serial.close()

    # 讀取資料庫排程資料
    def read_sql(self):

        # 讀取某個 gateway 的排程時間、資訊
        table_name = "schedule_list"

        column_1 = "schedule_group_id"
        column_2 = "group_state"
        where_condition = "gateway_id"
        gateway_id = 1

        sql = (
            "SELECT `{}`,`{}` "
            "FROM `{}` "
            "WHERE `{}` = '{}' "
        ).format(column_1, column_2, table_name, where_condition, gateway_id)

        print("sql:", sql)

        schedule_information = self.dbh.query(sql)

        print(schedule_information)

        for row in schedule_information:
            schedule_group_id = row["schedule_group_id"]
            group_state = row["group_state"]
            print(row)
            # print(schedule_group_id)
            # print(group_state)

            table_name = "group_list"
            column = "num"
            where_condition = "gateway_id"
            where_condition_2 = "group_id"

            sql = (
                "SELECT `{}` "
                "FROM `{}` "
                "WHERE `{}` = '{}' "
                "AND `{}` = '{}' "
            ).format(column, table_name, where_condition, gateway_id, where_condition_2, schedule_group_id)

            print("sql:", sql)

            result = self.dbh.query(sql)
            print(result)

            # 僅一列 data
            for row in result:
                group_num = row["num"]
                # print(group_num)
                # print(group_state)
                self.set_schedule(group_num=group_num, group_state=group_state)

    def tick(self):
        print("TICK !!")

    # 依排程資訊，設定某排程
    def set_schedule(self, group_num, group_state):
        print(group_num)
        print(group_state)
        # scheduler = BlockingScheduler()
        scheduler = BlockingScheduler()
        scheduler.add_job(self.tick, 'interval', seconds=5.000000)
        scheduler.start()

        print("Set END")


# if __name__ == '__main__':
#     print("Test schedule_api")

#     s1 = Schedule()
#     print("!!!")
#     s1.run()
#     print("END")


