import math
import redis
import random
from redis_lru import RedisLRU

client = redis.StrictRedis(host="localhost", port=6379, password=None)
cache = RedisLRU(client)


@cache
def get_circumference(radius):
    circumference = 2 * math.pi * radius
    print(f'fn call with radius {radius}')
    return circumference

print("Hello World!")

random_list = [random.randint(1,n) for n in range(1,10)]

result = [get_circumference(n) for n in random_list]

print(result)