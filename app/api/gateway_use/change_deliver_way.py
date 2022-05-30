import sys

deliver_way_flag = open("/var/www/dae-web/app/api/gateway_use/device/config/deliver_way_flag.py", 'r')
flag = deliver_way_flag.read()
deliver_way_flag.close()

print("Original:", flag)

if "Ethernet" in flag:
    text = 'DELIVER_WAY = "NB-IoT" '
elif "NB-IoT" in flag:
    text = 'DELIVER_WAY = "Ethernet" '

deliver_way_flag = open("/var/www/dae-web/app/api/gateway_use/device/config/deliver_way_flag.py", 'w')
deliver_way_flag.write(text)
deliver_way_flag.close()

deliver_way_flag = open("/var/www/dae-web/app/api/gateway_use/device/config/deliver_way_flag.py", 'r')
flag = deliver_way_flag.read()
deliver_way_flag.close()

print("Now:", flag)