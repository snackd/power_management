#!/usr/bin/env python3
# coding: UTF-8
import serial
import time
# from time import sleep

import redis
# from .config import setting as setting

class MCUinitialize:
    def __init__(self):
        # Set MCU On (with crc)
        self.data_MCU_set_on = [1, 66, 240, 47, 0, 3, 6, 0, 26, 0, 36, 25, 14, 126, 67]

        # Set MCU Off (with crc)
        self.data_MCU_set_off = [1, 66, 240, 47, 0, 3, 6, 0, 26, 0, 136, 125, 114, 149, 67]

        # Set MCU read model
        self.data_MCU_read_mode = [1, 66, 240, 47, 0, 3, 6, 0, 26, 4, 0, 0, 0, 181, 44]

        # 常單用這隻程式重啟 mcu，故不用 setting.R
        self.r = redis.Redis('localhost')
        # self.r = setting.R

        self.serial = None

    # Set MCU main process
    def mcu_process(self, port_type):
        # 檢查MCU版本
        if port_type == "MBUS":
            # mcu設定檔的路徑物件
            command = [1, 66, 240, 47, 0, 3, 6, 0, 26, 2, 1, 3, 0]
        else:
            command = [1, 66, 240, 47, 0, 3, 6, 0, 26, 2, 2, 3, 0]

        command_with_crc = command + self.get_modbus_crc(command)
        return self.set_mcu(command_with_crc)

    def set_mcu(self, cmd):

        self.open_serial()

        # write MCU On
        print('MCU Set On:1')
        self.send_data(self.data_MCU_set_on)
        rtn_set_on = self.read_data().hex()
        rtn_set_on_str = [str(int(rtn_set_on[i:i + 2], 16))
                          for i in range(0, len(rtn_set_on), 2)]

        if rtn_set_on_str and rtn_set_on_str[0] == '2':
            # write MCU
            print('Write MCU Model:2')
            self.send_data(cmd)
            rtn_set_mcu = self.read_data().hex()
            rtn_set_mcu_str = [str(int(rtn_set_mcu[i:i + 2], 16))
                               for i in range(0, len(rtn_set_mcu), 2)]

            # Write MCU Off
            print('MCU Set Off:3')
            self.send_data(self.data_MCU_set_off)
            self.read_data()
            self.close_serial()

            if rtn_set_mcu_str and rtn_set_mcu_str[0] == '2':
                return True
            else:
                print('Set MCU Model Error:3')
                print('Error: Set MCU mode error! Send data:{},Return data:{}'.format(
                    cmd, rtn_set_mcu_str))
                return False
        else:
            print('Set MCU ON Error:4')
            print('Error: Set MCU ON error! Return data:{}'.format(rtn_set_on_str))
            return False

    def open_serial(self):
        self.serial = serial.Serial(
            "/dev/ttyS2", 38400, timeout=0.5, write_timeout=0.5)

        if not self.serial.isOpen():
            self.serial.open()

    def close_serial(self):
        self.serial.close()

    def send_data(self, arr):

        serial_isOpen = self.r.get('serial.isOpen').decode('utf-8')
        print('Now serial.isOpen:', serial_isOpen)

        count = 0
        while(serial_isOpen != '0'):
            count += 1
            serial_isOpen = self.r.get('serial.isOpen').decode('utf-8')
            # print(serial_isOpen)
            time.sleep(0.1)
            if count >= 20:
                print("serial.isOpen. Can't write modbus")
                break

        self.r.set('serial.isOpen', 1)

        self.serial.write(arr)
        self.serial.flush()

    def read_data(self):
        r_data = self.serial.read(80)
        self.r.set('serial.isOpen', 0)

        return r_data

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


if __name__ == '__main__':
    ini_mcu = MCUinitialize()
    ini_mcu.mcu_process('BUS')
    ini_mcu.open_serial()
    ini_mcu.send_data(ini_mcu.data_MCU_read_mode)
    a = ini_mcu.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])
