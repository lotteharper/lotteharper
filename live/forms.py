from django import forms
import datetime, pytz
from django.utils import timezone
from live.models import VideoCamera, VideoFrame, Show
from users.models import Profile
from translate.translate import translate

class CameraForm(forms.ModelForm):
    timestamp = forms.CharField(required=True, min_length=1)
    confirmation_id = forms.CharField(widget=forms.HiddenInput())
    def __init__(self, *args, **kwargs):
        super(CameraForm, self).__init__(*args, **kwargs)
    class Meta:
        model = VideoFrame
        fields = ('frame',)

WIDTH_CHOICES = [['160x90','160x90'],['176x144','176x144'],['352x288','352x288'],['320x180','320x180'],['432x240','432x240'],['640x360','640x360'],['800x448','800x448'],['800x600','800x600'],['864x480','864x480'],['960x720','960x720'],['1024x574','1024x576'],['1280x720','1280x720'],['1600x896','1600x896'],['320x240','320x240'],['640x480','640x480'],['720x640', '720x640'],['1280x720','1280x720'],['1600x896','1600x896'],['1920x1080', '1920x1080'],['2304x1296','2304x1296'],['2304x1536','2304x1356'],['2400x1080', '2400x1080'],['2560x1440','2560x1440 (Quad HD or 1440P)'],['2560x2040','2560x2048'],['2840x2160','2840x2160 (4K UHD)'],['3840x2160', '3840x2160'],['4096x2160','4096x2160'],['4160x3120','4160x3120'],['7680x4320','7680x4320 (8K)']]

MIME_CHOICES = [['mp4; codecs="avc1.42E01E, mp4a.40.2"','mp4; codecs="avc1.42E01E, mp4a.40.2"'],['webm; codecs="vp9,opus"','webm; codecs="vp9,opus"'],['webm; codecs="vp8,opus"', 'webm; codecs="vp8,opus"'],['webm; codecs="vp9,vorbis"', 'webm; codecs="vp9,vorbis"'],['webm; codecs="vp8,vorbis"','webm; codecs="vp8,vorbis"']]

PRIVACY_CHOICES = [['public','public'],['unlisted','unlisted'],['private','private']]

MICROPHONE_CHOICES = [['default','default'],['echo cancellation','echo cancellation'],['communication','communication']]

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

ROTATION_CHOICES = [
    ['0','0° Horizontal'],
    ['1','90° Clockwise'],
    ['2','180° (Upside down)'],
    ['3','90° Counterclockwise (270°)'],
]

class NameCameraForm(forms.ModelForm):
    name = forms.CharField(required=True, min_length=1)
    mimetype = forms.CharField(widget=forms.Select(choices=MIME_CHOICES))
    width = forms.CharField(widget=forms.Select(choices=WIDTH_CHOICES))
    privacy_status = forms.CharField(widget=forms.Select(choices=PRIVACY_CHOICES))
    microphone = forms.CharField(widget=forms.Select(choices=MICROPHONE_CHOICES))
    category = forms.CharField(widget=forms.Select(choices=CATEGORY_CHOICES))
    rotation = forms.CharField(widget=forms.Select(choices=ROTATION_CHOICES))
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 7}))
    tags = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
#    vad_mode = forms.CharField(widget=forms.Select(choices=VAD_CHOICES))
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        from translate.translate import translate
        from django.conf import settings
        from django.utils import timezone
        import datetime
        super(NameCameraForm, self).__init__(*args, **kwargs)
#        self.fields['echo_cancellation'].initial = self.instance.echo_cancellation
        self.fields['use_websocket'].initial = self.instance.use_websocket
        self.fields['compress_video'].initial = self.instance.use_websocket
        from feed.middleware import get_current_request
        r = get_current_request()
        pl_email = user.email
        if self.fields['upload_email'].initial != user.email:
            pl_email = self.fields['upload_email'].initial
        playlist_choices = [['', translate(r, 'None', src='en')]]
        playlists = user.youtube_playlists.all()
        c = VideoCamera.objects.filter(name=self.instance.name, user=user).order_by('-last_frame').first()
        if c.last_updated_playlists < timezone.now() - datetime.timedelta(minutes=15):
            from recordings.youtube import list_youtube_playlists
            try:
                playlists = list_youtube_playlists(user, email=pl_email)
                if playlists:
                    for playlist, name in playlists:
                        playlist_choices += [[playlist, name]]
                        if not user.youtube_playlists.filter(youtube_id=playlist).first():
                            from live.models import UserPlaylist
                            UserPlaylist.objects.create(youtube_id=playlist, youtube_name=name, user=user)
                        elif user.youtube_playlists.filter(youtube_id=playlist).first() and not user.youtube_playlists.filter(youtube_id=playlist).first().youtube_name == name:
                            p = user.youtube_playlists.filter(youtube_id=playlist).first()
                            p.youtube_name = name
                            p.save()
                    c.last_updated_playlists = timezone.now()
                    c.save()
            except:
                import traceback
                print(traceback.format_exc())
                for playlist in user.youtube_playlists.all():
                    playlist_choices += [[playlist.youtube_id, playlist.youtube_name]]
        else:
            for playlist in user.youtube_playlists.all():
                playlist_choices += [[playlist.youtube_id, playlist.youtube_name]]
        email_choices = [[user.email, user.email]]
        import os
        for email in user.email_addresses.order_by('created_at'):
            if os.path.exists(os.path.join(settings.BASE_DIR, f"keys/{user.id}/", email.email)):
                email_choices += [[email.email, email.email]]
        self.fields['upload_playlist'].widget = forms.Select(choices=playlist_choices)
        self.fields['upload_playlist'].required = False
        self.fields['upload_email'].widget = forms.Select(choices=email_choices)
        self.fields['upload_email'].label = translate(r, 'Email for upload', src='en')
        self.fields['upload_playlist'].label = translate(r, 'Playlist for upload', src='en')
        self.fields['podcast_show_id'].label = translate(r, 'Podcast show for upload', src='en')
        podcast_show_choices = [[None, translate(r, 'No podcast', src='en')]]
        for podcast in user.transistorfm_podcasts.all():
            podcast_show_choices += [[podcast.transistorfm_id, podcast.title]]
        self.fields['podcast_show_id'].widget = forms.Select(choices=podcast_show_choices)
        self.fields['podcast_show_id'].required = False
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
        self.fields['broadcast_youtube'].label = translate(r, 'Broadcast stream to YouTube?', src='en')
        self.fields['recording'].label = translate(r, 'Recording on?', src='en')
        self.fields['upload'].label = translate(r, 'Upload to share video?', src='en')
        self.fields['privacy_status'].label = translate(r, 'Privacy status', src='en')
        self.fields['title'].label = translate(r, 'Video title', src='en')
        self.fields['category'].label = translate(r, 'Video category', src='en')
        self.fields['description'].label = translate(r, 'Video description', src='en')
        self.fields['tags'].label = translate(r, 'Video tags', src='en')
        self.fields['rotation'].label = translate(r, 'Default rotation', src='en')
        self.fields['video_length_minutes'].label = translate(r, 'Video length (in minutes)', src='en')
        self.fields['bucket'].label = translate(r, 'Upload the video to the media bucket?', src='en')
        self.fields['broadcast'].label = translate(r, 'Broadcast the video?', src='en')
        self.fields['framerate'].label = translate(r, 'Video framerate', src='en')
        self.fields['mirror'].label = translate(r, 'Mirror camera?', src='en')
        self.fields['censor_audio'].label = translate(r, 'Censor audio where appropriate?', src='en')
        self.fields['prompt'].label = translate(r, 'Enter a prompt for the upload', src='en')
        self.fields['podcast'].label = translate(r, 'Upload podcast?', src='en')
        self.fields['server_moderation'].label = translate(r, 'Enable server moderation?', src='en')
        from verify.tests import minor_identity_verified
        if not minor_identity_verified(user):
            self.fields['censor_video'].initial = True
            self.fields['censor_audio'].initial = True
            self.fields['censor_video'].widget = forms.HiddenInput()
            self.fields['censor_audio'].widget = forms.HiddenInput()

    def clean_title(self):
        data = self.cleaned_data['title']
        max_length = 100
        if len(data) > max_length:
            data = data[:max_length-3].rsplit(' ', 1)[0] + '...' # Truncate the text
        from better_profanity import profanity
        if profanity.contains_profanity(data):
            data = profanity.censor(data)
        return data

    def clean_name(self):
        data = self.cleaned_data['name']
        max_length = 100
        if len(data) > max_length:
            data = data[:max_length]
        return data

    def clean_tags(self):
        data = self.cleaned_data['tags']
#        data = data.replace(', ', ',').strip()
#        data = data.replace(' ,', ',')
        split = data.split(',')
        ov_split = self.instance.tags_overflow.split(',')
        tags = []
        overflow_tags = []
        max_length = 480
        length = 0
        for tag in split:
            if not tag.strip() in tags:
                if length + len(tag.strip()) < max_length:
                    tags += [tag.strip()]
                    length += len(tag.strip()) + 1
                elif not tag.strip() in ov_split:
                    overflow_tags += [tag.strip()]
        data = ','.join(tags)
#        if len(data) - data.count(',') > max_length:
#            op_data = data[:max_length + data.count(',')]
#        if data[max_length + data.count(','):]:
#            self.instance.tags_overflow = 
# data[max_length + data.count(','):]
        if overflow_tags:
            self.instance.tags_overflow += ',' + ','.join(overflow_tags)
            self.instance.save()
        return data

    def clean_description(self):
        data = self.cleaned_data['description']
        max_length = 2000
        if len(data) > max_length:
            data = data[:max_length-3].rsplit(' ', 1)[0] + '...' # Truncate the text
        return data

    class Meta:
        model = VideoCamera
        fields = ('upload', 'broadcast', 'podcast', 'broadcast_youtube', 'title', 'category', 'privacy_status', 'upload_email', 'upload_playlist', 'podcast_show_id', 'description', 'tags', 'prompt', 'video_length_minutes', 'name', 'mimetype', 'rotation', 'width', 'framerate', 'microphone', 'use_websocket', 'compress_video', 'censor_video', 'server_moderation', 'censor_audio', 'adjust_pitch', 'mirror', 'bucket', 'animate_video', 'short_mode', 'speech_only', 'embed_logo', 'live', 'recording')

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
        cams = VideoCamera.objects.filter(user=user).order_by('last_frame')
        cameras = []
        for camera in cams:
            if len(camera.name) < 32:
                cameras = cameras + [camera]
        CHOICES = list()
        for camera in cameras:
            CHOICES.append((camera.name,camera.name))
        self.fields['choice'].widget = forms.Select(choices=CHOICES)
        self.fields['choice'].initial = [cams.first().name]
