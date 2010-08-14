import os

from django.db import models
from django.conf import settings

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
    length = models.FloatField() #seconds
    name = models.CharField(max_length=250)
    uploader = models.ForeignKey(Uploader, null=True)
    
    def __unicode__(self):
        return '%(name)s, %(length)ss from %(uploader)s' % {'name': self.name, 'length': self.length,\
            'uploader': self.uploader.twitter}
