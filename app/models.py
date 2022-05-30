# coding=utf-8
from . import db
import datetime, time
from werkzeug.security import generate_password_hash, check_password_hash

# Alembic是 SQLAlchemy 的資料庫遷移的框架
# 關係資料庫圍繞結構性資料為中心，因此當結構更改時，資料庫中已經存在的資料需要遷移到修改後的結構

# 隨著應用程序的不斷增長，將需要更改該結構，很可能會添加新的東西，但有時還會修改或刪除項目。
# Alembic（Flask-Migrate使用的遷移框架）將以不需要重新創建數據庫的方式進行這些模式更改

class User( db.Model):
    _tablename_ = 'user'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    account = db.Column(db.VARCHAR(64))
    password = db.Column(db.VARCHAR(512))
    authority = db.Column(db.VARCHAR(20))

    def __init__(self, id, account, password, authority):
        self.id = id
        self.account = account
        self.password = password
        self.authority = authority

    def set_password(password):
        password = generate_password_hash(password)
        return password

    def check_password(password_hash, password):
        result = check_password_hash(password_hash, password)
        return result

    def insert(account, password):
        db.session.add(User(None, account, password, '1'))
        db.session.commit()

    def find_one(account):
        query_result = db.session.query(User.account).filter(User.account == account).first()
        db.session().commit()
        if query_result is None:
            return False
        else:
            return True

    def register_user(account, password):
        user_data = User.find_one(account)
        if user_data is False:
            password_hash = User.set_password(password)
            User.save_to_db(account, password_hash)
            return False
        return True

    def save_to_db(account, password):
        User.insert(account=account, password=password)

# ------------------------------------------------------------------------------------------------------

class Project(db.Model):
    _tablename_ = 'project'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    user_id = db.Column(db.INTEGER)
    project_name = db.Column(db.VARCHAR(64))
    account = db.Column(db.VARCHAR(64))

    def __init__(self, id, user_id, project_name, account):
        self.id = id
        self.user_id = user_id
        self.project_name = project_name
        self.account = account
# ------------------------------------------------------------------------------------------------------
class Area_list(db.Model):
    _tablename_ = 'area_list'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    project_id = db.Column(db.INTEGER)
    area_name = db.Column(db.VARCHAR(20))

    def __init__(self, id, project_id, area_name):
        self.id = id
        self.project_id = project_id
        self.area_name = area_name
# ------------------------------------------------------------------------------------------------------

class Gateway(db.Model):
    _tablename_ = 'gateway_list'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    uid = db.Column(db.VARCHAR(255))
    country = db.Column(db.VARCHAR(20))
    city = db.Column(db.VARCHAR(20))
    physical_address = db.Column(db.VARCHAR(255))
    gateway_name = db.Column(db.VARCHAR(127))
    project_id = db.Column(db.VARCHAR(20))
    sunrise = db.Column(db.TIME)
    sunset = db.Column(db.TIME)
    latitude = db.Column(db.VARCHAR(255))
    longitude = db.Column(db.VARCHAR(255))

    def __init__(self, id, uid,country, city, physical_address, gateway_name, project_id,sunrise,sunset):
        self.id = id
        self.uid = uid
        self.country = country
        self.city = city
        self.physical_address = physical_address
        self.gateway_name = gateway_name
        self.project_id = project_id
        self.sunrise = sunrise
        self.sunset = sunset

    def Gateway_to_json(self):
        return {
                    'table': 'Gateway',
                    'id': self.id,
                    'uid': self.uid,
                    'country': self.country,
                    'city': self.city,
                    'physical_address': self.physical_address,
                    'gateway_name': self.gateway_name,
                    'project_id': self.project_id,
                }

# ------------------------------------------------------------------------------------------------------




class DemandSettings(db.Model):
    _tablename_ = 'demand_settings'
    id = db.Column(db.INTEGER, primary_key=True)
    value = db.Column(db.INTEGER)
    value_max = db.Column(db.INTEGER)
    value_min = db.Column(db.INTEGER)
    load_off_gap = db.Column(db.INTEGER)
    reload_delay = db.Column(db.INTEGER)
    reload_gap = db.Column(db.INTEGER)
    cycle = db.Column(db.INTEGER)
    mode = db.Column(db.VARCHAR(255))
    groups = db.Column(db.VARCHAR(255))
    created_at = db.Column(db.DATETIME)
    updated_at = db.Column(db.DATETIME)

    def __init__(self, value, value_max, value_min, load_off_gap,
                 reload_delay, reload_gap, cycle, mode, groups, created_at, updated_at):
        self.value = value
        self.value_max = value_max
        self.value_min = value_min
        self.load_off_gap = load_off_gap
        self.reload_delay = reload_delay
        self.reload_gap = reload_gap
        self.cycle = cycle
        self.mode = mode
        self.groups = groups
        self.created_at = created_at
        self.updated_at = updated_at


class Links(db.Model):
    _tablename_ = 'links'
    id = db.Column(db.INTEGER, primary_key=True)
    domain = db.Column(db.VARCHAR(255))
    ip = db.Column(db.VARCHAR(255))
    path = db.Column(db.VARCHAR(255))
    port = db.Column(db.VARCHAR(255))
    key = db.Column(db.VARCHAR(255))
    created_at = db.Column(db.DATETIME)
    updated_at = db.Column(db.DATETIME)

    def __init__(self, domain, ip, path, port, key, created_at, updated_at):
        self.domain = domain
        self.ip = ip
        self.path = path
        self.port = port
        self.key = key
        self.created_at = created_at
        self.updated_at = updated_at


class Offloads(db.Model):
    _tablename_ = 'offloads'
    id = db.Column(db.INTEGER, primary_key=True)
    group = db.Column(db.INTEGER)
    hand_controls = db.Column(db.VARCHAR(20))
    offload_available = db.Column(db.VARCHAR(20))
    created_at = db.Column(db.DATETIME)
    updated_at = db.Column(db.DATETIME)

    def __init__(self, group, hand_controls, offload_available, created_at, updated_at):
        self.group = group
        self.hand_controls = hand_controls
        self.offload_available = offload_available
        self.created_at = created_at
        self.updated_at = updated_at


class Demand(db.Model):
    _tablename_ = 'demand'
    id = db.Column(db.INTEGER, primary_key=True)
    address = db.Column(db.VARCHAR(20))
    channel = db.Column(db.INTEGER)
    circuit = db.Column(db.VARCHAR(20))
    model = db.Column(db.VARCHAR(20))
    datetime = db.Column(db.DATETIME)
    demand_min = db.Column(db.FLOAT(precision='20,2'))
    demand_quarter = db.Column(db.FLOAT(precision='20,2'))
    R_value = db.Column(db.FLOAT(precision='20,2'))
    S_value = db.Column(db.FLOAT(precision='20,2'))
    T_value = db.Column(db.FLOAT(precision='20,2'))
    Total_value = db.Column(db.FLOAT(precision='20,2'))
    gateway_uid = db.Column(db.VARCHAR(255))

    def __init__(self, id, address, channel, circuit, model, datetime,
                 demand_min, demand_quarter, R_value, S_value,
                 T_value, Total_value, gateway_uid):
        self.id = id
        self.address = address
        self.channel = channel
        self.circuit = circuit
        self.model = model
        self.datetime = datetime
        self.demand_min = demand_min
        self.demand_quarter = demand_quarter
        self.R_value = R_value
        self.S_value = S_value
        self.T_value = T_value
        self.Total_value = Total_value
        self.gateway_uid = gateway_uid


# ------------------------------------------------------------------------------------------------------
db.Index('demand_index', Demand.datetime, Demand.address, Demand.channel)


class Setting(db.Model):
    _tablename_ = 'setting'
    id = db.Column(db.INTEGER, primary_key=True)
    model = db.Column(db.VARCHAR(20))
    address = db.Column(db.VARCHAR(20))
    ch = db.Column(db.VARCHAR(20))
    speed = db.Column(db.VARCHAR(20))
    circuit = db.Column(db.VARCHAR(20))
    pt = db.Column(db.VARCHAR(20))
    ct = db.Column(db.VARCHAR(20))
    meter_type = db.Column(db.VARCHAR(20))
    created_at = db.Column(db.DATETIME)
    updated_at = db.Column(db.DATETIME)
    gateway_uid = db.Column(db.VARCHAR(255))

    def __init__(self, id, model, address, ch, speed, circuit, pt,
                 ct, meter_type, created_at, updated_at, gateway_uid):
        self.id = id
        self.model = model
        self.address = address
        self.ch = ch
        self.speed = speed
        self.circuit = circuit
        self.pt = pt
        self.ct = ct
        self.meter_type = meter_type
        self.created_at = created_at
        self.updated_at = updated_at
        self.gateway_uid = gateway_uid

    def Setting_to_json(self):
        return {
              'id': self.id,
              'model': self.model,
              'address': self.address,
              'ch': self.ch,
              'speed': self.speed,
              'circuit': self.circuit,
              'pt': self.pt,
              'ct': self.ct,
              'meter_type': self.meter_type,
              'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
              'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
              'gateway_uid': self.gateway_uid
                }
# ------------------------------------------------------------------------------------------------------
class Node(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    gateway = db.Column(db.VARCHAR(255))
    device_address = db.Column(db.VARCHAR(20))
    model = db.Column(db.VARCHAR(20))
    node_name = db.Column(db.VARCHAR(20))
    node = db.Column(db.INTEGER)
    created_at = db.Column(db.DATETIME)
    updated_at = db.Column(db.DATETIME)
    model_type = db.Column(db.INTEGER)
    node_state = db.Column(db.VARCHAR(10))
    group_id = db.Column(db.INTEGER, db.ForeignKey('group.id'))

    def __init__(self, id, gateway, model, node_name, node, device_address,  created_at, updated_at, model_type, node_state, group_id):
        self.id = id
        self.gateway = gateway
        self.device_address = device_address
        self.model = model
        self.node_name = node_name
        self.node = node
        self.created_at = created_at
        self.updated_at = updated_at
        self.model_type = model_type
        self.group_id = group_id
        self.node_state = node_state

    def Node_to_json(self):
        return {
                    'id':self.id,
                    'gateway':self.gateway,
                    'device_address':self.device_address,
                    'model':self.model,
                    'node_name':self.node_name,
                    'node':self.node,
                    'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at is not None else None,
                    'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at is not None else None,
                    'model_type':self.model_type,
                    'group_id':self.group_id,
                    'node_state':self.node_state
                }


class Group(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    group_num = db.Column(db.INTEGER)
    group_name = db.Column(db.VARCHAR(20))
    group_state = db.Column(db.VARCHAR(20))
    created_at = db.Column(db.DATETIME)
    updated_at = db.Column(db.DATETIME)

    def __init__(self, id, group_num, group_name, group_state, created_at, updated_at):
        self.id = id
        self.group_num = group_num
        self.group_name = group_name
        self.group_state = group_state
        self.created_at = created_at
        self.updated_at = updated_at

    def Group_to_json(self):
        return {
                    'id':self.id,
                    'group_num':self.group_num,
                    'group_name':self.group_name,
                    'group_state':self.group_state,
                    'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at is not None else None,
                    'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at is not None else None,

                }

class Scenes(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    node = db.Column(db.INTEGER)
    node_state = db.Column(db.VARCHAR(10))
    scene_name = db.Column(db.VARCHAR(10))
    scene_number = db.Column(db.INTEGER)
    created_at = db.Column(db.DATETIME)
    updated_at = db.Column(db.DATETIME)

    def __init__(self, id, node, node_state, scene_name, scene_number, created_at, updated_at):
        self.id = id
        self.node = node
        self.node_state = node_state
        self.scene_name = scene_name
        self.scene_number = scene_number
        self.created_at = created_at
        self.updated_at = updated_at

    def Scenes_to_json(self):
        return {
                    'id':self.id,
                    'node':self.node,
                    'node_state':self.node_state,
                    'scene_name':self.scene_name,
                    'scene_number':self.scene_number,
                    'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at is not None else None,
                    'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at is not None else None,
                }


class Schedule(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    schedule_table = db.Column(db.VARCHAR(10))
    group_id = db.Column(db.INTEGER)
    schedule_group_state = db.Column(db.VARCHAR(10))
    control_time = db.Column(db.TIME)
    control_time_of_sun = db.Column(db.VARCHAR(10))
    setting = db.Column(db.VARCHAR(25))


    def __init__(self, id, schedule_table, group_id, schedule_group_state, control_time, control_time_of_sun, setting):
        self.id = id
        self.schedule_table = schedule_table
        self.group_id = group_id
        self.schedule_group_state = schedule_group_state
        self.control_time = control_time
        self.control_time_of_sun = control_time_of_sun
        self.setting = setting

    def Schedule_to_json(self):
        return {
            'id': self.id,
            'schedule_table': self.schedule_table,
            'group_id': self.group_id,
            'schedule_group_state': self.schedule_group_state,
            'control_time': transfer_time(self.control_time),
            'control_time_of_sun': self.control_time_of_sun,
            'setting': self.setting,

        }


class festival(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    date = db.Column(db.DATE)
    statement = db.Column(db.VARCHAR(255))
    bind_table = db.Column(db.VARCHAR(10))

    def __init__(self, id, date, statement, bind_table):
        self.id = id
        self.date = date
        self.statement = statement
        self.bind_table = bind_table

    def festival_to_json(self):
        return {
                    'id':self.id,
                    'date':self.date.strftime("%Y-%m-%d"),
                    'statement':self.statement,
                    'bind_table':self.bind_table
                }


class Log(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    gateway_uid = db.Column(db.VARCHAR(255))
    action = db.Column(db.VARCHAR(20))
    content = db.Column(db.VARCHAR(64))
    data = db.Column(db.TEXT)
    execute_state = db.Column(db.VARCHAR(64))
    datetime = db.Column(db.DATETIME)
    role = db.Column(db.VARCHAR(20))

    def __init__(self, id, gateway_uid, action, content, data, execute_state, datetime, role):
        self.id = id
        self.gateway_uid = gateway_uid
        self.action = action
        self.content = content
        self.data = data
        self.execute_state = execute_state
        self.datetime = datetime
        self.role = role

# 轉換datetime.timedelta
def transfer_time(value):
    if (value is None):
        return None
    else:
        value = time2seconds(str(value))
        hours, remainder = divmod(value, 3600)
        minutes, seconds = divmod(remainder, 60)
        if(hours == 0):
            hours = str(hours)+'0'
        if(minutes == 0):
            minutes = str(minutes)+'0'
        if(seconds == 0):
            seconds = str(seconds)+'0'
        return '{}:{}:{}'.format(hours, minutes, seconds)


def time2seconds(time):
    h, m, s = time.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


# ------------------------------------------------------------------------------------------------------


class UserData_information():
    tablename_ = 'electricity_information'
    # id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    db.ForeignKeyConstraint(
        ['user_source.user_id'],
        ['electricity_information.user_id']
    )
    user_id = db.Column(db.VARCHAR(20), primary_key=True)
    datetime = db.Column(db.DATETIME, primary_key=True)
    value = db.Column(db.FLOAT, nullable=True)
    Global_active_power = db.Column(db.FLOAT, nullable=True)
    Global_reactive_power = db.Column(db.FLOAT, nullable=True)
    Voltage = db.Column(db.FLOAT, nullable=True)
    Global_intensity = db.Column(db.FLOAT, nullable=True)
    Sub_metering_1 = db.Column(db.FLOAT, nullable=True)
    Sub_metering_2 = db.Column(db.FLOAT, nullable=True)
    Sub_metering_3 = db.Column(db.FLOAT, nullable=True)

    def __init__(self, id, user_id, datetime, value,
                 Global_active_power, Global_reactive_power, Voltage, Global_intensity, Sub_metering_1, Sub_metering_2, Sub_metering_3):
        self.id = id
        self.user_id = user_id
        self.datetime = datetime
        self.value = value
        self.Global_active_power = Global_active_power
        self.Global_reactive_power = Global_reactive_power
        self.Voltage = Voltage
        self.Global_intensity = Global_intensity
        self.Sub_metering_1 = Sub_metering_1
        self.Sub_metering_2 = Sub_metering_2
        self.Sub_metering_3 = Sub_metering_3


class electricity_information(UserData_information, db.Model):
    pass

# ------------------------------------------------------------------------------------------------------


class weather_information():
    tablename_ = 'weather'
    WindSpeed = db.Column(db.INTEGER)
    Temperature = db.Column(db.FLOAT)
    DateTime = db.Column(db.DATETIME, primary_key=True)
    RelHumidity = db.Column(db.FLOAT)
    apparent_temperature = db.Column(db.FLOAT)

    def __init__(self, DateTime, WindSpeed, Temperature, RelHumidity, apparent_temperature):
        self.DateTime = DateTime
        self.WindSpeed = WindSpeed
        self.Temperature = Temperature
        self.RelHumidity = RelHumidity
        self.apparent_temperature = apparent_temperature


db.Index('user_index', weather_information.DateTime)


class weather(weather_information, db.Model):
    pass


class Network_Record(db.Model):
    _tablename_ = 'networkrecord'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    datetime = db.Column(db.DATETIME)
    receive = db.Column(db.FLOAT(precision='20,2'))
    transmit = db.Column(db.FLOAT(precision='20,2'))

    def __init__(self, id, datetime, receive, transmit):
        self.id = id
        self.datetime = datetime
        self.receive = receive
        self.transmit = transmit
