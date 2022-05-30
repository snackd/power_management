#-*-coding:UTF-8 -*-
import serial
import time

#  Broker資訊
HOST = bytes("140.116.39.212", encoding="utf8")
PORT = bytes('1883', encoding="utf8")
TOPIC = bytes('kdd', encoding="utf8")

MSG = bytes('12321', encoding="utf8")
LEN = bytes(str(len(MSG)), encoding="utf8")


def start():
    # ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=5)
    # ser = serial.Serial('com6', 115200, timeout=5)
    # ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=5)
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

    while True:
        ser.flushInput()
        time.sleep(.1)
        ser.write(b'AT+SMSUB="%s",1\r' % (TOPIC))
        time.sleep(2)
        sub = ser.read(10000)
        print(sub)
        if len(sub.split(b',')) == 3:
            message = sub.split(b',')
            print(message)
            print(message[2].split(b'"')[1])

        ser.write(b'AT+SMUNSUB="%s"\r' % (TOPIC))
        time.sleep(.5)

        ser.flushInput()

    ser.write(b'AT+SMDISC\r')
    time.sleep(1)
    ser.write(b'AT+CNACT=0\r')
    time.sleep(1)


if __name__ == '__main__':
    start()
