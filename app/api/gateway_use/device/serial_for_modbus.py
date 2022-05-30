# encoding=utf-8
#! /usr/bin/python
import serial
# import sys
import gpio as GPIO
import logging

import threading

import time
# from time import sleep

# import redis
# import mcu_main as mcu
from . import mcu_main

from datetime import datetime

# from .config import setting as setting
# from .config.setting import *
from .config.setting import R

class Modbus(threading.Thread):

    def __init__(
            self,
            port='/dev/ttyS2',
            tr_pin=6,
            baudrate=38400,
            timeout=0.5,
            write_timeout=0.5):

        super(Modbus, self).__init__()

        # 被調用的程式，不為單一啟用，故用 setting.R 節省記憶體運作、加快程式運作時間，並非用 redis.Redis('localhost')
        self.r = R
        # self.r = setting.R
        # self.r = redis.Redis('localhost')
        # self.set_serial(port=port, baudrate=baudrate,
        #                 timeout=timeout, write_timeout=write_timeout)
        self.port = port
        self.set_serial(port=port, baudrate=baudrate)

    @staticmethod
    def get_modbus_crc(int_array):
        value = 0xFFFF
        for i in range(len(int_array)):
            value ^= int_array[i]
            for j in range(8):
                if (value & 0x01) == 1:
                    value = (value >> 1) ^ 0xA001
                else:
                    value >>= 1
        return [value & 0xff, (value >> 8) & 0xff]

    # 寫指令進入電表,並取得回應
    def write_command_to_modbus(self,
                                command_list):

        serial_isOpen = self.r.get('serial.isOpen').decode('utf-8')
        # print(serial_isOpen)
        # print(type(serial_isOpen))
        # print("serial.isOpen:", int(self.serial.isOpen()))

        # Serial Open, 1 = 有占用，0 = 未占用
        count = 0

        if not self.serial.isOpen():
            self.serial.open()
            self.r.set('serial.isOpen', int(self.serial.isOpen()))
            print("serial.isOpen:", int(self.serial.isOpen()))

        while(serial_isOpen != '0'):
            count += 1
            serial_isOpen = self.r.get('serial.isOpen').decode('utf-8')
            print("serial.isOpen:", serial_isOpen)
            time.sleep(0.05)
            if count >= 10:
                print("serial.isOpen. Can't write modbus")
                break


        # print("Command list:", command_list)

        full_command_list = command_list + Modbus.get_modbus_crc(command_list)
        # print('Modbus write:', full_command_list)

        read_length = full_command_list[5] * 2 + \
            5 if full_command_list[1] == 3 else len(full_command_list)

        # print("read_length:", read_length)

        data_list = self.write_read(full_command_list, read_length)

        if not data_list:
            count = 0
            while not data_list:
                count += 1
                data_list = self.write_read(full_command_list, read_length)
                time.sleep(0.05)
                if data_list:
                    break
                elif count > 10:
                    print("Modbus not response, To many count.(10)")
                    break
            print("No Data! Close")
            self.serial_close()
            self.r.set('serial.isOpen', int(self.serial.isOpen()))

            return data_list
        elif data_list:
            # print("Have Data! Close")
            self.serial_close()
            self.r.set('serial.isOpen', int(self.serial.isOpen()))

            return data_list

    def write_read(self, full_command_list, read_length):

        # 設定 GPIO 接腳 (6,1) = 6 號接腳，output
        GPIO.set(6, 1)
        time.sleep(0.05)
        self.serial.write(full_command_list)
        self.serial.flush()

        self.serial.reset_output_buffer()
        time.sleep(0.05)
        # print("Write Data:", full_command_list)

        # print("Read Length:", read_length)
        if self.port == "/dev/ttyS1":
            read_length = read_length + 8

        # 設定 GPIO 接腳 (6,0) = 6 號接腳，intput
        GPIO.set(6, 0)
        time.sleep(0.05)

        # Not use
        # self.serial.reset_input_buffer()
        read_data = self.serial.read(read_length)
        # print("Read Data:", read_data)

        # 將讀取出的資料儲存成 list
        data_list = list(read_data)
        print("Data List:", data_list)
        time.sleep(0.01)

        return data_list

    def set_serial(self, port, baudrate):

        self.port = port

        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate
        )

        # print("Set Serial 2")
        # print("port:", port)
        # print("baudrate:", baudrate)
        # print("-----")

    def serial_close(self):
        # 取消讀取、寫入、關閉序列埠
        self.serial.cancel_read()
        self.serial.cancel_write()
        self.serial.close()

    def GPIO_set(self, tr_pin):
        GPIO.log.setLevel(logging.WARNING)
        GPIO.setwarnings(False)
        GPIO.setup(tr_pin, GPIO.OUT)


if __name__ == '__main__':
    print("Serial for Modbus")