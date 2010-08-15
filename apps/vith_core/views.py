import datetime
import logging

from django.conf import settings
from django.core.mail import mail_admins
from django.shortcuts import get_object_or_404, render_to_response

from core import json_view, JsonResponse
from vith_core.forms import UploadForm
from vith_core.models import Track, Vote, TrackNotified, Uploader
from vlc_rc import rc as vlc_rc


logger = logging.getLogger('vith_core')


DELETE_THRESHOLD = getattr(settings, 'DELETE_THRESHOLD', 1)
TWITTER_USERNAME = getattr(settings, 'TWITTER_USERNAME', None)
TWITTER_PASSWORD = getattr(settings, 'TWITTER_PASSWORD', None)


@json_view
def tracks(request):
    """
    Return list of all unplayed tracks in json format
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

    return data


def _now_playing_fallback(request):
    """
    Fallback when vlc now_playing got broken.
    
    Work by comparison track's play time and datetime.now()
    """
    now = datetime.datetime.now()
    try:
        curr_track = Track.objects.current_track(now)
    except Track.DoesNotExist:
        return [], None

    if curr_track:
        curr_pos = (now - curr_track.play_time).seconds

    if curr_pos > curr_track.length:
        data = []
    else:
        tdata = curr_track.as_dict()
        tdata['position'] = curr_pos
        data = [tdata]

    return data, curr_track


@json_view
def now_playing(request):
    """
    Returns current track and now playing position.
    
    Connects to steaming server and asks this parameters.
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
        data, current_track = _now_playing_fallback(request)

    if data:
        tn = TrackNotified.objects.get_or_create(track=current_track)[0]
        if not current_track.tracknotified.twitter_now:
            next_track = Track.objects.filter(play_time__gt=current_track.play_time)\
                .exclude(pk=current_track.pk).order_by('play_time')
            if next_track:
                next_track = next_track[0]

            try:
                twitter_notify_now_playing(current_track, next_track)
            except Exception, e:
                mail_admins('Error while Tweeting', e, fail_silently=True)

            tn.twitter_now = True
            tn.save()

    return data


def upload(request):
    """
    Uploads and enqueues track
    """
    if not request.method == 'POST':
        return render_to_response('upload.html', {'form': UploadForm()})
    files = {
        'track_file': request.FILES.get('track_file', None) or request.FILES.get('USERFILE', None)
    }
    form = UploadForm(request.POST, files)
    if form.is_valid():
        track = form.save(commit=False)
        track.length = 0
        if request.POST.get('twitter'):
            track.uploader = Uploader.objects.get_or_create(twitter=request.POST.get('twitter'))[0]
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
    votes_count = track.votes_count + 1
    result = 'ok'

    if votes_count >= DELETE_THRESHOLD:
        # Note: get url before deleting a track, or file is being destroyed
        # and url cannot be calculated.
        url = track.track_file.url
        track.delete()
        _delete_from_remote_playlist(url)
        result = 'delete'

    return {'result': result}


def twitter_notify_now_playing(track, next_track):
    if TWITTER_USERNAME and TWITTER_PASSWORD:
        import twitter
        api = twitter.Api(username=TWITTER_USERNAME, password=TWITTER_PASSWORD)

        status = 'Now playing "%s" (%d:%02d)' % (track.name[:30], track.length/60, track.length % 60)
        if track.uploader and track.uploader.twitter:
            status += ' by @%s' % track.uploader.twitter
        if next_track:
            status += ', next one "%s" (%d:%02d)' % (next_track.name[:30], next_track.length/60, track.length %60)
            if next_track.uploader and next_track.uploader.twitter:
                status += ' by @%s' % next_track.uploader.twitter
        api.PostUpdate(status)


def _delete_from_remote_playlist(url):
    iface = vlc_rc.VlcRC().get(vlc_rc.INTERFACE_TELNET)
    rc = iface(host=settings.VLC_TELNET_HOST, port=settings.VLC_TELNET_PORT)
    try:
        rc.connect(password=settings.VLC_TELNET_PASSWORD)
        rc.remove_input(url)
    except Exception, e:
        mail_admins('Error while connecting to Vlc telnet!', e, fail_silently=True)
    finally:
        rc.close()
