from time import mktime


def datetime_to_timestamp(dt):
    if dt:
        return mktime(dt.timetuple()) + 1e-6 * dt.microsecond
    else:
        return None
