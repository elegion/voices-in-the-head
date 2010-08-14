from django import forms

from vith_core.models import Track


class UploadForm(forms.ModelForm):

    class Meta:
        fields = ('track_file', 'name')
        model = Track
