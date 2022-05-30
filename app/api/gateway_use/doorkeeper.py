# coding=utf-8
# import mqtt_api.mqtt_on_ethernet as mqtt_ethernet
# import mqtt_api.mqtt_on_nbiot as mqtt_nbiot
from mqtt_api.mqtt_on_ethernet import *
from mqtt_api.mqtt_on_nbiot import *

# import device.config.setting as setting
from device.config.setting import *

mqtt_broker = cloud_mqtt_host
server_id = server_host
gateway_id = mac_address
topic = '#'

print("Role:", ROLE)
print("Deliver way:", DELIVER_WAY)

if __name__ == "__main__":

    if DELIVER_WAY == "Ethernet":
        instance = MqttOnEthernet(
                                host=mqtt_broker, server_id=server_id,
                                gateway_id=gateway_id, topic=topic)
    elif DELIVER_WAY == "NB-IoT":
        instance = MqttOnNbiot(
                                host=mqtt_broker, server_id=server_id,
                                gateway_id=gateway_id, topic=topic)
    mqtt_service = threading.Thread(target=instance.run)
    mqtt_service.start()


