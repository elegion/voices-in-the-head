from django.http import HttpResponse
from django.utils import simplejson as json


def JsonResponse(obj):
    response = HttpResponse(content=json.dumps(obj), content_type='application/x-javascript')
    response.data = obj
    return response
