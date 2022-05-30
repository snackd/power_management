import redis
import json

import redis
import json

r = redis.Redis('localhost')

# redis_var = "publish"
redis_var = "transmit_publish"

queue_length = r.llen(redis_var)
print("Queue Length:", queue_length)

for i in range(queue_length):
    r.lpop(redis_var)
