from django import forms

from live.models import VideoRecording

class UploadForm(forms.ModelForm):
    class Meta:
        model = VideoRecording
        fields = ['file',]
