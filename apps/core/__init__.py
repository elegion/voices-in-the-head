from time import mktime
import logging

from django.http import HttpResponse
from django.utils import simplejson as json


logger = logging.getLogger('core')


def datetime_to_timestamp(dt):
    if dt:
        return mktime(dt.timetuple()) + 1e-6 * dt.microsecond
    else:
        return None


def json_view(f):
    def actual_dec(*args, **kwargs):
        try:
            return JsonResponse(f(*args, **kwargs))
        except Exception, e:
            logger.error(e)
            return JsonResponse({'result': 'error', 'error': unicode(e)})
    return actual_dec


def JsonResponse(obj):
    response = HttpResponse(content=json.dumps(obj), content_type='application/x-javascript')
    response.data = obj
    return response
