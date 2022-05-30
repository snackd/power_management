import datetime

year = 2017
month = 6
day = 9

start_time = datetime.datetime.now().replace(year=int(year), month=int(month), day=int(day), hour=0, minute=0, second=0, microsecond=0)
print(start_time)
end_time = datetime.datetime.now().replace(year=int(year), month=int(month), day=int(day)+1, hour=0, minute=0, second=0, microsecond=0)
print(end_time)


SELECT * FROM `demand` WHERE `datetime` >= '2017-06-08 00:00:00' AND `datetime` < '2017-06-09 00:00:00'