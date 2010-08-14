import datetime, os

from django.db import models
from django.forms.models import model_to_dict
from django.conf import settings


from core import datetime_to_timestamp
from core.dbfields import AudioFileField


MAX_LENGTH = getattr(settings, 'MAX_TRACK_LENGTH', 5*60)
NORMALIZE = getattr(settings, 'TRACK_NORMALIZE', -6)


class Uploader(models.Model):
    twitter = models.CharField(max_length=250)
    
    def __unicode__(self):
        return '@%s' % self.twitter
    
    
class Track(models.Model):
    track_file = AudioFileField(format='mp3', bitrate=196, normalize=NORMALIZE, max_length=MAX_LENGTH,
        upload_to=os.path.join(settings.WRITABLE_FOLDER, 'tracks'))
    length = models.PositiveSmallIntegerField() #seconds
    name = models.CharField(max_length=250)
    uploader = models.ForeignKey(Uploader, null=True)
    
    play_time = models.DateTimeField(null=True, blank=True)
    uploaded = models.DateTimeField(auto_now_add=True)

    def as_dict(self):
        tdict = model_to_dict(self)
        tdict['track_file'] = tdict['track_file'].name
        tdict['play_time'] = datetime_to_timestamp(tdict['play_time'])
        return tdict

    def __unicode__(self):
        return '%(name)s, %(length)ss from %(uploader)s' % {'name': self.name, 'length': self.length,\
            'uploader': self.uploader.twitter}

    def save(self, *args, **kwargs):
        """
        Calc playtime on track saving.
        FIXME: No thread safe :)
        """
        if not self.play_time:
            try:
                last = Track.objects.latest('play_time')
                if last.play_time + datetime.timedelta(seconds=last.length) < datetime.datetime.now():
                    raise Track.DoesNotExist('Track already played')
                self.play_time = last.play_time + datetime.timedelta(seconds=last.length)
            except Track.DoesNotExist:
                self.play_time = datetime.datetime.now()
            
        super(Track, self).save(*args, **kwargs)
