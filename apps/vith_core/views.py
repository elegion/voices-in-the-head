import datetime
from time import mktime

from django.utils import simplejson as json
from django.http import HttpResponse
from django.forms.models import model_to_dict

from vith_core.models import Track
from core import datetime_to_timestamp


def tracks(request):
    """
    Return list of all uploaded tracks in json format
    """
    tracks = Track.objects.all()#.filter(play_time__gte=datetime.datetime.now())
    data = []
    for t in tracks:
        tdict = model_to_dict(t)
        tdict['track_file'] = tdict['track_file'].name            
        tdict['play_time'] = datetime_to_timestamp(tdict['play_time'])
        data.append(tdict)
    
    return HttpResponse(json.dumps(data))#mimetype='application/json'