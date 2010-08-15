import datetime
import os

from django.conf import settings
from django.core.mail import mail_admins
from django.db import models
from django.forms.models import model_to_dict
from vlc_rc import rc as vlc_rc

from core import datetime_to_timestamp
from core.dbfields import AudioFileField


MAX_LENGTH = getattr(settings, 'MAX_TRACK_LENGTH', 5 * 60)
NORMALIZE = getattr(settings, 'TRACK_NORMALIZE', -6)


class Uploader(models.Model):
    twitter = models.CharField(max_length=250)

    def __unicode__(self):
        return '@%s' % self.twitter


class TrackManager(models.Manager):
    def current_track(self, time):
        try:
            return Track.objects.filter(play_time__lte=time) \
                                .order_by('-play_time')[0]
        except IndexError:
            raise Track.DoesNotExist


class Track(models.Model):
    track_file = AudioFileField(format='mp3', bitrate=196,
                                normalize=NORMALIZE,
                                max_length=MAX_LENGTH,
                                upload_to=os.path.join(settings.WRITABLE_FOLDER, 'tracks'))
    length = models.PositiveSmallIntegerField() #seconds
    name = models.CharField(max_length=250)
    uploader = models.ForeignKey(Uploader, null=True)

    play_time = models.DateTimeField(null=True, blank=True)
    uploaded = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    objects = TrackManager()

    class Meta(object):
        get_latest_by = 'play_time'
        ordering = ['play_time', 'uploaded']

    def __unicode__(self):
        return '%(name)s, %(length)ss from %(uploader)s' % {'name': self.name,
                                                            'length': self.length,
                                                            'uploader': self.uploader}

    def as_dict(self):
        tdict = model_to_dict(self)
        tdict['track_file'] = tdict['track_file'].url
        tdict['play_time'] = datetime_to_timestamp(tdict['play_time'])
        return tdict

    def save(self, *args, **kwargs):
        """
        Calc playtime on track saving.
        FIXME: No thread safe :)
        """
        if not self.length and self.track_file:
            self.length = self.track_file._duration

        if not self.play_time:
            try:
                last = Track.objects.latest('play_time')
                if last.play_time + datetime.timedelta(seconds=last.length) < datetime.datetime.now():
                    raise Track.DoesNotExist('Track already played')
                self.play_time = last.play_time + datetime.timedelta(seconds=last.length)
            except Track.DoesNotExist:
                self.play_time = datetime.datetime.now()

        super(Track, self).save(*args, **kwargs)


def update_remote_playlist(sender, instance, created, **kwargs):
    """
    Enque the track into the Vlc playlist via full URL.
    """
    if sender == Track and instance:
        iface = vlc_rc.VlcRC().get(vlc_rc.INTERFACE_TELNET)
        rc = iface(host=settings.VLC_TELNET_HOST,
                   port=settings.VLC_TELNET_PORT)
        try:
            rc.connect(password=settings.VLC_TELNET_PASSWORD)
            rc.add_input(instance.track_file.url)
            rc.close()
        except Exception, e:
            mail_admins('Error while connecting to Vlc telnet!', e, fail_silently=True)


models.signals.post_save.connect(update_remote_playlist, sender=Track)
