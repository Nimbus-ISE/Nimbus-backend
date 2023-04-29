import datetime
import random
import math
import time

def timeStringToTime(time_str):
    hour_str, minute_str = time_str.split(":")
    hour = int(hour_str)
    minute = int(minute_str)
    if hour == 24:
        hour = 23
        minute = 59

    return datetime.time(hour, minute)


def randInt(n):
    random.seed(time.time())
    return math.floor((n + 1) * random.random())
