from django.db import models


class AudioFileField(models.FileField):
    """
    Special field for audio files. Validates and preprocess files
    
    Supported options:
     * max_length files will be cutted if track length is greater than this value, seconds
     * normalize volume will be normalized to this value, dB
     * format -- files will be encoded in this format 
     * bitrate -- bitrate for encoding in prefered format
    """
    def __init__(self, max_length=None, normalize=None, format=None, bitrate=None, *args, **kwargs):
        self._max_length = max_length
        self._normalize = normalize
        self._format = format
        self._bitrate = bitrate
        super(AudioFileField, self).__init__(*args, **kwargs)
        
        