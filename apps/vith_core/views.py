import datetime

from django.forms.models import model_to_dict

from core import JsonResponse, datetime_to_timestamp
from vith_core.forms import UploadForm
from vith_core.models import Track


def tracks(request):
    """
    Return list of all uploaded tracks in json format
    """
    tracks = Track.objects.filter(play_time__gte=datetime.datetime.now())
    data = []
    for t in tracks:
        tdict = model_to_dict(t)
        tdict['track_file'] = tdict['track_file'].name            
        tdict['play_time'] = datetime_to_timestamp(tdict['play_time'])
        data.append(tdict)
    
    return JsonResponse(data)


def upload(request):
    """
    Uploads and enqueues track
    """
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        track = form.save(commit=False)
        track.length = 0
        track.save()
        return JsonResponse({
            'status': 'ok',
            'name': track.name,
            'length': track.length
        })
    
    return JsonResponse({
        'status': 'error',
        'errors': dict(form.errors)
    });