# encoding=utf-8
#! /usr/bin/python

import threading
import time


class Condition(threading.Thread):
    def __init__(self):
        super(Condition, self).__init__()
        self._cond = threading.Condition()
        self._is_wait = False


    def change_wait_status(self):
        self._is_wait = False if self._is_wait else True


    @property
    def condition(self):
        return self._cond


    @property
    def is_wait(self):
        return self._is_wait


    def acquire(self):
        self._cond.acquire()


    def notify(self):
        self._cond.notify()


    def wait(self):
        self._cond.wait()


    def release(self):
        self._cond.release()
