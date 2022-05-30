# encoding=utf-8
#! /usr/bin/python
import serial
import sys
import gpio as GPIO
import logging

import threading

import time
import array
# from crc import get_crc16

from redis import Redis


class Modbus(threading.Thread):

    def __init__(
            self,
            port='/dev/ttyS2',
            tr_pin=6,
            baudrate=38400,
            timeout=0.5,
            write_timeout=0.5):

        super(Modbus, self).__init__()

        self._ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            write_timeout=write_timeout
        )
        self._tr = tr_pin

        if not self._ser.isOpen():
            self._ser.open()

        GPIO.log.setLevel(logging.WARNING)
        GPIO.setwarnings(False)
        GPIO.setup(tr_pin, GPIO.OUT)

    # 提取 modbus CRC 驗證碼
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
                                command_list,
                                port='/dev/ttyS2',
                                baudrate=38400,
                                timeout=0.5,
                                write_timeout=0.5):

        cli = Redis('localhost')
        flag = cli.get('device_flag')
        flag = flag.decode('utf-8')

        if not self._ser.isOpen():
            self._ser.open()

        while(flag != '0'):
            flag = cli.get('device_flag')

        cli.set('device_flag', '1')

        print("Command list:", command_list)

        full_command_list = command_list + Modbus.get_modbus_crc(command_list)

        print('Modbus write: {}'.format(full_command_list))

        read_length = full_command_list[5] * 2 + 5 if full_command_list[1] == 3 else len(full_command_list)

        # 設定 GPIO 接腳 (6,1) = 6 號接腳，output
        GPIO.set(6, 1)
        self._ser.write(full_command_list)
        self._ser.flush()
        self._ser.reset_output_buffer()

        # 設定 GPIO 接腳 (6,0) = 6 號接腳，intput
        GPIO.set(6, 0)
        time.sleep(0.005)
        self._ser.reset_input_buffer()
        read_data = self._ser.read(read_length)

        # 將讀取出的資料儲存成 list
        data_list = list(read_data)

        time.sleep(0.01)

        # 取消讀取、寫入、關閉序列埠
        self._ser.cancel_read()
        self._ser.cancel_write()
        self._ser.close()

        cli.set('device_flag', '0')

        if not data_list:
            data_list = self.write_command_to_modbus(command_list)
            return data_list
        elif data_list:
            return data_list


    def close(self):
        self._serial.close()


def switch_node(device_address, node_num, status):
    if node_num < 1 or node_num > 4:
        raise Exception('node_num error')

    ser = Modbus()
    Reg = node_num - 1 + (device_address - 1) * 8 + 256

    RH = Reg // 256
    RL = Reg % 256

    if status == 'ON':
        cmd = [1, 5, RH, RL, 0, 0]
    elif status == 'OFF':
        cmd = [1, 5, RH, RL, 255, 0]
    else:
        raise Exception('status error')

    ser.write_command_to_modbus(cmd)
    time.sleep(3)


def switch_group(group_num, status):
    ser = Modbus()
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
    ser = Modbus()
    if scene_num < 64 and scene_num > 127:
        raise Exception('scene_num error')

    cmd_num = (scene_num - 1) + 64
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
    print("Start")
    # PM210
    # command_pm210 = [1, 3, 0, 20, 0, 36]

    # node_num = 2
    # device_address = 2
    # Reg = node_num - 1 + (device_address - 1) * 8 + 256
    # RH = Reg // 256
    # RL = Reg % 256
    # cmd = [1, 5, 1, 9, 0, 0]

    cmd = [1, 5, 0, 65, 255, 0]

    # Read node DO status
    # device_address = 2
    # Reg = (device_address-1) // 2
    # RH = Reg // 256
    # RL = Reg % 256
    # print("RH,RL:(",RH ,",",RL,")")
    # cmd = [1, 3, RH, RL, 0, 2]

    # Read Group Status
    # Reg = 160
    # RH = Reg // 256
    # RL = Reg % 256
    # print("RH,RL:(",RH ,",",RL,")")
    # cmd = [1, 1, RH, RL, 0, 32]

    # Read Pattern Status
    # Reg = 164
    # RH = Reg // 256
    # RL = Reg % 256
    # print("RH,RL:(",RH ,",",RL,")")
    # cmd = [1, 3, RH, RL, 0, 4]
    m1 = Modbus()
    data_list = m1.write_command_to_modbus(cmd)
    print('Modbus read: {}'.format(data_list))

    time.sleep(0.01)

