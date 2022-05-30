"""
Server settings variable file json path

The variables:
    isRun - Decide whether to return device status
    record_gap - The meter data is returned to the server interval
    config_gap - The meter device status is returned to the server interval
    domain - Server api domain (ex: http://google.com.tw)
    ip - Server ip (ex: http://123.123.123.123)
    path - Server api path (ex: connect.php)
    port - Server api port (ex: 80)
    key - Data encryption key

"""
SERVER_SETTINGS_PATH = "/var/www/html/web/storage/app/config.json"


"""
Meter table database path

The database path of the meter address table
"""
METER_DATABASE_PATH = "/var/www/DAE_SG/app/api/gateway_use/device/config/meter.sqlite"

"""
Meter boot config path (json file)

The file path of the meter config
"""

BOOT_CONFIG_PATH = "/var/www/dae-web/app/api_1_0/resident/method/config/boot.json"
