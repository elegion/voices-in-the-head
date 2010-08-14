import datetime

from core import JsonResponse, datetime_to_timestamp
from vith_core.forms import UploadForm
from vith_core.models import Track


def tracks(request):
    """
    Return list of all uploaded tracks in json format
    """
    tracks = Track.objects.filter(play_time__gte=datetime.datetime.now())
    
    return JsonResponse([t.as_dict() for t in tracks])


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
            'track': track.as_dict()
        })
    
    return JsonResponse({
        'status': 'error',
        'errors': dict(form.errors)
    })
