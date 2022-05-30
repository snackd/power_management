# encoding=utf-8
#! /usr/bin/python

# import method.condition as condition
import device.condition as condition
import threading

# from method.meter import Meter
from device.meter import Meter
import device.common as common


class PostAPI(threading.Thread):
    def run(self):
        pass

        # while True:
        #     thetime = common.get_now_sec()

        #     while int(thetime) % 10 != 0:
        #         thetime = common.get_now_sec()

        #     thetime = common.get_now()
        #     print("Post")
        #     file = open(
        #         '/var/www/dae-web/app/api_1_0/resident/method/config/last_data.json', 'r', encoding='utf-8')
        #     last_data = file.read()
        #     while(last_data == ''):
        #         last_data = file.read()
        #     data = json.loads(last_data)
        #     file.close()
        #     # data = r.get('meter_data')
        #     # print("Data:", data)

        #     # data[0]['datetime'] = thetime
        #     # response = common.post_data_to_server(data)
        #     # response = common.post_http_data_to_server(data)
        #     response = common.post_mqtt_data_to_server(data)
        #     time.sleep(10)
        #     print("-" * 10)

def main():
    try:
        # flag.flag=1

        # print("Before Read Meter")

        cond = condition.Condition()
        meter_thread = Meter(cond)

        meter_thread.run()
        # print("OK")

        # demand = meter_thread.read_demand()

        # print("Demand：", demand)

        # print("After Read Meter")
        # # start thread
        # meter_thread.start()
        # PostAPI().start()

    except:
        print("Read error")
        pass


if __name__ == '__main__':
    main()
