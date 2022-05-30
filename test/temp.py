# encoding=utf-8
#! /usr/bin/python
import serial as pyserial
import sys
import gpio as GPIO
import logging
import time
import array
from crc import get_crc16

from redis import Redis

class TestModbusSerial:

    def __init__(self, port='/dev/ttyS2', tr_pin=6, baudrate=38400, timeout=0.5):
        super(TestModbusSerial, self).__init__()
        self._serial = pyserial.Serial(
            port=port, baudrate=baudrate, timeout=timeout)
        self._tr = tr_pin

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
        # if len(response) != length or data_list[0] != response[0] or data_list[1] != response[1]:
        #     # 資料錯誤就重新讀ii
        #     print("ERROR", response)
        #     ex = ser.read(1)
        #     time.sleep(0.03)
        #     response = self.write_command_to_modbus(data[:-2])
        #     return response
        # else:
        #     return response
        return response

    def close(self):
        self._serial.close()

def switch_node(device_address, node_num, status):
    if node_num < 1 or node_num > 4:
        raise Exception('node_num error')

    ser = TestModbusSerial()
    cmd_num = node_num - 1 + (device_address-1)*8
    print("Num:", cmd_num)

    if status == 'ON':
        cmd = [1, 5, 1, cmd_num, 0, 0]
    elif status == 'OFF':
        cmd = [1, 5, 1, cmd_num, 255, 0]
    else:
        raise Exception('status error')

    ser.write_command_to_modbus(cmd)
    time.sleep(3)

def switch_group(group_num, status):
    ser = TestModbusSerial()
    if group_num < 1 and group_num > 63:
        raise Exception('group_num error')

    print("Num:", group_num)

    if status == 'ON':
        cmd = [1, 5, 0, group_num, 255, 0]
    elif status == 'OFF':
        cmd = [1, 5, 0, group_num, 0, 0]
    else:
        raise Exception('status error')

    ser.write_command_to_modbus(cmd)
    time.sleep(3)

def switch_scene(scene_num, status):
    ser = TestModbusSerial()
    if scene_num < 64 and scene_num > 127:
        raise Exception('scene_num error')

    cmd_num = scene_num + 63
    print("Num:", cmd_num)

    if status == 'ON':
        cmd = [1, 5, 0, cmd_num, 255, 0]
    elif status == 'OFF':
        cmd = [1, 5, 0, cmd_num, 0, 0]
    else:
        raise Exception('status error')

    ser.write_command_to_modbus(cmd)
    time.sleep(3)

if __name__ == '__main__':
    print("Test Start")
    # ser = TestModbusSerial()
    # [CC1000 address, Function code, RH, RL, Num of high, Num of low]
    # cmd = [addr, 1, 0, 0, 0, 8]
    # data_list = ser.write_command_to_modbus(cmd)
    # print("read:", data_list)
    # command_pm210 = [1, 3, 0, 20, 0, 36]
    # device_address = 2
    # for node_num in range(1, 5):
    # switch_node(device_address, node_num, 'ON')
    # for group_num in range(1, 4):
    #     switch_group(group_num, 'ON')
    ser = TestModbusSerial()
    # LT address 2
    node_num = 1
    device_address = 2
    cmd_num = node_num - 1 + (device_address - 1) * 8
    print("CMD Num:", cmd_num)
    cmd = [1, 5, 1, cmd_num, 255, 0]

    # read_num = (2 - 1) % 2
    # cmd = [1, 3, 1, read_num, 0, 1]
    ser.write_command_to_modbus(cmd)
    # time.sleep(10)

    # for scene_num in range(1, 4):
    #     switch_scene(scene_num, 'ON')
# temp = b'\x01\x03\x02\x00\x00\xb8D'
# int.from_bytes(temp, byteorder='big')
