import json
import time
# from . import serialforschedule as serial2
# from . import serialforset as serialset
from . import serial_for_modbus as serial_api

from . import mysql as daesql
from . import condition as conditioni
from .config import database_setting as dbconfig
from . import mcu
from config import G_CONTROL_VALUE_TYPE_LIST


def set_group(gateway_id, group_id, group_number):
    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('MBUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

    # ser = serialset.TestModbusSerial()
    ser = serial_api.Modbus()

    """
    read data from mysql
    """
    dbh=daesql.MySQL(dbconfig.mysql_config)
    node_list_sql = "SELECT `nl`.`node_id`, `nl`.`device_address`, `nl`.`num` AS `node_number` " \
                    "FROM `node_list` AS `nl` " \
                    "INNER JOIN `group_node_list` AS `gnl` ON(`nl`.`node_id` = `gnl`.`node_id` AND `nl`.`gateway_id` = `gnl`.`gateway_id`) " \
                    " WHERE `gnl`.`gateway_id` = {} AND `gnl`.`group_id` = {}".format(gateway_id, group_id)
    result = dbh.query(node_list_sql)
    print("result=", result)
    rule = {}
    state = {}
    for row in result:
        device_address = row['device_address']
        node_number = row['node_number']
        node_number = 1<<(node_number - 1)
        if(rule.__contains__(device_address)):
            a = rule[device_address]
            a = a + node_number
            rule[device_address] = a
        else:
            rule[device_address] = node_number
    key=rule.keys()

    for a in key:
        b=rule.get(a)
        if (int(a)!=3):

            cmd=[int(a),16,40,group_number*2,0,2,4,group_number,b,1,0]
        elif(int(a)==3):
            cmd=[3,16,80,group_number*4,0,4,8,group_number,b,1,0,80,80,80,80]
        print("set cmd=",cmd)
        ser.write_command_to_modbus(cmd)
        time.sleep(0.1)


    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('BUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])
    time.sleep(0.03)

def set_scene(gateway_id, scene_id, scene_number):
    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('MBUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

#    time.sleep(10)
    # ser = serialset.TestModbusSerial()
    ser = serial_api.Modbus()

    """
    read data from mysql
    """
    dbh=daesql.MySQL(dbconfig.mysql_config)
    scene_node_sql = "SELECT `nl`.`node_id`, `nl`.`type_id`, `nl`.`device_address`, " \
                     "`nl`.`num` AS `node_number`, `snl`.`node_state` " \
                     "FROM `node_list` AS `nl` " \
                     "INNER JOIN `scene_node_list` AS `snl` ON(`nl`.`node_id` = `snl`.`node_id` AND `nl`.`gateway_id` = `snl`.`gateway_id`) " \
                     "WHERE `snl`.`gateway_id` = {} AND `snl`.`scene_id` = {} ".format(gateway_id, scene_id, scene_number)

    result = dbh.query(scene_node_sql)
    rule={}
    state={}
    nstate=[0,0,0,0]
    for row in result:
        nnode=1<<(row['node_number']-1)

        if(rule.__contains__(row['device_address'])):
            a=rule[row['device_address']]
            a=a+nnode
            rule[row['device_address']]=a
            if(row['type_id'] in G_CONTROL_VALUE_TYPE_LIST):
                nstate[(row['node_number']-1)]=int(row['node_state'])
                a=state[row['device_address']]
                a=a+nnode
                state[row['device_address']]=a
            elif(row['node_state'] > 0):
                a=state[row['device_address']]
                a=a+nnode
                state[row['device_address']]=a
        else:
            rule[row['device_address']]=nnode
            state[row['device_address']]=0
            if(row['type_id'] in G_CONTROL_VALUE_TYPE_LIST):
                nstate[(row['node_number']-1)]=int(row['node_state'])
                state[row['device_address']]=nnode
            elif(row['node_state'] > 0):
                state[row['device_address']]=nnode



    print("final=",rule)
    print("state for 4x=",nstate)
    print("state for 3x=",state)
    key=rule.keys()
    local=(scene_number+16)*2
    scene_number=scene_number+63
    for a in key:
        b=rule.get(a)

        c=state.get(a)
        if (int(a)!=3):
            cmd=[int(a),16,40,local,0,2,4,scene_number,b,c,0]
        elif(int(a)==3):
            cmd=[3,16,80,local*2,0,4,8,scene_number,b,c,0,nstate[0],nstate[1],nstate[2],nstate[3]]

        ser.write_command_to_modbus(cmd)
        time.sleep(0.1)


    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('BUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])
    time.sleep(0.03)

def delete_group(gateway_id, group_id, group_number):
    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('MBUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

    # ser = serialset.TestModbusSerial()
    ser = serial_api.Modbus()

    """
    read data from mysql
    """
    dbh=daesql.MySQL(dbconfig.mysql_config)
    node_list_sql = "SELECT `nl`.`node_id`, `nl`.`device_address`, `nl`.`num` AS `node_number` " \
                    "FROM `node_list` AS `nl` " \
                    "INNER JOIN `group_node_list` AS `gnl` ON(`nl`.`node_id` = `gnl`.`node_id` AND `nl`.`gateway_id` = `gnl`.`gateway_id`)" \
                    "WHERE `gnl`.`gateway_id` = {} AND `gnl`.`group_id` = {}".format(gateway_id, group_id)
    result = dbh.query(node_list_sql)
    rule={}
    state={}
    for row in result:
        device_address = row['device_address']
        node_number = row['node_number']
        node_number = 1<<(node_number - 1)
        if(rule.__contains__(device_address)):
            a = rule[device_address]
            a = a + node_number
            rule[device_address]=a
        else:
            rule[device_address]=node_number
    key=rule.keys()
    for a in key:
        b=rule.get(a)
        if (int(a)!=3):

            cmd=[int(a),16,40,group_number * 2,0,2,4,0,0,0,0]
        elif(int(a)==3):
            cmd=[3,16,80,group_number * 4,0,4,8,0,0,0,0,0,0,0,0]
        print("delete cmd=",cmd)
        ser.write_command_to_modbus(cmd)
        time.sleep(0.1)


    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('BUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])
    time.sleep(0.03)


def delete_scene(gateway_id, scene_id, scene_number):
    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('MBUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

    # ser = serialset.TestModbusSerial()
    ser = serial_api.Modbus()

    """
    read data from mysql
    """
    dbh=daesql.MySQL(dbconfig.mysql_config)
    scene_node_sql = "SELECT `nl`.`node_id`, `nl`.`type_id`, `nl`.`device_address`, " \
                     "`nl`.`num` AS `node_number`, `snl`.`node_state` " \
                     "FROM `node_list` AS `nl` " \
                     "INNER JOIN `scene_node_list` AS `snl` ON(`nl`.`node_id` = `snl`.`node_id` AND `nl`.`gateway_id` = `snl`.`gateway_id`) " \
                     "WHERE `snl`.`gateway_id` = {} AND `snl`.`scene_id` = {} ".format(gateway_id, scene_id, scene_number)

    result = dbh.query(scene_node_sql)
    rule={}
    state={}
    nstate=[0,0,0,0]
    for row in result:

        device_address = row['device_address']

        if(rule.__contains__(device_address)):
            pass
        else:
            rule[device_address]=0
            state[device_address]=0

    key=rule.keys()
    local=(scene_number+16)*2
    scene_number=scene_number+63
    for a in key:
        b=rule.get(a)

        c=state.get(a)
        if (int(a)!=3):
            cmd=[int(a),16,40,local,0,2,4,scene_number,b,c,0]
        elif(int(a)==3):
            cmd=[3,16,80,local*2,0,4,8,scene_number,b,c,0,nstate[0],nstate[1],nstate[2],nstate[3]]

        ser.write_command_to_modbus(cmd)
        time.sleep(0.1)


    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('BUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])
    time.sleep(0.03)

def switch_power(num,group,status):
    if group < 1 or group > 4:
        raise Exception('group error')
    # ser = serial2.TestModbusSerial()
    ser = serial_api.Modbus()

    if status == 'ON':
        group=group-1+(num-1)*8
        cmd = [1, 5, 1, group, 255, 0]
        ser.write_command_to_modbus(cmd)
    elif status == 'OFF':
        group=group-1+(num-1)*8
        cmd = [1, 5, 1, group, 0, 0]
        ser.write_command_to_modbus(cmd)
    else:
        mcuser=mcu.MCUinitialize()
        mcuser.mcu_process('MBUS')
        mcuser.open_serial()
        mcuser.send_data(mcuser.data_MCU_read_mode)
        a = mcuser.read_data().hex()
        print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

        status=int(status)
        cmd = [num, 16, 240, 2, 0, 1,2,group,status]
        ser.write_command_to_modbus(cmd)
        time.sleep(0.1)

        mcuser=mcu.MCUinitialize()
        mcuser.mcu_process('BUS')
        mcuser.open_serial()
        mcuser.send_data(mcuser.data_MCU_read_mode)
        a = mcuser.read_data().hex()
        print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])
        time.sleep(0.03)


"""

def switch_percent(num,group,status):
    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('MBUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])

    ser = serial2.TestModbusSerial()
    if status >=-1 and status <=100:
        cmd = [num, 16, 240, 2, 0, 1,2,group,status]
    else:
        raise Exception('status error')
    if group < 1 or group > 4:
        raise Exception('group error')


    ser.write_command_to_modbus(cmd)


    mcuser=mcu.MCUinitialize()
    mcuser.mcu_process('BUS')
    mcuser.open_serial()
    mcuser.send_data(mcuser.data_MCU_read_mode)
    a = mcuser.read_data().hex()
    print([str(int(a[i:i + 2], 16)) for i in range(0, len(a), 2)])
"""

# 開關群組
def switch_group(group,status):
    # ser = serial2.TestModbusSerial()
    ser = serial_api.Modbus()
    if status == 'ON':
        cmd = [1, 5, 0, group, 255, 0]
    elif status == 'OFF':
        cmd = [1, 5, 0, group, 0, 0]
    else:
        raise Exception('status error')
    if group < 1 and group > 63:
        raise Exception('group error')
    ser.write_command_to_modbus(cmd)


# 開關場景
def switch_scene(scene,status):
    scene=scene+63
    # ser = serial2.TestModbusSerial()
    ser = serial_api.Modbus()
    if status == 'ON':
        cmd = [1, 5, 0, scene, 255, 0]
    elif status == 'OFF':
        cmd = [1, 5, 0, scene, 0, 0]
    else:
        raise Exception('status error')
    if scene < 64 and scene > 127:
        raise Exception('scene error')
        #filex = json.load(file)
    ser.write_command_to_modbus(cmd)


