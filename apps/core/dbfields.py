from django.db import models
from django.db.models.fields.files import FieldFile
from django.core.files import File
from django.core import signals

from hachoir_parser import createParser
from hachoir_metadata import extractMetadata


class AudioFile(File):
    @property
    def _duration(self):
        """
        File duration in sec
        """
        if getattr(self, '_duration_cache', None):
            return self._duration_cache
        duration = extractMetadata(createParser(self.path)).get('duration')
        if not duration:
            raise Exception(u'Not an audio file')
        else:
            duration = duration.seconds
        self._duration_cache = duration
        return duration


class AudioFieldFile(AudioFile, FieldFile):
    pass
    
    
class AudioFileField(models.FileField):
    """
    Special field for audio files. Validates and preprocess files. Calcs duration
    
    Supported options (not supported :D
     * max_length files will be cutted if track length is greater than this value, seconds
     * normalize volume will be normalized to this value, dB
     * format -- files will be encoded in this format 
     * bitrate -- bitrate for encoding in prefered format
    """
    attr_class = AudioFieldFile
    
    def __init__(self, max_length=None, normalize=None, format=None, bitrate=None, *args, **kwargs):
        self._max_length = max_length
        self._normalize = normalize
        self._format = format
        self._bitrate = bitrate

        self.duration_field = None
        
        super(AudioFileField, self).__init__(*args, **kwargs)
    #     
    # def contribute_to_class(self, cls, name):
    #     super(ImageField, self).contribute_to_class(cls, name)
    #     signals.post_init.connect(self.update_duration, sender=cls)
    # 
    # def update_duration(self, instance, force=False, *args, **kwargs):
    #     """
    #     Updates field's width and height fields, if defined.
    # 
    #     This method is hooked up to model's post_init signal to update
    #     dimensions after instantiating a model instance.  However, dimensions
    #     won't be updated if the dimensions fields are already populated.  This
    #     avoids unnecessary recalculation when loading an object from the
    #     database.
    # 
    #     Dimensions can be forced to update with force=True, which is how
    #     ImageFileDescriptor.__set__ calls this method.
    #     """
    #     # Nothing to update if the field doesn't have have dimension fields.
    #     # has_dimension_fields = self.width_field or self.height_field
    #     # if not has_dimension_fields:
    #     #     return
    #     if not self.duration_field:
    #         return
    # 
    #     # getattr will call the ImageFileDescriptor's __get__ method, which
    #     # coerces the assigned value into an instance of self.attr_class
    #     # (ImageFieldFile in this case).
    #     file = getattr(instance, self.attname)
    # 
    #     # Nothing to update if we have no file and not being forced to update.
    #     if not file and not force:
    #         return
    # 
    #     # dimension_fields_filled = not(
    #     #     (self.width_field and not getattr(instance, self.width_field))
    #     #     or (self.height_field and not getattr(instance, self.height_field))
    #     # )
    #     # When both dimension fields have values, we are most likely loading
    #     # data from the database or updating an image field that already had
    #     # an image stored.  In the first case, we don't want to update the
    #     # dimension fields because we are already getting their values from the
    #     # database.  In the second case, we do want to update the dimensions
    #     # fields and will skip this return because force will be True since we
    #     # were called from ImageFileDescriptor.__set__.
    #     if not(self.duration_field and not getattr(instance, self.duration_field)) and not force:
    #         return
    # 
    #     # file should be an instance of ImageFieldFile or should be None.
    #     if file:
    #         duration = file.duration
    #     else:
    #         duration = None
    # 
    #     if self.duration_field:
    #         setattr(instance, self.duration_field, duration)
