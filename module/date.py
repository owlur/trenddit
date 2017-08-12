import time


def str2stamp(date):
    date += " 00:00"
    return time.mktime(time.strptime(date, '%Y%m%d %H:%M'))


# In[8]:

def stamp2str(timestamp, hm=False):
    time_format = "%Y%m%d"
    if hm:
        time_format += " %H:%M"
    return time.strftime(time_format, time.localtime(int(timestamp)))


def date2list(start_date, end_date, pre_day=0):
    day = 86400

    stamp_start_date = str2stamp(start_date)
    stamp_end_date = str2stamp(end_date)

    date = stamp_start_date - pre_day * day

    result = [stamp2str(date)]

    while (date < stamp_end_date):
        date += day

        result.append(stamp2str(date))

    return result


def split_date(date):
    '''start_time = date[0] + " 00:00"
    end_time = date[1]+" 00:00"

    start_time = time.mktime(time.strptime(start_time, '%Y%m%d %H:%M'))
    end_time = time.mktime(time.strptime(end_time, '%Y%m%d %H:%M'))
    '''

    date = date.split(":")

    start_time = str2stamp(date[0])
    end_time = str2stamp(date[1])

    return start_time, end_time
