import datetime

def timeStringToFloat(time_str):
    hour_str, minute_str = time_str.split(":")
    hour = int(hour_str)
    minute = int(minute_str)
    time_float = hour + minute/60.0
    return time_float

def minuteFloatToTime(min_float):
    # Convert float to timedelta representing the number of seconds
    # since midnight
    seconds = int(min_float * 3600)
    delta = datetime.timedelta(seconds=seconds)

    # Create a datetime object for today at midnight
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Add the timedelta to get the time of day
    time_of_day = today + delta

    # Format the time as "HH:MM am/pm"
    time_str = time_of_day.strftime('%I:%M %p')

    return time_str

def minuteFloatToHourMinSec(minute_float):
    # Convert duration to seconds
    duration_in_seconds = minute_float * 60

    # Convert seconds to hours, minutes, and seconds
    hours, seconds_remainder = divmod(duration_in_seconds, 3600)
    minutes, seconds = divmod(seconds_remainder, 60)

    hours = int(hours)
    minutes = int(minutes)

    minutes_unit = 'Mins' if minutes > 1 else 'Min'
    hours_unit = 'Hrs' if hours > 1 else 'Hr'
    
    if hours < 1: # less than an hour
        return f'{minutes} {minutes_unit}'
    else:
        return f'{hours} {hours_unit} {minutes} {minutes_unit}'
