# import json
import time
from . import mcu_main as mcu
from . import serial_for_modbus as serial_api

# import serial_for_modbus as serial_api
# import mcu_main as mcu

# Set DO On/Off (F5x100)，開關點位用的函式
def switch_node(device_address, node_num, state):
    # 檢查輸入型態是否正確
    if type(device_address) == int and type(node_num) == int and type(state) == int:
        # 如果點位大於此數，號碼出問題，通常為 1-8，此案例是因為我們專案最多就 1-4
        if node_num < 1 or node_num > 4:
            raise Exception("Node_num error")
        # 使用 serial 寫入 modbus 指令
        ser = serial_api.Modbus()
        # LT、DO
        print("Device address(LT):", device_address, " Node num(DO):", node_num)
        # Reg = (LT - 1) * 8 + (DO - 1) + 256
        Reg = (device_address - 1) * 8 + (node_num - 1) + 256
        RH = Reg // 256
        RL = Reg % 256
        # switch ON
        if(state >= 1 and state <= 100):
            cmd = [1, 5, RH, RL, 255, 0]
        # switch OFF
        elif(state == 0):
            cmd = [1, 5, RH, RL, 0, 0]
        data = ser.write_command_to_modbus(cmd)
        if data:
            control_response = "ok"
        else:
            control_response = "fail"
    else:
        # raise Exception("Control node Input Not Int Type")
        control_response = "fail"
        return control_response


# Set Group On/Off (F5x001)，開關群組用的函式
def switch_group(group_num, state):
    # Group 1-63
    if group_num < 1 and group_num > 63:
        raise Exception('group_num error')

    # 使用 serial 寫入 modbus 指令
    ser = serial_api.Modbus()
    print("Group num:", group_num)

    # Reg = Group
    Reg = group_num

    RH = Reg // 256
    RL = Reg % 256

    # switch OFF
    if(state == 0):
        cmd = [1, 5, RH, RL, 0, 0]
    # switch ON
    elif(state >= 1 and state <= 100):
        cmd = [1, 5, RH, RL, 255, 0]

    # if state == 'ON':
    #     # cmd = [1, 5, 0, group_num, 255, 0]
    #     cmd = [1, 5, RH, RL, 255, 0]
    # elif state == 'OFF':
    #     # cmd = [1, 5, 0, group_num, 0, 0]
    #     cmd = [1, 5, RH, RL, 0, 0]
    # else:
    #     raise Exception('state error')

    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    if data:
        response = "OK"
    else:
        response = "Fail"

    return response


# Activate Pattern (F5x040)，開啟場景用的函式
def switch_scene(scene_num):
    # Pattern 64-127
    if scene_num < 1 and scene_num > 63:
        raise Exception('scene_num error')

    # 使用 serial 寫入 modbus 指令
    ser = serial_api.Modbus()
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

    if data:
        response = "OK"
    else:
        response = "Fail"

    return response


# 調光點位(專門給調光點位使用)
def switch_dimmer(device_address, node_num, state):
    # 切成 MBUS
    mcuser = mcu.MCUinitialize()
    mcuser.mcu_process('MBUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

    # device_address = 3
    # node_num = 1
    state = int(state)
    cmd = [device_address, 16, 240, 2, 0, 1, 2, node_num, state]
    ser = serial_api.Modbus()
    data = ser.write_command_to_modbus(cmd)
    time.sleep(0.1)

    if data:
        response = "OK"
    else:
        response = "Fail"

    # 切回 BUS
    mcuser = mcu.MCUinitialize()
    mcuser.mcu_process('BUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

    return response


# 額外函式
# 10 進位 轉 2 進位
def dec_to_bin(num):
    bin_list = []
    # num = 128
    while num / 2 > 0:
        # 除 2 的餘數加入陣列
        bin_list.append(num % 2)
        # 原數字等於自身商數
        num = num // 2

    # num 轉 bin_list 不足 8 位方法一 (補 0)
    bin_length = len(bin_list)
    bin_must_length = 8
    for i in range(bin_length, bin_must_length):
        bin_list.append(0)

    # 反轉陣列
    bin_list.reverse()

    print("Node Bin List:", bin_list)

    return bin_list


# 顯示點位開或關
def display_node(node_list):
    node_list_len = len(node_list)

    # 再反轉陣列 / 求顯示時按順序
    node_list.reverse()
    for i in range(node_list_len):
        # print("Node ", (i+1) ," : ", node_list[i])

        if node_list[i] == 1:
            node_state = "ON"
        elif node_list[i] == 0:
            node_state = "OFF"
        else:
            node_state = "Error"

        print("Node ", (i+1) ," : ", node_state)


# F3
# Read DO state (F3x000) / Read node (Bytes)
def read_node(device_address):

    # 使用 serial 寫入 modbus 指令
    ser = serial_api.Modbus()

    # Reg - (LT - 1) // 2
    Reg = (device_address - 1) // 2

    RH = Reg // 256
    RL = Reg % 256

    cmd = [1, 3, RH, RL, 0, 4]
    data = ser.write_command_to_modbus(cmd)

    # cmd_result = [1, 3, 2, 15, 0, 189, 180]
    # node_num 1-4 ON = 1 + 2 + 4 + 8 = 15

    # 取 List 的第 4 格
    node_result = data[3]
    print("Node Bin Total Num:", node_result)

    node_list = dec_to_bin(node_result)

    display_node(node_list)


# Read Group state (F3x0A4) / Read Group (Bytes)
def read_group(device_address):

    # 使用 serial 寫入 modbus 指令
    ser = serial_api.Modbus()

    # Patterns 1-16 : 164
    # Patterns 17-32 : 165
    # Patterns 33-48 : 166
    # Patterns 49-63 : 167
    Reg = 164

    RH = Reg // 256
    RL = Reg % 256

    cmd = [1, 3, RH, RL, 0, 4]
    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    if data:
        response = "OK"
    else:
        response = "Fail"

    return response

# Read DO state (F3x000) / Read Pattern Activation state (Bytes)
def read_scene(device_address):

    # 使用 serial 寫入 modbus 指令
    ser = serial_api.Modbus()

    # Reg - (LT - 1) // 2
    Reg = (device_address - 1) // 2

    RH = Reg // 256
    RL = Reg % 256

    cmd = [1, 3, RH, RL, 0, 1]
    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    if data:
        response = "OK"
    else:
        response = "Fail"

    return response

# F1
# Read DO state (F1x100) / Read Node (Bytes)
def read_node_F1(device_address, node_num):
    # LT 1-64
    # DO 1-2000
    if device_address < 1 or device_address > 63:
        raise Exception('device_address error')
    if node_num < 1 or node_num > 2000:
        raise Exception('node_num error')

    # 使用 serial 寫入 modbus 指令
    ser = serial_api.Modbus()

    print("Device address(LT):", device_address)
    print("Node num(DO):", node_num)

    # Reg = (LT - 1)*8 + (DO - 1) + 256
    Reg = (device_address - 1)*8 + (node_num - 1) + 256

    RH = Reg // 256
    RL = Reg % 256

    # N of DO 1-2000
    cmd = [1, 1, RH, RL, 0, node_num]
    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    if data:
        response = "OK"
    else:
        response = "Fail"

    return response

# Read Group state(F1x001) / Read Group (Bytes)
def read_group_F1(group_num):
    # Group 1-63
    if group_num < 1 or group_num > 63:
        raise Exception('group_num error')

    # 使用 serial 寫入 modbus 指令
    ser = serial_api.Modbus()
    print("Group num:", group_num)

    # Reg = (Group - 1) + 1
    Reg = (group_num - 1) + 1

    RH = Reg // 256
    RL = Reg % 256

    # N of Group 1-63
    cmd = [1, 1, RH, RL, 0, group_num]
    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    if data:
        response = "OK"
    else:
        response = "Fail"

    return response

# Read Pattern state (F1x040) / Read Scene (Bytes)
def read_scene_F1(scene_num):
    # Pattern 64-127
    if scene_num < 1 or scene_num > 63:
        raise Exception('scene_num error')

    # 使用 serial 寫入 modbus 指令
    ser = serial_api.Modbus()
    print("Scene Num:", scene_num)

    # Reg = (Pattern - 1) + 64
    Reg = (scene_num - 1) + 64

    RH = Reg // 256
    RL = Reg % 256

    # N of Pattern 1-64
    cmd = [1, 1, RH, RL, 0, scene_num]
    data = ser.write_command_to_modbus(cmd)
    time.sleep(3)

    if data:
        response = "OK"
    else:
        response = "Fail"

    return response

if __name__ == '__main__':
    print("Test switch_api")

    # 開關點位
    # data = switch_node(device_address=2, node_num=1, state=0)

    # 開關群組
    # data = switch_group(group_num=3, state=0)

    # 開場景
    # data = switch_scene(scene_num=2)

    # 調光點位設置
    data = switch_dimmer(device_address=3, node_num=1, state=0)

    print(data)