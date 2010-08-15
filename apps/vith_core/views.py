import datetime

from django.conf import settings
from django.core.mail import mail_admins

from core import JsonResponse
from vith_core.forms import UploadForm
from vith_core.models import Track
from vlc_rc import rc as vlc_rc


def tracks(request):
    """
    Return list of all uploaded tracks in json format
    """
    tracks = Track.objects.filter(play_time__gte=datetime.datetime.now())

    return JsonResponse([t.as_dict() for t in tracks])


def _now_playing_fallback(request):
    """
    Fallback when vlc got broken.
    """
    now = datetime.datetime.now()
    try:
        curr_track = Track.objects.current_track(now)
    except Track.DoesNotExist:
        return JsonResponse('')

    if curr_track:
        curr_pos = (now - curr_track.play_time).seconds

    if curr_pos > curr_track.length:
        data = []
    else:
        tdata = curr_track.as_dict()
        tdata['position'] = curr_pos
        data = [tdata]

    return JsonResponse(data)


def now_playing(request):
    """
    Returns current track and now playing position.
    """
    data = []

    iface = vlc_rc.VlcRC().get(vlc_rc.INTERFACE_TELNET)
    rc = iface(host=settings.VLC_TELNET_HOST, port=settings.VLC_TELNET_PORT)
    try:
        rc.connect(password=settings.VLC_TELNET_PASSWORD)
        url, percentage = rc.now_playing()
    except Exception, e:
        mail_admins('Error while connecting to Vlc telnet!', e, fail_silently=True)
    else:
        if url and percentage is not None:
            current_track = Track.objects.get_by_url(url)
            if current_track:
                data = [current_track.as_dict()]
                data[0]['position'] = int(current_track.length * percentage)
    finally:
        rc.close()

    if not data:
        return _now_playing_fallback(request)

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
