import redis
import json

r = redis.Redis('localhost')

redis_var = "response"

queue_length = r.llen(redis_var)
print("Queue Length:", queue_length)

for i in range(queue_length):
    r.lpop(redis_var)
