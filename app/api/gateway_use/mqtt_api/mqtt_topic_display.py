# coding=utf-8
count = 10
symbol = '-' * count
task_segment = '/'

# 偵錯用的函式
def display(action, target):
    task_job = symbol + action + '/' + target + symbol
    # print(symbol, action, task_segment, table, symbol)
    print(task_job)
