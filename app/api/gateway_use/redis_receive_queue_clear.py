import redis
import json

r = redis.Redis('localhost')

redis_var = "receive"
# redis_var = "transmit_receive"

queue_length = r.llen(redis_var)
print("Queue Length:", queue_length)

for i in range(queue_length):
    r.lpop(redis_var)