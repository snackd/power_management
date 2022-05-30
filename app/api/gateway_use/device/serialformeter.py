# encoding=utf-8
#! /usr/bin/python
import serial as pyserial
import sys
import gpio as GPIO
import logging
import time
import array
import threading
from .crc import get_crc16
from . import condition as condition
from redis import Redis
from time import sleep


class TestModbusSerial:

    def __init__(self, port='/dev/ttyS1', tr_pin=6, baudrate=9600, timeout=0.5):
        super(TestModbusSerial, self).__init__()
        self._serial = pyserial.Serial(
            port=port, baudrate=baudrate, timeout=timeout)
        self._tr = tr_pin

        if not self._serial.isOpen():
            self._serial.open()

        GPIO.log.setLevel(logging.WARNING)
        GPIO.setwarnings(False)
        GPIO.setup(tr_pin, GPIO.OUT)

    # 寫指令進入電表,並取得回應
    def write_command_to_modbus(self, data):
        # 確認flag是否為0
        cli = Redis('localhost')
        flag = cli.get('device_flag')
        flag = flag.decode()
        while(flag != '0'):
            flag = cli.get('device_flag')

        cli.set('device_flag', '1')

        # flag_txt = open(
        #     "/var/www/dae-web/app/api_1_0/resident/method/config/device_flag.txt", 'r', encoding='utf-8')
        # flag = flag_txt.read()
        # print('\n#1 flag=',flag,'\n')
        # while(flag != '0'):
        #     flag_txt.close()
        #     flag_txt = open(
        #         "/var/www/dae-web/app/api_1_0/resident/method/config/device_flag.txt", 'r', encoding='utf-8')
        #     flag = flag_txt.read()
        #     if flag == '0':
        #         flag = 1
        #         flag_txt.close()
        #         flag_txt = open("/var/www/dae-web/app/api_1_0/resident/method/config/device_flag.txt", 'w', encoding='utf-8')
        #         flag_txt.write('1')
        #         flag_txt.close()
        #         break

        ser = self._serial
        data_list = get_crc16(data)
        data_list = array.array('B', data_list)

        # write data to rs485 and get response
        GPIO.set(self._tr, 1)
        ser.write(data_list)
        ser.flush()
        GPIO.set(self._tr, 0)
        words = data_list[5]  # words length
        length = 3 + words * 2 + 2
        response = ser.read(length)  # get response
        response = array.array('B', response)
        # print('#2 response', response,'\n')
        time.sleep(0.01)

        cli.set('device_flag', '0')
        # flag_txt = open(
        #     "/var/www/dae-web/app/api_1_0/resident/method/config/device_flag.txt", 'w', encoding='utf-8')
        # flag_txt.write('0')
        # flag_txt.close()

        if data_list[1] == 5:  # switch command
            if len(response) != length or data_list[0] != response[0]:
                ex = ser.read(1)
                time.sleep(0.03)
                response = self.write_command_to_modbus(data[:-2])

        else:  # read meter
            if len(response) != length or data_list[0] != response[0] or data_list[1] != response[1]:
                ex = ser.read(1)
                time.sleep(0.03)
                response = self.write_command_to_modbus(data[:-2])

        return response

    def close(self):
        self._serial.close()
