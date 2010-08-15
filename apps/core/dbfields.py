from io import BytesIO

from django.db import models
from django.db.models.fields.files import FieldFile
from django import forms
from django.core.files import File
from django.utils.translation import ugettext_lazy as _

from hachoir_parser import guessParser
from hachoir_metadata import extractMetadata
from hachoir_core.stream import InputIOStream


class AudioField(forms.FileField):
    default_error_messages = {
        'invalid_format': _(u"Upload a valid mp3-file. The file you uploaded was either not an mp3 or a corrupted mp3."),
    }

    def to_python(self, data):
        f = super(AudioField, self).to_python(data)
        if f is None:
            return None

        if hasattr(data, 'temporary_file_path'):
            file = open(data.temporary_file_path(), 'rb')
        else:
            if hasattr(data, 'read'):
                file = BytesIO(data.read())
            else:
                file = BytesIO(data['content'])

        try:            
            parser = guessParser(InputIOStream(file))

            if not (parser.validate() and parser.mime_type == u'audio/mpeg'):
                raise Exception
        except ImportError:
            raise
        except Exception: #not an mp3
            raise forms.ValidationError(self.error_messages['invalid_format'])
        if hasattr(f, 'seek') and callable(f.seek):
            f.seek(0)
        return f


class AudioFile(File):
    @property
    def _duration(self):
        """
        File duration in sec
        """
        if getattr(self, '_duration_cache', None):
            return self._duration_cache
        duration = extractMetadata(guessParser(\
            InputIOStream(self))).get('duration')
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

        super(AudioFileField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'form_class': AudioField}
        defaults.update(kwargs)
        return super(AudioFileField, self).formfield(**defaults)