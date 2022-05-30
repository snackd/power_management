# encoding=utf-8
#! /usr/bin/python


import sys
import threading

from device.schedule import Schedule

import time

def main():
    try:

        print("Run schedule_api")

        s1 = Schedule()

        print("OK")

        s1.run()

        print("After schedule_api")

    except:
        print("Run Schedule Error")
        pass


if __name__ == '__main__':
    main()
