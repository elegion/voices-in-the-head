from time import mktime

from django.http import HttpResponse
from django.utils import simplejson as json


def datetime_to_timestamp(dt):
    if dt:
        return mktime(dt.timetuple()) + 1e-6 * dt.microsecond
    else:
        return None


def JsonResponse(obj):
    response = HttpResponse(content=json.dumps(obj), content_type='application/x-javascript')
    response.data = obj
    return response
