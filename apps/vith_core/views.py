from django.utils import simplejson as json
from django.http import HttpResponse


def tracks(request):
    """
    Return list of all uploaded tracks in json format
    """
    
    return HttpResponse('test')