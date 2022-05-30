from device.config.setting import *

def redis_record_calculating_time():
    content = R.lpop("transmit_receive").decode(coding)
    content_action, content_table, content_time = content.split('/')
    receive_time = float(content_time)

    content = R.lpop("transmit_publish").decode(coding)
    content_action, content_table, content_time = content.split('/')
    publish_time = float(content_time)

    if ROLE == "Gateway":
        response_time = receive_time - publish_time

    if ROLE == "Server":
        response_time = publish_time - receive_time

    return content_action, content_table, response_time

def record(action, table ,response_time):
    sql_start_time = datetime.now()

    try:
        sql = (
            "INSERT INTO `transmit_list` "
            "(`role`, `deliver_way`, `action`, `table`, `response_time`) "
            "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}') "
        ).format(ROLE, DELIVER_WAY, action, table, response_time)
        log_result = dbh.execute(sql)

    except BaseException as n:
        print("Log Fail:", n)

    sql_end_time = datetime.now()
    write_sql_time = sql_end_time - sql_start_time

    # print("Role:", ROLE," Delivery:", DELIVER_WAY)
    print("Action:", action, " Table:", table)
    print("Write SQL Time:", write_sql_time)


def transmit_check_monitor():
    print("Transmit Monitor Start")

    while True:

        time.sleep(5)

        # 檢查有幾封接收的訊息(任務)
        receive_queue = R.llen("transmit_receive")
        publish_queue = R.llen("transmit_publish")

        if receive_queue and publish_queue:

            print("---")
            print("receive_queue:", receive_queue)
            print("publish_queue:", publish_queue)

            # DONE:計算收、發訊時間差
            action, table, response_time = redis_record_calculating_time()

            # DONE:寫到資料庫
            record(action=action, table=table, response_time=response_time)


# 當這隻程式為主程式執行時
if __name__ == '__main__':
    transmit_check_monitor()