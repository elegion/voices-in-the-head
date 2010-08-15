import datetime
import os

from django.conf import settings
from django.core.mail import mail_admins
from django.db import models
from django.forms.models import model_to_dict
from vlc_rc import rc as vlc_rc

from core import datetime_to_timestamp
from core.dbfields import AudioFileField


MAX_LENGTH = getattr(settings, 'MAX_TRACK_LENGTH', 5 * 60) #dont used
NORMALIZE = getattr(settings, 'TRACK_NORMALIZE', -6) #dont used
NON_EDIT_TIME = getattr(settings, 'NON_EDIT_TIME', 300) #sec
DELETE_THRESHOLD = getattr(settings, 'DELETE_THRESHOLD', 1)
TWITTER_USERNAME = getattr(settings, 'TWITTER_USERNAME', None)
TWITTER_PASSWORD = getattr(settings, 'TWITTER_PASSWORD', None)


class Uploader(models.Model):
    """
    Man who uploaded track. Now we need twitter name only.
    """
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

    def get_by_url(self, url):
        filename = url.rpartition('/')[2]
        base_path = self.model._meta.get_field_by_name('track_file')[0].upload_to
        path = os.path.join(base_path, filename)
        try:
            return self.get_query_set().filter(track_file=path)[0]
        except IndexError:
            raise Track.DoesNotExist


class Track(models.Model):
    track_file = AudioFileField(upload_to=os.path.join(settings.WRITABLE_FOLDER, 'tracks'))
    length = models.PositiveSmallIntegerField() #seconds
    name = models.CharField(max_length=250)
    uploader = models.ForeignKey(Uploader, null=True)

    play_time = models.DateTimeField(null=True, blank=True)
    uploaded = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    votes_count = models.PositiveSmallIntegerField(default=0)

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
        if tdict['track_file']: # Dummy condition for tests, in real world track file is required and not null
            tdict['track_file'] = tdict['track_file'].url
        else:
            tdict['track_file'] = ''
        tdict['play_time'] = datetime_to_timestamp(tdict['play_time'])
        return tdict

    def can_vote(self):
        return self.play_time > datetime.datetime.now() + datetime.timedelta(seconds=NON_EDIT_TIME)

    def delete(self, *args, **kwargs):
        super(Track, self).delete(*args, **kwargs)
        # Ugly, slow, not thread-safe piece of code:
        for track in Track.objects.filter(play_time__gt=self.play_time):
            track.play_time = track.play_time - datetime.timedelta(seconds=self.length)
            track.save()

    def save(self, *args, **kwargs):
        """
        Calc playtime on track saving.
        
        If not tracks use datetime.now, else get last track and add it's duration
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


class TrackNotified(models.Model):
    """
    Remember ways which we notified people about this track
    """
    track = models.OneToOneField(Track)
    twitter_now = models.BooleanField(default=False)
    twitter_uploader = models.BooleanField(default=False)


class VoteManager(models.Manager):
    def can_vote(self, ip, track):
        if not ip:
            return False
        return self.get_query_set().filter(ip=ip, track=track).count() == 0


class Vote(models.Model):
    """
    People can vote agains track, if votes count (denormalized in Track) 
    is greater settings.DELETE_THRESHOLD track is removed
    """
    track = models.ForeignKey(Track)
    ip = models.IPAddressField()
    created = models.DateTimeField(auto_now_add=True)

    objects = VoteManager()

    class Meta:
        unique_together = ('track', 'ip')


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
        except Exception, e:
            mail_admins('Error while connecting to Vlc telnet!', e, fail_silently=True)
        finally:
            rc.close()


def update_votes_count(sender, instance, created, **kwargs):
    """
    Support votes count denormalization
    """
    if sender == Vote and instance:
        Track.objects.filter(pk=instance.track.pk).update(votes_count=models.F('votes_count') + 1)


models.signals.post_save.connect(update_remote_playlist, sender=Track)
models.signals.post_save.connect(update_votes_count, sender=Vote)
