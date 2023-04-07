def timeStringToFloat(time_str):
    hour_str, minute_str = time_str.split(":")
    hour = int(hour_str)
    minute = int(minute_str)
    time_float = hour + minute/60.0
    return time_float