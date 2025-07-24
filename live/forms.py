from django import forms
import datetime, pytz
from django.utils import timezone
from live.models import VideoCamera, Show
from users.models import Profile
from translate.translate import translate

class CameraForm(forms.ModelForm):
    timestamp = forms.CharField(required=True, min_length=1)
    confirmation_id = forms.CharField(widget=forms.HiddenInput())
    def __init__(self, *args, **kwargs):
        super(CameraForm, self).__init__(*args, **kwargs)
    class Meta:
        model = VideoCamera
        fields = ('frame',)

WIDTH_CHOICES = [['320','320x240'],['640','640x480'],['720', '720x640'],['1280','1280x720'],['1920', '1920x1080'],['2560','2560x2048'],['4096','4096x2160']]

MIME_CHOICES = [['mp4; codecs="avc1.42E01E, mp4a.40.2"','mp4; codecs="avc1.42E01E, mp4a.40.2"'], ['webm; codecs="vp9,opus"', 'webm; codecs="vp9,opus"'], ['webm; codecs="vp8,opus"', 'webm; codecs="vp8,opus"'], ['webm; codecs="vp9,vorbis"', 'webm; codecs="vp9,vorbis"'], ['webm; codecs="vp8,vorbis"', 'webm; codecs="vp8,vorbis"']]

PRIVACY_CHOICES = [['public','public'], ['unlisted','unlisted'], ['private','private']]

MICROPHONE_CHOICES = [['default', 'default'], ['echo cancellation', 'echo cancellation'], ['communication', 'communication']]

CATEGORY_CHOICES = [
    ["2", "Autos & Vehicles"],
    ["23", "Comedy"],
    ["27", "Education"],
    ["24", "Entertainment"],
    ["1", "Film & Animation"],
    ["20", "Gaming"],
    ["26", "Howto & Style"],
    ["10", "Music"],
    ["25", "News & Politics"],
    ["29", "Nonprofits & Activism"],
    ["22", "People & Blogs"],
    ["15", "Pets & Animals"],
    ["28", "Science & Technology"],
    ["17", "Sports"],
    ["19", "Travel & Events"],
]

VAD_CHOICES = [
    ['0', '0 - Least filtering, more non speech'],
    ['1', '1 - Partial filtering'],
    ['2', '2 - More filtering, default'],
    ['3', '3 - Most filtering, less non speech'],
]

class NameCameraForm(forms.ModelForm):
    name = forms.CharField(required=True, min_length=1)
    mimetype = forms.CharField(widget=forms.Select(choices=MIME_CHOICES))
    width = forms.CharField(widget=forms.Select(choices=WIDTH_CHOICES))
    privacy_status = forms.CharField(widget=forms.Select(choices=PRIVACY_CHOICES))
    microphone = forms.CharField(widget=forms.Select(choices=MICROPHONE_CHOICES))
    category = forms.CharField(widget=forms.Select(choices=CATEGORY_CHOICES))
#    vad_mode = forms.CharField(widget=forms.Select(choices=VAD_CHOICES))
    def __init__(self, *args, **kwargs):
        super(NameCameraForm, self).__init__(*args, **kwargs)
#        self.fields['echo_cancellation'].initial = self.instance.echo_cancellation
        self.fields['use_websocket'].initial = self.instance.use_websocket
        self.fields['compress_video'].initial = self.instance.use_websocket
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        for c in MICROPHONE_CHOICES:
            c[1] = translate(r, c[1], src='en').capitalize()
        self.fields['microphone'].widget = forms.Select(choices=MICROPHONE_CHOICES)
        for c in PRIVACY_CHOICES:
            c[1] = translate(r, c[1], src='en').capitalize()
        self.fields['privacy_status'].widget = forms.Select(choices=PRIVACY_CHOICES)
        for c in CATEGORY_CHOICES:
            c[1] = translate(r, c[1], src='en').capitalize()
        self.fields['category'].widget = forms.Select(choices=CATEGORY_CHOICES)
#        for c in VAD_CHOICES:
#            c[1] = translate(r, c[1], src='en').capitalize()
#        self.fields['vad_mode'].widget = forms.Select(choices=VAD_CHOICES)
#        self.fields['vad_mode'].label = translate(r, 'VAD speech detection mode', src='en')
        self.fields['name'].label = translate(r, 'Camera name', src='en')
        self.fields['microphone'].label = translate(r, 'Configure microphone', src='en')
        self.fields['speech_only'].label = translate(r, 'Require speech for recording?', src='en')
        self.fields['mimetype'].label = translate(r, 'Camera mimetype', src='en')
        self.fields['width'].label = translate(r, 'Video resolution', src='en')
        self.fields['use_websocket'].label = translate(r, 'Use a websocket?', src='en')
        self.fields['compress_video'].label = translate(r, 'Enable zip compression?', src='en')
        self.fields['adjust_pitch'].label = translate(r, 'Adjust video pitch as specified in vendor settings?', src='en')
        self.fields['animate_video'].label = translate(r, 'Animate the video with AnimeGAN? (GPU required)', src='en')
        self.fields['short_mode'].label = translate(r, 'Enable short mode for <1min videos?', src='en')
        self.fields['embed_logo'].label = translate(r, 'Embed the logo?', src='en')
        self.fields['censor_video'].label = translate(r, 'Censor video where appropriate?', src='en')
        self.fields['live'].label = translate(r, 'Camera on?', src='en')
        self.fields['recording'].label = translate(r, 'Recording on?', src='en')
        self.fields['upload'].label = translate(r, 'Upload?', src='en')
        self.fields['privacy_status'].label = translate(r, 'Privacy status', src='en')
        self.fields['title'].label = translate(r, 'Video title', src='en')
        self.fields['category'].label = translate(r, 'Video category', src='en')
        self.fields['description'].label = translate(r, 'Video description', src='en')
        self.fields['tags'].label = translate(r, 'Video tags', src='en')
        self.fields['video_length_minutes'].label = translate(r, 'Video length (in minutes)', src='en')
        self.fields['bucket'].label = translate(r, 'Upload the video to the media bucket?', src='en')
        self.fields['broadcast'].label = translate(r, 'Broadcast the video?', src='en')

    def clean_title(self):
        data = self.cleaned_data['title']
        max_length = 100
        if len(data) > max_length:
            data = data[:max_length-3].rsplit(' ', 1)[0] + '...' # Truncate the text
        return data

    class Meta:
        model = VideoCamera
        fields = ('upload', 'title', 'category', 'privacy_status', 'description', 'tags', 'video_length_minutes', 'broadcast', 'name', 'mimetype', 'width', 'microphone', 'use_websocket', 'compress_video', 'censor_video', 'adjust_pitch', 'bucket', 'animate_video', 'short_mode', 'speech_only', 'embed_logo', 'live', 'recording')

# 'vad_mode',

class LiveShowForm(forms.ModelForm):
    choice = forms.CharField()
    def __init__(self, *args, **kwargs):
        super(LiveShowForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['choice'].label = translate(get_current_request(), 'Choose a time for the private show')
        user = self.instance.user
        CHOICES = list()
        for x in range(7):
            date = timezone.now() + datetime.timedelta(hours=24*x)
            for y in range(settings.LIVE_SCHEDULE_HOURS):
                time = datetime.time(settings.LIVE_SCHEDULE_BEGINS + y, 0)
                dt = datetime.datetime.combine(date, time).astimezone(pytz.timezone(settings.TIME_ZONE))
                if dt > timezone.now() + datetime.timedelta(minutes=60) and not Show.objects.filter(start__gte=dt, end__lte=dt + datetime.timedelta(settings.LIVE_SHOW_LENGTH_MINUTES)).first():
                    CHOICES.append((dt.strftime('%m/%d/%Y %H:%M:%S'), translate(get_current_request(), 'On {}'.format(dt.strftime('%B %d, %Y at %-I:%M %p')))))
        self.fields['choice'].widget = forms.Select(choices=CHOICES)

    class Meta:
        model = Profile
        fields = ['choice']

class ChooseCameraForm(forms.Form):
    choice = forms.CharField()
    def __init__(self, *args, **kwargs):
        super(ChooseCameraForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['choice'].label = translate(r, 'Choose a camera to begin', src='en')
        from feed.middleware import get_current_user
        user = get_current_user()
        cams = VideoCamera.objects.filter(user=user).order_by('-last_frame')
        cameras = []
        for camera in cams:
            if len(camera.name) < 32:
                cameras = cameras + [camera]
        CHOICES = list()
        for camera in cameras:
            CHOICES.append((camera.name,camera.name))
        self.fields['choice'].widget = forms.Select(choices=CHOICES)
        self.fields['choice'].initial = [cams.first().name]
