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

    def __init__(self, port='/dev/ttyS2', tr_pin=6, baudrate=38400, timeout=0.5):
        super(TestModbusSerial, self).__init__()
        self._serial = pyserial.Serial(
            port=port, baudrate=baudrate, timeout=timeout)
        self._tr = tr_pin
        # self._cond=cond

        if not self._serial.isOpen():
            self._serial.open()
        GPIO.log.setLevel(logging.WARNING)
        GPIO.setwarnings(False)
        # GPIO.setmode(GPIO.BCM)
        GPIO.setup(tr_pin, GPIO.OUT)
        # self._serial.flushOutput()

    # 寫指令進入電表,並取得回應
    def write_command_to_modbus(self, data):
        cli = Redis('localhost')
        flag = cli.get('device_flag')
        flag = flag.decode('utf-8')

        #
        while(flag != '0'):
            flag = cli.get('device_flag')

        cli.set('device_flag', '1')

        ser = self._serial
        data_list = get_crc16(data)
        data_list = array.array('B', data_list)

        print(data_list)

        # write data to rs485
        GPIO.set(self._tr, 1)
        # time.sleep(.03)
        ser.write(data_list)
        ser.flush()
        # ser.flushInput()

        # Get resposne
        GPIO.set(self._tr, 0)
        # time.sleep(.03)
        # 前三碼固定 後兩碼CRC
        words = data_list[5]  # words length
        length = 3 + words * 2 + 2
        # print("Get response")
        response = ser.read(length)  # send command to meter and get response
        # ser.flush()
        # Convert hex string to array
        print("Get response:", response)
        response = array.array('B', response)

        time.sleep(0.01)

        cli.set('device_flag', '0')

        # if length is not match then reload it
        if len(response) != length or data_list[0] != response[0] or data_list[1] != response[1]:
            # 資料錯誤就重新讀ii
            print("ERROR", response)
            ex = ser.read(1)
            time.sleep(0.03)
            response = self.write_command_to_modbus(data[:-2])
            return response
        else:
            return response

    def close(self):
        self._serial.close()
