# encoding=utf-8
#! /usr/bin/python
import serial
import sys
import gpio as GPIO
import logging

import threading

import time

# import array
# from crc import get_crc16
# from time import sleep

import redis
import mcu_main as mcu

class Modbus(threading.Thread):

    def __init__(
            self,
            # port='/dev/ttyS3',
            port='/dev/ttyS2',
            # port='/dev/ttyS1',
            tr_pin=6,
            baudrate=38400,
            # baudrate=19200,
            # baudrate=9600,
            timeout=0.5,
            write_timeout=0.5):

        super(Modbus, self).__init__()
        self.redis = redis.Redis('localhost')
        self.set_serial(port=port, baudrate=baudrate,
                        timeout=timeout, write_timeout=write_timeout)
        self.GPIO_set(tr_pin=tr_pin)

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

        serial_isOpen = self.redis.get('serial.isOpen').decode('utf-8')
        # print(serial_isOpen)
        # print(type(serial_isOpen))

        count = 0
        while(serial_isOpen != '0'):
            count += 1
            serial_isOpen = self.redis.get('serial.isOpen').decode('utf-8')
            print(serial_isOpen)
            time.sleep(0.1)
            if count >= 20:
                print("serial.isOpen. Can't write modbus")
                break

        if not self.serial.isOpen():
            self.serial.open()
        self.redis.set('serial.isOpen', int(self.serial.isOpen()))

        print("Command list:", command_list)

        full_command_list = command_list + self.get_modbus_crc(command_list)

        print("Get CRC:", full_command_list)
        # print('Modbus write:', full_command_list)

        read_length = full_command_list[5] * 2 + \
            5 if full_command_list[1] == 3 else len(full_command_list)
        # print('read_length:', read_length)

        data_list = self.write_read(full_command_list, read_length)

        if not data_list:
            count = 0
            while not data_list:
                count += 1
                data_list = self.write_read(full_command_list, read_length)
                time.sleep(0.1)
                if data_list:
                    break
                elif count > 10:
                    print("Modbus not response, To many count.(10)")
                    break

            self.serial_close()
            self.redis.set('serial.isOpen', int(self.serial.isOpen()))

            return data_list
        elif data_list:

            self.serial_close()
            self.redis.set('serial.isOpen', int(self.serial.isOpen()))

            return data_list

    def write_read(self, full_command_list, read_length):

        # 設定 GPIO 接腳 (6,1) = 6 號接腳，output
        GPIO.set(6, 1)
        time.sleep(0.05)
        self.serial.write(full_command_list)
        self.serial.flush()
        self.serial.reset_output_buffer()
        print("Write Data:", full_command_list)

        # 設定 GPIO 接腳 (6,0) = 6 號接腳，intput
        GPIO.set(6, 0)
        time.sleep(0.05)
        # self.serial.reset_input_buffer()
        read_data = self.serial.read(read_length)
        print("Read Data:", read_data)

        # 將讀取出的資料儲存成 list
        data_list = list(read_data)
        print("Data List:", data_list)
        time.sleep(0.01)

        return data_list

    def set_serial(self, port, baudrate, timeout, write_timeout):
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            write_timeout=write_timeout
        )

    def serial_close(self):
        # 取消讀取、寫入、關閉序列埠
        self.serial.cancel_read()
        self.serial.cancel_write()
        self.serial.close()

    def GPIO_set(self, tr_pin):
        GPIO.log.setLevel(logging.WARNING)
        GPIO.setwarnings(False)
        GPIO.setup(tr_pin, GPIO.OUT)


# Set DO On/Off (F5x100)
def switch_node(device_address, node_num, status):
    # 如果點位大於此數，號碼出問題，通常為 1-8，此案例是因為我們專案最多就 1-4
    if node_num < 1 or node_num > 4:
        raise Exception('node_num error')

    # 使用 serial 寫入 modbus 指令
    ser = Modbus()

    print("Device address(LT):", device_address)
    print("Node num(DO):", node_num)

    # Reg = (LT - 1) * 8 + (DO - 1) + 256
    Reg = (device_address - 1) * 8 + (node_num - 1) + 256

    RH = Reg // 256
    RL = Reg % 256


    # switch ON
    if(status == 0):
        cmd = [1, 5, RH, RL, 255, 0]
    # switch OFF
    elif(status >= 1 and status <= 100):
        cmd = [1, 5, RH, RL, 0, 0]
    else:
        # raise Exception('status error')
        dimmer_light(ser, device_address, node_num, status)

    # if status == 'ON':
    #     cmd = [1, 5, RH, RL, 0, 0]
    # elif status == 'OFF':
    #     cmd = [1, 5, RH, RL, 255, 0]
    # else:
    #     raise Exception('status error')
        # status = int(status)
        # cmd = [device_address, 16, 240, 2, 0, 1, 2, node_num, status]

    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    return data

# Set Group On/Off (F5x001)
def switch_group(group_num, status):
    # Group 1-63
    if group_num < 1 and group_num > 63:
        raise Exception('group_num error')

    # 使用 serial 寫入 modbus 指令
    ser = Modbus()
    print("Group num:", group_num)

    # Reg = Group
    Reg = group_num

    RH = Reg // 256
    RL = Reg % 256

    # switch OFF
    if(status == 0):
        cmd = [1, 5, RH, RL, 0, 0]
    # switch ON
    elif(status >= 1 and status <= 100):
        cmd = [1, 5, RH, RL, 255, 0]

    # if status == 'ON':
    #     # cmd = [1, 5, 0, group_num, 255, 0]
    #     cmd = [1, 5, RH, RL, 255, 0]
    # elif status == 'OFF':
    #     # cmd = [1, 5, 0, group_num, 0, 0]
    #     cmd = [1, 5, RH, RL, 0, 0]
    # else:
    #     raise Exception('status error')

    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    return data


# Activate Pattern (F5x040)
def switch_scene(scene_num):
    # Pattern 64-127
    if scene_num < 1 and scene_num > 63:
        raise Exception('scene_num error')

    # 使用 serial 寫入 modbus 指令
    ser = Modbus()
    print("Scene Num:", scene_num)

    # Reg = (Pattern - 1) +64
    Reg = (scene_num - 1) + 64
    # cmd_num = (scene_num - 1) + 64

    RH = Reg // 256
    RL = Reg % 256

    # scene only On
    # cmd = [1, 5, 0, cmd_num, 255, 0]
    cmd = [1, 5, RH, RL, 255, 0]

    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    return data

def switch_dimmer(device_address, node_num, status):
    mcuser = mcu.MCUinitialize()
    mcuser.mcu_process('MBUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

    # device_address = 3
    # node_num = 1
    status = int(status)
    cmd = [device_address, 16, 240, 2, 0, 1, 2, node_num, status]
    ser = Modbus()
    ser.write_command_to_modbus(cmd)
    time.sleep(0.1)

    mcuser = mcu.MCUinitialize()
    mcuser.mcu_process('BUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

def read_pm210():
    ser = Modbus()

    cmd = [1, 3, 0, 20, 0, 36]
    # cmd = [1, 3, 0, 20, 0, 12]
    # cmd = [1, 5, 0, 1, 255, 0]

    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    return data

def test(num, status):
    ser = Modbus()

    if status == 0:
        cmd = [1, 5, 1, num, 255, 0]

    elif(status >= 1 and status <= 100):
        cmd = [1, 5, 1, num, 0, 0]

    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    return data


if __name__ == '__main__':
    print("Serial for Modbus")

    # data = test(num=0, status=0)
    # data = test(num=1, status=0)
    # data = test(num=2, status=0)
    # data = test(num=3, status=0)

    # data = read_pm210()
    # data = switch_dimmer(device_address=3, node_num=1, status=0)
    data = switch_node(device_address=1, node_num=1, status=100)
    data = switch_node(device_address=2, node_num=1, status=100)
    # data = switch_node(device_address=2, node_num=2, status=100)
    # data = switch_node(device_address=2, node_num=3, status=100)
    # data = switch_node(device_address=2, node_num=4, status=100)
    # data = switch_scene(scene_num=10)
    # print("Data:", data)
    # data = switch_group(group_num=1, status=0)

    time.sleep(0.01)
