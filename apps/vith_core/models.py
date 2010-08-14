import os
import datetime

from django.db import models
from django.conf import settings

from core.dbfields import AudioFileField


MAX_LENGTH = getattr(settings, 'MAX_TRACK_LENGTH', 5*60)
NORMALIZE = getattr(settings, 'TRACK_NORMALIZE', -6)


class Uploader(models.Model):
    twitter = models.CharField(max_length=250, null=True, blank=True)
    
    def __unicode__(self):
        return '@%s' % self.twitter
    
    
class Track(models.Model):
    track_file = AudioFileField(null=True, blank=True, format='mp3', bitrate=196, normalize=NORMALIZE,\
        max_length=MAX_LENGTH, upload_to=os.path.join(settings.WRITABLE_FOLDER, 'tracks'))
    length = models.PositiveSmallIntegerField() #seconds
    name = models.CharField(max_length=250)
    uploader = models.ForeignKey(Uploader)

    play_time = models.DateTimeField(null=True, blank=True)
    uploaded = models.DateTimeField(auto_now_add=True)
        
    class Meta(object):
        get_latest_by = 'play_time'
        ordering = ['play_time', 'uploaded']
        
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
                last = Track.objects.latest()
                self.play_time = last.play_time + datetime.timedelta(seconds=last.length)
            except:
                self.play_time = datetime.datetime.now()
            
        super(Track, self).save(*args, **kwargs)
        
    