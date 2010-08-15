import datetime
import logging

from django.conf import settings
from django.shortcuts import get_object_or_404

from core import json_view, JsonResponse
from vith_core.forms import UploadForm
from vith_core.models import Track, Vote


logger = logging.getLogger('vith_core')


DELETE_THRESHOLD = getattr(settings, 'DELETE_THRESHOLD', 5)


def tracks(request):
    """
    Return list of all uploaded tracks in json format
    """
    tracks = Track.objects.filter(play_time__gte=datetime.datetime.now())
    
    data = []
    for track in tracks:
        tdict = track.as_dict()
        ip = request.META.get('REMOTE_ADDR', None)
        tdict['can_vote'] = track.can_vote()
        if Vote.objects.can_vote(ip, track):
            tdict['voted'] = ''
        else:
            tdict['voted'] = 'voted'
        data.append(tdict)

    return JsonResponse(data)


def now_playing(request):
    """
    Returns current track and now playing position
    FIXME synchronize with audio streamer
    """
    now = datetime.datetime.now()
    try:
        curr_track = Track.objects.current_track(now)
    except Track.DoesNotExist:
        return JsonResponse([])

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
        return JsonResponse({'status': 'ok',
                             'track': track.as_dict()})

    return JsonResponse({'status': 'error',
                         'errors': dict(form.errors)})


@json_view
def vote(request):
    """
    Vote for deletion of track
    """
    track = get_object_or_404(Track, pk=request.POST.get('track_id'))
    if not track.can_vote():
        raise Exception('Can\'t vote for coming soon tracks.')
    
    ip = request.META.get('REMOTE_ADDR', None)
    
    if not Vote.objects.can_vote(ip, track):
        raise Exception('You already voted from this ip for this track.')
    
    vote = Vote.objects.create(track=track, ip=ip)
    result = 'ok'

    if track.votes_count >= DELETE_THRESHOLD:
        track.delete()
        result = 'delete'
        
    return {'result': result}