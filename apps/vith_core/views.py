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


def now_playing(request):
    """
    Returns current track and now playing position
    FIXME synchronize with audio streamer
    """    
    now = datetime.datetime.now()
    curr_track = Track.objects.filter(play_time__lte=now)\
        .order_by('-play_time')[0]
    if curr_track:
        curr_pos = (now - curr_track.play_time).seconds
        
    if curr_pos > curr_track.length:
        data = []
    else:
        tdata = curr_track.as_dict()
        tdata['position'] = curr_pos
        data = [tdata]
    
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
            'track': track.as_dict()
        })
    
    return JsonResponse({
        'status': 'error',
        'errors': dict(form.errors)
    })