

import time


def isDateBefore(date, before):
    return (time.strptime(str(date.strip()), '%Y-%m-%d') < time.strptime(before, '%Y-%m-%d'))