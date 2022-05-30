#-*-coding:UTF-8 -*-
import serial
import time
import json
#  Broker資訊
HOST = bytes("140.116.39.212", encoding="utf8")
PORT = bytes('1883', encoding="utf8")
TOPIC = bytes('kdd', encoding="utf8")
# x = [
# {
#     "gateway": "09ea6335-d2bd-4678-9ca9-647b5574a09e", "gateway_address": "1", "group_id": 5, "id": 6, "model": "LT3070", "model_type": 1, "node": 1, "node_name": "\u7a97\u7c3e-\u5de6\u908a", "node_state": "ON"
# },
# {
#     "gateway2": "09ea6335-d2bd-4678-9ca9-647b5574a09e", "gateway_address": "1", "group_id": 5, "id": 6, "model": "LT3070", "model_type": 1, "node": 1, "node_name": "\u7a97\u7c3e-\u5de6\u908a", "node_state": "ON"
# }
# ]
y = []
y.append({"gateway": "09ea6335-d2bd-4678-9ca9-647b5574a09e", "gateway_address": "1", "group_id": 5, "id": 6,
          "model": "LT3070", "model_type": 1, "node": 1, "node_name": "\u7a97\u7c3e-\u5de6\u908a", "node_state": "ON"})
# y.append({   "gateway": "09ea6335-d2bd-4678-9ca9-647b5574a09e", "gateway_address": "1", "group_id": 5, "id": 6, "model": "LT3070", "model_type": 1, "node": 1, "node_name": "\u7a97\u7c3e-\u5de6\u908a", "node_state": "ON"})
# y.append({   "gateway": "09ea6335-d2bd-4678-9ca9-647b5574a09e", "gateway_address": "1", "group_id": 5, "id": 6, "model": "LT3070", "model_type": 1, "node": 1, "node_name": "\u7a97\u7c3e-\u5de6\u908a", "node_state": "ON"})
# print(y)
message = json.dumps(y)
# # message = json.dumps({"value": "test connection"})
# print(message)
message = "aaa"

MSG = bytes(message, encoding="utf8")
print("Length of message :")
print(len(MSG))
LEN = bytes(str(len(MSG)), encoding="utf8")


def start():
    # ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=5)
    # ser = serial.Serial('com6', 115200, timeout=5)
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=5)
    time.sleep(.2)
    ser.write(b'AT+CGPADDR=1\r')
    time.sleep(.1)
    ser.write(b'AT+CNACT=1,"nbiot"\r')
    time.sleep(.1)
    ser.write(b'AT+SMCONF="url","%s",%s\r' % (HOST, PORT))
    time.sleep(.1)
    ser.write(b'AT+SMCONF="USERNAME",""\r')
    time.sleep(.1)
    ser.write(b'AT+SMCONF="PASSWORD",""\r')
    time.sleep(.1)
    ser.write(b'AT+SMCONF="QOS",2\r')
    time.sleep(.1)
    ser.write(b'AT+SMCONF="KEEPTIME",60\r')
    time.sleep(.1)
    ser.write(b'AT+SMCONN\r')
    time.sleep(1)
    ser.flushInput()
    time.sleep(.1)
    ser.write(b'AT+SMPUB="%s","%s",2,0\r' % (TOPIC, LEN))
    time.sleep(1)
    ser.write(MSG + b'\r')
    time.sleep(1)
    sub = ser.read(70)
    print(sub)
    ser.write(b'AT+SMDISC\r')
    time.sleep(.1)
    ser.write(b'AT+CNACT=0\r')
    time.sleep(.1)


if __name__ == '__main__':
    start()
