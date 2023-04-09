import datetime

def timeStringToTime(time_str):
    hour_str, minute_str = time_str.split(":")
    hour = int(hour_str)
    minute = int(minute_str)
    if hour == 24:
        hour = 23
        minute = 59

    return datetime.time(hour, minute)
