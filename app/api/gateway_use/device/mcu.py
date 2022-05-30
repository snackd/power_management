#!/usr/bin/env python3
# coding: UTF-8
import serial
from redis import Redis
from time import sleep


class MCUinitialize:
    def __init__(self):
        self.data_MCU_set_on = [1, 66, 240, 47, 0, 3, 6, 0,
                                26, 0, 36, 25, 14, 126, 67]  # 寫入MCU設定on(with crc)
        self.data_MCU_set_off = [1, 66, 240, 47, 0, 3, 6, 0,
                                 26, 0, 136, 125, 114, 149, 67]  # 寫入MCU設定off(with crc)
        self.data_MCU_read_mode = [1, 66, 240, 47, 0,
                                   3, 6, 0, 26, 4, 0, 0, 0, 181, 44]  # 讀取MCU模式
        self.serial = None

    # 設定MCU之主流程
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
        # 寫入MCU設定on
        self.send_data(self.data_MCU_set_on)
        rtn_set_on = self.read_data().hex()
        rtn_set_on_str = [str(int(rtn_set_on[i:i + 2], 16))
                          for i in range(0, len(rtn_set_on), 2)]
        print('MCU Set On:1')

        if rtn_set_on_str and rtn_set_on_str[0] == '2':
            # 寫入MCU模式
            print('Write MCU Model:2')
            self.send_data(cmd)
            rtn_set_mcu = self.read_data().hex()
            rtn_set_mcu_str = [str(int(rtn_set_mcu[i:i + 2], 16))
                               for i in range(0, len(rtn_set_mcu), 2)]
            # 寫入MCU設定off
            print('MCU Set Off:3')
            self.send_data(self.data_MCU_set_off)
            self.read_data()
            self.close_serial()

            if rtn_set_mcu_str and rtn_set_mcu_str[0] == '2':
                return True
            else:
                print('Set MCU mode error:3')
                print('Error: Set MCU mode error! Send data:{},Return data:{}'.format(
                    cmd, rtn_set_mcu_str))
                return False
        else:
            print('Set MCU ON error:4')
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

        cli = Redis('localhost')
        flag = cli.get('device_flag')
        flag = flag.decode()
        print('redis MCU_Useing Flag', flag)
        while(flag != '0'):
            flag = cli.get('device_flag')

        cli.set('device_flag', '1')
        # filex = open(
        #     "/var/www/dae-web/app/api_1_0/resident/method/config/device_flag.txt", 'r', encoding='utf-8')
        # a = filex.read()
        # while(a == ''):
        #     a = filex.read()
        # a = int(a)
        # filex.close()
        # while(a != 0):
        #     filex = open(
        #         "/var/www/dae-web/app/api_1_0/resident/method/config/device_flag.txt", 'r', encoding='utf-8')
        #     a = filex.read()
        #     while(a == ''):
        #         a = filex.read()
        #     a = int(a)
        #     filex.close()
        # filex = open(
        #     "/var/www/dae-web/app/api_1_0/resident/method/config/device_flag.txt", 'w', encoding='utf-8')
        # filex.write('1')
        # filex.close()

        self.serial.write(arr)
        self.serial.flush()

    def read_data(self):
        r_data = self.serial.read(80)
        # filex = open(
        #     "/var/www/dae-web/app/api_1_0/resident/method/config/device_flag.txt", 'w', encoding='utf-8')
        # filex.write('0')
        # filex.close()
        cli = Redis('localhost')
        cli.set('device_flag', '0')

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
