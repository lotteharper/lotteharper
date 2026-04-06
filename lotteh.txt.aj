
    resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
  else:
    # When it is not obtained by video stream, the entire file is returned by generator to save memory
    from wsgiref.util import FileWrapper
    resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type=content_type)
    resp['Content-Length'] = str(size)
  resp['Accept-Ranges'] = 'bytes'
  return resp

#@login_required
#@user_passes_test(identity_verified, login_url='/verify/', redirect_field_name='next')
@csrf_exempt
def video_frame(request, username):
  from users.models import Profile
  from .models import VideoCamera
  from django.contrib.auth.models import User
  profile = get_object_or_404(Profile, name=username, identity_verified=True, vendor=True)
  cameras = VideoCamera.objects.filter(user=profile.user, name=request.GET.get('camera'))
  model = User.objects.get(profile__name=username)
#  if request.user != model and (not is_live_show(request, model) or (not model in request.user.profile.subscriptions.all())):
#    messages.warning(request, 'You need to follow {} before you can see their interactive feed.'.format(username))
#    return redirect(reverse('feed:follow', kwargs={'username': username}))
  c = cameras.first()
  init = int(request.GET.get('index')) - (camera.frames.count() - camera.frame_count)
  frame = c.frames.filter(processed=True, public=True if profile.user != request.user else None).order_by('time_captured')[int(request.GET.get('index')) if not camera.default else -1]
  filename = frame.name.split('/')[-1]
  from django.http import HttpResponse
  return HttpResponse(reverse('live:stream-video', kwargs={'filename': filename}))

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@csrf_exempt
def stream_video(request, filename):
  import os, re
  from django.http import StreamingHttpResponse
  from django.conf import settings
  path = os.path.join(settings.BASE_DIR,'media/live/files/', filename)
  """Responding to the video file by streaming media"""
  range_header = request.META.get('HTTP_RANGE', '').strip()
  range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
  range_match = range_re.match(range_header)
  size = os.path.getsize(path)
  content_type, encoding = mimetypes.guess_type(path)
  content_type = content_type or 'application/octet-stream'
  if range_match:
    first_byte, last_byte = range_match.groups()
    first_byte = int(first_byte) if first_byte else 0
    last_byte = first_byte + 1024 * 1024 * 8    # 8M Each piece, the maximum volume of the response body
    if last_byte >= size:
      last_byte = size - 1
    length = last_byte - first_byte + 1
    resp = StreamingHttpResponse(file_iterator(path, offset=first_byte, length=length), status=206, content_type=content_type)
    resp['Content-Length'] = str(length)
    resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
  else:
    from wsgiref.util import FileWrapper
    # When it is not obtained by video stream, the entire file is returned by generator to save memory
    resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type=content_type)
    resp['Content-Length'] = str(size)
  resp['Accept-Ranges'] = 'bytes'
  return resp

def remote_api(request):
    from .models import VideoCamera
    from django.utils import timezone
    from django.http import HttpResponse
    from django.core.exceptions import PermissionDenied
    camera = None
    if request.user.is_authenticated:
        camera, created = VideoCamera.objects.get_or_create(user=request.user, name=request.GET.get('camera'))
    else:
        camera = VideoCamera.objects.get(key=request.GET.get('key', None))
        camera.updated = timezone.now()
        camera.save()
    if not identity_verified(camera.user): raise PermissionDenied()
    return HttpResponse('r' if camera.live else 'x')

LIVE_UPDATE_SECONDS = 1

@csrf_exempt
@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def remote(request):
    from .models import VideoCamera
    import datetime
    from django.utils import timezone
    from django.http import HttpResponse
    cameras = VideoCamera.objects.filter(user=request.user, name=request.GET.get('camera'))
    if cameras.count() < 1 and request.user.is_authenticated and request.user.profile.vendor:
        cameras = VideoCamera.objects.filter(user=request.user, name=request.GET.get('camera'))
    camera = cameras.first()
    if request.method == 'POST':
        if not camera.updated > timezone.now() - datetime.timedelta(seconds=LIVE_UPDATE_SECONDS):
            camera.live = not camera.live
            camera.updated = timezone.now()
            camera.save()
    return HttpResponse('<i class="bi bi-toggle-on"></i>' if camera.live else '<i class="bi bi-toggle-off"></i>')

@csrf_exempt
def mute(request):
    from .models import VideoCamera
    from django.http import HttpResponse
    from django.utils import timezone
    import datetime
    cameras = VideoCamera.objects.filter(user__profile__name=request.GET.get('user', None), name=request.GET.get('camera'), key=request.GET.get('key', ''))
    if cameras.count() < 1 and request.user.is_authenticated and request.user.profile.vendor:
        cameras = VideoCamera.objects.filter(user=request.user, name=request.GET.get('camera'))
    camera = cameras.first()
    if request.method == 'POST':
        if not camera.updated > timezone.now() - datetime.timedelta(seconds=LIVE_UPDATE_SECONDS):
            camera.muted = not camera.muted
            camera.updated = timezone.now()
            camera.save()
    return HttpResponse('<i class="bi bi-mic-fill"></i>' if camera.muted else '<i class="bi bi-mic-mute-fill"></i>')

@csrf_exempt
@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def record_remote(request):
    from .models import VideoCamera
    import datetime
    from django.utils import timezone
    cameras = VideoCamera.objects.filter(user=request.user, name=request.GET.get('camera'))
    if cameras.count() < 1 and request.user.is_authenticated and request.user.profile.vendor:
        cameras = VideoCamera.objects.filter(user=request.user, name=request.GET.get('camera'))
    camera = cameras.first()
    if request.method == 'POST':
        if not camera.updated > timezone.now() - datetime.timedelta(seconds=LIVE_UPDATE_SECONDS):
            camera.recording = not camera.recording
            camera.updated = timezone.now()
            camera.save()
    from django.http import HttpResponse
    print('Toggling camera recording status.')
    from django.shortcuts import render
    return HttpResponse('<i class="bi bi-toggle-on"></i>' if camera.recording else '<i class="bi bi-toggle-off"></i>')

def confirm(request, id):
    from django.http import HttpResponse
    from .models import VideoFrame
    from django.utils import timezone
    import datetime
    return HttpResponse('y' if VideoFrame.objects.filter(confirmation_id=id, time_captured__gte=timezone.now() - datetime.timedelta(minutes=5)).count() > 0 or VideoCamera.objects.filter(confirmation_id=id, time_captured__gte=timezone.now() - datetime.timedelta(minutes=5)).count() > 0 else 'n')


@never_cache
@csrf_exempt
@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def golivevideo(request):
    from .models import VideoCamera, VideoFrame, VideoRecording
    from django.core.exceptions import PermissionDenied
    from .forms import CameraForm
    import datetime
    import pytz
    from django.utils import timezone
    from django.http import HttpResponse
    from django.conf import settings
    from lotteh.celery import delay_remove_frame
    name = request.GET.get('camera')
    if not name:
        name = 'private'
    camera = None
    if request.user.is_authenticated:
        camera = VideoCamera.objects.filter(user=request.user, name=name).order_by('-last_frame').first()
    if request.method == 'POST':
        import shutil, os
        from .still import get_still, is_still
        try:
            form = CameraForm(request.POST, request.FILES)
            if not form.is_valid(): print(form.errors)
            camera.last_frame = timezone.now()
            camera.confirmation_id = form.cleaned_data.get('confirmation_id', '')
            camera.save()
            timestamp = datetime.datetime.fromtimestamp(int(form.cleaned_data.get('timestamp')) / 1000, tz=pytz.UTC)
            form.instance.user = camera.user
            form.instance.compressed = camera.compress_video
            form.instance.time_captured = timestamp
            form.instance.confirmation_id = form.cleaned_data.get('confirmation_id', '')
            recording = None
            if camera.recording:
                # Find the most recent active recording for this camera/user
                recording = VideoRecording.objects.filter(
                    user=camera.user,
                    camera=camera.name,
                    camera_id=videouid,
                    processing=False
                ).order_by('-last_frame').first()
                # Decide if you need to start a new recording
                should_start_new = (
                    not recording or
                    ((recording.frames.count() * (settings.LIVE_INTERVAL/1000.0)) > (camera.video_length_minutes * 60.0))
                )

                is_a_short = (camera.short_mode and (recording.frames.count() * (settings.LIVE_INTERVAL/1000.0) > settings.LIVE_SHORT_SECONDS))

                if should_start_new or is_a_short:
                    recording = VideoRecording.objects.create(
                        user=camera.user,
                        camera=camera.name,
                        last_frame=timestamp,
                        camera_id=videouid
                    )
            is_frame_still, error = is_still(camera.frame.path)
            form.instance.difference = error
            frame = form.save()
            if recording:
                recording.frames.add(frame)
                recording.last_frame = timestamp
                recording.save()
                process_recording.apply_async([recording.id], countdown=(settings.LIVE_INTERVAL/1000) * 5)
            else: print('Not saving frame')
            process_live.delay(camera.id, frame.id)
            print('5 second video uploaded')
            return HttpResponse(status=200)
        except:
            import traceback
            print(traceback.format_exc())
        return HttpResponse(status=200)
    from django.shortcuts import redirect
    from django.utils.crypto import get_random_string
    camera_key = get_random_string(length=settings.CAMERA_KEY_LENGTH)
    camera.key = camera_key
    camera.save()
    from django.urls import reverse
    if not request.user.is_authenticated: return redirect(reverse('users:login'))
    from django.shortcuts import render
    return render(request, 'live/golivevideo.html', {'title': 'Go Live', 'camera': camera, 'full': True, 'form': CameraForm(), 'preload': False, 'load_timeout': 0, 'should_compress_live': request.user.vendor_profile.compress_video, 'key': camera_key, 'use_websocket': camera.use_websocket, 'logo_alpha': camera.user.vendor_profile.logo_alpha, 'nudity_censor_scale': settings.NUDITY_CENSOR_FRONTEND_SCALE, 'nudity_censor': camera.censor_video if minor_identity_verified(request.user) else True, 'nudity_censor_px': settings.NUDITY_CENSOR_FRONTEND_PX, 'fps': camera.framerate})

@never_cache
@csrf_exempt
@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def screencast(request):
    from .models import VideoCamera, VideoFrame, VideoRecording
    from django.core.exceptions import PermissionDenied
    from .forms import CameraForm
    import datetime
    import pytz
    from django.utils import timezone
    from django.http import HttpResponse
    from django.conf import settings
    from lotteh.celery import delay_remove_frame
    name = request.GET.get('camera')
    if not name:
        name = 'private'
    camera = None
    if request.user.is_authenticated:
        camera = VideoCamera.objects.filter(user=request.user, name=name).order_by('-last_frame').first()
    if request.method == 'POST':
        import shutil, os
        from .still import get_still, is_still
        try:
            form = CameraForm(request.POST, request.FILES)
            if not form.is_valid(): print(form.errors)
            camera.last_frame = timezone.now()
            camera.confirmation_id = form.cleaned_data.get('confirmation_id', '')
            camera.save()
            timestamp = datetime.datetime.fromtimestamp(int(form.cleaned_data.get('timestamp')) / 1000, tz=pytz.UTC)
            form.instance.user = camera.user
            form.instance.compressed = camera.compress_video
            form.instance.time_captured = timestamp
            form.instance.confirmation_id = form.cleaned_data.get('confirmation_id', '')
            recording = None
            if camera.recording:
                # Find the most recent active recording for this camera/user
                recording = VideoRecording.objects.filter(
                    user=camera.user,
                    camera=camera.name,
                    camera_id=videouid,
                    processing=False
                ).order_by('-last_frame').first()
                # Decide if you need to start a new recording
                should_start_new = (
                    not recording or
                    ((recording.frames.count() * (settings.LIVE_INTERVAL/1000.0)) > (camera.video_length_minutes * 60.0))
                )

                is_a_short = (camera.short_mode and (recording.frames.count() * (settings.LIVE_INTERVAL/1000.0) > settings.LIVE_SHORT_SECONDS))

                if should_start_new or is_a_short:
                    recording = VideoRecording.objects.create(
                        user=camera.user,
                        camera=camera.name,
                        last_frame=timestamp,
                        camera_id=videouid
                    )
            is_frame_still, error = is_still(camera.frame.path)
            form.instance.difference = error
            frame = form.save()
            if recording:
                recording.frames.add(frame)
                recording.last_frame = timestamp
                recording.save()
                process_recording.apply_async([recording.id], countdown=(settings.LIVE_INTERVAL/1000) * 5)
            else: print('Not saving frame')
            process_live.delay(camera.id, frame.id)
            print('5 second video uploaded')
            return HttpResponse(status=200)
        except:
            import traceback
            print(traceback.format_exc())
        return HttpResponse(status=200)
    from django.shortcuts import redirect
    from django.utils.crypto import get_random_string
    camera_key = get_random_string(length=settings.CAMERA_KEY_LENGTH)
    camera.key = camera_key
    camera.save()
    from django.urls import reverse
    if not request.user.is_authenticated: return redirect(reverse('users:login'))
    from django.shortcuts import render
    return render(request, 'live/screencast.html', {'title': 'Screencast', 'camera': camera, 'full': True, 'form': CameraForm(), 'preload': False, 'load_timeout': 0, 'should_compress_live': request.user.vendor_profile.compress_video, 'key': camera_key, 'use_websocket': camera.use_websocket, 'logo_alpha': camera.user.vendor_profile.logo_alpha, 'nudity_censor_scale': settings.NUDITY_CENSOR_FRONTEND_SCALE, 'nudity_censor': camera.censor_video if minor_identity_verified(request.user) else True, 'nudity_censor_px': settings.NUDITY_CENSOR_FRONTEND_PX, 'fps': camera.framerate})

#@login_required
#@user_passes_test(identity_verified, login_url='/verify/', redirect_field_name='next')
@csrf_exempt
def livevideo(request, username):
    from django.contrib.auth.models import User
    from django.contrib import messages
    from django.urls import reverse
    from django.shortcuts import redirect
    from users.models import Profile
    from security.middleware import get_qs
    from django.shortcuts import get_object_or_404
    import datetime
    from django.utils import timezone
    from live.show import is_live_show, get_live_show
    from live.models import VideoCamera
    from django.conf import settings
    model = User.objects.get(profile__name=username)
    if not request.GET.get('key') and not model == request.user and is_live_show(request, model) and hasattr(request, 'user') and get_live_show(request, model) and get_live_show(request, model).user != request.user:
        messages.warning(request, '{} is in a live show with someone else right now. Please book a private show.'.format(username))
        return redirect(reverse('live:book-live-show', kwargs={'username': username}) + get_qs(request.GET))
#    if not request.GET.get('key') and not model == request.user and request.GET.get('camera', None) and not request.GET.get('camera').startswith('private'):
#        messages.warning(request, 'You need to follow {} before you can see their live show.'.format(username))
#        return redirect(reverse('feed:follow', kwargs={'username': username}) + get_qs(request.GET))
    hidenav = None
    if request.GET.get('hidenavbar','') != '':
        hidenav = True
    profile = get_object_or_404(Profile, name=username, identity_verified=True, vendor=True)
    cameras = VideoCamera.objects.filter(user=profile.user, name=request.GET.get('camera') if request.GET.get('camera') else 'private')
    camera = cameras.first()
    if camera and request.GET.get('key') and camera.key != request.GET.get('key') and not camera.public:
        return redirect(reverse('feed:follow', kwargs={'username': username}) + get_qs(request.GET))
    if not (cameras.first() and cameras.first().last_frame > timezone.now() - datetime.timedelta(seconds=settings.LIVE_INTERVAL/1000*3)):
        messages.warning(request, '{}\'s camera is not active. Consider booking a show.'.format(username))
        return redirect(reverse('live:book-live-show', kwargs={'username': username}) + get_qs(request.GET)) if hasattr(request, 'user') and request.user.is_authenticated else redirect(reverse('feed:follow', kwargs={'username': username}) + get_qs(request.GET))
    from django.shortcuts import render
    return render(request, 'live/livevideo.html', {'profile': profile, 'camera': cameras.first(), 'title': 'Live Video', 'use_websocket': camera.use_websocket, 'hidenavbar': hidenav, 'should_compress_live': model.vendor_profile.compress_video, 'frame_count': camera.frames.count()-1})

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@csrf_exempt
def last_frame_video(request, username):
    from .models import VideoCamera
    from django.shortcuts import get_object_or_404
    from users.models import Profile
    profile = get_object_or_404(Profile, name=username, identity_verified=True, vendor=True)
    cameras = VideoCamera.objects.filter(user=profile.user, name=request.GET.get('camera'))
    return render(request, 'live/lastframe.html', {'profile': profile, 'camera': cameras.first(), 'frame': camera.frames.all().last()})

```


--- File: lotteharper-main/live/voice_changer.py ---
```python
import sys, os, uuid
from moviepy import *
import moviepy as mp
from django.conf import settings
from synthesizer.utils import adjust_pitch
from tts.slice import convert_wav
from live.models import get_file_path
from django.conf import settings

def replace_audio(video_path, audio_path, output_path):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    video_with_new_audio = video.with_audio(audio)
    video_with_new_audio.write_videofile(output_path)

def adjust_video_pitch(video_path, output_path, semitones=12):
    temp_wav = convert_wav(video_path)
    path = os.path.join(settings.BASE_DIR, 'media/', get_file_path(None, 'file.wav'))
    replace_audio(video_path, adjust_pitch(temp_wav, path, semitones), output_path)
    os.remove(temp_wav)
    os.remove(path)
    return output_path
```


--- File: lotteharper-main/livevideotest.html ---
```html
{% extends 'base.html' %}
{% load app_filters %}
{% block head %}
{% if camera.user.vendor_profile.logo %}<link rel="preload" as="image" href="{{ camera.user.vendor_profile.logo.url }}">{% endif %}
<style>
video {
    width: 100%;
    pointer-events: none;
}
{% if camera.user.vendor_profile.video_intro_font %}
@font-face { font-family: 'VendorSpecified'; src: url('{{ camera.user.vendor_profile.video_intro_font.url }}'); }
{% endif %}
#video-container {
  position: relative;
  width: 100%; /* or 100vw for responsive fullscreen */
  margin: auto;
}

#video {
  width: 100%;
  height: auto;
  display: block;
}

#chatbox a {
  color: #4da3ff; /* Lighter blue */
  text-decoration: none; /* Optional: remove underline */
}

#chatbox a:hover,
#chatbox a:focus {
  color: #80cfff; /* Even lighter blue on hover/focus */
}

#rec-status {
    position: absolute;
    top: 5px;
    left: 50%;
    transform: translate(-50%, 0%);
}

#chat-overlay {
  position: absolute;
  bottom: 10px; /* Above controls */
  right: 10px;
  width: 300px;
  max-width: 90%;
  max-height: 60%;
  min-height: 30%;
  background: rgba(0,0,0,0.5);
  color: #fff;
  border-radius: 10px;
  padding: 10px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

#chatbox {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 5px;
}

#chatinput {
  width: 100%;
  padding: 5px;
  border: none;
  border-radius: 5px;
}

#fullscreenToggle {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 2;
}
</style>
{% endblock %}
{% block content %}
<h1>{{ 'Live Recording'|etrans }}</h1>
<legend>{% if request.GET.camera %}{{ request.GET.camera }}{% else %}private{% endif %} {{ 'camera'|etrans }}</legend>
<div id="container">
{% if request.GET.with %}
<div style="z-index: 1; position: absolute;">
{% endif %}
<p id="errormessage" class="hide" style="text-color: red;">{{ 'Please enable your camera in your web browser and device settings to continue. Reload to continue.'|etrans }} <button onclick="window.location.reload();" title="Reload page" class="btn btn-outline-primary">{{ 'Reload'|etrans }}</button></p>
<div id="video-container">
    <div style="text-align: center;" id="rec-status"></div>
    <button id="fullscreenToggle" class="btn btn-sm btn-outline-secondary" title="{{ 'Toggle Fullscreen' }}"><i class="bi bi-arrows-fullscreen"></i></button>
    <div id="mediaWrapper"></div>
    {% if camera.broadcast %}
    <div id="chat-overlay">
{% autoescape off %}        <div id="chatbox">{% for message in camera.user.stream_messages|recent_stream_messages:1 %}<div><b>{% if message.user %}@{{ message.user.profile.name }}{% if message.user == vendor %} ({{ 'Streamer'|etrans }}){% endif %}{% else %}{{ 'Guest'|etrans }}{% endif %}:</b> {{ message.message|trans }}</div>{% endfor %}</div>{% endautoescape %}
        <div class="input-group mb-3">
            <input id="chatinput" type="text" class="form-control" placeholder="{{ 'Type your message here'|etrans }}" aria-label="{{ 'Message'|etrans }}" style="max-width: 75%;">
            <div class="input-group-append">
                <button class="btn btn-outline-secondary" type="button" id="button-addon2" onclick="sendChat();">{{ 'Send'|etrans }}</button>
            </div>
        </div>
    </div>
    {% endif %}
</div>
{% if request.GET.with %}
</div>
{% endif %}
<form method="POST" enctype="multipart/form-data" id="live-form" style="position: absolute; display: none; visibility: hidden;" action="{{ request.path }}?camera={% if request.GET.camera %}{{ request.GET.camera }}{% else %}private{% endif %}&key={{ key }}">
{{ form }}
</form>
{% if request.GET.with %}
<iframe src="/live/{{ request.GET.with }}/?fullscreen=t&hidenavbar=t" width="100%" height="700px" id="live"></iframe>
{% endif %}
{% blocktrans en %}
{% if request.GET.back %}
<a class="btn btn-outline-primary" href="{{ request.path }}?camera={% if request.GET.camera %}{{ request.GET.camera }}{% else %}private{% endif %}{% if request.GET.with %}&with={{ request.GET.with }}{% endif %}">Front Facing Camera</a>
{% else %}
<a class="btn btn-outline-secondary" href="{{ request.path }}?camera={% if request.GET.camera %}{{ request.GET.camera }}{% else %}private{% endif %}{% if request.GET.with %}&with={{ request.GET.with }}{% endif %}&back=true">Back Facing Camera</a>
{% endif %}
{% if not request.GET.mirror %}
<a class="btn btn-outline-primary" href="{{ request.path }}?camera={% if request.GET.camera %}{{ request.GET.camera }}{% else %}private{% endif %}&mirror=t{% if request.GET.with %}&with={{ request.GET.with }}{% endif %}{% if request.GET.back %}&back=t{% endif %}">Mirror camera</a>
{% else %}
<a class="btn btn-outline-secondary" href="{{ request.path }}?camera={% if request.GET.camera %}{{ request.GET.camera }}{% else %}private{% endif %}{% if request.GET.with %}&with={{ request.GET.with }}{% endif %}{% if request.GET.back %}&back=t{% endif %}">Disable mirroring (enabled)</a>
{% endif %}
<hr>
<div class="display: inline-block;">
    <button class="btn btn-outline-success" id="startWebcam" title="Start Webcam">Start Webcam</button>
    <button class="btn btn-outline-danger" id="startRecording" title="Record Resulting Stream">Record Stream</button>
    <button class="btn btn-outline-warning" id="stopRecording" title="Stop Recording">Stop Recording</button>
    <button class="btn btn-outline-light" id="stopAllStreams" title="Stop All Streams"{% if not darkmode %} style="color: black !important;"{% endif %}>Stop Stream</button>
</div>
{% endblocktrans %}
<div style="display: flex; justify-content: space-around;">
{% if request.user.profile.vendor and not request.GET.fullscreen %}
{% include 'live/go_remote.html' %}
{% endif %}
<button id="audioBtn" title="{{ 'Mute or unmute the video'|etrans }}" class="btn btn-outline-dark pink-borders">{% if camera.muted %}<i class="bi bi-mic-mute-fill"></i>{% else %}<i class="bi bi-mic-fill"></i>{% endif %}</button>
<button id="rotateLeftBtn" title="{{ 'Rotate the video left'|etrans }}" class="btn btn-outline-dark pink-borders"><i class="bi bi-arrow-counterclockwise"></i></button>
<button id="rotateRightBtn" title="{{ 'Rotate the video right'|etrans }}" class="btn btn-outline-dark pink-borders"><i class="bi bi-arrow-clockwise"></i>
</button>
<a href="{% url 'live:screencast' %}?camera={{ request.GET.camera }}" title="{{ 'Switch to screencasting mode'|etrans }}" class="btn btn-outline-dark pink-borders"><i class="bi bi-person-video3"></i></a>
<a href="{% url 'live:name-camera' %}?camera={{ camera.name }}" title="{{ 'Return to camera settings and options'|etrans }}" class="btn btn-outline-dark pink-borders"><i class="bi bi-gear-fill"></i></a>
<button onclick="window.location.reload();" title="{{ 'Reload the page to stop the stream and create a new video'|etrans }}" class="btn btn-outline-dark pink-borders"><i class="bi bi-arrow-clockwise"></i></button>
{% if request.user.profile.vendor and not request.GET.fullscreen %}
{% include 'live/recording_remote.html' %}
{% endif %}
</div>
{% include 'live/camera_settings_frame.html' %}
{% if nudity_censor %}
<canvas id="cvcanvas" style="display: none;"></canvas>
{% endif %}
{% endblock %}
{% block javascripts %}
{% if nudity_censor %}
<script src="/static/js/tensorflow.min.js"></script>
<script src="/static/js/nsfwjs.min.js"></script>
{% endif %}
{% endblock %}
{% block javascript %}
{% if nudity_censor %}
var overlay;
{% endif %}
var updateCameraToggle = document.getElementById('update-camera-toggle');
var cameraSettings = document.getElementById('camera-settings');
var cameraUpdateOpen = false;
Array.from(document.getElementsByClassName('update-camera-toggle')).forEach(function (element) {
    $(element).on('click', function() {
        cameraUpdateOpen = !cameraUpdateOpen;
        if(cameraUpdateOpen) {
            cameraSettings.height = '600px';
            $('#hide-dupe').removeClass('hide');
        } else {
            cameraSettings.height = '0px';
            $('#hide-dupe').addClass('hide');
        }
    });
});
function generateRandomString(length = 6) {
  return Math.random().toString(36).substring(2, 2 + length);
}
var CAMERA_ID = generateRandomString(8);
const MINUTES_PER_LOGO = 5;
var captureInterval;
var liveButton = document.getElementById('golivebutton');
var recordButton = document.getElementById('recordbutton');
var muteButton = document.getElementById('mutebutton');
var muted = false;
var mediaRecorder;
function reportWindowSize() {
        var iFrame = document.getElementById('live');
        resizeIFrameToFitContent(iFrame);
}
window.onresize = reportWindowSize;
function resizeIFrameToFitContent(iFrame) {
    iFrame.height = iFrame.contentWindow.document.body.scrollHeight;
}
window.onmessage = function(event){
    if (event.data == 'resize') {
        var iFrame = document.getElementById('live');
        resizeIFrameToFitContent(iFrame);
    }
};
var live = false;
var recording = false;
var unconfirmedFrames = [];
var videoFrames = {};
var retryCount = {};
var mediaSocket;
var mediaSocketReconnectTimeout;
function openMediaSocket() {
        {% if use_websocket %}
        if(mediaSocketReconnectTimeout) {
            clearTimeout(mediaSocketReconnectTimeout);
            mediaSocketReconnectTimeout = null;
        }
        if(mediaSocket && mediaSocket.readyState == WebSocket.OPEN) mediaSocket.close();
        mediaSocket = new WebSocket((window.location.protocol == 'https:' ? "wss://" : "ws://") + window.location.hostname + '/ws/live/camera/{{ camera.user.profile.name }}/{{ camera.name }}/?key={% if request.GET.key %}{{ request.GET.key }}{% else %}{{ camera.key }}{% endif %}');
        mediaSocket.addEventListener("open", (event) => {
                console.log('Media socket open.');
        });
        mediaSocket.addEventListener("close", (event) => {
                console.log('Socket closed.');
                if(mediaSocketReconnectTimeout) clearTimeout(mediaSocketReconnectTimeout);
                mediaSocketReconnectTimeout = setTimeout(function() {
                        openMediaSocket();
                }, {{ reload_time }});
        });
        mediaSocket.addEventListener("error", (event) => {
                console.log('Socket error.');
                if(mediaSocketReconnectTimeout) clearTimeout(mediaSocketReconnectTimeout);
                mediaSocketReconnectTimeout = setTimeout(function() {
                        openMediaSocket();
                }, {{ reload_time }});
        });
        mediaSocket.addEventListener("message", (event) => {
                /*return;
                if(unconfirmedFrames.includes(event.data)) {
                        var index = unconfirmedFrames.indexOf(event.data);
                        console.log('Frame posted');
                        unconfirmedFrames.splice(index, 1);
                        videoFrames.splice(index, 1);
                        videoFrames[event.data] = null;
                } else {
                        if(retryCount[event.data] < 5) {
                                mediaSocket.send(videoFrames[event.data]);
                                console.log('Sending capture again');
                        } else {
                                console.log('Forfeiting capture');
                                videoFrames[event.data] = null;
                                return;
                        }
                        if(!(event.data in retryCount)) retryCount[event.data] = 0;
                        retryCount[event.data] = retryCount[event.data] + 1;
                }*/
        });
        {% endif %}
}
openMediaSocket();
var form = document.getElementById('live-form');
var data;
var mediaChunks = [];
{% if nudity_censor %}
var censorVideo = false;
const cvcanvas = document.getElementById('cvcanvas');
const cvctx = cvcanvas.getContext('2d');
var nsfwjsmodel;
nsfwjs.load('/static/js/models/mobilenet_v2/').then(function(model) {
    nsfwjsmodel = model;
});
{% endif %}
function detectVideo() {
        cvcanvas.width = Math.trunc(overlay.videoWidth * {{ nudity_censor_scale }});
        cvcanvas.height = Math.trunc(overlay.videoHeight * {{ nudity_censor_scale }});
        cvctx.clearRect(0, 0, cvcanvas.width, cvcanvas.height);
        cvctx.drawImage(pipOverlayStream, 0, 0, Math.trunc(overlay.videoWidth * {{ nudity_censor_scale }}), Math.trunc(overlay.videoHeight * {{ nudity_censor_scale }}));
        nsfwjsmodel.classify(cvcanvas, 1).then(function (predictions) {
            console.log(predictions[0]);
            if(predictions[0].className == 'Porn' && predictions[0].probability > 0.95) {
                console.log('Nude');
                censorVideo = true;
            } else {
                console.log('not nude');
                censorVideo = false;
            }
        });
}
function capture(){
        mediaRecorder.stop();
        {% if nudity_censor %}
        if(overlay) {
            setTimeout(detectVideo, 0);
        }
        {% endif %}
}
const clone = (items) => items.map(item => Array.isArray(item) ? clone(item) : item);
let localCamStream,
  localScreenStream,
  localOverlayStream,
  rafId,
  cam,
  screen,
  audioContext,
  audioDestination;
let mediaWrapperDiv = document.getElementById("mediaWrapper");
let startWebcamBtn = document.getElementById("startWebcam");
let startRecordingBtn = document.getElementById("startRecording");
let stopRecordingBtn = document.getElementById("stopRecording");
let stopAllStreamsBtn = document.getElementById("stopAllStreams");
let canvasElement = document.createElement("canvas");
let canvasCtx = canvasElement.getContext("2d");
var mimeType = 'video/' + {% autoescape off %}'{{ camera.mimetype }}'.split(',')[0].replace('"', ''){% endautoescape %};

let encoderOptions = {
    mimeType: mimeType,
};
let recordedChunks = [];
let audioTracks = [];

/**
 * Internal Polyfill to simulate
 * window.requestAnimationFrame
 * since the browser will kill canvas
 * drawing when tab is inactive
 */
const requestVideoFrame = function(callback) {
  return window.setTimeout(function() {
    callback(Date.now());
  }, 1000 / 60); // 60 fps - just like requestAnimationFrame
};

/**
 * Internal polyfill to simulate
 * window.cancelAnimationFrame
 */
const cancelVideoFrame = function(id) {
  clearTimeout(id);
};
async function startWebcamFn() {
  if(!localCamStream) {
      CAMERA_ID = generateRandomString(8);
      localCamStream = await navigator.mediaDevices.getUserMedia({
        video: { {% if request.GET.back %}facingMode: "environment", {% endif %}width: { ideal: {{ camera.width|parsevideowidth }} }, height: { ideal: {{ camera.width|parsevideoheight }} },  frameRate: { ideal: {{ fps }} } },
        audio: {% if camera.muted %}false{% elif camera.microphone == 'communications' %}deviceId: { ideal: "communications" }{% elif camera.microphone == 'default' %}true{% elif camera.microphone == 'echo cancellation' %}{ echoCancellation: true, }{% endif %},
      }).catch((error) => {
        console.log(error);
        $('#errormessage').removeClass('hide');
      });
      if (localCamStream && !document.getElementById("justWebcam")) {
        cam = await attachToDOM("justWebcam", localCamStream);
      }
      setTimeout(mergeStreamsFn, 500);
  }
}
const baseAlpha = {{ logo_alpha }};
var logo = new Image();
{% if camera.user.vendor_profile.logo %}logo.src = "{{ camera.user.vendor_profile.logo.url }}";{% endif %}
var currentRotation = {% if camera.rotation %}{{ camera.rotation }}{% else %}0{% endif %};

async function makeComposite() {
  if (cam) {
    canvasCtx.save();
    canvasCtx.globalAlpha = 1;
    var videoWidth = cam.videoWidth;
    var videoHeight = cam.videoHeight;
    if(currentRotation % 2 == 0) {
        canvasElement.setAttribute("width", `${cam.videoWidth}px`);
        canvasElement.setAttribute("height", `${cam.videoHeight}px`);
        canvasCtx.clearRect(0, 0, cam.videoWidth, cam.videoHeight);
    } else {
        videoHeight = cam.videoWidth;
        videoWidth = cam.videoHeight;
        canvasElement.setAttribute("width", `${cam.videoHeight}px`);
        canvasElement.setAttribute("height", `${cam.videoWidth}px`);
        canvasCtx.clearRect(0, 0, cam.videoHeight, cam.videoWidth);
    }
    {% if nudity_censor %}
    if(censorVideo) {
        canvasCtx.filter = 'blur({{ nudity_censor_px }}px)';
    }
    {% endif %}
    canvasCtx.translate(canvasElement.width / 2, canvasElement.height / 2);
    const angleInRadians = currentRotation * 90 * (Math.PI / 180);
    canvasCtx.rotate(angleInRadians);
    canvasCtx.drawImage(
      cam,
      -Math.floor(cam.videoWidth)/2,
      -Math.floor(cam.videoHeight)/2,
      Math.floor(cam.videoWidth),
      Math.floor(cam.videoHeight),
    ); // this is just a rough calculation to offset the webcam stream to bottom left
/*    canvasCtx.save();
    canvasCtx.restore();*/
    canvasCtx.resetTransform();
    canvasCtx.filter = '';
    {% if camera.embed_logo and camera.user.vendor_profile.logo %}
/*    canvasCtx.translate(canvasElement.width / 2, canvasElement.height / 2);
    canvasCtx.rotate(angleInRadians);*/
    canvasCtx.globalAlpha = baseAlpha;
    const logoSize = parseInt(videoWidth / 13);
    canvasCtx.drawImage(
        logo,
        10,
        videoHeight - 10 - logoSize, /*-Math.floor(cam.videoHeight)/2,*/
        logoSize,
        logoSize
    );
    canvasCtx.globalAlpha = 1;
    canvasCtx.resetTransform();
    {% if camera.user.vendor_profile.video_intro_text %}
/*    canvasCtx.translate(canvasElement.width / 2, canvasElement.height / 2);
    canvasCtx.rotate(angleInRadians);*/
    const currentTime = new Date().getTime()/1000;
    if(currentTime - recordingStartTime < 1) {
        canvasCtx.globalAlpha = (currentTime - recordingStartTime) * baseAlpha;
        canvasCtx.font = new String(parseInt(videoWidth/20)) + 'px {% if camera.user.vendor_profile.video_intro_font %}VendorSpecified{% else %}Arial{% endif %}';
        canvasCtx.fillStyle = "{{ camera.user.vendor_profile.video_intro_color }}";
        canvasCtx.fillText("{{ camera.user.vendor_profile.video_intro_text }}", parseInt(videoWidth/13) + 20, videoHeight - logoSize/2.7);
        canvasCtx.globalAlpha = 1;
    } else if(currentTime - recordingStartTime < 14) {
        canvasCtx.globalAlpha = baseAlpha;
        canvasCtx.font = new String(parseInt(videoWidth/20)) + 'px {% if camera.user.vendor_profile.video_intro_font %}VendorSpecified{% else %}Arial{% endif %}';
        canvasCtx.fillStyle = "{{ camera.user.vendor_profile.video_intro_color }}";
        canvasCtx.fillText("{{ camera.user.vendor_profile.video_intro_text }}", parseInt(videoWidth/13) + 20, videoHeight - logoSize/2.7);
        canvasCtx.globalAlpha = 1;
    } else if(currentTime - recordingStartTime < 15) {
        canvasCtx.globalAlpha = (15 - (currentTime - recordingStartTime)) * baseAlpha;
        canvasCtx.font = new String(parseInt(videoWidth/20)) + 'px {% if camera.user.vendor_profile.video_intro_font %}VendorSpecified{% else %}Arial{% endif %}';
        canvasCtx.fillStyle = "{{ camera.user.vendor_profile.video_intro_color }}";
        canvasCtx.fillText("{{ camera.user.vendor_profile.video_intro_text }}", parseInt(videoWidth/13) + 20, videoHeight - logoSize/2.7);
        canvasCtx.globalAlpha = 1;
    } else if(currentTime - recordingStartTime > {{ video_interval }}/1000 * 60 * MINUTES_PER_LOGO) {
        recordingStartTime = new Date().getTime()/1000;
    }
    canvasCtx.resetTransform();
    {% endif %}
    {% endif %}
    try {
      let imageData = canvasCtx.getImageData(
        0,
        0,
        videoWidth,
        videoHeight
      ); // this makes it work
      canvasCtx.putImageData(imageData, 0, 0); // properly on safari/webkit browsers too
    } catch {}
    canvasCtx.restore();
    rafId = requestVideoFrame(makeComposite);
  }
}

async function mergeStreamsFn() {
  await makeComposite();
  audioContext = new AudioContext();
  audioDestination = audioContext.createMediaStreamDestination();
  let fullVideoStream = canvasElement.captureStream();
  let existingAudioStreams = [
    ...(localCamStream ? localCamStream.getAudioTracks() : []),
  ];
  audioTracks.push(
    audioContext.createMediaStreamSource(
      new MediaStream([existingAudioStreams[0]])
    )
  );
  if (existingAudioStreams.length > 1) {
    audioTracks.push(
      audioContext.createMediaStreamSource(
        new MediaStream([existingAudioStreams[1]])
      )
    );
  }
  audioTracks.map((track) => track.connect(audioDestination));
  console.log(audioDestination.stream);
  localOverlayStream = new MediaStream([...fullVideoStream.getVideoTracks()]);
  let fullOverlayStream = new MediaStream([
    ...fullVideoStream.getVideoTracks(),
    ...audioDestination.stream.getTracks()
  ]);
  console.log(localOverlayStream, existingAudioStreams);
  if (localOverlayStream) {
    overlay = await attachToDOM("pipOverlayStream", localOverlayStream);
    mediaRecorder = new MediaRecorder(fullOverlayStream, encoderOptions);
    mediaRecorder.ondataavailable = handleDataAvailable;
    overlay.volume = 0;
    cam.volume = 0;
    try {
        cam.style.display = "none";
        // localCamStream.getAudioTracks().map(track => { track.enabled = false });
        // localScreenStream.getAudioTracks().map(track => { track.enabled = false });
    } catch {}
    {% if nudity_censor %}
    if(overlay) {
        setTimeout(detectVideo, 3000);
    }
    {% endif %}
{% if camera.broadcast %}
var signalingSocket;
var signalingSocketReconnectTimeout;
function openSignalingSocket() {
    signalingSocket = new WebSocket("wss://" + window.location.host + "/ws/signaling/{{ request.user.profile.name }}/{{ camera.name }}/?broadcast=true");
    signalingSocket.onerror = (event) => {
        if(signalingSocketReconnectTimeout) clearTimeout(signalingSocketReconnectTimeout);
        signalingSocketReconnectTimeout = setTimeout(function() {
            openSignalingSocket();
        }, {{ reload_time }});
    };
    signalingSocket.onclose = (event) => {
        if(signalingSocketReconnectTimeout) clearTimeout(signalingSocketReconnectTimeout);
        signalingSocketReconnectTimeout = setTimeout(function() {
            openSignalingSocket();
        }, {{ reload_time }});
    };
    signalingSocket.onmessage = async (event) => {
        let data = JSON.parse(event.data);
        if (data.type === "answer") {
            let pc = peers[data.from];
            if (pc) await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
        }
        else if (data.type === "candidate") {
            let pc = peers[data.from];
            if (pc) await pc.addIceCandidate(data.candidate);
        }
        else if (data.type === "new_viewer") {
            // Call handleViewer with the viewer's channel name
            handleViewer(data.id);
        }
    };
    signalingSocket.onopen = async (event) => {
        signalingSocket.send(JSON.stringify({type: 'rotate', data: currentRotation}));
    };
}
openSignalingSocket();

const stunConfig = { iceServers: [{urls: "stun:lotteh.com:3478"}] };
let peers = {};
// When a viewer connects, create a peer connection and send offer
function handleViewer(id) {
    let pc = new RTCPeerConnection(stunConfig);
    peers[id] = pc;
    localOverlayStream.getTracks().forEach(track => pc.addTrack(track, localOverlayStream));
    pc.onicecandidate = e => {
        if (e.candidate) {
            signalingSocket.send(JSON.stringify({type:"candidate", candidate:e.candidate, to:id}));
        }
    };
    pc.createOffer().then(offer => {
        pc.setLocalDescription(offer);
        signalingSocket.send(JSON.stringify({type:"offer", offer, to:id}));
    });
}
{% endif %}
  }
}
var recordingStartTime;
async function startRecordingFn() {
  if(!localCamStream) {
    await startWebcamFn();
    await new Promise(r => setTimeout(r, 4000));
  }
  if(!live) {
      recordingStartTime = new Date().getTime()/1000;
      live = true;
      mediaRecorder.start();
      console.log(mediaRecorder.state);
      console.log("recorder started");
      document.getElementById("pipOverlayStream").style.border = "4px solid red";
      captureInterval = setInterval(capture, {{ video_interval }});
      
  }
}
async function stopRecordingFn() {
    if(live) {
        live = false;
        if(live && mediaSocket && mediaSocket.readyState === WebSocket.OPEN) {
            document.getElementById("rec-status").innerHTML = '<i style="font-size: 20px;" class="bi bi-circle-fill color-red"></i>';
        } else {
            document.getElementById("rec-status").innerHTML = '<i style="font-size: 20px;" class="bi bi-circle"></i>';
        }
        if(captureInterval) clearInterval(captureInterval);
        document.getElementById("pipOverlayStream").style.border = "none";
        mediaRecorder.stop();
    }
}

async function stopAllStreamsFn() {
  [
    ...(localCamStream ? localCamStream.getTracks() : []),
    ...(localOverlayStream ? localOverlayStream.getTracks() : [])
  ].map((track) => track.stop());
  live = false;
  document.getElementById("rec-status").innerHTML = '';
  if(captureInterval) clearInterval(captureInterval);
  localOverlayStream = null;
  localCamStream = null;
  audioTracks = [];
  cancelVideoFrame(rafId);
  mediaWrapperDiv.innerHTML = "";
  try {  document.getElementById("pipOverlayStream").style.border = "none"; }
  catch { }
}

startRecordingBtn.addEventListener("click", startRecordingFn);
stopRecordingBtn.addEventListener("click", stopRecordingFn);
startWebcamBtn.addEventListener("click", startWebcamFn);
stopAllStreamsBtn.addEventListener("click", stopAllStreamsFn);

async function attachToDOM(id, stream) {
  let videoElem = document.createElement("video");
{% if camera.mirror or request.GET.mirror and not request.GET.back %}  if(id == 'pipOverlayStream') { videoElem.style.transform = 'rotateY(180deg)'; }{% endif %}
  videoElem.id = id;
  videoElem.autoplay = true;
  videoElem.volume = 0;
  videoElem.setAttribute("playsinline", true);
  videoElem.srcObject = new MediaStream(stream.getTracks());
  videoElem.play();
  mediaWrapperDiv.appendChild(videoElem);
  return videoElem;
}
var audioEnabled = {% if camera.muted %}true{% else %}false{% endif %};
document.getElementById("audioBtn").onclick = () => {
    audioEnabled = !audioEnabled;
    localOverlayStream.getAudioTracks().forEach(track => track.enabled = audioEnabled);
    document.getElementById("audioBtn").innerHTML = audioEnabled ? '<i class="bi bi-mic-fill"></i>' : '<i class="bi bi-mic-mute-fill"></i>';
};

document.getElementById("rotateLeftBtn").onclick = () => {
    currentRotation--;
    signalingSocket.send(JSON.stringify({type: 'rotate', data: currentRotation}));
};
document.getElementById("rotateRightBtn").onclick = () => {
    currentRotation++;
    signalingSocket.send(JSON.stringify({type: 'rotate', data: currentRotation}));
};
function handleDataAvailable(event) {
  console.log("data-available");
  if (event.data.size > 0) {
    recordedChunks.push(event.data);
    console.log(recordedChunks);
    download();
  } else {}
}
var remoteSocketReconnectTimeout;
var cameraon = false;
function openRemoteSocket() {
        var remoteSocket = new WebSocket((window.location.protocol == 'https:' ? "wss://" : "ws://") + window.location.hostname + '/ws/live/remote/{{ camera.user.profile.name }}/{{ camera.name }}/');
        remoteSocket.addEventListener("open", (event) => {
            console.log('Remote socket open.');
        });
        remoteSocket.addEventListener("close", (event) => {
            console.log('Remote socket closed.');
            if(remoteSocketReconnectTimeout) clearTimeout(remoteSocketReconnectTimeout);
            remoteSocketReconnectTimeout = setTimeout(function() {
                openRemoteSocket();
            }, {{ reload_time }});
        });
        remoteSocket.addEventListener("error", (event) => {
            console.log('Remote socket error.');
            if(remoteSocketReconnectTimeout) clearTimeout(remoteSocketReconnectTimeout);
            remoteSocketReconnectTimeout = setTimeout(function() {
                openRemoteSocket();
            }, {{ reload_time }});
        });
        remoteSocket.addEventListener("message", (event) => {
            var instructions = event.data.split(',');
            if(instructions[0] == 'y' && !cameraon) {
                cameraon = true;
                setTimeout(startWebcamFn, 1000);
                liveButton.innerHTML = '<i class="bi bi-toggle-on"></i>';
            } else if(instructions[0] == 'n' && cameraon) {
                cameraon = false;
                stopAllStreamsFn();
                liveButton.innerHTML = '<i class="bi bi-toggle-off"></i>';
            }
            if(instructions[1] == 'y' && !recording) {
                recording = true;
                setTimeout(startRecordingFn, 4000);
                recordButton.innerHTML = '<i class="bi bi-toggle-on"></i>';
            } else if(instructions[1] == 'n' && recording) {
                recording = false;
                stopRecordingFn();                
                recordButton.innerHTML = '<i class="bi bi-toggle-off"></i>';
            }
            if(instructions[2] == 'y' && !muted) {
                muted = true;
                muteButton.innerHTML = '<i class="bi bi-mic-mute-fill"></i>';
            } else if(instructions[2] == 'n' && muted) {
                muted = false;
                muteButton.innerHTML = '<i class="bi bi-mic-fill"></i>';
            }
        });
}
openRemoteSocket();

function download() {
        if(live) { mediaRecorder.start(); }
        if(live && mediaSocket && mediaSocket.readyState === WebSocket.OPEN) {
            document.getElementById("rec-status").innerHTML = '<i style="font-size: 20px; color: red !important;" class="bi bi-circle-fill"></i>';
        } else {
            document.getElementById("rec-status").innerHTML = '<i style="font-size: 20px; color: red !important;" class="bi bi-circle"></i>';
        }
        var file = new Blob(recordedChunks, {'type': 'video/' + '{% autoescape off %}{{ camera.mimetype }}{% endautoescape %}'.split(';')[0]});
        recordedChunks = [];
        var formdata = new FormData(form);
        var utc_timestamp = String(new Date().toISOString());
        formdata.append('confirmation_id', String(Math.floor(Math.random() * 1000000000)));
        formdata.append('timestamp', utc_timestamp);
        formdata.append('viduid', CAMERA_ID);
        var id = formdata.get('confirmation_id');
        {% if use_websocket %}
        {% if should_compress_live %}
        var zip = new JSZip();
        {% autoescape off %}
        zip.file('frame.' + '{{ camera.mimetype }}'.split(';')[0], new File([file], 'frame.' + '{{ camera.mimetype }}'.split(';')[0]));
        {% endautoescape %}
        zip.generateAsync({type:"blob"}).then(function (file) {
        var zipfile = new File([file], 'frame.zip');
        var reader = new FileReader();
        reader.readAsDataURL(zipfile);
        reader.onload = function () {
            formdata.append("frame", reader.result);
                var data = new URLSearchParams(formdata).toString();
                if(mediaSocket.readyState == WebSocket.OPEN) mediaSocket.send(data);
            };
            reader.onerror = function (error) {
                    console.log('Error: ', error);
            };
        });
        {% else %}
        var reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = function () {
        formdata.append("frame", reader.result);
        var data = new URLSearchParams(formdata).toString();
            if(mediaSocket.readyState == WebSocket.OPEN) mediaSocket.send(data);
        };
        reader.onerror = function (error) {
            console.log('Error: ', error);
        };
        {% endif %}
        {% else %}
        {% if should_compress_live %}
        var zip = new JSZip();
        {% autoescape off %}
        zip.file("frame." + '{{ camera.mimetype }}'.split(';')[0], new File([file], 'frame.' + '{{ camera.mimetype }}'.split(';')[0]));
        {% endautoescape %}
        zip.generateAsync({type:"blob"}).then(function (file) { // 1) generate the zip file
            formdata.append('frame', new File([file], 'frame.zip'));
            $.ajax({
               url: window.location.href,
               type: "POST",
               data: formdata,
               processData: false,
               contentType: false,
               timeout: {{ request_timeout }},
               tryCount: 0,
               retryLimit: 5,
               error: (xhr, textStatus, errorThrown) => {
                   this.tryCount++;
                   if(this.tryCount >= this.retryLimit) return;
                   $.ajax(this);
               },
               success: (data) => {
/*                   $.ajax({
                        url: '/live/confirm/' + id + '/',
                        method: 'POST',
                        success: function(data) {
                            if(data != 'y') {
                                    $.ajax(this);
                            }
                        },
                    });*/
                },
            }).done(function(respond){
                console.log(respond);
            });
        }, function (err) {
            console.log("Error zipping file");
        });
        {% else %}
        formdata.append('frame', new File([file], 'frame.webm'));
        $.ajax({
            url: window.location.href,
            type: "POST",
            data: formdata,
            processData: false,
            contentType: false,
            timeout: {{ request_timeout }},
            tryCount: 0,
            retryLimit: 5,
            error: (xhr, textStatus, errorThrown) => {
                console.log('Error uploading');
                this.tryCount++;
                if(this.tryCount >= this.retryLimit) return;
                $.ajax(this);
            },
            success: (data) => {
/*                $.ajax({
                   url: '/live/confirm/' + id + '/',
                    method: 'POST',
                    success: function(data) {
                        if(data != 'y') {
                            $.ajax(this);
                        }
                    },
                });*/
            },
        }).done(function(respond){
            console.log(respond);
        });
        {% endif %}
    {% endif %}
}
{% include 'live/remote.js' %}
const container = document.getElementById('video-container');
var fullscreenButton = document.getElementById('fullscreenToggle');
fullscreenButton.addEventListener('click', () => {
  if (!document.fullscreenElement) {
    fullscreenButton.innerHTML = '<i class="bi bi-fullscreen-exit"></i>';
    // Enter fullscreen mode
    if (container.requestFullscreen) {
      container.requestFullscreen();
    } else if (container.mozRequestFullScreen) { // Firefox
      container.mozRequestFullScreen();
    } else if (container.webkitRequestFullscreen) { // Chrome, Safari and Opera
      container.webkitRequestFullscreen();
    } else if (container.msRequestFullscreen) { // IE/Edge
      container.msRequestFullscreen();
    }
  } else {
    fullscreenButton.innerHTML = '<i class="bi bi-arrows-fullscreen"></i>';
    // Exit fullscreen mode
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.mozCancelFullScreen) { // Firefox
      document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) { // Chrome, Safari and Opera
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) { // IE/Edge
      document.msExitFullscreen();
    }
  }
});
{% if camera.broadcast %}
var chatSocket;
var chatSocketReconnectTimeout;
function openChatSocket() {
    chatSocket = new WebSocket(
        "wss://" + window.location.host + "/ws/chat/{{ request.user.profile.name }}/?lang={{ lang }}"
    );
    chatSocket.onerror = function() {
        if(chatSocketReconnectTimeout) clearTimeout(chatSocketReconnectTimeout);
        chatSocketReconnectTimeout = setTimeout(openChatSocket, {{ reload_time }});
    };
    chatSocket.onclose = function() {
        if(chatSocketReconnectTimeout) clearTimeout(chatSocketReconnectTimeout);
        chatSocketReconnectTimeout = setTimeout(openChatSocket, {{ reload_time }});
    };
    chatSocket.onmessage = function(event) {
        let data = JSON.parse(event.data);
        let chatbox = document.getElementById('chatbox');
        chatbox.innerHTML += `<div><b>${data.username}:</b> ${data.message}</div>`;
        chatbox.scrollBy(0, 1000);
    };
}
openChatSocket();
function sendChat() {
    let input = document.getElementById('chatinput');
    if(input.value != "") {
        chatSocket.send(JSON.stringify({
            message: input.value,
            username: "@{{ request.user.profile.name }} (Streamer)"
        }));
        input.value = "";
    }
}
const inputField = document.getElementById('chatinput');
inputField.addEventListener('keydown', function(event) {
    if (event.keyCode === 13) { // 13 is the keyCode for the Enter key
        event.preventDefault(); // Prevent default Enter key behavior
        sendChat();
    }
});
chatbox.scrollBy(0, 9999999);
{% endif %}
{% endblock %}
```


--- File: lotteharper-main/login.py ---
```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')

import django
django.setup()
from django.contrib.auth.models import User
from django.conf import settings
u = User.objects.get(id=settings.MY_ID)
u.is_active = True
u.save()
print('Login here:')
print(settings.BASE_URL + u.profile.create_auth_url())
```


--- File: lotteharper-main/logo.png ---
```
âPNG

   IHDR   ¿   ¿   R‹l   IDATxÏ}`’µˆ7€õzoñlÀ7å¡Ñ`™)ÅzØ…KHBMHÖBLx	/!Ô%˘C…Ô—B‡ Kh¶ô¶\qó-Y∂$´Øv•-ívˇsf5ª3[§]≠∂HyÓÃùsœ-sÊú{ø{Óùµ∆Ø˛©ò∆–@˝S%0ç%†¿4~˘Í£™dJ¸√T≥üÇzdR™dB˙√.‡‡Äso&jWÎîI`ÄL
Èé6<Ï˚+∞ıﬂÄÅ˝ÈÆ]≠O&’ d¬Hyî{˛›˜≠k ütõWé™ZÖC$Ñ¥™§K‰¨¸˚⁄÷*kÙt ªÔS·êR*iªS ]¢fÿ”˙J†ÁØ”±¯‚nÇC¬S‘˚K@5Ä‹ÛÔ~ {b’Á>l˘ç*ä%¢T–UHÖT•2Y˘EÿÛÜD˝Ínv˛idN0:kR©jÊ†Tä"ëΩ‰Ìâ{bUÁ§‡ã_©p(ñ|&òÆ¿T,é{~ˆˆ¥åx{Db'ˆ©p(ÅçüU5ÄÒÀ.zNV~ˆÑy{¢s«¶2⁄•zábhbRTò9ÜJŸ˚Mxcx{B\Ò≈TÔP|rJÇK5Ä$Ñß» =ø{^Ü∏»•HL‚ÜΩCõÔ†âÒ*D],#!$uÑgV \"„πgÂüÿ´n^,€•zábâ'∫j …HO ;oèî7ﬁ+oúSÀ‚ïV‹|™ƒ-™(å‹Ûã∞gúﬁû(EéJÚ–:¡ñ’ÍbŸ®BJ,Q5Äƒ‰‚fÂO%Ï	’§åÒú@ı)eíƒùj „^:`O¨∂âﬁ°_”bYs,ïß¶ëƒ)ë±ÿ∏Áﬂu?0ﬁEÆ± è7ù◊	DÔ–n °záH„:THDl¨¸çèáí\‰J§Œ—xy≈òçë'»£Ò©i1%†@L—DI`ÿ”2Aã\Qä…IÎ™wh\¢„L™∞∆
‹ÛsOõiÿ´ù<1VΩC±§3*]5ÄQ≈Câ¨¸çÀÿCMäz∞∞wH¸º2*áJå"’ ¢EA‚/π≤µÁW4în$ÔPÿáˆî§—%†@tπ %y{§ÿcÒeù∑M0r–‹ ™wh¨◊£@4	â∞áº=·∞G„ÕFØP´ﬁ°1ﬂéj —D$¬û,ÛˆDkÁh4©⁄è&"NÀò√æﬂû]°©ˆ˜Ñ}„Zÿ[˚!C B∑C.Ü›Ó‘Öﬁ&ØøﬁÉ0–⁄Ç˛÷÷¨	^ªùı/„!c‡lu‚Â^Œûp˝x˘‚ÂüÓƒÀ®MyX˜§ù€ˆ°w˜Ó‘ÜÕÔ£˝âØcÎ=?∆˙ªÓ ö–¥fMZî¨J2f c5,ÌÈ ∆Œ~_⁄´NuÖf≥3j>á—ËLuUìÆ|’ ¯Wö˚õ ﬁ[3ï_“HΩﬁÖ∫ü¬lÍìHÍï$0ΩÄï‡ ƒﬂË$aLıÉç†≤bãj≤=Ω`
√Ÿ;VDÉp»†¬!ÃÙ4 Ó˘ßÏ·-Ëı®´e8ƒûòÈΩX6Ö ⁄´'+ˇ4Ç=ÙƒQ=Õ	*+	ôß˜ú`˙¿4Ñ=Q-Äà<!ûQMﬁ°iá¶èpœ?çaÈ{‘ÉGÇ öû#¡Ù0 V~ˆD5 &≤LWÔ–Ù0 ˆ∞ûèﬁ°œ¶›bŸ‘6 Ó˘ß#ÏU’c'ÚH .ñ— 1¶…VÍ©k ¨¸*Ïâ≠Ì1Rÿ¶ö∫†¬û*>6YÙÒﬁ°i‡öz¿=#¶˙ﬁû±’89	Íj◊O˘mSÀ X˘Eÿ”ï‹€Wsã–”äq Òä±Hörß©e {Ü˝>|aﬂè◊⁄6‚ï÷X{h3∫ºé)˜Ú„y†ÄwàÀ&…VÍxûIŒ35Ä{˛	ÙˆlÓm¬Ø∂=ãGˆΩÖ«ﬂ∆ˇÏ]ãõ>˚o¨i˘\.ªåƒnz|NﬂΩû∑RBphÍçìﬁ ¥F/
j∑BÎ?4a
πÆsg‘≤˙Ü\QÈÈ Ë¬}kÌ¯˛]∏Ó±N‹˘œ^4u•£j±ùŒÉ~'<û~Ò~™ú&ΩÃ:ÂmÃø¯Tü<1øÖ„'ˇ˜˙ûÜ®Ô˜Ñ“√¢“SM˙qÔ⁄>‹ıB/˛πa Ø·¬oı·„w™´ñﬂÁ–·≥>Ï‹πnw˙Í6 EëIk ‹Ûœ9ÛuT,ﬂΩ≈É⁄ØÏCÌM–|IâjCO#‹√ﬁà2
6îõ
êâøC}√xu´ã`O®ˆ´Á.∑	ûA?Z{á±∑c{Ü¿FLL2bÔ”·ı7Ú–”£•¿KF∞IñöŸ'•∞Ú◊ù¯> ﬂ™ê"è’´$e{ˆ* înN.["E”~]ªÕÖfÇ@Úäøwj.ZA$u:}∏˝πn\Ú¿!úˆªV\x_;˛Á]ÿ(DÜ$NÌÌzºıv.éê™xΩ^466¢øÚ√°–S%!§tgeÿ√=øF'«¿ ≈&(‘ÑÍSé´IÓ·AÏËãÃ+@¿≤¸∫qïôl&?ÕuˇÙÜrÚ9´Dè≥ñZÇE?ÚæèºÔƒ∂ñAqÇº˚– ⁄i‘–&˘vÌ}z|¯Qz{µ¡∫§+ˇû={‡ren^$µ%ôkí"J¶ÍƒÛrœ?Á´ÿÆ¸RiZ√0jOo 8¥_4âœuè≥ˆ°»°Ω>ßÖ∆úxäòpûø⁄Oêf8XÆF ŒXbFUA@){»#ÙÙß œãlú∫»›»Ãú@Ñïˇı◊sEÿ√F-+èªvÌö‘ph“ +ø{ñ*aO¥√¥Íìi$·PHyò>Z88–◊P$˛Ø≥î¬¢5éñ5%i›˝><ÙûCQvæEÉìÊõ†QÓW∑àÿ_Œt‚<3éû9˛ˆ∂∑ˆ‰¿·[=ÿM÷9¡ÿO(ól„≥NyGú∆Í˘√õ∆#Å4'OãvÔ!¯≥ØøCº¶ c0iòõ[	Ω&–„ íR}wßª⁄ı‘Í•Ÿ&2¿~rÉ>ª~ ·ﬁ6Ç?ˇ˙\~¸Tw0¸‰Ô›¯øœ∆∆Ïˆ>¡[Tÿ£hàÏÜ·–Ó›ª'•w(Î@K~˛z—€≥Ò*øÙn¥áDÔ√°—ΩC√ÏËî≤ØVÍ˘k-%¡˚TGI≥ªhR€–>àÁ7ÙÉæ‰uÓÌƒ·w@˘˜öpƒÍÉxkG$ˇ`∑”º@x$˘’ãΩh!Oëº<yúï_ÚˆƒÇ=r~yúGÇù;wN:8î’¿ œ∞ß<Ã€#|<Òäm=ﬁ~ ^ﬁK1™ÃÖ·‰î‹≥Ú?≥æﬂ~§ó˛πœoåúè8‹~∞◊G°†q¥ÜÁeCy^Ùë,ö∑	˛±Ï€∑oRyá≤⁄ Ö=±ﬁèíƒ‚Ÿÿ€òwE—Õ<˘&≈Åï˚Y2Äw˙ÏÎPz∏¬´ñÊ rz}©˜^Yå7RÅwn≠¿{∑«◊¸†7ìÎî'—Ú<∑è‚Ì·ÙDœÿ;4YÀ≤“ ∏Á,r%{bΩ,6Ç⁄ØÏ%ÔPSTÔ–Ü(˛ÉÜvÒ‹XEN8›†fíã≥,7≤ó.Œ—‚Ÿ –xœt˛©ﬂ?-WQøñﬁ‰≈+¨‡∞§∆ÄÖU,®é≥Î‘§è4dV˛±º=ää‚∏·ë`≤¿![OîFV~Ü=·ã\’ibÃ!ïŸÊÓEÉ≥M∫^è,¨áQ£ﬁß:b3jØgÂ„«E∫\OY`¬Q≥å∞ô ?>W¬£bõ'Ã3!Z´›ÿìó∑'V±Ëlì¡;îu0sUbﬁûX/ ù?`°ØM¢Ò_í˛Ω?&ÉÄW»µ)oOéIÉUÕ∞P”ﬂﬂÂép}Œ´–c)ı¸úO∞ãﬁûD[‰ä'<<ì¡;î5¿=?√û #7&ÏÌâÁe»yÿp®–·˝émÚd1^f G•π@åßÛƒÆœ∆N%˛ÁâÎ±ı&±ÓA?ﬁ'/è”£ú–ìFçxæX˘«ÎÌë¿âGÜCl	dãõ5YFM≤LD~V˛T¬ûXm¨>πö_†œØ\Ie˛99∞ÈÃM[˘E∑¶›•TÓØ,6£td^¿[ﬁﬁ·V¥iNôß/∂(h—n¸D,r)˜ˆ9•A∂¬!MJü<Œ¬g•ˆƒjèál{1‡S*îûΩÍmÂ0i'ˇÛÎ◊m¬Í≠O·Á[ûƒkmõ‡Ò){yn#Ø¸Æ€„Å‹≈…®ÎOMx_ŸÍ¬Åeﬁo¨ÃÅ.∆õÏv„·˜∏ÈÒ.|ˇÒn<˘Ü no‡˙“ÿ;îçãe1ƒñ—pœ/ÓÌIÏâˆD√¥Ë¥£a ˝.Âv	´÷ÑY÷≤hY¶Ÿªˇƒ√{ﬂƒ.Gã8Ÿ˛k„€xjﬂG+Î›÷‚≈ñ^EÏª/!©Ωè“ó‹@ÿ;ƒ˚~8]
‹”˜Ù˚ƒo˝¸ ~L´¿O~Ïƒﬂ>v‡˜Î˜°-Cÿx$`8ƒ∆¿mî⁄õ…k∆@k¢é∑4«π∑'B≤;Ü±% Jjô9u÷R$˚Áˆ‚ÈÊ±π∑IQ‘∞ﬂáw∂¢©G9Ú¸◊€ }?ùÄK»µ)e˛p∑;√∂F∞Áß$G˘wœÕOt‚W/ÙÇaïîüØŒ¡AlÎÌÂhFAccc÷¨+%óFësüHhoO*ö÷c∆Á[#˜«,œüEê"“üHxe˘•÷œiÇΩ¨·yπá~iShﬁ»`9ﬂíjÊìwG¢ÒWaRúØfÚÎØúcªO˘ûCwˇ0Æz∞ØnqÅG¶Ö;A8-ù˜<!~·˘Á—‹LNàtV•Æ øÙ˚aMíﬁ$˝∑uÁ ¬&úzÍuØ∏,èÀ|„*ﬂ1‰¬„MÔ‚ñ·ŸÊué`}ﬁT˜ùŸßëg©0Xná#ÑÂ_ÁT(,cˇïså(¥^˜¸ª)7∆íÔˇhZê
‰èÂØ{¥ÌCç`åΩ‘÷ba~æƒÜS¿£$d “›”É;Ó∏</À1]ö€ên⁄*eÂúj[K!Û«”/uG4‚ÀG⁄∞Ëkm®^’<.#xÜî~MÀÁA≈ó*»”[px¡Lh H$B ﬁE’ó6)∂ÚÃZ¯2—H‡Y∑«Êf¶»äôFÃ-◊S"‘·Ø¿ÿE*Ë§°Úœ®™Bç’ä#_o4Ã≤Ÿ(5ÛGgg'Óøˇ~Ï›˝+ºt¥PìéJBu<L—W(x)dˆpì˝√ıJÃÕ-∫ÙÏbR¸aTüºlLã7lÍ›á∑⁄∑¬Oˇ¬ÛTõã‡Ñ€Í≈såÒo‹ÔEÕG‰yxe˜Xò∆n—∑»ı…k |/ﬁˆ ≈€Œ=ˆ°r•J¥ï••8¢®€Ìv8Ü£M-)û¡ ±d¸ ˚ÜÓæ˚n8p #m	ºÅîWÕ=?¡¨°ˇER   IDATö2Ø¸‘º¯F/º¥®ƒq)Tî∞Ù0ãxÀ.“Zq+uƒÿp»9‰&ËÛÜ|JœéXùñ‰◊¢≈›¸‡û:g∞ü° «{=‚ßåƒ<.< ƒˆ=‰—ŸDFL§ØúJ´√è˚ﬂÏ/ﬁ–âaŒqee`ºøô‡Üè`Üûzˇ•ÖÖ∞Ítƒë=«°Cá∞zıj444êxª•©yi0 V˛ø—„¨•êÈ^}◊—ò£óYQîØTi$–éÒküw7†”›Q¶D‡â6{3˙á<"©∫@'.nı–§ı”}Jﬂ?3úwD¿9ŒÈ·æˇ´è¡ò¶Œ!<ÒQh1OK÷µ¥† åˇ?loGÎ»/8Ã (¥(?üãÃ∫¿Fpﬂ}˜âFêŒ∆iR_√ûÏÈ˘˘y€:Ò≈.%Ê÷ìGÂpÍ˝-f•Hx$ç`îÌ]‰Ó‹do¢≈≠A.>jË£ıÄm}Õé=‹ÚöXtË¶ﬁ}}c¿(§åßf∆ÏRΩtãß>	)7ı‰†:sI»@¯˘Wa‹√Û§˜ìŒN|@¿yx>pQ]ùÿ˚˜˙®£#cÎ‹ûhÅ'ƒø˛ıØ±ˇ˛h…)°)ﬂˆÑV·¢“≤ˆPÉƒÉΩ?ˆ>%T)»’a˘b+MLE≈âç Ù°}$b¯≥€—™»Shı–ú∞ÀŸÇΩŒ¿Ø◊5z,.®|:¸˛5;\ﬁÄQ0áìò¯"Üè˜∫æıayùydƒ¡ÛÇù°åÒ;<¨!\=‰Û—ä∂WŒöÖ"£ë&Á>¸Ω±œ65·¡]ª–E|TL÷dòáxnêÔPäÄï?{º=Ú∑À´øÏ˚wêÁENØ†w~ΩYNäàWã⁄7ÉBûÿ<–âNO˛ÿt&úT≤HŒÇmˆ–$Ø⁄RÑZ˝‹˝b/˛˛IøÇèø‹:ua†wÁo~˛\è"ùoU¿^"˛}–ß?ÌGsÿ÷Êyë|Ï.Zi6jµ8≠≤ÚÚh=¬ˆÙ⁄ ÛNg˛l
lÈÚ•» &yfá∑á¢8˙HÒyıó'üÚÑU+sa6ç.V|≠
)3ó±ΩOy_i.ƒ í0hΩ4Û»√â•Òó€–á›r≤_(*∑ M–ˇ¸V65{E∫t2/ºJºπy˜¨ÈÖ”≠ïö…ÂŸ7≤ÿuvMæTRBÓTùNº—“"éìN,/!ëTv6]•√;4˙OX"‹Ûg'Ïë•≥{ümQˆ∫‰¡9ßH,£^Ÿ¬ΩCﬁ·ÄãQ Xh∞!ó¸˛gU%ëW˛µÈO:˜ë«H	}òÈHÇ7¸Â÷_ﬁr‡øﬂs`X©€`◊)›µô„ÍˇnGKîè‹*à·Œ∑ÊÃ¡ä‚b0˛ﬂG ˇyYˇÛ$˘À••òO£Û{V<1f8îJÔêf‚ûúï?;aè¸◊}ÓD8¸Y<ﬂÇŸµ!‹-ÁèóFÇhﬁ!≠†Aª€ty∆*caUh¢À<¸YcKÔVˇ£wΩ–ÇÔLVãQ@+Ò|Î·N∞Ô_ë8rc&7Á93f`)∏á`–˚‰f|tœ–‰WR˛S	ç∞gıÖç‡ﬁ{Ôœ	∏°&– ≤ˆ»Öˆ˜"a«Yß$Ó‰ë 0'8(¬yüı4‡ûˇ¿´mÂ‰`<Wg∆-G/ƒCﬂ®“8¬
œø˛¸Ëæ•r1)g•gŸ◊8±í≥ª≤?7)˝?…ìÚám€«Ì€Ò*¡Ó˘5‰]NcßVT õ{~Ÿ£àQV~ˆ•bÔ– ˜¸Ÿ{D)“ÈP« 6nS¬"cfµ-áº‚æ ^#`Z<Åç†ˆ+8ˇr˙êJπi≈∑€Î˚˛uÇÛs´á#˛9Úªxh≈¯ÛQﬂ≈ô3aFÅµE°uDÏ‚˘	œ%Ö‡_zÄÏèΩ>i‡v÷—™.ÔÛa,œ -±Ò¢{wíˇø√Ì∆ YñÅp√°≥hN`¶B‚ù,Wﬁ6ë
8î§∞Úg?Ïë^ÚcœvJQ≈ı€∑Ó√Â75‡∂o∆cœt–ÅC≤-
fŸçè4ïÒÀg∫p∆I˘–jCF¿lºˇÁ¨ #qÀ‹Ø°‘òõﬁL.IÂ6Ñª/,@E~h≤¨£Ë	ÛM¯œÀäp≈19‚áÓ\ñ<ä.˜‰WŒûçÉºÂÅÉYKôÂåg√`C9ó —˘µµà∆Clì‚hß5^,õ»ΩCI¿‰Ä=¸vﬂ˘®OΩ˝?œ£{›xvM7~˘«É∏Êñ\qs|≤çÕ∞ÎîÀ‡00‡√[Î˙pœü[q÷7v·V2öº-Ó˙Q5~peé-ûècäÁ‚¬öc∞z—%8Ø˙hZë5s÷®·dZÙz˙˙2‹qv>n>%O~ß~Ωß/2”‰∏Ì¨|ús∏“ã≤êíüG Ã!OØÀd%ˇJUÆù;'ºaØœQ4˘=ñº?_ØØ«’d(G“Ω“<≈¨ìÓ4—ﬁ!IÆ	
Ç{˛(œ
^
Ÿ}íKÒ√œú§^ùïUßã≠
Zî‚ï‚÷;pÁÔbÂ€P{ÃF‘Ω’+6`Óâõp’˜«á⁄∞y˚ ﬁx/∞•¢0_áÔ›êèﬂﬁºﬂ_xŒØ˛ L˘c˛¶®N#à{˛o>5wúSÄìòQhïΩñAŒ(òã;?7/X ^Yπ√˝˜zÇ8ºÎìw2,∫∏ÆÁRèœ˛û#ƒ~bL∫?ûˇ‚ø'∆….ñ…$ØX˘ˆºoÜ	‚1zΩÄ´Œ/∆üÔûâﬂˇ¢∑ﬂXâÔ´ßóá¥¯5öAHµ2‘ë‚“5?Wãü\W!›ä◊¿ƒ¯ ¢yáDÜNÌ‚Ø4Áäˇ9˚ÌY¡µ4ëM†à)À pËO˙»µõÃCé√ &Ïë¶∫¬Äcé∞·¥„ÛpÌÂ•¯·µ¯˝ÍZ<ˆáŸxÂØÛÛÔU·L¬Ò9∂H-/áıoÈa¸‡€ÂxÓ¡π8ˇåBy2)˛0$#P$$xcÆ–Üﬁ(ˇ9EÇEMYvû∞w(ô≠‘	 ˜¸ì√€œgEf8T¡[ fõÒù+JÒóﬂÃƒˆ7ó`›?‚dåÎÙ›
¸€¯≈-U∏˜Æ:l|e1^zd~≠
ÃùiA^_¿;¥7Êœ0ÜÛáﬂ≥ÚOÙœÜ◊1UÓy€D2ﬁ°8Äïüaœ⁄©"∑Qü£¶“Äœ,ƒ7..¡˜ˇ•∑\∫ˆ≤Rú{zä
BnÀQ°ƒ–bŸ0›≈w§ÚÁ
„k¡‰„‚9¡xΩCq¿#$ïÏ‹€CÀ⁄ÉGÇÄå´çˆ>b˝ü\q0çôÿ;484Üpœœ∞Áemˆ{{®ëYw∞‘ÚØRü…ªH√6ˆ»ZÀ ˇ˙»E1·ñÒ©—ÿ‡âÒœ˛ÛÑºC£ +ˇÙÅ=±≈:1)’'5¢z’ö$+ç¿O≈ÀΩ=t´IHÄWåyÔOê„)fxòÚ´∞áÑ0!èÔêÚ∑p˙ToœÑ»W^ªF„ÖCQÄ{~Ü=ìcëK˛‡Ÿg#®ï}hﬂGòˇı7r≈ﬂÍTaœƒæ=ÜCÒxá¬ÄΩØRKRÔÌq{Lÿ∏cÈ¥]UË,6Ω°á°›É"ók⁄€»;§l);ÿ;ÙË£è“B¢#fa¿∑ãâ9óBjª£ è=ˇı¥áG˛yxÚ‹ˇƒIx¯óßΩ~~Ê◊ûâ∫\(ÓÎ√¸ÓÓi ˙#wÂF”∏dhÉÀñ-É≈bâYkº,ëwåÃ¶˚;)îPH›·Ûp[“vÓ~œ<{
^Zs%^~Â<˚‹ÈX˚÷–—’≥Œ=˙ú~8˙5ƒc¶êLõÕËÚπ∞©∞kz òaÃ†Û˚†ÛMØ†M1ÊcÂ?˚Ï≥qﬁyÁAßãΩvf í¬œ†»ÌÊPòá◊€KÓ1^œ`øãÙL~tu}éææ]!xr°π˘El€ˆGlﬁ¸klŸÚ[Ïﬁ˝0z{∑¡O
då;‚á√t O√£Ô	Ê6C»°éáé Qç$%´’äÀ.ªW_}ıòÂƒ0 Œ7ãN7P(£0˘ßsÜÜúb6W /o^Ω∑w+vÏ∏ççGKÀÎ8p‡EÏ⁄ı
bp∞/Ç,Ç€–ç¶≤ó‡2t(YIÒ˝V¿î)Í›8$¿=ˇE]Ñsœ=Ç@¬£åQÄ33ZMEîRòÃá››õ·ı⁄#"7wÙ˙‹0∫ü<3Ãﬂ≠†sœØ’†—ƒRƒ?‹Ü.Ï™|Çîøù(~
aâ⁄oÛC 8äá•™∑qJ¿h4‚¸Ûœ«\Ä—`èº∏Q@b´¶»œ(∞1–eg˙˙ˆtV¥^£—£∏¯(Ëı6}hhÄ<{âﬂß†ÇñFãÖ$\´Ç˚∆'¡û=a∞'?èö\z%™ƒQL:√û+Æ∏b2EI iG°Fê›H‘b
È:&ÆÜ>«ûàu:x î«ß∑w;¬ˇÙ˙2Ä˘DVÚ!Í·"ÿ”ˆDÂ&"Î≥¯†Õ”“çzƒ+Ü=_|1æˆµØ≈õ%»ß–õA=e∫ã¬‰ÉC.WıË‘vÂa±T†®hôíHwnw'î?vEdçÖ(,d71ﬂç¸p:Gá=±≤ì®á-√–‰—´°x,6ïê +<ﬁû w‰ô§IåMë‡–‰ÚµµΩıë**N"z§ñµ∂æIÙ»£®h9¥ZsdÇÇ"y{ûÅWÊÌQ∞ƒq√#ÅÍ]P{.ø¸r—€#ëÔqÙ‹Å‘Ä31ö\ﬁ°ññhüo
®©9ó("∞˚3ÇHÑ∫∫ãË<˙”€3z∂»Tzü<'ç 2u⁄Sx¬{…%ó‡úsŒÅ ê∞∆)ëq W∆‚’TejÀ®Ç§èææ›`^PYŸJy·d∞ªtp0“[ƒÓRõ≠.Ç?DèÌÌ	1«#Q≥wHÖCJq1Ï·.Òz{î%ÑÓ∆a Rf	Òà —≤Ôz‡+QUUuZT:˚¸£%Ãúyi4Ú- {‚ıˆådä}	Ka8§záBaÿ√ûJrÁ$Ä+Êë‡&ädÁƒÿÁDG««‘>ÂaµV£†`âíHwÏÁ?tËä)ç∆ ∫Kï‘–ùã¸¸QπB,…≈h$Ar%MÍ‹‹Û_x·Ö‡IÔD=Hí@oFÙ›IÌ…æ„ﬁﬁ/‡ÒD˛\^ﬁÚ˝á/~AÑ?O‰èg±ß»dä˜$oœì‰ıâ±»EíôêÉDÌ≥˙¶Ìb+?+~"ã\Ò»=Iê™`8t›dówàÒˇ‡†r+,˜ÊEEG@ß≥R{ïá›æ·¸Ä ˙˛ıaãe@`ë´°"9o¸Nå… Ã:iŸm6õ∏¿uÕ5◊@&ˆ¡'» X∂<`ÔPv¿!^ÕÌÈŸÜA‹:)π»œ?L∫^}æ!ÿÌª1<Ï
“8˙h   IDAT¢ß≈ØÇÇ•$xÂ‚{{Z‰‚¬&"–˚g#ÁQ^ñó¡ﬁ^‰‚ﬁ?Mù@†7û∞w®8mM®LÓ…Ìˆùyÿõìó«´π §¡¡>2ÄmJ"›˘d0(&)ˆHE«{%Q3“ÚèÍR<ﬁlìÅOﬁFÜ=ÏÈ·ê¨∑G^Æ<ÆëﬂLLºÜä˘^9¶KÜß≥˝˝Mµ◊‘úE¥H≠Òx∫¡˚Ö(Qq.Å—X4BK≠∑g§í∏/ºïZ	"'Ó2≤ïëΩ=º»5QﬁûXœô‡™X˘yÔPÊ&∆mmÔFlf„ñUVFwvv~å°°»Øî™™Œ‰lbò(oèÎãfº˚˙∏y{'ûÔrAπEO¨*æ)>{áRπX÷04Ñµ€qUW~€◊á^ü/æ∂%¡≈=?{{xë+âb‚ ö"†7ÑCÈ7∆Ûº!ÄÍÍ3£N~ô±Ω=“˝…=qÒrJˆÉïw•Ã€„Ûc∏w ˝ü6†˚©–~ﬂ´ËzÏ∏wµ¿˛{Q	“·¸`˙^€Ñﬁ∂^lqzqœûj¿∞_‚˚ ¨ –=‰C’e7c´aø"Ωîı
ˇ·p†u8∂iq
+˜}ƒwÒﬂﬁéovwcùÏøMm°¸∑ıˆ‚5∑;…ûqπ∫∑ß–Û≥‚≥§
ˆ»%ú"ê™»åw®ª˚söÃHç^ÀÀyÔO6qπZ¡_Ü	#ëöö¿ÓBﬁ“,ˇíÀÁDˇ˙Ù<˜úÔo«`K¸ﬁAu9‡Xªﬁ˝ëÆW.í√≥ßç£¡‡!CzºΩOw`à5;ò=‚ı˚Òj∑w6ŸÒ”ΩΩ¯Ÿ>;V7ˆ·;∫Oó{IQ˜Qxj`@4VÙí®å«˚˚q)Û£ƒ◊D¸n¢mƒ=dí·∞Å4í»Ûo%ûª»–vSû8ö+œ:f\ÚˆƒÛ%◊òÖ≈…êb‡V∞wËzäDÛ£9GS”s•Ê‰Ã›ô	DËË¯$.	ÇÂÂ'"‹€„s∫aq=˙?⁄Öa{§ë±q∏w_©h≈!hÄˇ'<ËÙ·˛V'nÿ”ç˚<$ec	ﬁ∂z|¯›Aﬁµ{∞©ü—(Úæò'»å|Íı‚#YèŒ	=‘{Ø&HÛó˛~¥Ö)7ß˜S›íi¢´«˚TÊ…x˛á Ë¢Ú8_≤Å{~ˆˆågKs2uG¬dJå»+ÖÁ´È:öPÚCCŒ®ìŸúúŸ¥¯eã®ÅWx1Ç.∫JÛtä-Õæ~˙ﬁ‹
os∏7ÁLÇN]Q¥y`ƒGÕ–Ò¿´Ë˛€{ÍëÕ+(›4ø
—˛‹4lp‚˚Ω∏jGZº—˙n‡	-˙˙»À‡óXa–¢HØÅ K‡˙†L…]§‹8ùxóX22#µ©F´_ˆWBÙπ:]‡Y œ_®¨s;;¡£…ï¡'Å1?ª9SÈÌâ’M¨Ñâßœ†"Ÿ;4áÆ…√√nÙÙlÔ€/©´kºﬁ^Y£1†®hπˇ≥‚s9ºX60†Ñ%úYSl¡˛öWB∞ìÇ:ﬁ›OCàW0Èa=f.äÆ<∂ïÛ!Ëïk√4Z¯<êˇÒ"øèﬂÎ∆-Œà§ûaº‹„é†üV`¬˝ı∏°“ìFn†Â∫˚ë^!<œ
ÃT+)ˇ∑¨V‹ôó≈ôf†k¡HœœJÕpâÈ±Çáˇ*sº#{{.ãÛˆXmHÜûF‡fÚ:/ñ%71ˆx∫∞i”/Ò·á◊‚Ω˜Æ¶¯]ÿ∑ÔI46>ÉÊÊÁ…õ£TA–àˇÛœo«∫u◊âyﬁ}˜r∫^ÖıÎuªDOÛ&zÂ5◊sÀùÔÜ{gG≈ î±.üÎ3RVlˇê≤◊÷XM–óÂâ¸|bO#oô†,DXj5–9˙1ﬂ¨èH¯_Í˝yŒ O86◊àõ´rPe‘ÇGöC˛óC
Õ˜{≥ﬂO=6c}æËtä…ÑK,∞Q04"Jà∆HØøé î4Ç‰–3V–à¿<·°î“Lî/ú>÷=˜¸“ÏcÒ¶*=Õ¿büMœ≤ö¬¯ç@ß≥¡j≠∆¿@Ïˆ§Ù/‡ã/~è≠[ã∂∂w"<˜Ù--Ø°•Âu2Ñœƒ<«^8ùMpπøRq©qÑ·›`eÌyÓc∏∂6Sÿb‰$1ËJra^L£Ω|øwÉm4Í–(!&éú,Kk¡Iº•û“M£áœË¡WYª˙|‹3+_Lñü 	Œ\Vjñì–FêË˝>ØÇñCFx^±≈}|î“Óı¡KıP4xUdÇóƒ~/MnÂΩy)ÛÂ§¸L{v 0óae∏∆fÉñr3˝1¬¯£xT¯w%((@∏∞‚≥!Âë([‹+¢∞«]xå¸Ã	∞O+{án°¬,?x;√ú9◊¢≤ÚT¬ıëõ⁄‚+QC∑.*´Æ–Cmâ8ﬁˇÈ0˛2Sog;n4Ê@ÓsyEOP0ù"õ	¶yïæ/‹€ÄG	Aß<ö¯ı:<Hìﬂ G‡¨'eΩô†åÜÍPÁè^tÖaˇ√,:¨»	¥aÄ∫˛˝û° Û»πî£$O¿ß:/∂“0B/ÁöÕ`#¯dí˘k4‚
Ã)?ªA9˛U)é0V®SO£≈Ò#yò7û†%„;˛Ñƒ˝=Òßí'C¿èTJ'˛¿$È&ÅC@~˛,Yr+VÆ|+V¸ııWìóGæeA*N@]›Eò9Û2,^|+æÙ•˚p¸Ò√	'<ÅÂÀ#1)Æ9´#ÔÃeb`E˜íä»zV√åb™
ÉyºMv(˜ôTA0ËÇ<ÆÕM4J>¥—W¡X[åWœÔrA.`¡¢#rî2qêØˇ}Ú˙Ñ√üs©˜ó0?ÛÑóµ2œ∆Ëê‚:dﬁö2R¿ã®˜goOàπ˙2ç◊Ÿlª:◊–|Åo â~)Ò≤Ôˇmö<áè0°§9Ûè4T^ee%Íg3ã;ıÈ4 ~8+ùÊRPæp"ƒuËD(4••«`˛¸a2ïF‰´¨\ÖEã~åÖoAmÌ˘‡üA·_Ç»!∑høÚß 93˜‹RPç… >ru˙˙∞Ö”9X˙H=4¡ˆ˙0]
MÜMxîPx]¿InSÜPÇQèúì¡M˘;$Û´ézˇHiu ◊“J–fπ;â%xî4Xïo
ﬁ7∏á¿ìdâ¿eùNì„5ÿ] PFJªåz?ç<'pía3ƒπî&√3©7gËÛøâ:»`t‘∆sàóÁº∂∞â÷ §2¯ ∆q:çó{ó˛èÚˇâÊ;àü°ôî∆ _VVÜÚÚr=¨îê¡´R“iàôjeœE«yxΩvtt|ñ[@E≈)a¥–-œBwÅòeMjQÒÏﬁ”*^•ì∆b „ÈﬁCΩø˜†Ú¥x‚ÑGd<Œu;Ï∂cÁAk3·Ç4vÚˇÁBr©÷˚Û‚ÿ√mN8‚∏Áoñzkæc%7¶π4âÆ1Íù.Ïëç26jÉë2˝-fÌqëûCpËlRd-—?†^˛C
ª@9çÈèìR3Mæ>2bH462%X˘ˇJÍI √#ß3Ï·ûø∫:‘10=”!ÄE`°”x·e•£Ω˝Éà≠œ6[ÚÛRj‰·ıˆê+u≥"Å'¨∆∫mÄRπuÖ9mÙ"èﬂ3à˛uëø+™++ èºV0∞°ë†Mê)áqVYp^`Ôr`ê&œDï‘´◊ôt¡{é<D ˇ6¡éK°Ü<>+rC£Ê•6”ÇîÆ•ŒıxIûÔv·âéÖ+‘MZzıŒºµÅ˘y"|)réF^˘˝≠√8çÈ≈D¶QÇ’ò&ûÙ.◊‰ —:»†&≈Á¸Ïb=ÜÊ<IÊûüïü{~â7[ÆYb ,6Çy	ΩX∫âÎ”j!/O8s>)?Oò√È‰Œ¡ÅÉ/"!l/K‘Wí‚íÎRF˚ÚÂ˜∫‚\‘≥Rf∏∂∫I%6"]°ïí˝`h4∞a/@0IõcÜu˘¨Äa,foµ[ «◊ìÚç–íÚrú{ıwHÒü¶<¨Û«—‰˙,°	.Û5Ùπó÷òüÔ9Î§:mÎG¯ºÅ}˚¨†<w∏ f„~3¡ëFÇD∑ˆˆÇ±>C¶E_–oë«˛s.ÂíqP≤xpôøu8¿ÓV&g4‚TUàáüÉ å<3dI»"`âòË4á]‚<\Æ8˚‹Z≠ÖÖK†ç¯?∆fÏ˚©z9˙≤|h£K˘Iq•∏t»É#h5∂ˆb`S£Ë’ë“¯ _ûGêÁ»Ò÷VJ'’§˜n]Q}e`‚Ãû†·>Â§ôÛZ®\ær‡≠ºf'EÊ{)∞ÅîÎ5`‹ﬁEÍø»ã‘¡ìtâÅÆ¨ÙØPÔÔä“~JF≠QãWÁ‡[£åâ´ˇö Q3ı‡<˛úF {!aÊÂ )5«•`†C#∫ÄÛ›”◊'Æ0Û˝2n …ÅA´EUUïò-döñe¿‚`ÂOıˆn–¬π•`0‰ì.›Øº´≥A˜úa√ä´Ø( H!$fAóhCm=pæ∑ˆ?√p∑r¡çyDÿ≥æ˝üÏÅË="√≤≠\ ”¬Në¿F$ﬁ»Nü”DóΩ=ømÓ√ø5ıa/ıÓ≤d1 :˝≈¿ a˚\øßè¬Gà^2ÁÒ¨"ÓTƒ¨¡S–*ö ˚,~<:Ë¬è®Áﬂ82aùM=;˜˛9Ç‰◊»‚Ò Mí?ßÖ2^C∏ùÚøJû&N„âÒssQFÂ0Ï)£I/”≥5d°∞®xBÚ˚áiak;Ü¬ˆÚ[,U‡9 ó~∏ùÿU˘$}{‡#¸†Œ<i’óÁndg—(d˜û∆q'®Ë“êè†?ûH{Öÿƒ=øÂôê+ºhl≈9 W‰k∫›¯¡ﬁ^<C∞ßè\üÚ4)Noızpw≥˚»@xí,•IWjÍi.ÒÁ9¯ÍÂu ◊ºëÊ'nj«I[⁄q_Wÿ„£•ÃÛt:¸g~>ÿMJ∑¡„$xƒ	(¬;Hb∑„7v|¢qÂ‘„ˇÑî>A'V¸lÖ=‘¸‡°îLêúÓπ±1ƒn{∫ª∑D0‘’]$£˘¯œ)ûÅG”/o_T.ÈE¸œ˛Y6äöi5W>*I<¬∂¶9ï»9e1@që(;i»”√=øı»Ÿ¬êø∂"E‰©ëeQD˘≈
J|7º)Óä+~=3Àl\·¨"3◊«*Åa–Ÿyf‹Sêﬁ Œ«~˛»SƒFû∆˜‹÷£IÈÔ Â?Å†√ûlÛˆp;£n{4zñ–,‘é:

—€`è±  aIDATÜ>}};âZ≠ë÷Viº•Y˙›Ó°á:RAäòÊU—9Ú0Õ*áyQ†âJ†∏ıÀsësÚ"òÊT Á¯‡ﬁ^Ã-‚
r¡π+ nÖê-ÜâÈ#ßY‰Ó¸›Ï∞∑F'åÈ¢°¿´ªﬂ•’`ä*é9fd¨ä¥:ÍÒD∏˛ﬁ˙|∑“
æg^VÓk ¨∏¶Ãû?(2—Õa=~33ﬂ´ÕAEæé(—èk…St3·z69G>ˇ˜à~g^V–§∑íπ∏˜óÛdsúÂùÕÌ£∂Y(Ã£›|√√ óuuBKF r ÜˇÁÏ}˜ÌPâ“¡æ}cù“˝)•	‰Ò…]µ≈WùÄº3ñ!üª‰∫”a=™öÉﬁBk≈ﬂ\Ö¸≥è˘
Œ?:∞V@iR9·WÅu&-~7+Ô,-√3á·—yÖxsi)Xâ	ﬁ0‹!6Ò–SY∑÷‰‚Y‚˚iMnÆ≤·'§w‘Ê‚ÂE%¯˚Ç"\\bAçQÊ3çúrHÛøSa√õKJq7ç?•|∑QYèQ}Q¯rÆ‚ÌgmT?/†ΩZRÇ7(<VXàÈ˙¶|b»√AÑëö≥ˇíAHD8áÍ)ÉÖÇÚhm]´ ∞‚óóüL¥ Ï	ˇπBë≈3I‚êéX{Ù•tæj¨`>„Ã“Poœ	#Ac6¿8ª⁄"€%˛ãûÙe⁄Íç-Ì‰›yù|˚Ú[ı®&ÂÆ&æä-∏≤‘äI·œ*4£ò&µrﬁXq3ïÕ´«P>ﬁD7üÍW ü≈á±>¥g˜Á|ΩºîÎ‚EÆ™,˜ˆp;£ÖÁè∆ì%4+µc&Ö–H–’ıúŒF¢Ò!†®ËH,^|¯ˇ¸r∫ ¡NïÇk€~)∏Roeö[àg…yπ0˝°∆ê}`ôMè<ù&DLUå*AuhUTT†,ÀΩ=±%çUıxË<Ã£å#»ßÖ.ﬁÿvÍ©k’ØÆ√1«‹èÍÍ3‡19¿ﬁóÅ˜ﬁá4i∞•>g.	:-˙hÛÿ∏êÏª±KπFPH=<Ô˚O€Àb#à„gY˘YÒŸ Å2eÖkD⁄döX≥F„6Q‚
V¬˘&∆6£±à†8?ä“Ï^}Ëø"%fÒπ¡∆¥†÷£ÁÄ'±4ñÄAâL>}‚¢;Ã∑9õ&∏siúÓ¶Ò/–â?πE∑%ÿ3Yº=±d«Z+-ãÈj[•‚≤∑g¥ü+4–D7˜+Àêªj1l«ÃÉôß¥π\ïØ]mÎÑ3l‡´¥òe ¸ûˆ&í‚≥àsYÂ‹ÛO6oè¨˘äË$5 ~V‹πa##‹€C	á†’Ä=7Ç^–ÀE¶˛b‘À[ó˘√óhätúQ`éë#díìè‡êv‰g5Ñ˘ˆîg—ñÊd§†I&sÊÛ≤b‘Ï±cO˘”°ÿ3ﬂ∞qµ†—3ÑŸ÷e.‰“R6tée6õá°£uÇ ™JögUg∂1X˚$7 ñÑZﬂ<¯®g‚ª…ÿı)ﬂuôß’‡∏º»’ÈL<£Ü‰[^Vô®?UuN Ãﬁò€ÚÀR%ßîó€OÄ∫‹äz'◊g	√55˝7AÉ2[*r* Ñâ“ﬂÑî’8%Ä•cÚVcNÎm∞∫Î˘v“Ö…˜œ{ı•ÜÛ§ó∑Dÿ¥ôU8≠Fã™‹*TÁVKMõR◊)c ¸V,ûY®møÜ°bæù4ÅΩûºTﬁ‡|R¸Â9dR˝5‘ÛWÊT¢Ã:q#´¸≥!>• §.VO=Êºì‡P	&Àﬂñ~/ZΩ Ø”ÊYÙòe“eÏX˘YÒÀmÂÑLöajE0≈  ,3Õ	Ê¥ﬁNpàÃ¥l=Û>˙Õ‰˚wÑ˘˛/)±d¨…ZAÓ˘´Û¶&ÏëvJ ? √°:ÜCY>1ÊEØçd É∏›jåZ,∑8öˆ¿=en%∏ÁO{Â®p   ¿‚ôçy-´	ï"[ˇ¯WxõCÆ.Ù*Œ(4Aõ‘°!ÃœäœA2–Äº§ê‘3Py:™4âﬁ°üâ∆êé˙≠ÉΩ=_/≥‚Œ⁄\|´‹ä+h·Îú"s¢≈$Õ/y{ÿ„ìtaì®Ä4@Ê§b!ÔP]˚ç4gÆ£‘Ã˚Ùy∑Áµ6‹XôÉt˚˛πÁØ¥MmoO,ÒO ¡!^ò◊rAˆ¬!Z>!}Ç=¢∑'gj{{bItö@‡Ò%8dugøw(–‚‘ûEÿìSÖÈ‡Ìâ%…ie ,Ñ ¢≈≤,˜q[S∏ÁgW'oqHe=Ÿ^ˆ¥3 ≤ΩC%òé¨¸ÏÈ· i∆\Y&ih Å7¿p®æçΩC≥ÑTû≥®l^‰bOá,jV∆ö2mÄ%nuœ∆ÃC7eıƒò€9QÅ{~ﬁ—…ìﬁâ*s≤ó3≠ "™ß≈2ﬁ;4u7|Å˛X˘YÒŸ az√GòÊê√°¿VÍ©ÈΩ=º•yÏÌ	º—¯œ3 õ8ÛÃÏ	ÆöÖÎèºÛ™KQJK©˛Fl\ZÇıáó¶4l>≤9Á]ä≤ãæë=¬ÊøhQ¸ZöBŒå@a!p›uŸ¸_f„ÒoÆ∆Ú≈®≠EJÉ°kOÆ¡Àß÷¶,ºÒï90›xÊ‹˛Æø>#¬é˘íè;.Öj—3Ä¯õò^Œöº¸Ï∏ü°æpr~Y&IÀ™∑‚Ú≈ó„ä%WH$ıE™DJ}A=n\q„§˝ †5‡¬√.ƒ9ÛŒâÚt*I.’ ‰“âÇÄŸ≥±˙ƒ’‚«‡#‰Iq1jç¢‚≥Ë4∫I—ÊL6R5ÄQ§œÇﬂ∂Ú6Ã)ú3
Wˆ$Ÿ6Ú\ΩÙÍÏiTñ∑D5Ä1^–¨¸Y∏˛®ÎQb…Óm‹Û_ºb|mÓ◊∆x"5Y.ÅÄºö…Aú3 V#`Ãˆº≥qﬁ¸Û†¬ûƒtM5Ä8Â5#oÜË 68ƒﬁûÀ]ˆƒ˘"√ÿT»h∑<1æa≈Y31Êûˇ¢Ö·‹˘Áé÷l5m	®0äp¬ìaƒ;tyá2¸cQå˘œü>.XpÅ
{¬_T˜™$ ,âUÙwõ87êhÈºJﬁuë+y©´0NJﬁ°bKqd	)§à∞Á∞ãToœ…X5Äq
Rq}‡ó'˛•÷“qñíX6V~ˆˆúø‡|ˆ$&∫ò‹™ƒM|	5#{áRÌRΩ=ÒΩèDπTHTbQ¯âﬁ°MåπÁÁE.ˆˆ¢¥@%çW™åWr≤|Ç0‚:qıÑ√!—€CêGÖ=2ÅO`T5Ä	¶ËZyfLÃáˆ{ÆX|8L`3SZ‘d+\5Ä	~cºXv”äõPbMnÔ√ûãÿ€3O›€3¡ØHQúj 
q$#Ç∏>¿ﬁ!˛}<%≤Úãﬁû√Toœx‰óH’ ëVº"¢≈≤DΩCVÉUÑ<º∑GP'º	H||¨™åOnqÂíºCÒÆÑ˜íÖóÄ{U˘„q“L™$-¬ÿB¿;tÁ	wb¨cÜ=ºùôÉ∫•9∂L':e`¢õ6u „__æ˝∏€≈œ,£={{‘ÿ£I&ı4’ R/c±—;tÙMÎ‹ÛÛ˜ªÍÏ¢ò“~R M"Ñ8t‚ù¡_õ`Âgº¡aÍñÊ4ΩÜàjTàIj	íwhY˘2\π‰J\≥ÙÚı©≠T-=¶Tà)ö‘%∞wËG_˛ë∫•9u"éªd’ ‚’(å	&	ÇÄ\cÆ∫•9Aπ•Ç]5ÄTHU-s“H@5ÄIÛ™‘Ü¶B™§B™jôìF™LöW•64P RùFeNˆG˝ˇ   ˇˇ´⁄$c   IDAT AÜ∂%âÈÓ}    IENDÆB`Ç```


--- File: lotteharper-main/logout_everyone.py ---
```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')

import django
django.setup()
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.sessions.models import Session
Session.objects.all().delete()
```


--- File: lotteharper-main/logout.py ---
```python
import re, traceback, requests, json, regex, sys, glob, time, threading, datetime, asyncio, random
from subprocess import Popen, STDOUT, PIPE

def run_command(command):
    cmd = command.split(' ')
    proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, cwd=str("/"))
    time.sleep(0.05)
    proc.kill()
    return proc.stdout.read().decode("unicode_escape")

import random
code = run_command('sudo tail --lines 1 /etc/banner')
new_code = random.randrange(111111, 999999)
run_command("./home/team/lotteh/set_code.sh {}".format(str(new_code)))

with open('/etc/apis.json') as config_file:
    keys = json.load(config_file)

output = ''

def unique(thelist):
    u = []
    for i in thelist:
        if i not in u: u.append(i)
    return u

def check_blacklist(ip):
    try:
        with open('blacklist.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.replace('\n', '') == ip: return True
        return False
    except: pass
    return False

def blacklist(ip):
    with open('blacklist.txt', 'a') as file:
        file.write('{}\n'.format(ip))
        file.close()

logpath = glob.glob('/var/log/auth.log')[-1]

def load_path1():
    global output
#    print(output)

def load_path2():
    global output
    try:
        if glob.glob('/var/log/auth.log.*')[-1]:
            run_command('sudo rm {}*'.format(logpath))
    except:
        run_command('sudo rm {}*'.format(logpath))
    sys.exit(1)
    logpath = glob.glob('/var/log/auth.log.*')[-1]
    output = run_command('tail -n 5000 {}'.format(logpath))

thread_started = False

from lotteh import settings

ipv4_pattern = r"\bAccepted publickey for {} from ".format(settings.BASH_USER) + r"(?:\d{1,3}\.){3}\d{1,3}\b"
ipv6_pattern = r"\bAccepted publickey for {} from ".format(settings.BASH_USER) + r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"

output = run_command('sudo tail -n 500 {}'.format(logpath))
#time.sleep(1)
op = output.split('\n')
op.reverse()
output = '\n'.join(op)
ips = unique(re.findall(ipv6_pattern + '|' + ipv4_pattern, output))

thread_started = False
while not output:
    print('awaiting output')
    time.sleep(3)
    if output:
        op = output.split('\n')
        op.reverse()
        output = '\n'.join(op)
        ips = unique(re.findall(ipv6_pattern + '|' + ipv4_pattern, output))
        if len(ips) == 0 and thread_started: sys.exit(2)
    if not thread_started:
        thread_started = True
        load_path2()
        break

if len(ips) == 0:
    sys.exit(2)

ip = ips[0][len("Accepted publickey for {} from ".format(settings.BASH_USER)):]

def thread_function(ip_address, code):
    global ip
    TIMEOUT_SECONDS = 60 * 5
    t = 0
    from security.geolocation import get_ip_location, get_country
    latitude, longitude = get_ip_location(ip_address)
    country = None
    if latitude != None and longitude != None:
        country = get_country(latitude, longitude)
    login = ShellLogin.objects.create(ip_address=ip_address, code=code, latitude=latitude, longitude=longitude, country=country)
    while True:
        try:
            login = ShellLogin.objects.get(id=login.id)
        except:
            pass
        print('{} {} '.format(login.validated, login.approved))
        if login.validated:
            if not login.approved:
                sys.exit(2)
                run_command('doveadm kick team {}'.format(ip))
            else: sys.exit(0)
        time.sleep(10)
        t = t + 10
        if t > TIMEOUT_SECONDS: sys.exit(2)
    sys.exit(2)

if ip != '127.0.0.1':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
    import django
    django.setup()
    from django.conf import settings
    from requests.auth import HTTPBasicAuth
    from shell.models import ShellLogin
    from security.models import UserIpAddress
    for i in UserIpAddress.objects.filter(ip_address=ip):
        if i.risk_detected:
            sys.exit(2)
    FRAUDGUARD_USER = settings.FRAUDGUARD_USER
    FRAUDGUARD_SECRET = settings.FRAUDGUARD_SECRET
    RISK_LEVEL = 1
    def check_raw_ip_risk(ip_addr, soft=False):
        try:
            ip=requests.get('https://api.fraudguard.io/ip/' + ip_addr, verify=True, auth=HTTPBasicAuth(FRAUDGUARD_USER, FRAUDGUARD_SECRET))
            j = ip.json()
            if int(j['risk_level']) > RISK_LEVEL:
                return True
            else:
                return False
        except:
            print(traceback.format_exc())
            return not soft
        return False
#    for ip in ips:
#        if not ip == '127.0.0.1' and check_raw_ip_risk(ip, True):
#            run_command('doveadm kick team {}'.format(output))
    print(ip)
    if ip != '127.0.0.1':
         thread_function(ip, code[:6])
#        x = threading.Thread(target=thread_function, args=(ip,))
#        x.start()

```


--- File: lotteharper-main/logout.py.save ---
```
import re, traceback, requests, json, regex, sys, glob, time, threading, datetime, asyncio
with open('/etc/apis.json') as config_file:
    keys = json.load(config_file)
from subprocess import Popen, STDOUT, PIPE

output = ''

def run_command(command):
    cmd = command.split(' ')
    proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, cwd=str("/"))
    time.sleep(2)
    proc.kill()
    return proc.stdout.read().decode("unicode_escape")

def unique(thelist):
    u = []
    for i in thelist:
        if i not in u: u.append(i)
    return u

def check_blacklist(ip):
    try:
        with open('blacklist.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.replace('\n', '') == ip: return True
        return False
    except: pass
    return False

def blacklist(ip):
    with open('blacklist.txt', 'a') as file:
        file.write('{}\n'.format(ip))
        file.close()

logpath = glob.glob('/var/log/auth.log')[-1]

def load_path1():
    global output
#    print(output)

def load_path2():
    global output
    logpath = glob.glob('/var/log/auth.log.*')[-1]
    output = run_command('tail -n 5000 {}'.format(logpath))

thread_started = False
#load_path1()
IPV4SEG  = r'(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
IPV4ADDR = r'(?:(?:' + IPV4SEG + r'\.){3,3}' + IPV4SEG + r')'
IPV6SEG  = r'(?:(?:[0-9a-fA-F]){1,4})'
IPV6GROUPS = (
    r'(?:' + IPV6SEG + r':){7,7}' + IPV6SEG,                  # 1:2:3:4:5:6:7:8
    r'(?:' + IPV6SEG + r':){1,7}:',                           # 1::                                 1:2:3:4:5:6:7::
    r'(?:' + IPV6SEG + r':){1,6}:' + IPV6SEG,                 # 1::8               1:2:3:4:5:6::8   1:2:3:4:5:6::8
    r'(?:' + IPV6SEG + r':){1,5}(?::' + IPV6SEG + r'){1,2}',  # 1::7:8             1:2:3:4:5::7:8   1:2:3:4:5::8
    r'(?:' + IPV6SEG + r':){1,4}(?::' + IPV6SEG + r'){1,3}',  # 1::6:7:8           1:2:3:4::6:7:8   1:2:3:4::8
    r'(?:' + IPV6SEG + r':){1,3}(?::' + IPV6SEG + r'){1,4}',  # 1::5:6:7:8         1:2:3::5:6:7:8   1:2:3::8
    r'(?:' + IPV6SEG + r':){1,2}(?::' + IPV6SEG + r'){1,5}',  # 1::4:5:6:7:8       1:2::4:5:6:7:8   1:2::8
    IPV6SEG + r':(?:(?::' + IPV6SEG + r'){1,6})',             # 1::3:4:5:6:7:8     1::3:4:5:6:7:8   1::8
    r':(?:(?::' + IPV6SEG + r'){1,7}|:)',                     # ::2:3:4:5:6:7:8    ::2:3:4:5:6:7:8  ::8       ::
    r'fe80:(?::' + IPV6SEG + r'){0,4}%[0-9a-zA-Z]{1,}',       # fe80::7:8%eth0     fe80::7:8%1  (link-local IPv6 addresses with zone index)
    r'::(?:ffff(?::0{1,4}){0,1}:){0,1}[^\s:]' + IPV4ADDR,     # ::255.255.255.255  ::ffff:255.255.255.255  ::ffff:0:255.255.255.255 (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
    r'(?:' + IPV6SEG + r':){1,4}:[^\s:]' + IPV4ADDR,          # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
)
IPV6ADDR = '|'.join(['(?:{})'.format(g) for g in IPV6GROUPS[::-1]])  # Reverse rows for greedy match
output = run_command('tail -n 5000 {}'.format(logpath))

ps = []
thread_started = False
while not output:
    print('awaiting output')
    time.sleep(3)
    if output:
        op = output.split('\n')
        op.reverse()
        output = '\n'.join(op)
        ips = unique(re.findall(IPV4ADDR + '|' + IPV6ADDR, output))
        if len(ips) == 0 and thread_started: sys.exit(2)
    if not thread_started:
        thread_started = True
        load_path2()
        break

#print(output)

#print(ips)
if len(ips) == 0:
    logpath = glob.glob('/var/log/auth.log.*')[-1]
    if logpath: output2 = run_command('sudo tail -n 5000 {}'.format(logpath))
    op = output2.split('\n')
    op.reverse()
    output = '\n'.join(op)
    ips = unique(re.findall(IPV4ADDR + '|' + IPV6ADDR, output))

ip = ips[0]

def thread_function(ip_address):
    global ip
    TIMEOUT_SECONDS = 60 * 5
    t = 0
    login = ShellLogin.objects.create(ip_address=ip_address)
    while True:
        try:
            login = ShellLogin.objects.get(id=login.id)
        except:
            pass
        print('{} {} '.format(login.validated, login.approved))
        if login.validated:
            if not login.approved:
                sys.exit(2)
                run_command('doveadm kick team {}'.format(ip))
            else: sys.exit(0)
        time.sleep(10)
        t = t + 10
        if t > TIMEOUT_SECONDS: sys.exit(2)
    sys.exit(2)

if ip != '127.0.0.1':
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
    import django
    django.setup()
    from django.conf import settings
    from requests.auth import HTTPBasicAuth
    from shell.models import ShellLogin
    from security.models import UserIpAddress
    for i in UserIpAddress.objects.filter(ip_address=ip):
        if i.risk_detected:
            sys.exit(2)
    FRAUDGUARD_USER = settings.FRAUDGUARD_USER
    FRAUDGUARD_SECRET = settings.FRAUDGUARD_SECRET
    RISK_LEVEL = 1
    def check_raw_ip_risk(ip_addr, soft=False):
        try:
            ip=requests.get('https://api.fraudguard.io/ip/' + ip_addr, verify=True, auth=HTTPBasicAuth(FRAUDGUARD_USER, FRAUDGUARD_SECRET))
            j = ip.json()
            if int(j['risk_level']) > RISK_LEVEL:
                return True
            else:
                return False
        except:
            print(traceback.format_exc())
            return not soft
        return False
#    for ip in ips:
#        if not ip == '127.0.0.1' and check_raw_ip_risk(ip, True):
#            run_command('doveadm kick team {}'.format(output))
    ip = ips[0]
    print(ip)
    if ip != '127.0.0.1':
         thread_function(ip)
#        x = threading.Thread(target=thread_function, args=(ip,))
#        x.start()

```


--- File: lotteharper-main/logout_script.py ---
```python
from security.logout import logout_malicious_users
logout_malicious_users()
```


--- File: lotteharper-main/logout_script.sh ---
```bash
cd /home/love/bd/
venv/bin/python security/logout_script.py
```


--- File: lotteharper-main/logout.sh ---
```bash
#!/bin/bash
return_code=0
/home/team/lotteh/venv/bin/python /home/team/lotteh/logout.py
return_code=$(($return_code + $?))
echo $return_code
if [ $return_code == 1 ]; then
    exit 0
fi
if [ $return_code == 2 ]; then
    exit 103
fi
if [ $return_code == 0 ]; then
    exit 0
else
    exit 103
fi
```


--- File: lotteharper-main/lotteh/asgi.py ---
```python
"""
ASGI config for lotteh project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
import django
from channels.routing import get_default_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')

django.setup()

application = get_default_application()
```


--- File: lotteharper-main/lotteh/celery.py ---
```python
from __future__ import absolute_import
from django.conf import settings
from celery import Celery
import os
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
app = Celery('lotteh')
import django
django.setup()
# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
from celery.schedules import crontab

from django.contrib.auth.models import User

me = None
try:
    me = User.objects.get(id=settings.MY_ID) if User.objects.count() > 1 else None
except: pass

import asyncio
from celery import shared_task

@shared_task
def do_async_stuff():
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(async_func())
    loop.close()
    return result

#def do_async_stuff():

from asgiref.sync import sync_to_async

@sync_to_async
def reply_message(phone, message, user_id):
    from django.contrib.auth.models import User
    user = User.objects.filter(id=int(user_id)).first() if user_id else None
    preferred_language = user.profile.preferred_language if user else settings.DEFAULT_LANG
    lang = preferred_language
    from voice.ai import get_ai_response
    response = get_ai_response(message, lang)
    from users.tfa import send_text
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(send_text(phone, response))
    loop.close()

@shared_task
def reply_message_async(phone, message, user_id):
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(reply_message(phone, message, user_id))
    loop.close()
    return result

#@app.task
#def reply_message_async(phone, message, user_id):

@app.task
def update_video_description(user_id, recording_id, video_id, thumbnail_url, original_description, original_title, original_category_id, prompt):
    from live.process import update_video_description
    update_video_description(user_id, recording_id, video_id, thumbnail_url, original_description, original_title, original_category_id, prompt)

@app.task
def async_check_upload(post_id):
    from feed.models import Post
    from feed.upload import check_offsite
    check_offsite(Post.objects.get(id=post_id))

@app.task
def async_get_sun(user_id, user_is_authenticated, ip):
    from feed.sun import get_sun
    get_sun(user_id, user_is_authenticated, ip)

@app.task
def async_user_tasks(user_is_authenticated, user_id, ip, language_code):
    from users.tasks import user_tasks
    user_tasks(user_is_authenticated, user_id, ip, language_code)

@app.task
def async_process_user_request(ip, user_id, user_is_authenticated, path, content_length, http_referrer, querystring, method, index):
    from security.risk import process_user_request
    process_user_request(ip, user_id, user_is_authenticated, path, content_length, http_referrer, querystring, method, index)

@app.task
def async_verify_payments():
    from payments.verify import verify_payments
    verify_payments()


@app.task
def async_sessions():
    from security.build import async_build_sessions, delete_old_sessions
    async_build_sessions()
    from django.conf import settings
    delete_old_sessions(minutes=settings.LOGIN_VALID_MINUTES)

@app.task
def update_auctions():
    from feed.auctions import update_auctions
    update_auctions()


@app.task
def automatic_backup():
    from web.generate import generate_site
    from shell.execute import run_command
    generate_site()
    print(run_command('sudo backup'))

@app.task
def upload_post(post_id):
    from feed.models import Post
    self = Post.objects.get(id=post_id)
    self.upload()

@app.task
def write_post_book(post_id):
    from feed.models import Post
    self = Post.objects.get(id=post_id)
    from feed.books import generate_post_book
    self.compile_content()
    self.file = generate_post_book(self)
    self.save()
    towrite = self.file_bucket.storage.open(self.file.path, mode='wb')
    with self.file.open('rb') as file:
        towrite.write(file.read())
    self.file_bucket = self.file.path
    towrite.close()
    self.save()

@app.task
def remove_duplicates(post_id):
    pass

@app.task
def delay_delete_session(id):
    from security.models import SessionDedup
    SessionDedup.objects.get(id=id).delete()

@app.task
def notify_expiry():
    from users.utils import send_expiry_notifications
    send_expiry_notifications()

#@app.task
#def update_dovecot():
#    from mail.views import write_dovecot
#    write_dovecot()

@app.task
def update_file(path, new_text, shell_user):
    from pathlib import Path
    import os
    from shell.execute import run_command
    from shell.models import SavedFile
    status = None
    owner = None
    group = None
    path_exists = os.path.exists(path)
    if path_exists:
        status = os.stat(path)
        path = Path(str(path))
        owner = path.owner()
        group = path.group()
        run_command('sudo chmod a+rw ' + str(path))
    with open(path, 'w') as f:
        f.writelines(new_text)
    if path_exists:
        run_command('sudo chmod a-rw ' + str(path))
        run_command('sudo chown {}:{}'.format(owner, group) + ' ' + str(path))
        run_command('sudo chmod ' + oct(status.st_mode)[-3:] + ' ' + str(path))
    for file in SavedFile.objects.filter(path=str(path), current=True):
        file.current = False
        file.save()
    file = SavedFile.objects.create(user=User.objects.get(id=shell_user), path=str(path), content=new_text, current=True)
    file.save()

@app.task
def async_geolocation(ip_obj, ip):
    from security.geolocation import get_ip_location, get_country
    from security.models import UserIpAddress
    ip_obj = UserIpAddress.objects.filter(id=ip_obj).last()
    ip_obj.latitude, ip_obj.longitude = get_ip_location(ip)
    ip_obj.country = get_country(ip_obj.latitude, ip_obj.longitude)
    ip_obj.save()

@app.task
def remove_if_nude(scan_id):
    from barcode.models import DocumentScan
    scan = DocumentScan.objects.get(id=scan_id)
    from feed.nude import is_nude_fast
    if is_nude_fast(scan.document.path):
        scan.delete()

@app.task
def notify_mail_update():
    from mail.views import update_notify
    update_notify()

@app.task
def send_scheduled_emails():
    from django.utils import timezone
    from retargeting.models import ScheduledEmail
    emails = ScheduledEmail.objects.filter(send_at__lte=timezone.now(), sent=False)
    for email in emails:
        email.send()
        email.sent = True
        email.save()

@app.task
def send_scheduled_user_emails():
    from django.utils import timezone
    from retargeting.models import ScheduledUserEmail
    emails = ScheduledUserEmail.objects.filter(send_at__lte=timezone.now(), sent=False)
    count = 0
    for email in emails:
        count = count + 1
        if count > 3: return
        email.send()
        email.sent = True
        email.save()

@app.task
def send_idscan_emails():
    from barcode.email import send_routine_email
    send_routine_email()

@app.task
def push_notification():
    from notifications.push import routine_push
    routine_push()

@app.task
def process_live(camera_id, frame_id):
    from live.process import process_live
    process_live(camera_id, frame_id)

@app.task
def routine_safe_reload():
    from shell.reload import safe_reload
    safe_reload()

@app.task
def delay_delete_post(id):
    from feed.models import Post
    Post.objects.get(id=id).delete()

@app.task
def delay_remove_frame(id):
    from live.models import VideoFrame
    VideoFrame.objects.get(id=id).delete()

@app.task
def crypto_trading_bots():
    from crypto.models import Bot
    from crypto.bot import run_bot_once
    for bot in Bot.objects.filter(live=True, investment_amount_usd__gt=0):
        try:
            run_bot_once(bot.id)
        except: pass

@app.task
def rekey_cameras():
    from live.models import VideoCamera
    import datetime as dt
    from django.utils import timezone
    for camera in VideoCamera.objects.filter(updated__lte=timezone.now() - dt.timedelta(seconds=60)):
        camera.key = ''
        camera.save()

@app.task
def clear_shell_logins():
    from shell.models import ShellLogin
    import datetime as dt
    from django.utils import timezone
    for login in ShellLogin.objects.all():
        if login.time + dt.timedelta(minutes=10) < timezone.now():
            login.delete()

@app.task
def logout_fraudulent_connections():
    from shell.logout import logout_malicious_users
    logout_malicious_users()

@app.task
def delay_remove(filename):
    import os
    os.remove(filename)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.task
def show_reminder_text():
    from live.models import Show
    from django.utils import timezone
    import datetime
    from users.tfa import send_user_text
    shows = Show.objects.filter(start__lte=timezone.now() + datetime.timedelta(minutes=65), start__gte=timezone.now() - datetime.timedelta(minutes=5))
    for show in shows:
        send_user_text(show.model, 'Remember to log in to your live show with {} starting {}'.format(show.user, show.start.strftime('%m/%d/%Y %H:%M:%S')))
        send_user_text(show.user, 'Remember to log in to your live show with {} starting {}. Here is a link: {}'.format(show.model, show.start.strftime('%m/%d/%Y %H:%M:%S'), settings.BASE_URL + reverse('live:livevideo', kwargs={'username': model.profile.name})))

@app.task
def reload_server():
    import requests
    from django.conf import settings
    op = None
    try:
        op = requests.get(settings.BASE_URL, timeout=15)
    except:
        op = None
    if not op:
        from shell.restart import start_server_safe
        start_server_safe()

@app.task
def pend_id_verification(user_id):
    from django.contrib.auth.models import User
    u = User.objects.get(id=user_id)
    u.profile.identity_verified = True
    u.profile.identity_verifying = False
    u.save()

@app.task
def update_subscriptions():
    pass
#    sub_update()

def send_text(text):
    from django.conf import settings
    from django.contrib.auth.models import User
    from users.tfa import send_user_text
    send_user_text(User.objects.get(id=settings.MY_ID), text)

reminders = ['first','second','third']

@app.task
def process_recording(id):
    from live.process import process_recording
    process_recording(id)

@app.task
def process_recordings(num=None):
    from live.models import VideoRecording, VideoCamera
    import datetime
    from django.utils import timezone
    for recording in VideoRecording.objects.filter(processed=False, last_frame__lte=timezone.now() - datetime.timedelta(seconds=60)).order_by('-last_frame')[:num if num else 3]:
        camera = VideoCamera.objects.filter(user=recording.user, name=recording.camera).order_by('-last_frame').first()
        try:
            process_recording(recording.id)
        except:
            import traceback
            print(traceback.format_exc())

@app.task
def validate_bitcoin_payment(uid, mid, balance, transaction_id, fee, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if not model in user.profile.subscriptions.all() and model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from users.tfa import send_user_text
        send_user_text(model, '{} has sucessfully subscribed to your profile with crypto, {}.'.format(user.profile.name, model.profile.preferred_name))
        user.profile.subscriptions.add(model)
        user.profile.save()
        from payments.models import Subscription
        Subscription.objects.create(user=user, model=model, expire_date = timezone.now() + datetime.timedelta(days=30), fee=fee)

@app.task
def validate_surrogacy_payment(uid, mid, balance, transaction_id, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from users.tfa import send_user_text
        send_user_text(model, '{} has sucessfully paid for a surrogacy plan with crypto, {}.'.format(user.profile.name, model.profile.preferred_name))
        mother = model
        send_user_text(mother, '{} (@{}) has purchased a surrogacy plan with you. Please update them with details.'.format(user.verifications.last().full_name, user.username))
        from payments.surrogacy import save_and_send_agreement
        save_and_send_agreement(mother, user)

@app.task
def validate_photo_payment(uid, mid, balance, transaction_id, post_id, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from feed.models import Post
        p = Post.objects.get(id=post_id)
        if p.recipient == user or user in p.paid_users.all(): return
        if not p.paid_file:
            p.recipient = user
        else:
            p.paid_users.add(user)
            p.save()
        from feed.email import send_photo_email
        if not p.private: send_photo_email(user, p)
        from barcode.tests import minor_document_scanned
        if p.private and minor_document_scanned(user): send_photo_email(user, p)

@app.task
def validate_cart_payment(uid, mid, balance, transaction_id, cart, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from payments.cart import process_cart_purchase
        process_cart_purchase(user, cart, private=True)

@app.task
def validate_invoice_payment(uid, mid, balance, transaction_id, invoice_id, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from payments.invoice import process_invoice
        process_invoice(invoice)

@app.task
def validate_tip_payment(uid, mid, balance, transaction_id, crypto, network):
    from django.conf import settings
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    import sys
    tip = model.vendor_payments_profile.validate_crypto_transaction(user, 0.01, transaction_id, crypto, network, True)
    if tip:
        print('sending tip email')
        from payments.email import send_tip_email
        send_tip_email(user, model, tip, crypto, network)


@app.task
def remove_secure(path):
    import os
    os.remove(path)

@app.task
def birth_control_reminder_text(uid):
    from django.contrib.auth.models import User
    import pytz
    from django.utils import timezone
    from users.tfa import send_user_text
    from django.conf import settings
    user = User.objects.filter(id=uid).first()
    if user:
        if (not user.birthcontrol_profile.took_birth_control_today()) and user.birthcontrol_profile.send_pill_reminder:
            profile = user.birthcontrol_profile
            if profile.reminders >= len(reminders):
                profile.reminders = 0
                profile.save()
            send_user_text(user, 'It\'s time to take your your {} birth control pill and input notes, {}. This is your {} reminder {}/birthcontrol/take/'.format(timezone.now().strftime("%A"), user.profile.preferred_name, reminders[profile.reminders], settings.BASE_URL))
            profile.reminders = profile.reminders + 1
            profile.save()

@app.task
def birth_control_text(uid):
    from django.contrib.auth.models import User
    import pytz
    from django.utils import timezone
    from users.tfa import send_user_text
    from django.conf import settings
    user = User.objects.filter(id=uid).first()
    if user:
        if not user.birthcontrol_profile.took_birth_control_today() and user.birthcontrol_profile.send_pill_reminder:
            send_user_text(user, 'Make sure to take your {} birth control pill and input notes, {}. {}/birthcontrol/take/'.format(timezone.now().strftime("%A"), user.profile.preferred_name, settings.BASE_URL))

@app.task
def sleep_reminder_text(uid):
    from django.contrib.auth.models import User
    import pytz
    from users.tfa import send_user_text
    from django.conf import settings
    from django.utils import timezone
    user = User.objects.filter(id=uid).first()
    if user:
        pill_reminder_time = user.birthcontrol_profile.reminder_time
        pill_reminder_hour = pill_reminder_time.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%-I%p')
        if user.birthcontrol_profile.send_sleep_reminder:
            send_user_text(user, 'Remember to go to sleep, {}. Sleep is healthy and it\'s already almost midnight. You wake up at {} tomorrow.'.format(user.profile.preferred_name, pill_reminder_hour))

#@app.task
#def logout_sessions():
#    for user in User.objects.all():
#        if user.is_authenticated and user.profile.tfa_expires < timezone.now():
#            logout_user(user)

#@app.task
#def require_ids():
#    for user in User.objects.all().exclude(id=settings.MODERATOR_USER_ID):
#        user.profile.id_front_scanned = False
#        user.profile.id_back_scanned = False
#        user.profile.save()

@app.task
def clear_tokens():
    from django.contrib.auth.models import User
    for user in User.objects.all():
        user.profile.recovery_token = ''
        user.profile.save()

@app.task
def start_server():
    from shell.execute import run_command
    run_command('sudo systemctl start apache2')

@app.task
def system_broadcast_stream_message(user_id, message):
    from django.contrib.auth.models import User
    from stream.models import ChatMessage
    ChatMessage.objects.create(vendor=User.objects.get(id=int(user_id)), message=message, system=True)

celery_beat_schedules = {}

for user in User.objects.filter(birthcontrol_profile__send_pill_reminder=True) if me else []:
    import pytz
    pill_reminder_time = user.birthcontrol_profile.reminder_time.astimezone(pytz.timezone(settings.TIME_ZONE))
    pill_reminder_hours = int(pill_reminder_time.strftime('%-H'))
    prm = int(pill_reminder_time.strftime('%-M'))
    pill_reminder_minutes = ''
    for x in range(3):
        pill_reminder_minutes = pill_reminder_minutes + str((prm + 5 * (x + 1))%60) + ','
    pill_reminder_minutes = pill_reminder_minutes[:-1]
    celery_beat_schedules.update({
        'birth-control-take-pill-reminder-{}'.format(user.id): {
            'task': 'lotteh.celery.birth_control_reminder_text',
            'schedule': crontab(hour=pill_reminder_hours, minute=pill_reminder_minutes),
            'args': (user.id,)
        },
        'birth-control-sleep-reminder-{}'.format(user.id): {
            'task': 'lotteh.celery.sleep_reminder_text',
            'schedule': crontab(hour='0,22,23', minute='0'),
            'args': (user.id,)
        }
    })

# Comprehensive Celery Beat holiday schedule builder
# Usage:
#   from celerybeat_schedule import build_holiday_schedule
#   schedule = build_holiday_schedule(vendors, year=2026, time_hour=9, time_minute=0)
#
# vendors should be an iterable of objects/dicts that expose:
#   vendor.id (int/str) and vendor.profile.name (str)
# or you can pass simple dicts with keys 'id' and 'profile_name' (the helper will normalize).
#
# For movable holidays that require lunar/calendar conversion (Chinese New Year, Diwali, Eid),
# pass a `custom_dates` dict with keys matching the holiday slug and values as (month, day).
# Example:
#   custom_dates = {'chinese_new_year': (2, 10), 'diwali': (10, 24)}
#
# The returned dict is safe to assign to CELERY_BEAT_SCHEDULE or update it.

from datetime import date, timedelta
from calendar import monthrange
from celery.schedules import crontab
from typing import Iterable, Dict, Any, Tuple, Optional

def _normalize_vendors(vendors):
    """Yield normalized vendor dicts with 'id' and 'name'."""
    for v in vendors:
        yield {'id': v.id, 'name': v.profile.name}

# --- Date helper functions ---

def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the date of the nth weekday in a month. weekday: Monday=0 .. Sunday=6"""
    d = date(year, month, 1)
    first_weekday = d.weekday()
    # offset days to the first desired weekday
    offset = (weekday - first_weekday) % 7
    day = 1 + offset + (n - 1) * 7
    if day > monthrange(year, month)[1]:
        raise ValueError("No such weekday occurrence")
    return date(year, month, day)

def last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the date of the last weekday in a month."""
    last_day = monthrange(year, month)[1]
    d = date(year, month, last_day)
    offset = (d.weekday() - weekday) % 7
    return d - timedelta(days=offset)

def easter_date(year: int) -> date:
    """Compute Easter (Gregorian) for given year using Anonymous Gregorian algorithm."""
    # Source: Meeus/Jones/Butcher algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

# --- Holidays definitions ---
# Each entry: slug -> dict with
#   'name': human friendly name
#   'type': 'fixed' or 'nth_weekday' or 'last_weekday' or 'easter' or 'custom'
#   'spec': depending on type:
#       fixed: (month, day)
#       nth_weekday: (month, weekday(int Mon=0..Sun=6), n)
#       last_weekday: (month, weekday)
#       easter: none
#       custom: will be filled from custom_dates mapping

HOLIDAYS = {
    # US Federal and commonly observed
    'new_years_day':        {'name': "New Year's Day", 'type': 'fixed', 'spec': (1, 1)},
    'mlk_day':              {'name': "Martin Luther King Jr. Day", 'type': 'nth_weekday', 'spec': (1, 0, 3)}, # 3rd Mon Jan
    'valentines_day':       {'name': "Valentine's Day", 'type': 'fixed', 'spec': (2, 14)},
    'presidents_day':       {'name': "Presidents' Day", 'type': 'nth_weekday', 'spec': (2, 0, 3)}, # 3rd Mon Feb
    'international_womens_day': {'name': "International Women's Day", 'type': 'fixed', 'spec': (3, 8)},
    'st_patricks_day':      {'name': "St. Patrick's Day", 'type': 'fixed', 'spec': (3, 17)},
    'easter':               {'name': "Easter", 'type': 'easter'},
    'earth_day':            {'name': "Earth Day", 'type': 'fixed', 'spec': (4, 22)},
    'may_day':              {'name': "May Day / Labour Day (many countries)", 'type': 'fixed', 'spec': (5, 1)},
    'memorial_day':         {'name': "Memorial Day", 'type': 'last_weekday', 'spec': (5, 0)}, # last Monday May
    'juneteenth':           {'name': "Juneteenth", 'type': 'fixed', 'spec': (6, 19)},
    'independence_day':     {'name': "Independence Day (US)", 'type': 'fixed', 'spec': (7, 4)},
    'labour_day_us':        {'name': "Labor Day (US)", 'type': 'nth_weekday', 'spec': (9, 0, 1)}, # 1st Mon Sep
    'halloween':            {'name': "Halloween", 'type': 'fixed', 'spec': (10, 31)},
    'columbus_indigenous_day': {'name': "Columbus Day / Indigenous Peoples' Day", 'type': 'nth_weekday', 'spec': (10, 0, 2)}, # 2nd Mon Oct
    'veterans_day':         {'name': "Veterans Day", 'type': 'fixed', 'spec': (11, 11)},
    'thanksgiving':         {'name': "Thanksgiving (US)", 'type': 'nth_weekday', 'spec': (11, 3, 4)}, # 4th Thu Nov (weekday 3)
    'black_friday':         {'name': "Black Friday", 'type': 'relative', 'spec': ('thanksgiving', 1)},
    'christmas':            {'name': "Christmas Day", 'type': 'fixed', 'spec': (12, 25)},
    'boxing_day':           {'name': "Boxing Day", 'type': 'fixed', 'spec': (12, 26)},
    'new_years_eve':        {'name': "New Year's Eve", 'type': 'fixed', 'spec': (12, 31)},

    # Popular world holidays (fixed-date or simple)
    'international_womens_day': {'name': "International Women's Day", 'type': 'fixed', 'spec': (3, 8)},
    'cinco_de_mayo':        {'name': "Cinco de Mayo", 'type': 'fixed', 'spec': (5, 5)},
    'pride_month_start':    {'name': "Pride Month Begins", 'type': 'fixed', 'spec': (6, 1)},
    'bastille_day':         {'name': "Bastille Day (France)", 'type': 'fixed', 'spec': (7, 14)},
    'german_unity_day':     {'name': "German Unity Day", 'type': 'fixed', 'spec': (10, 3)},

    # Placeholders for complex/movable lunar-based holidays ‚Äî user should provide custom_dates
    'chinese_new_year':     {'name': "Chinese New Year (provide custom date)", 'type': 'custom', 'spec': None},
    'diwali':               {'name': "Diwali (provide custom date)", 'type': 'custom', 'spec': None},
    'eid_al_fitr':          {'name': "Eid al-Fitr (provide custom date)", 'type': 'custom', 'spec': None},
    'hanukkah_start':       {'name': "Hanukkah (provide custom date)", 'type': 'custom', 'spec': None},
}

# --- Messages per holiday ---
DEFAULT_MESSAGES = {
    'new_years_day': "Happy New Year! Wishing you a joyous start to the year ‚Äî send @{} your first cheer of the year!",
    'mlk_day': "Honoring Martin Luther King Jr. today. Spread love and kindness ‚Äî send @{} a supportive message during the stream.",
    'valentines_day': "Happy Valentine's Day! Send @{} a valentine right here during my livestream.",
    'presidents_day': "Happy Presidents' Day! Show some love to @{} during today's livestream.",
    'international_womens_day': "Happy International Women's Day! Celebrate strength and kindness ‚Äî send @{} a message.",
    'st_patricks_day': "Happy St. Patrick's Day! Feeling lucky? Send @{} some green cheer in the chat.",
    'easter': "Happy Easter! Wishing you a joyful day ‚Äî hop into @{}'s stream and say hello!",
    'earth_day': "Happy Earth Day! Love the planet ‚Äî send @{} an eco-friendly greeting in stream.",
    'may_day': "Happy May Day! Celebrate spring ‚Äî send @{} some blooms in the chat.",
    'memorial_day': "This Memorial Day we remember and honor. Share a respectful message with @{} during the stream.",
    'juneteenth': "Happy Juneteenth! Celebrate freedom and community ‚Äî send @{} a celebratory message.",
    'independence_day': "Happy 4th of July! Fireworks and fun ‚Äî send @{} your BBQ and fireworks stories!",
    'labour_day_us': "Happy Labor Day! Rest and celebrate ‚Äî send @{} your appreciation messages today.",
    'halloween': "Happy Halloween! Spooky vibes in chat ‚Äî send @{} a trick or treat message!",
    'columbus_indigenous_day': "Marking Columbus Day / Indigenous Peoples' Day ‚Äî reflect and celebrate culture ‚Äî send @{} a thoughtful message.",
    'veterans_day': "Honoring Veterans today. Send @{} a respectful thank-you message in stream.",
    'thanksgiving': "Happy Thanksgiving! What are you thankful for? Tell @{} in the chat.",
    'black_friday': "Black Friday deals! Share your finds with @{} during the livestream.",
    'christmas': "Merry Christmas! Send @{} your holiday wishes and cheer during the stream.",
    'boxing_day': "Happy Boxing Day! Keep the holiday spirit going ‚Äî send @{} seasonal greetings.",
    'new_years_eve': "Happy New Year's Eve! Count down with @{} and share your wishes.",
    'cinco_de_mayo': "Happy Cinco de Mayo! Celebrate with @{} and share party vibes in chat.",
    'pride_month_start': "Happy Pride Month! Celebrate love and inclusion ‚Äî send @{} supportive messages.",
    'bastille_day': "Happy Bastille Day! Celebrate with @{} and enjoy the festivities.",
    'german_unity_day': "Happy German Unity Day! Share unity and joy with @{}.",
    # placeholders for custom ones will be generic:
    'chinese_new_year': "Happy Chinese New Year! Wishing prosperity ‚Äî send @{} your best wishes.",
    'diwali': "Happy Diwali! Wish @{} light and happiness during the stream.",
    'eid_al_fitr': "Eid Mubarak! Celebrate with @{} and send warm greetings.",
    'hanukkah_start': "Happy Hanukkah! Share light and joy with @{}.",
}

def _compute_holiday_date(slug: str, year: int, custom_dates: Optional[Dict[str, Tuple[int, int]]] = None) -> Optional[date]:
    """Return a date for the given holiday slug and year or None if not computable."""
    info = HOLIDAYS.get(slug)
    if not info:
        return None
    htype = info['type']
    if htype == 'fixed':
        month, day = info['spec']
        return date(year, month, day)
    if htype == 'nth_weekday':
        month, weekday, n = info['spec']
        return nth_weekday(year, month, weekday, n)
    if htype == 'last_weekday':
        month, weekday = info['spec']
        return last_weekday(year, month, weekday)
    if htype == 'easter':
        return easter_date(year)
    if htype == 'custom':
        if custom_dates and slug in custom_dates:
            m, d = custom_dates[slug]
            return date(year, m, d)
        # not provided; skip
        return None
    if htype == 'relative':
        ref_slug, offset_days = info['spec']
        ref_date = _compute_holiday_date(ref_slug, year, custom_dates)
        if ref_date is None:
            return None
        return ref_date + timedelta(days=offset_days)
    return None

def build_holiday_schedule(vendors: Iterable[Any],
                           year: int,
                           time_hour: int = 9,
                           time_minute: int = 0,
                           timezone: Optional[str] = None,
                           custom_dates: Optional[Dict[str, Tuple[int, int]]] = None,
                           messages: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Build a Celery beat schedule dict for the specified vendors and year.
    - vendors: iterable of vendor objects/dicts. Must supply id and profile name.
    - year: the calendar year for which this schedule is generated.
    - time_hour/time_minute: local time for the scheduled messages (crontab fields).
    - timezone: optional timezone name; celery will use CELERY_TIMEZONE if set globally.
    - custom_dates: mapping for complex movable holidays, e.g. {'chinese_new_year': (2,10)}
    - messages: optional mapping to override DEFAULT_MESSAGES
    Returns a dict suitable for CELERY_BEAT_SCHEDULE.
    """
    messages = messages or {}
    merged_messages = DEFAULT_MESSAGES.copy()
    merged_messages.update(messages)

    schedule = {}
    vendors_norm = list(_normalize_vendors(vendors))

    for v in vendors_norm:
        vid = v['id']
        vname = v['name']
        for slug in HOLIDAYS.keys():
            hol_date = _compute_holiday_date(slug, year, custom_dates=custom_dates)
            if hol_date is None:
                # skip holidays we can't compute unless a custom date was provided
                continue

            # special-case Black Friday computed as the day after Thanksgiving
            if slug == 'black_friday':
                # Thanksgiving slug 'thanksgiving' exists
                tg = _compute_holiday_date('thanksgiving', year, custom_dates=custom_dates)
                if tg is None:
                    continue
                hol_date = tg + timedelta(days=1)

            # Build unique schedule name
            sched_name = 'scheduled-system-broadcast-message-{vendor}-{holiday}-{year}'.format(
                vendor=vid, holiday=slug, year=year
            )

            # Build message text, substituting vendor profile name where '{}' appears
            template = merged_messages.get(slug, "Happy {name}! Send @{profile} some love today.")
            try:
                # allow templates that expect a single replacement slot for vendor name
                message = template.format(vname, profile=vname) if '{}' in template else template.format(profile=vname, name=HOLIDAYS[slug]['name'])
            except Exception:
                # fallback: simple replacement for legacy templates using @{}
                message = template.replace('@{}', '@{}'.format(vname)).replace('{}', vname)
            # Ensure message still mentions @profile if original pattern used '@{}'
            if '@' not in message and '{}' in merged_messages.get(slug, ''):
                message = merged_messages.get(slug, '').replace('{}', vname)

            # Create crontab schedule for the exact month and day
            schedule[sched_name] = {
                'task': 'lotteh.celery.system_broadcast_stream_message',
                'schedule': crontab(month_of_year=hol_date.month, day_of_month=hol_date.day, hour=time_hour, minute=time_minute),
                'args': (vid, message)
            }
            # Optionally attach timezone key for clarity (Celery uses CELERY_TIMEZONE global config)
            if timezone:
                schedule[sched_name]['options'] = {'timezone': timezone}

    return schedule

try:
    for vendor in User.objects.filter(profile__vendor=True):
        from django.utils import timezone
        sched = build_holiday_schedule([vendor], year=timezone.now().year, time_hour=9, time_minute=0, timezone=settings.TIME_ZONE)
        celery_beat_schedules.update(sched)
        celery_beat_schedules.update({
            'scheduled-system-broadcast-message-{}'.format(vendor.id): {
                'task': 'lotteh.celery.system_broadcast_stream_message',
                'schedule': crontab(month_of_year=2, day_of_month=14, hour=9, minute=0),
                'args': (vendor.id, 'Happy Valentine\'s Day! Send @{} a valentine right here during my livestream.'.format(vendor.profile.name))
            },
        })
except:
    import traceback
    print(traceback.format_exc())


@app.task
def clear_recordings():
    from live.models import VideoRecording
    from django.utils import timezone
    import datetime as dt
    from django.conf import settings
    recordings = VideoRecording.objects.filter(camera__icontains='*', last_frame__lte=timezone.now() - dt.timedelta(hours=24*settings.RECORDING_EXPIRY_DAYS))
    for recording in recordings:
        recording.delete()

@app.task
def send_admin_text():
    pass
#    admin = User.objects.get(id=settings.ADMIN_ID)
#    send_user_text(admin, '{} is sending you a text to keep your phone active, {}'.format(settings.SITE_NAME, admin.profile.name))
#    call('+12062409036')

@app.task
def hourly_review():
    pass
#    review_server()

@app.task
def sweep_bitcoin_payments():
    pass
#    sweep_all_to_master()

@app.task
def authorize_faces():
    from face.models import Face
    from django.utils import timezone
    import datetime as dt
    faces = Face.objects.filter(timestamp__lte=timezone.now()-dt.timedelta(minutes=30), authorized=False)
    for face in faces:
        face.authorized = True
        face.save()

@app.task
def send_emails():
    from retargeting.email import send_retargeting_emails, send_retargeting_email
    send_retargeting_emails()

@app.task
def send_email():
    from retargeting.email import send_retargeting_emails, send_retargeting_email
    send_retargeting_email()

@app.task
def routine_filter():
    import os
    from feed.models import Post
    post = Post.objects.filter(published=False, moderated=False).exclude(image=None).last()
    if post:
        try:
            from feed.nude import is_nude_fast
            from feed.tests import minor_identity_verified
            if post.image and not os.path.exists(post.image.path) and post.image_bucket: post.download_photo()
            post = Post.objects.get(id=post.id)
            if post.image and os.path.exists(post.image.path) and is_nude_fast(post.image.path):
                post.public = False
                post.secure = True
                if settings.NUDITY_FILTER and not minor_identity_verified(post.author):
                    os.remove(post.image.path)
                    post.image = None
                elif settings.NUDITY_FILTER:
                    post.private = True
                    post.public = False
                post.save()
    #        from security.safety import is_safe_file, is_safe_image
    #        if (post.image and os.path.exists(post.image.path) and not is_safe_image(post.image.path)) or (post.file and os.path.exists(post.file.path) and not is_safe_file(post.file.path)):
    #            post.safe = False
    #            post.secure = False
    #            try:
    #                if post.image: os.remove(post.image.path)
    #            except: pass
    #            try:
    #                if post.file: os.remove(post.file.path)
    #            except: pass
    #            post.private = True
    #            post.save()
            else:
                post.published = True
                post.save()
        except:
            import traceback
            print(traceback.format_exc())
        post.moderated = True
        post.save()
    return

@app.task
def async_risk_detection(ip_id):
    from security.models import UserIpAddress
    from security.apis import check_ip_risk
    ip = UserIpAddress.objects.filter(id=ip_id).last()
    ip.risk_detected = check_ip_risk(ip)
    ip.save()

@app.task
def routine_bucket_posts():
    from feed.models import Post
    from enhance.image import bucket_post
    import os
    for post in Post.objects.filter(published=True, uploaded=False):
        if post.image and os.path.exists(post.image.path):
            bucket_post(post.id)
            return

@app.task
def update_surrogacy_plans():
    from payments.models import SurrogacyPlan
    from django.conf import settings
    import datetime
    from django.conf import timezone
    from dateutil.relativedelta import relativedelta
    for plan in SurrogacyPlan.objects.filter(unpaid__gt=0, timestamp__gte=timezone.now() - relativedelta(weeks=37), completed=False, signed=True).order_by('-timestamp'):
        from payments.invoice import generate_invoice
        price = (settings.SURROGACY_FEE - settings.SURROGACY_DOWN_PAYMENT)/36
        if price > 0:
            generate_invoice(plan.mother, plan.expected_parent, price, 'This invoice is for the remaining balance of your surrogacy plan with {}, which is ${}.'.format(plan.mother.profile.name, str(round(price, 2))))


@app.task
def reset_chat_camera_keys():
    from chat.models import Key
    from django.utils import timezone
    import datetime
    for key in Key.objects.filter(created_at__lte=timezone.now()-datetime.timedelta(days=28)):
        key.delete()

app.conf.beat_schedule = {
    'async-sessions': {
        'task': 'lotteh.celery.async_sessions',
        'schedule': crontab(hour='*', minute='0,15,30,45'),
    },
    'clear-tokens': {
        'task': 'lotteh.celery.clear_tokens',
        'schedule': crontab(hour=0, minute=0),
    },
    'routine-filter': {
        'task': 'lotteh.celery.routine_filter',
        'schedule': crontab(hour='*', minute='*'),
    },
    'clear-recordings': {
        'task': 'lotteh.celery.clear_recordings',
        'schedule': crontab(day_of_month='*', hour=15, minute=0),
    },
    'reset-chat-camera-keys': {
        'task': 'lotteh.celery.reset_chat_camera_keys',
        'schedule': crontab(day_of_month='*', hour=0, minute=0),
    },
    'send-routine-engagement-emails': {
        'task': 'lotteh.celery.send_emails',
        'schedule': crontab(day_of_week=5, hour=6, minute=0),
    },
    'send-routine-retargeting-email': {
        'task': 'lotteh.celery.send_email',
        'schedule': crontab(day_of_week=4, hour=6, minute=0),
    },
    'clear-shell-logins': {
        'task': 'lotteh.celery.clear_shell_logins',
        'schedule': crontab(hour='*', minute=0)
    },
    'authorize-old-faces': {
        'task': 'lotteh.celery.authorize_faces',
        'schedule': crontab(hour='*', minute='*/30')
    },
    'rekey-cameras': {
        'task': 'lotteh.celery.rekey_cameras',
        'schedule': crontab(hour='0', minute='0')
    },
}

app.conf.beat_schedule.update(celery_beat_schedules)

app.conf.timezone = 'America/Los_Angeles'
```


--- File: lotteharper-main/lotteh/__init__.py ---
```python
from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ['celery_app']
```


--- File: lotteharper-main/lotteh/message_storage.py ---
```python
from django.contrib.messages.storage.session import SessionStorage
from django.contrib.messages.storage.base import Message

#TypeError: unhashable type: 'ErrorDict'

class DedupMessageMixin(object):
    def __iter__(self):
        try:
            msgset = [tuple(m.__dict__.items())
                      for m in super(DedupMessageMixin, self).__iter__()]
            return iter([Message(**dict(m)) for m in set(msgset)])
        except: return iter([])

class SessionDedupStorage(DedupMessageMixin, SessionStorage):
    pass
```


--- File: lotteharper-main/lotteh/pricing.py ---
```python
def get_zeroes(length):
    z = ''
    for x in range(int(length)): z = z + '0'
    return z

def get_pricing_options(length=54):
    tickets = []
    tickets_per_deca = 4
    t = [25,50,75,100,200]
    for x in range(0, 5):
        tickets = tickets + [str(t[x])]
    for x in range(5, int(length)):
        tickets = tickets + [str(t[x%5]) + get_zeroes(int(x/5))]
    return [1,2,3,4,5,10,15,20] + tickets
```


--- File: lotteharper-main/lotteh/routing.py ---
```python
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import SessionMiddlewareStack
from django.urls import path, re_path
from shell import consumers as shell_consumers
from live import consumers as live_consumers
from vibe import consumers as vibe_consumers
from chat import consumers as chat_consumers
from chat import video_consumers as video_consumers
from photobooth import consumers as photobooth_consumers
from remote import consumers as remote_consumers
from games import consumers as games_consumers
from security import consumers as security_consumers
from users import consumers as auth_consumers
from kick import consumers as kick_consumers
from stream import consumers as stream_consumers
from meetings import consumers as meetings_consumers
from django.core.asgi import get_asgi_application
from django.conf import settings

django_asgi_app = get_asgi_application()

# URLs that handle the WebSocket connection are placed here.
websocket_urlpatterns = [
    path('ws/terminal/websocket/', shell_consumers.TerminalConsumer.as_asgi()),
    path('ws/shell/websocket/', shell_consumers.ShellConsumer.as_asgi()),
    path('ws/remote/', remote_consumers.RemoteConsumer.as_asgi()),
    path('ws/live/remote/<str:username>/<str:name>/', live_consumers.RemoteConsumer.as_asgi()),
    path('ws/live/camera/<str:username>/<str:name>/', live_consumers.CameraConsumer.as_asgi()),
    path('ws/live/signaling/<str:username>/<str:name>/', live_consumers.StreamConsumer.as_asgi()),
    path('ws/live/video/<str:username>/<str:name>/', live_consumers.VideoConsumer.as_asgi()),
    path('ws/photobooth/remote/<str:username>/<str:name>/', photobooth_consumers.PhotoboothRemoteConsumer.as_asgi()),
    path('ws/photobooth/<str:username>/<str:name>/', photobooth_consumers.PhotoboothConsumer.as_asgi()),
    path('ws/chat/video/', video_consumers.VideoConsumer.as_asgi()),
    path('ws/chat/text/<str:username>/', chat_consumers.ChatConsumer.as_asgi()),
    path('ws/vibe/remote/receive/<str:username>/', vibe_consumers.RemoteReceiveConsumer.as_asgi()),
    path('ws/vibe/remote/send/', vibe_consumers.RemoteConsumer.as_asgi()),
    path('ws/games/<str:id>/<str:code>/', games_consumers.GameConsumer.as_asgi()),
    path('ws/security/modal/', security_consumers.ModalConsumer.as_asgi()),
    path('ws/auth/', auth_consumers.AuthConsumer.as_asgi()),
    path('ws/kick/', kick_consumers.KickConsumer.as_asgi()),
    re_path(r'ws/signaling/(?P<channel_name>\w+)/(?P<camera_name>\w+)/$', stream_consumers.WebRTCSignalingConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<room_name>\w+)/$', stream_consumers.ChatConsumer.as_asgi()),
    path('ws/meeting/<str:meeting_id>/', meetings_consumers.MeetingConsumer.as_asgi()),
    path('ws/meeting/chat/<str:meeting_id>/', meetings_consumers.ChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            AllowedHostsOriginValidator(
                SessionMiddlewareStack(
                    URLRouter(websocket_urlpatterns)
                )
            ),
        ),
    }
)
```


--- File: lotteharper-main/lotteh/settings.py ---
```python
"""
Django settings for lotteh project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
import os
import json

# Open and load config
with open('/etc/config.json') as config_file:
    config = json.load(config_file)

with open('/etc/apis.json') as config_file:
    keys = json.load(config_file)

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'sulottehir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config['SECRET_KEY']

# SECURITY WARNING: do not run with debug turned on in production!
DEBUG = False

# Site config
SITE_NAME = 'Lotte Harper'
PROTOCOL = 'https'
DOMAIN = 'lotteh.com'
SITE_ID = 1
BASE_URL = PROTOCOL + '://' + DOMAIN

# Static site
STATIC_DOMAIN = 'glamgirlx.com'
ADD_DOMAIN = 'qoshlli.com'
OLD_DOMAIN = 'femmebabe.com'

ADD_URL = PROTOCOL + '://' + ADD_DOMAIN

ALLOWED_HOSTS = [DOMAIN, STATIC_DOMAIN, ADD_DOMAIN, OLD_DOMAIN, '172.234.244.64', '2600:3c0a::f03c:95ff:feda:ca7a']

INTERNAL_IPS = [
    '127.0.0.1',
    '172.234.244.64',
    '2600:3c0a::f03c:95ff:feda:ca7a'
]

# Application definition
INSTALLED_APPS = [
    'daphne',
    'simple_history',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'landing',
    'users',
    'crispy_forms',
    'crispy_bootstrap4',
    'django_recaptcha',
    'vendors',
    'vibe',
    'verify',
    'feed',
    'misc',
    'security',
    'errors',
    'live',
    'chat',
    'go',
    'birthcontrol',
    'recordings',
    'interactive',
    'voice',
    'sms',
    'face',
    'kick',
    'audio',
    'stacktrace',
    'tts',
    'payments',
    'recovery',
    'barcode',
    'jsignature',
    'shell',
    'hypnosis',
    'photobooth',
    'address',
    'stream',
    'meetings',
#    'hot',
    'survey',
#    'mfa',
#    'pwa_webpush',
    'webpush',
    'notifications',
    'storages',
    'synthesizer',
    'channels',
    'crypto',
    'app',
    'melanin',
    'remote',
    'retargeting',
    'django_summernote',
    'mail',
    'translate',
    'django.contrib.sites',
    'games',
#    'debug_toolbar',
    'webauth',
    'contact',
    'web',
    'django_extensions',
#    'desktop',
    'links',
    'events',
    'podcasts',
    'backup',
    'defender',
    'cookielaw',
#    '',
]

# Auth backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


# Middleware goes between a URL pattern and a view
MIDDLEWARE = [
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.simple_middleware',
    'security.middleware.security_middleware',
    'users.middleware.CurrentUserMiddleware',
    'feed.middleware.CurrentUserMiddleware',
    'feed.middleware.CurrentRequestMiddleware',
    'feed.middleware.ExceptionVerboseMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'defender.middleware.FailedLoginMiddleware',
#    '',
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

#SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
#SESSION_COOKIE_NAME = "user_session"
#SESSION_COOKIE_HTTPONLY = True
#SESSION_SAVE_EVERY_REQUEST = True
#SESSION_EXPIRE_AT_BROWSER_CLOSE = True

ROOT_URLCONF = 'lotteh.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'feed.context_processors.feed_context',
                'live.context_processors.live_context',
                'audio.context_processors.audio_context',
                'cookielaw.context_processors.cookielaw',
            ],
            'libraries':{
                'filters': 'templates.tags.filters',
                'feed_filters': 'feed.templatetags.app_filters',
                'shell_filters': 'shell.templatetags.shell_filters',
            },
        },
    },
]

# The default application
WSGI_APPLICATION = 'lotteh.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'dj_db_conn_pool.backends.postgresql',
        'NAME': 'lotteharper_db',
        'USER': 'lotteharper_db_user',
        'PASSWORD': 'LotteHarperPrivateDBAuthorizedAccessOnly',
        'HOST': 'localhost',
        'PORT': '',
        'POOL_OPTIONS': {
            'POOL_SIZE': 500,
            'MAX_OVERFLOW': 500,
            'RECYCLE': -1,
        },
    },
}

OLD_DATABASES = {
    'cache_db': {
        'ENGINE': 'dj_db_conn_pool.backends.postgresql',
        'NAME': 'lotteharper_cache_db',
        'USER': 'lotteharper_cache_db_user',
        'PASSWORD': 'LotteHarperPrivateCacheDBAuthorizedAccessOnly',
        'HOST': 'localhost',
        'PORT': '',
        'POOL_OPTIONS': {
            'POOL_SIZE': 2000,
            'MAX_OVERFLOW': 5000,
            'RECYCLE': -1,
        },
    },
    'translation_cache_db': {
        'ENGINE': 'dj_db_conn_pool.backends.postgresql',
        'NAME': 'lotteharper_translation_cache_db',
        'USER': 'lotteharper_translation_cache_db_user',
        'PASSWORD': 'LotteHarperPrivateTranslationCacheDBAuthorizedAccessOnly',
        'HOST': 'localhost',
        'PORT': '',
        'POOL_OPTIONS': {
            'POOL_SIZE': 2000,
            'MAX_OVERFLOW': 5000,
            'RECYCLE': -1,
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Cacheing
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "lotteharper_private_cache_table",  # Name of your cache table
        "DATABASE": "cache_db",  # Name of the alternate database
        "TIMEOUT": 60 * 60 * 24 * 3, # 1 week expiry
    },
}

OLD_CACHES = {
    "translation_cache": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "lotteharper_private_translation_cache_table",  # Name of your cache table
        "DATABASE": "translation_cache_db",  # Name of the alternate database
        "TIMEOUT": 60 * 60 * 24 * 7 * 4 * 12, # 1 week expiry
    },
#    "old": {
#        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
#        'LOCATION': os.path.join(BASE_DIR, 'cache/'),
#        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
#        "LOCATION": "dj_cache_table",  # Choose a unique table name
#    },
}

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://{}".format(STATIC_DOMAIN),
    "https://{}".format(ADD_DOMAIN),
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Los_Angeles'

USE_I18N = True

USE_TZ = True

# Language for translation
DEFAULT_LANG = 'en'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Login URL config
LOGIN_REDIRECT_URL = 'app:app'
LOGIN_REDIRECT_QUERYSTRING = '?p=1'
LOGIN_URL = 'users:login'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy forms config
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

MAIL_NAME = 'lotteh.com'

EMAIL_HOST = DOMAIN
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_ADDRESS = 'team@{}'.format(MAIL_NAME)
EMAIL_HOST_USER = 'team' #'Love@MamaSheen.com'
EMAIL_HOST_PASSWORD = config['EMAIL_HOST_PASSWORD']
DEFAULT_FROM_EMAIL = '{} <{}>'.format(SITE_NAME, EMAIL_ADDRESS)

# Upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 1000000000
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Login settings
SESSION_EXPIRE_SECONDS = 60*60*24*28
SESSION_COOKIE_AGE = SESSION_EXPIRE_SECONDS
LOGIN_VALID_MINUTES = SESSION_EXPIRE_SECONDS/60/2

# Auth and cookies
VERIFY_AGE_EXPIRATION_HOURS = 3
VERIFY_UNAX_EXPIRATION_HOURS = 24 * 2
PUSH_COOKIE_EXPIRATION_HOURS = 24 * 7
LANDING_COOKIE_EXPIRATION_DAYS = 30 * 3

# CELERY STUFF
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Los_Angeles'

# redis server host
DEFENDER_REDIS_URL = CELERY_RESULT_BACKEND

# redis password quote for special character
DEFENDER_REDIS_PASSWORD_QUOTE = False
DEFENDER_USE_CELERY = True
DEFENDER_LOCKOUT_URL = 'https://glamgirlx.com'

# Monero mining
ACTIVATE_MINING = False
MONERO_ADDRESS = config['MONERO_ADDRESS']

# Programmanble SMS keys
TWILIO_ACCOUNT_SID = keys['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = keys['TWILIO_AUTH_TOKEN']

# Moderation keys
SIGHTENGINE_USER = keys['SIGHTENGINE_USER']
SIGHTENGINE_SECRET = keys['SIGHTENGINE_SECRET']

FRAUDGUARD_USER = keys['FRAUDGUARD_USER']
FRAUDGUARD_SECRET = keys['FRAUDGUARD_SECRET']

ANTIDEO_KEY = keys['ANTIDEO_KEY']

IDSCAN_AUTH_KEY = keys['IDSCAN_AUTH_KEY']

# Maps key
GOOGLE_API_KEY = keys['GOOGLE_MAPS_API_KEY']

# Payment processing keys
OPENNODE_KEY = keys['OPENNODE_KEY']

NOWPAYMENTS_KEY = keys['NOWPAYMENTS_KEY']
NOWPAYMENTS_EMAIL = keys['NOWPAYMENTS_EMAIL']
NOWPAYMENTS_PASSWORD = keys['NOWPAYMENTS_PASSWORD']

ANET_KEY = keys['ANET_KEY']
ANET_NAME = keys['ANET_NAME']

# Hosting keys
TENSORDOCK_KEY = keys['TENSORDOCK_KEY']
TENSORDOCK_TOKEN = keys['TENSORDOCK_TOKEN']
TENSORDOCK_SERVER = keys['TENSORDOCK_SERVER']

# AES Keys for internal encryption
AES_KEY = keys['AES_KEY']
PRV_AES_KEY = keys['PRV_AES_KEY']
PUB_AES_KEY = keys['PUB_AES_KEY']
REL_AES_KEY = keys['REL_AES_KEY']

# AWS s3 Bucket keys
AWS_ACCESS_KEY_ID = keys['AWS_ACCESS']
AWS_SECRET_ACCESS_KEY = keys['AWS_SECRET']
AWS_QUERYSTRING_EXPIRE = 60*60*24*7

# Tensorfusion API key
TF_API_KEY = keys['TF_API_KEY']

# ipstack.com geolocation key
IPSTACK_GEOLOCATION_API_KEY = keys['IPSTACK_GEOLOCATION_API_KEY']

# abuseipdb.com key
ABUSEIPDB_KEY = keys['ABUSEIPDB_KEY']

# virustotal.com api key
VIRUSTOTAL_API_KEY = keys['VIRUSTOTAL_API_KEY']

# Geolocation API key
GEOLOCATION_API_KEY = keys['GEOLOCATION_API_KEY']

# Twitter Keys
TWITTER_KEY = keys['TWITTER_KEY']
TWITTER_SECRET = keys['TWITTER_SECRET']
TWITTER_ACCESS_TOKEN = keys['TWITTER_ACCESS_TOKEN']
TWITTER_TOKEN_SECRET = keys['TWITTER_TOKEN_SECRET']

# Google recaptcha keys
RECAPTCHA_PUBLIC_KEY = config['RECAPTCHA_PUBLIC_KEY']
RECAPTCHA_PRIVATE_KEY = config['RECAPTCHA_PRIVATE_KEY']

# Stripe keys
STRIPE_API_KEY = config['STRIPE_KEY']
STRIPE_PUBLIC_KEY = config['STRIPE_PUBLIC_KEY']

# Square keys
SQUARE_APP_ID = config['SQUARE_APP_ID']
SQUARE_ACCESS_TOKEN = config['SQUARE_ACCESS_TOKEN']

# Cloudinary keys (not in use)
CLOUDINARY_CLOUD_NAME = config['CLOUDINARY_CLOUD_NAME']
CLOUDINARY_API_KEY = config['CLOUDINARY_API_KEY']
CLOUDINARY_API_SECRET = config['CLOUDINARY_API_SECRET']

# TOTP Key
OTP_SECRET_CODE = config['OTP_SECRET_CODE']

# Paypal keys
PAYPAL_ID = config['PAYPAL_ID']
PAYPAL_SECRET = config['PAYPAL_SECRET']

# Location for Square
SQUARE_LOCATION = config['SQUARE_LOCATION']

# Crypto wallets
BITCOIN_WALLET = config['BITCOIN_WALLET']
ETHEREUM_WALLET = config['ETHEREUM_WALLET']

# Vivokey cryptobionics JWT API key
VIVOKEY_KEY = config['VIVOKEY_KEY']

# YouTube Data API v3 Key
YOUTUBE_KEY = config['YOUTUBE_KEY']

# Image host key
IMAGE_HOST_KEY = keys['IMAGE_HOST_KEY']

# OpenAI key for GPT
OPENAI_KEY = keys['OPENAI_KEY']

# Upload key for youtube api
UPLOAD_KEY = keys['UPLOAD_KEY']

# Helcim key
HELCIM_KEY = keys['HELCIM_KEY']

# Imgur keys
IMGUR_ID = keys['IMGUR_ID']
IMGUR_SECRET = keys['IMGUR_SECRET']

# OpenAI key for GPT
CCA_KEY = keys['CCA_VALIDATOR_KEY']

# Transistor.fm Key
TRANSISTORFM_KEY = keys['TRANSISTORFM_KEY']

# Message storage dedup middleware
MESSAGE_STORAGE = 'lotteh.message_storage.SessionDedupStorage'

# Django MFA config
#from django.conf.global_settings import PASSWORD_HASHERS as DEFAULT_PASSWORD_HASHERS #Preferably at the same place where you import your other modules
MFA_UNALLOWED_METHODS=()   # Methods that shouldnt be allowed for the user e.g ('TOTP','U2F',)
MFA_LOGIN_CALLBACK=""      # A function that should be called by username to login the user in session
MFA_RECHECK=True           # Allow random rechecking of the user
MFA_REDIRECT_AFTER_REGISTRATION="users:login"   # Allows Changing the page after successful registeration
MFA_SUCCESS_REGISTRATION_MSG = "Please log in again to continue." # The text of the link
MFA_RECHECK_MIN=10         # Minimum interval in seconds
MFA_RECHECK_MAX=30         # Maximum in seconds
MFA_QUICKLOGIN=True        # Allow quick login for returning users by provide only their 2FA
MFA_ALWAYS_GO_TO_LAST_METHOD = False # Always redirect the user to the last method used to save a click (Added in 2.6.0).
MFA_RENAME_METHODS={} #Rename the methods in a more user-friendly way e.g {"RECOVERY":"Backup Codes"} (Added in 2.6.0)
MFA_HIDE_DISABLE=False
#('FIDO2',)     # Can the user disable his key (Added in 1.2.0).
MFA_OWNED_BY_ENTERPRISE = False  # Who owns security key
#PASSWORD_HASHERS = DEFAULT_PASSWORD_HASHERS # Comment if PASSWORD_HASHER already set in your settings.py
#PASSWORD_HASHERS += ['mfa.recovery.Hash']
RECOVERY_ITERATION = 350000 #Number of iteration for recovery code, higher is more secure, but uses more resources for generation and check...
TOKEN_ISSUER_NAME=SITE_NAME      #TOTP Issuer name
U2F_APPID=BASE_URL    #URL For U2F
FIDO_SERVER_ID=DOMAIN      # Server rp id for FIDO2, it is the full domain of your project
FIDO_SERVER_NAME=SITE_NAME

# Site descriotionn
BASE_DESCRIPTION = 'Professional entertainment, photos, videos, audio, livestreaming and casual gameplay, as well as ID scanning, web development and surrogacy services.'

# Icon for navbar and media
ICON_URL = '/media/static/logo.png'
PWA_ICON_URL = '/media/static/lotteh.png'

# PWA config
PWA_APP_NAME = SITE_NAME
PWA_APP_DESCRIPTION = BASE_DESCRIPTION
PWA_APP_THEME_COLOR = '#c93443'
PWA_APP_BACKGROUND_COLOR = '#b31717'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/',
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_ICONS = [
    {
        'src': '/media/static/android-chrome-192x192.png',
        'sizes': '192x192'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'

# Webpush settings
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": keys['VAPID_PUBLIC_KEY'],
    "VAPID_PRIVATE_KEY": keys['VAPID_PRIVATE_KEY'],
    "VAPID_ADMIN_EMAIL": "lotte.grace.harper@gmail.com"
}

PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'templates', 'serviceworker.js')
ASGI_APPLICATION = "lotteh.routing.application" #routing.py will be created later
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': "channels.layers.InMemoryChannelLayer"
    }
}

# Websocket retry time
RELOAD_TIME = 10000

# Secure file storage
REMOVE_SECURE_TIMEOUT_SECONDS = 600
REMOVE_SECURE_STILL_TIMEOUT_SECONDS = 600
REMOVE_SECURE_TIMEOUT_VIDEO_SECONDS = 600
REMOVE_SECURE_TIMEOUT_FILE_SECONDS = 600 * 10
REMOVE_SECURE_BLUR_TIMEOUT_SECONDS = 600

# URL length
SECURE_MEDIA_CODE_LENGTH = 230

# Required verififcation
MELANIN_VERIFICATION_MINUTES = 5

# Multi factor auth settings
FACE_VALID_MINUTES = 5
AUTH_VALID_MINUTES = 5
ENFORCE_TFA = True
MFA_TOKEN_LENGTH = 8
MFA_TOKEN_ATTEMPTS = 10

# Minimum age
MIN_AGE = 13 # For signup
MIN_AGE_ADULT = 18 # For adult content
MIN_AGE_VERIFIED = 21 # For surrogacy


# User subscription presenntation settings
WEBPUSH_QUERY_DELAY_SECONDS = 60 * 2
EMAIL_QUERY_DELAY_SECONDS = 60 * 3

# Crypto currencies accepted/settings
CRYPTO_PROVIDER = 'https://bitpay.com/buy-crypto/'
DEFAULT_CRYPTO = 'USDC'
MIN_BITCOIN_PERCENTAGE = 0.90
BITCOIN_DECIMALS = 8

# Free settings
FREE_POSTS = 210
PAID_POSTS = 12
PAID_POSTS_SELECTION = 45

# End user ecurity settings
IPS_BEFORE_VERIFY = 100
ID_VERIFICATION_EXPIRES_DAYS = 30 * 3
PAGE_LOADS_PER_API_CALL = 20
CONTENT_RISK_ASSESS_TIMEOUT = 60 * 5
REDIRECT_URL = 'https://glamgirlx.com/'
ALT_REDIRECT_URL = 'https://www.youtube.com/watch?v=SRfwnvXRsRk&t=18s'

# SMS settings
PHONE_NUMBER = '+12063394443' #'+19705857901'

# AFR settings
FACE_LIVENESS_ZERO_TO_ONE = 0.1
FACE_PASSING_SCORE = 20/100.0
ID_FACE_PASSING_SCORE = 10/100.0

# 60 seconds * 60 minutes * 24 hours * X days
ID_VERIFICATION_COUNTDOWN = 60 * 60 * 24 * 3
MINUTES_PER_IDSCAN = 30
MINUTES_PER_IDSCAN_STAFF = 3

# Security app and auth settings
VERIFICATION_MRZ_LENGTH = 8
VERIFICATION_OCR_LENGTH = 16
VERIFICATION_NFC_LENGTH = 456
MRZ_SCAN_REQUIRED_MINUTES = 60 * 2
NFC_SCAN_REQUIRED_MINUTES = 60 * 24
VIVOKEY_SCAN_REQUIRED_MINUTES = 60 * 10
PIN_REQUIRED_MINUTES = 60 * 24
OTP_REQUIRED_MINUTES = 60 * 24
BIOMETRIC_REQUIRED_MINUTES = 60 * 24
RECENT_FACE_MATCH_REQUIRED_MINUTES = 20

# Recovery settings
RECOVERY_TOKEN_LENGTH = 32

# Signature settings
JSIGNATURE_WIDTH = 250
JSIGNATURE_HEIGHT = 100

# Live video/audio settings
AUDIO_LIVE_INTERVAL = 1000 * 60 * 3
PITCHES_PER_SECOND = 8
TARGET_PITCH = 'G3'
MAX_PITCH = 1200
DEFAULT_CAMERA_ALPHA = 0.8
LIVE_INTERVAL = 1000 * 5
LIVE_SHORT_SECONDS = 50
RECORDING_LENGTH_SECONDS = 60 * 15
CAMERA_KEY_LENGTH = 64
# Font for logo in live
#LOGO_FONT = ""


# recordings with a * in the name expire after this many days
RECORDING_EXPIRY_DAYS = 30
CV2_MSE_DIV = 1 # WIDTH / DIV = MSE (10)  1920 / 192 = 10
DEFAULT_SAFETY_SCALE = 0.3

# Important user ids
ADMIN_ID = 1
MY_ID = 2
MODERATOR_USER_ID = 3

# New account throttle
NEW_USERS_PER_DAY = 99

# Photo upload config
MAX_IMAGE_DIMENSION = 3000 * 4
MAX_RED_IMAGE_DIMENSION = 1500
THUMB_IMAGE_DIMENSION = 300

# Live config
VIDEO_SEGMENTS_PER_MODERATION = 7
LIVE_VIDEO_LENGTH_MINUTES = 15
LIVE_SHOW_LENGTH_MINUTES = 15
LIVE_SCHEDULE_BEGINS = 14
LIVE_SCHEDULE_HOURS = 8
SHOWS_PER_USER_WEEK = 3
SHOWS_PER_MODEL_WEEK = 9
SHOW_BOOK_OUT_MINUTES = 60 * 5

# line seperated, these are the sample texts for photo upload
STATUS_SAMPLE = 3457

# Large private text on modals
PRIVATE_TEXT_LARGE = False

# the threshold balance before the server powers off to save money (GPU hosting only)
SERVER_SHUTDOWN_THRESHOLD = 25
SERVER_COST_MINUTE = 0.40

# Limit logins without facial recognition to one session
LIMIT_BYPASS_LOGIN = False

# Summernote Config
SUMMERNOTE_THEME = 'bs5'
SUMMERNOTE_CONFIG = {
    'summernote': {
        'width': '100%',
    },
}
TEXTAREA_ROWS = 7
EMAIL_PER_PAGE = 20

# Turn ads on
SHOW_ADS = True
SHOW_WISHLIST = True

# Payments config
PAYMENT_PROCESSOR = 'square'

# Stripe config
CURRENCY = "USD"
PRICE_CHOICES = 24
PHOTO_CHOICES = 24

# Surrogacy settings
APPLICATION_FEE = 15
APPLICATION_FEE_SURROGACY = 10000
APPLICATION_FEE_PHOTO = 1
SURROGACY_FEE = 80000
SURROGACY_DOWN_PAYMENT = 10000

# Filter nudity
NUDITY_FILTER = True
NUDITY_FILTER_SECONDS = 2

# Bash config
BASH_USER = 'team'
BASH_PASS = BASH_USER

# Syntax highlighting
USE_PRISM = True

# the text on the main screen
SPLASH = 280

# Default feed name
DEFAULT_FEED = 'private'

# Path to line seperated embeddable ads
#ADS_PATH = 'misc/ads.txt'

GOOGLE_CLIENT_ID = keys['OAUTH_GOOGLE_CLIENT_ID'],
GOOGLE_CLIENT_SECRET = keys['OAUTH_GOOGLE_SECRET'],

# oAuth config
SOCIALACCOUNT_LOGIN_ON_GET=True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': keys['OAUTH_GOOGLE_CLIENT_ID'],
            'secret': keys['OAUTH_GOOGLE_SECRET'],
        },
        'SCOPE': [
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
ACCOUNT_DEFAULT_HTTP_PROTOCOL='https'
SESSION_COOKIE_DOMAIN = DOMAIN
USE_ALLAUTH = True

# Company/Agent info
UBI = '604-691-289'
COMPANY_NAME = 'Charlotte Grace Harper'
AUTHOR_NAME = 'Charlotte Grace Harper'
CITY_STATE = 'Burien, Washington'
ADDRESS = '15035 8th Avenue South Apt 100, Burien, WA 98148-1112, USA'
AGENT_NAME = 'Dr. Charlotte Harper, PhD'
AGENT_PHONE = '+1 (425) 535-8727'
BUSINESS_TYPE = 'sole proprietorship'

# Free Trial
DEFAULT_MODEL_TRIAL_DAYS = str(30)
IDSCAN_TRIAL_DAYS = 3

# Reader
POST_READER_LENGTH = 10000

# Default app page
DEFAULT_PAGE = 2

# Fertility clinic name
FERTILITY_CLINIC = 'Pacific Northwest Fertility'

# Color options
BACKGROUND_COLOR = "#EBF9FF"
BACKGROUND_COLOR_DARK = "#343A40"
# Email color
HEADER_COLOR = "#54D1F0"
FOOTER_COLOR = "#54D1F0"

# Webauth settings
WEBAUTH_RP_ID = DOMAIN
WEBAUTH_RP_NAME = SITE_NAME
WEBAUTH_ORIGIN = BASE_URL
WEBAUTH_VERIFY_URL = "/webauth/verify/"

# Contact settings
TYPICAL_RESPONSE_TIME_HOURS = 12

# Social URLs
SHOW_SOCIAL_LINKS = True
RESUME_URL = 'https://docs.google.com/document/d/1MIeT0hJl3Hpbr5oX9wfUskBMzAwV3_NS6DJCKvaXNXo/edit?usp=sharing'
GITHUB_URL = 'https://github.com/lotteharper'
LINKEDIN_URL = 'https://www.linkedin.com/in/charlotte-grace-harper/'
INSTAGRAM_LINK = 'https://instagram.com/yourlocalfemme'
TWITTER_LINK = 'https://x.com/teamfemmebabe'
YOUTUBE_LINK = 'https://youtube.com/@LotteHarper'
PODCAST_LINK = 'https://thedamita.transistor.fm/'

# Static site
STATIC_SITE_URL = 'https://' + STATIC_DOMAIN
STATIC_SITE_NAME = 'Glam Girl X'

# Session to deliver
SESSION_INDEX = 2

# Audio fingerprinting
AUDIO_FINGERPRINT_FIDELITY = 1000

# Game codes
GAME_CODE_LENGTH = 4

# Coupon code for NFC tag
COUPON_CODE = 'CHIPPED69'

# Filter sessions by this many days
SESSION_FILTER_DAYS = 30

# Interval at which to upload posts
UPLOAD_INTERVAL = 4000

# ID Scanner
MIN_CONFIDENCE = 90
BANNED_ID_TYPES = ['SexOffenderCard', 'ViolentOffenderCard', 'OffenderCard']
ENABLE_AGECHECKER = False
USE_IDWARE = True
BARCODE_SIZE = 300
REQUIRE_SUBJECTION = True
OCR_LANG = 'eng'

# Interval to assess kick
ASSESS_KICK_INTERVAL = 60 * 30

# Number of words to add to post for unique naming
POST_WORDS = 3

# Audio sample length in ms
FREE_AUDIO_MS = 10000

# Auction settings
AUCTION_END_DAYS=0
MIN_BID = 10

# Remove duplicate content
REMOVE_DUPLICATES = True

# Bank/processing statement descriptor
STATEMENT_DESCRIPTOR = 'LOTTEH.COM'

# Icon URL for email
EMAIL_ICON_URL = '/email/static/logo.png'

# Session update query interval
SESSION_UPDATE_SECONDS = 15

# Minimum crypto payment percentage
MIN_CRYPTO_PERCENTAGE = 90

# Programmable voice blog feed
VOICE_FEED = 'blog'

# Offsite images (eg. imgur)
USE_OFFSITE = True

# Id scan is valid for (hours)
ID_VALID_HOURS = 24 * 30 * 12
# Signature valid for
SIG_VALID_HOURS = 24 * 30 * 12

# Multiple sales of one product
ALLOW_MULTIPLE_SALES = False

# Vibration settings
DEFAULT_VIBRATION = 400

# Adult content allowed?
ADULT_CONTENT = True

# Blur nude parts of image only? (vs full photo)
BLUR_ONLY_NUDE = True
# Liberally?
BLUR_ALL_NUDE = False

# Search in your language?
MULTILINGUAL_SEARCH = True

# Text for the site ad
AD_TEXT = 'Charlotte Harper is a full stack developer living in {}. I use she/her pronouns and build internet enabled software, including apps, games, devices, and other software. This website is a secure Kubernetes at the edge solution where you can visit me and see what I\'m building. Thank you for visiting my webapp.'.format(CITY_STATE)

# The timeout to cache URLs from the media storage feed/storages.py
MEDIA_URL_CACHE_TIMEOUT = 60 * 60 * 24 * 3 # Cache timeout in seconds

# Require account verification for webauthn (custom setting defined in scripts/webauth_views.py for patch to the venv
WEBAUTHN_USER_VERIFICATION_REQUIRED = True

# Censor nudity in video
NUDITY_CENSOR = False
NUDITY_CENSOR_FRONTEND = True
NUDITY_CENSOR_FRONTEND_PX = 20
NUDITY_CENSOR_FRONTEND_SCALE = 0.3
NUDITY_CENSOR_SCALE = 0.3

# Bypass login is valid for X minutes
LOGIN_BYPASS_VALID_MINUTES = 60 * 6

SESSION_SAVE_EVERY_REQUEST = True

DEFAULT_CAMERA_NAME = 'private'

LOGIN_EXPIRY_WARNING_MINUTES = 30

# Sentry
#import sentry_sdk
#sentry_sdk.init(
#    dsn="https://c321f4368422e514f39fcb2b07ba8ffc@o4506803873447936.ingest.sentry.io/4506803875282944",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
#    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
#    profiles_sample_rate=0.5,
#)
```


--- File: lotteharper-main/lotteh/storages.py ---
```python
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import Storage
from django.core.cache import cache
from django.conf import settings
import os

class BackupMediaStorage(S3Boto3Storage):
    bucket_name = 'charlotteharper-backups'

    def _get_cache_key(self, name):
        return f'media_url_{name}'

    def url(self, name):
        cache_key = self._get_cache_key(name)
        cached_url = cache.get(cache_key)
        if cached_url:
            return cached_url

        url = super(MediaStorage, self).url(name)
        cache.set(cache_key, url, settings.MEDIA_URL_CACHE_TIMEOUT) # Set a timeout
        return url

    def delete(self, name):
        cache_key = self._get_cache_key(name)
        cache.delete(cache_key)
        self.storage.delete(name)
```


--- File: lotteharper-main/lotteh/urls.py ---
```python
"""lotteh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users import views as user_views
from kick import views as kick_views
from landing import views as landing_views
from errors import views as error_views
from misc import views as misc_views
from django_summernote.urls import urlpatterns as summernote_urlpatterns
from django.conf import settings

urlpatterns = [
    path('admin/login/', user_views.login),
    path('admin/defender/', include('defender.urls')),
    path('admin/', admin.site.urls),
    path('', include(('app.urls'), namespace='app')),
    path('', include(('landing.urls'), namespace='landing')),
    path('', include(('misc.urls'), namespace='misc')),
    path('', landing_views.landing, name='/'),
    path('logs/', error_views.logs, name='logs'),
    path('logs/api/', error_views.logs_api, name='logs-api'),
    path('accounts/', include(('users.urls'), namespace='users')),
    path('feed/', include(('feed.urls'), namespace='feed')),
    path('vendors/', include(('vendors.urls'), namespace='vendors')),
    path('vibe/', include(('vibe.urls'), namespace='vibe')),
    path('live/', include(('live.urls'), namespace='live')),
    path('chat/', include(('chat.urls'), namespace='chat')),
    path('verify/', include(('verify.urls'), namespace='verify')),
    path('birthcontrol/', include(('birthcontrol.urls'), namespace='birthcontrol')),
    path('go/', include(('go.urls'), namespace='go')),
    path('security/', include(('security.urls'), namespace='security')),
    path('recordings/', include(('recordings.urls'), namespace='recordings')),
    path('interactive/', include(('interactive.urls'), namespace='interactive')),
    path('voice/', include(('voice.urls'), namespace='voice')),
    path('sms/', include(('sms.urls'), namespace='sms')),
    path('face/', include(('face.urls'), namespace='face')),
    path('kick/', include(('kick.urls'), namespace='kick')),
    path('audio/', include(('audio.urls'), namespace='audio')),
    path('tts/', include(('tts.urls'), namespace='tts')),
    path('pay/', include(('payments.urls'), namespace='payments')),
    path('payments/', include(('payments.urls'), namespace='payments-fbck')),
    path('recovery/', include(('recovery.urls'), namespace='recovery')),
    path('barcode/', include(('barcode.urls'), namespace='barcode')),
    path('shell/', include(('shell.urls'), namespace='shell')),
    path('stream/', include(('stream.urls'), namespace='stream')),
    path('', include(('links.urls'), namespace='links')),
    path('hypnosis/', include(('hypnosis.urls'), namespace='hypnosis')),
    path('photobooth/', include(('photobooth.urls'), namespace='photobooth')),
    path('notifications/', include(('notifications.urls'), namespace='notifications')),
    path('survey/', include(('survey.urls'), namespace='survey')),
    path('synthesizer/', include(('synthesizer.urls'), namespace='synthesizer')),
    path('crypto/', include(('crypto.urls'), namespace='crypto')),
    path('melanin/', include(('melanin.urls'), namespace='melanin')),
    path('remote/', include(('remote.urls'), namespace='remote')),
    path('send/', include(('retargeting.urls'), namespace='retargeting')),
    path('mail/', include(('mail.urls'), namespace='mail')),
    path('contact/', include(('contact.urls'), namespace='contact')),
#    path('meet/', include(('meet.urls'), namespace='meet')),
    path('games/', include(('games.urls'), namespace='games')),
#    path('desktop/', include(('desktop.urls'), namespace='desktop')),
    path('meeting/', include(('meetings.urls'), namespace='meetings')),
    path('events/', include(('events.urls'), namespace='events')),
    path('appeal/', kick_views.reasess_kick, name='appeal'),
    path('password-reset-confirm/<uidb64>/<token>/', user_views.password_reset, name='password_reset_confirm'),
#         auth_views.PasswordResetConfirmView.as_view(
#             template_name='users/password_reset_confirm.html'
#         ),
#         name='password_reset_confirm'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
#    path('', include('pwa_webpush.urls')),
    path('webpush/', include('webpush.urls')),
    path('summernote/', include('django_summernote.urls')),
#    path("__debug__/", include("debug_toolbar.urls")),
    path("webauth/", include("webauth.urls")),
]

handler404 = 'errors.views.handler404'
handler500 = 'errors.views.handler500'
handler403 = 'errors.views.handler403'
handler400 = 'errors.views.handler400'

title = '{} Admin Panel'.format(settings.SITE_NAME)

admin.site.site_title = title
admin.site.site_title = title
admin.site.index_title = title
```


--- File: lotteharper-main/lotteh/wsgi.py ---
```python
"""
WSGI config for lotteh project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')

application = get_wsgi_application()
```


--- File: lotteharper-main/mail/admin.py ---
```python
from django.contrib import admin

# Register your models here.
```


--- File: lotteharper-main/mail/apps.py ---
```python
from django.apps import AppConfig


class MailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mail'
```


--- File: lotteharper-main/mail/__init__.py ---
```python
```


--- File: lotteharper-main/mail/migrations/0001_initial.py ---
```python
# Generated by Django 4.2.5 on 2023-10-04 16:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LastUpdatedMail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField(default=-1)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_mail', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/mail/migrations/__init__.py ---
```python
```


--- File: lotteharper-main/mail/models.py ---
```python
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class LastUpdatedMail(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE, related_name='updated_mail')
    count = models.IntegerField(default=-1)
    updated = models.DateTimeField(default=timezone.now)
```


--- File: lotteharper-main/mail/templates/mail/inbox.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block content %}
<legend>Inbox</legend>
<form class="d-flex" action="{% url 'retargeting:email' %}" method="GET">
        <input class="form-control mr-sm-2" type="email" placeholder="person@email.com" aria-label="email" required id="u" name="u">
        <button class="btn btn-success my-2 my-sm-0" type="submit">Send</button>
</form>
<hr>
<div>
    {% for message in mails %}
      {% include 'mail/_message.html' %}
    {% endfor %}
</div>
{% include 'pagelinks.html' %}
{% endblock %}
```


--- File: lotteharper-main/mail/templates/mail/_message.html ---
```html
<p><i>{{ message.id }}</i> <b>{{ message.sender }}</b> {{ message.time }}</p>
<p><i>{{ message.subject }}</i></p>
<p>{{ message.excerpt }}</p>
<a class="btn btn-outline-primary" title="View message from {{ message.sender }}" href="{% url 'mail:message' message.id %}">View</a>
<hr>
```


--- File: lotteharper-main/mail/templates/mail/message.html ---
```html
{% extends 'base.html' %}
{% block content %}
{% load feed_filters %}
<a href="{% url 'mail:inbox' %}" class="btn btn-outline-primary" title="Back to inbox">Inbox</a>
<a href="{% url 'retargeting:email' %}?u={{ from|stripsender }}" class="btn btn-outline-info" title="Reply">Reply</a>
<a href="{% url 'payments:send-invoice' %}?email={{ from|stripsender }}" class="btn btn-outline-info" title="Send invoice">Invoice</a>
<hr>
<p>From <b>{{ from }}</b> To <i>{{ to }}</i> on {{ time }}</p>
<p><i>{{ subject }}</i></p>
<iframe width="100%" height="500px" id="message" style="background-color: white;"></iframe>
{% endblock %}
{% block javascript %}
var iframe = document.getElementById("message");
{% autoescape off %}
iframe.srcdoc = `{{ content }}`;
{% endautoescape %}
{% endblock %}
```


--- File: lotteharper-main/mail/tests.py ---
```python
```


--- File: lotteharper-main/mail/urls.py ---
```python
from django.urls import path
from . import views

app_name='mail'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('message/<str:id>/', views.message, name='message'),
]
```


--- File: lotteharper-main/mail/views.py ---
```python
from face.tests import is_superuser_or_vendor
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import pediatric_identity_verified

def getbody(message):
    body = None
    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
               for subpart in part.walk():
                    if subpart.get_content_type() == 'text/html':
                        body = subpart.get_payload(decode=True)
            elif part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
    elif message.get_content_type() == 'text/plain':
        body = message.get_payload(decode=True)
    elif message.get_content_type() == 'text/html':
        body = message.get_payload(decode=True)
    return body

def gettextbody(message):
    body = None
    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
               for subpart in part.walk():
                    if subpart.get_content_type() == 'text/plain':
                        body = subpart.get_payload(decode=True)
            elif part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
    elif message.get_content_type() == 'text/plain':
        body = message.get_payload(decode=True)
    elif message.get_content_type() == 'text/html':
        body = message.get_payload(decode=True)
    return body

def get_subject(message):
    from email.header import decode_header
    header = message["subject"]
    if not header:
        return ''
    header, encoding = decode_header(header)[0]
    if encoding is not None:
        try:
            header = header.decode(encoding)
        except:
            header = header.decode('latin-1')
    return header

@login_required
@user_passes_test(is_superuser_or_vendor)
def inbox(request):
    import datetime, os, re, mailbox, pytz
    from django.shortcuts import render, redirect
    from django.urls import reverse
    from django.utils import timezone
    from django.contrib import messages
    from django.conf import settings
    from django.core.paginator import Paginator
    from dateutil.parser import parse
    from django.contrib.auth.models import User
    from mail.models import LastUpdatedMail
    from django.utils.html import strip_tags
    import os
    page = 1
    if(request.GET.get('page', '') != ''):
        page = int(request.GET.get('page', ''))
    a = list(mailbox.mbox('/var/mail/{}'.format(request.user.profile.bash)))
    a.reverse()
    p = Paginator(a, settings.EMAIL_PER_PAGE)
    mails = []
    current = (page-1) * settings.EMAIL_PER_PAGE
    for msg in p.page(page):
        content = gettextbody(msg)
        sender = msg['from']
        excerpt = strip_tags(content.decode("utf-8"))[:400] if content else ''
        mails = mails + [{'id': current, 'sender': sender, 'subject': get_subject(msg), 'excerpt': excerpt, 'time': parse(msg['date']).astimezone(pytz.timezone(settings.TIME_ZONE))}]
        current = current + 1
    return render(request, 'mail/inbox.html', {
        'title': 'Inbox',
        'mails': mails,
        'count': p.count,
        'page_obj': p.get_page(page),
        'current_page': page
    })

@login_required
@user_passes_test(is_superuser_or_vendor)
def message(request, id):
#    from shell.execute import run_command
#    run_command('/bin/sudo chown {}:users {}'.format(settings.BASH_USER, config_dir))
    from django.shortcuts import render
    import datetime, os, re, mailbox, pytz
    from django.utils import timezone
    from dateutil.parser import parse
    from django.conf import settings
    a = list(mailbox.mbox('/var/mail/{}'.format(request.user.profile.bash)))
    a.reverse()
    i = a[int(id)]
    return render(request, 'mail/message.html', {'title': 'Message {}'.format(id), 'subject': get_subject(i), 'content': getbody(i).decode("utf-8"), 'from': i['from'], 'to': i['to'], 'time': parse(i['date']).astimezone(pytz.timezone(settings.TIME_ZONE))})

def notify_user(user, from_email, subject, body):
    from django.conf import settings
    payload = {"head": 'New Mail ({}) - {}'.format(from_email, subject), "body": body[:200] + '' if len(body) <= 200 else '...', "url": settings.BASE_URL + '/mail/message/0/', 'icon': '{}{}'.format(settings.BASE_URL, settings.ICON_URL)}
    from webpush import send_user_notification
    send_user_notification(user=user, payload=payload, ttl=1000)

def update_notify():
    from django.contrib.auth.models import User
    users = User.objects.filter(profile__email_verified=True, is_active=True).exclude(profile__bash='').order_by('-profile__last_seen')
    for user in users:
        update_user(user)

def update_user(user):
    import datetime, os, re, mailbox, pytz
    from .models import LastUpdatedMail
    from django.utils import timezone
    a = list(mailbox.mbox('/var/mail/{}'.format(user.profile.bash)))
    a.reverse()
    updated, created = LastUpdatedMail.objects.get_or_create(user=user)
    if not created and len(a) > updated.count:
        msg = a[0]
        try:
            notify_user(user, msg['from'], get_subject(msg), strip_tags(getbody(msg).decode("utf-8")))
        except: pass
        updated.count = len(a)
        updated.updated = timezone.now()
        updated.save()
    elif created:
        updated.count = len(a)
        updated.updated = timezone.now()
        updated.save()

def get_dovecot(user, password):
    from shell.execute import run_command
    import os, re
    from django.contrib.auth.models import User
    from django.conf import settings
    dove = ''
#    write_user(user)
    hash = os.popen('sudo doveadm pw -s SHA512-CRYPT -p {} -u {}'.format(password, user.profile.bash)).read()
    dove = dove + user.profile.bash + ':' + '{}\n'.format(hash)
    return dove


def write_dovecot_user(user, password):
    import os
    from django.conf import settings
    from shell.execute import run_command
    bash = user.profile.bash
    config_dir = str(os.path.join(settings.BASE_DIR, 'config/etc_dovecot_users'))
    run_command('sudo adduser --disabled-password --gecos "" {}'.format(bash))
    run_command('sudo chown {}:users {}'.format(settings.BASH_USER, config_dir))
#    try:
#        user_line = int(os.popen('grep -n "{}:" {}'.format(user.profile.bash, config_dir)).read().split(':')[0])
#    except:
#        user_line = 0
    config = os.popen('cat {}'.format(config_dir)).read()
    user_line = 1 if '{}:'.format(user.profile.bash) in config else 0
#    print(user_line)
    op = '\n'
    if user_line < 1:
        op = op + get_dovecot(user, password)
    for line in config.split('\n'):
        if line.startswith(user.profile.bash):
            op = op + get_dovecot(user, password)
        else: op = op + ((line + '\n') if line != '' else '')
    with open(os.path.join(settings.BASE_DIR, 'config/etc_dovecot_users'), 'w') as file:
        file.write(op)
        file.close()
    run_command('sudo cp {} /etc/dovecot/users'.format(config_dir))
    run_command('sudo chown root:root /etc/dovecot/users')
```


--- File: lotteharper-main/make_email_list.py ---
```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')

import django
django.setup()
from django.contrib.auth.models import User
from django.conf import settings
un = ''
for user in User.objects.all():
    un += user.username + ',' + user.email + '\n'
with open('email_list.txt', 'w') as file:
    file.write(un)
file.close()
```


--- File: lotteharper-main/management/commands/clear_cache.py ---
```python
# your_app/management/commands/clear_cache.py
    from django.core.management.base import BaseCommand
    from django.core.cache import cache

    class Command(BaseCommand):
        help = 'Clears the entire Django cache.'

        def handle(self, *args, **kwargs):
            cache.clear()
            self.stdout.write(self.style.SUCCESS('Successfully cleared the cache.'))
```


--- File: lotteharper-main/manage.py ---
```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
```


--- File: lotteharper-main/meetings/admin.py ---
```python
from django.contrib import admin

# Register your models here.
```


--- File: lotteharper-main/meetings/apps.py ---
```python
from django.apps import AppConfig


class MeetingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'meetings'
```


--- File: lotteharper-main/meetings/consumers.py ---
```python
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

@sync_to_async
def get_auth(user_id, session_key):
    from django.contrib.auth.models import User
    user = User.objects.get(id=int(user_id)) if user_id else None
    from security.models import UserSession
    from django.utils import timezone
    for u in UserSession.objects.filter(user__id=user_id, session_key=session_key).order_by('-timestamp'):
        if u.expires > timezone.now() and (u.authorized and u.bypass) and not u.deauth:
            return True
    return False

@sync_to_async
def get_user_name(id):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(id=int(id))
    except: return False
#    if not (user.profile.vendor or user.is_superuser): return False
    return user.profile.name

@sync_to_async
def censor_profanity(text):
    from better_profanity import profanity
    return profanity.censor(text)

@sync_to_async
def translate_message(self, message, lang):
    from translate.translate import translate_html
    return translate_html(None, message, target=self.lang, src=lang)

@sync_to_async
def create_stream_message(user_id, meeting_id, message, lang):
    from django.contrib.auth.models import User
    user = User.objects.filter(id=int(user_id)).first() if user_id else None
    from meetings.models import ChatMessage
    ChatMessage.objects.create(user=user, meeting_id=meeting_id, message=message, lang=lang)

class ChatConsumer(AsyncWebsocketConsumer):
    lang = 'en'
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.room_group_name = f'meeting_chat_{self.meeting_id}'
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'lang' in query_params and query_params['lang']: self.lang = query_params['lang'][0]
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        from feed.templatetags.app_filters import embedlinks
        data['message'] = await censor_profanity(embedlinks(data['message']))
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data['message'],
                'username': data.get('username', 'Guest'),
                'lang': self.lang,
            }
        )
        await create_stream_message(self.scope["user"].id if self.scope['user'] else None, self.meeting_id, data['message'], self.lang)

    async def chat_message(self, event):
        mess = await translate_message(self, event['message'], event['lang'])
        await self.send(text_data=json.dumps({
            'message': mess,
            'username': event['username']
        }))

class MeetingConsumer(AsyncWebsocketConsumer):
    audio_volume = -1000
    connected = False
    username = 'Guest'
    audios = {}
    videos = {}
    async def connect(self):
        self.meeting_id = self.scope["url_route"]["kwargs"]["meeting_id"]
        self.room_group_name = f"meeting_{self.meeting_id}"
        self.user_id = self.channel_name  # Unique per connection

        # Announce new peer
        self.username = await get_user_name(self.scope['user'].id)
        if not self.username:
            import random
            self.username = "Guest {}".format(random.randrange(111,999))

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "peer.joined",
                "peer_id": self.user_id,
                "peer_name": self.username,
            }
        )

        await asyncio.sleep(5)

        for a in self.audios.values():
            await self.channel_layer.group_send(
                self.room_group_name,
                a
            )

        for v in self.videos.values():
            await self.channel_layer.group_send(
                self.room_group_name,
                v
            )

        self.connected = True

    async def disconnect(self, close_code):
        # Announce peer left
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "peer.left",
                    "peer_id": self.user_id,
                }
            )
        except: pass
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        self.connected = False

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        target = data.get("target")
        payload = data.get("data", {})

        # Signal relay: send signal to a specific peer
        if action == "signal":
#            print("Signal + " + str(payload))
            await self.channel_layer.send(target, {
                "type": "signal.message",
                "from": self.user_id,
                "data": payload,
                "username": self.username,
            })
        if action == "volume":
            self.audio_volume = payload['volume'] if 'volume' in payload else -1000
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "volume_event",
                    "peer_id": self.user_id,
                    "volume": self.audio_volume
                }
            )
        if action == "audio":
            self.audios[self.user_id] = {
                "type": "audio",
                "from": self.user_id,
                "data": payload,
                "username": self.username,
            }
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "audio",
                    "from": self.user_id,
                    "data": payload,
                    "username": self.username,
                }
            )
        if action == "video":
            self.videos[self.user_id] = {
                "type": "video",
                "from": self.user_id,
                "data": payload,
                "username": self.username,
            }
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "video",
                    "from": self.user_id,
                    "data": payload,
                    "username": self.username,
                }
            )

    async def peer_joined(self, event):
        # Notify all peers except the one who just joined
        if event["peer_id"] != self.user_id and 'peer_name' in event and event['peer_name']:
            await self.send(text_data=json.dumps({
                "type": "peer-joined",
                "peer_id": event["peer_id"],
                "peer_name": event["peer_name"],
    #event["peer_name"],
            }))

    async def peer_left(self, event):
        # Notify peers
        try:
            await self.send(text_data=json.dumps({
                "type": "peer-left",
                "peer_id": event["peer_id"],
            }))
        except: pass

    async def signal_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "signal",
            "from": event["from"],
            "data": event["data"],
            "username": event["username"],
        }))

    async def volume_event(self, event):
        # Notify peers
        await self.send(text_data=json.dumps({
            "type": "volume",
            "peer_id": event["peer_id"],
            "volume": event["volume"],
        }))

    async def video(self, event):
        await self.send(text_data=json.dumps({
            "type": "video",
            "from": event["from"],
            "data": event["data"],
            "username": event["username"],
        }))

    async def audio(self, event):
        await self.send(text_data=json.dumps({
            "type": "audio",
            "from": event["from"],
            "data": event["data"],
            "username": event["username"],
        }))

```


--- File: lotteharper-main/meetings/email.py ---
```python
def send_meeting_email(event):
    meeting = event.meeting
    from django.urls import reverse
    from django.conf import settings
    participants = event.participants.replace(' ','')
    import pytz
    from django.contrib.auth.models import User
    for email in participants.split(','):
        user = User.objects.filter(email=email).order_by('-profile__last_seen').first()
        context = {
            'username': user.profile.name if user else 'guest',
            'meeting': meeting,
            'calendar_link': event.get_calendar_url(),
            'meeting_link': meeting.get_absolute_url(),
            'site_name': settings.SITE_NAME,
            'start_time': event.start_time.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%m/%d/%Y at %H:%M:%S'),
        }
        from django.template.loader import render_to_string
        content = render_to_string('meetings/email.html', context)
        from users.email import send_email
        send_email(email, 'You have been scheduled by {} to join a video meeting online with {}'.format(meeting.created_by.profile.name, settings.SITE_NAME), content)
```


--- File: lotteharper-main/meetings/__init__.py ---
```python
```


--- File: lotteharper-main/meetings/migrations/0001_initial.py ---
```python
# Generated by Django 5.2.4 on 2025-07-27 05:28

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('identifier', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/meetings/migrations/0002_chatmessage.py ---
```python
# Generated by Django 5.2.4 on 2025-07-31 08:54

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('meeting_id', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('message', models.TextField(blank=True, default='', null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_meeting_messages', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/meetings/migrations/0003_alter_meeting_created_at.py ---
```python
# Generated by Django 5.2.4 on 2025-08-01 04:11

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0002_chatmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meeting',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
```


--- File: lotteharper-main/meetings/migrations/0004_alter_meeting_created_by.py ---
```python
# Generated by Django 5.2.4 on 2025-08-01 04:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0003_alter_meeting_created_at'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='meeting',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
```


--- File: lotteharper-main/meetings/migrations/0005_chatmessage_lang.py ---
```python
# Generated by Django 5.2.8 on 2025-11-07 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0004_alter_meeting_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='lang',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
```


--- File: lotteharper-main/meetings/migrations/__init__.py ---
```python
```


--- File: lotteharper-main/meetings/models.py ---
```python
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid

class Meeting(models.Model):
    id = models.AutoField(primary_key=True)
    identifier = models.UUIDField(default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def get_absolute_url(self):
        from django.urls import reverse
        from django.conf import settings
        return settings.BASE_URL + reverse('meetings:meeting', kwargs={'meeting_id': self.identifier})

class ChatMessage(models.Model):
    id = models.AutoField(primary_key=True)
    meeting_id = models.CharField(max_length=50, default='', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_meeting_messages', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    lang = models.CharField(null=True, blank=True, max_length=10)
    message = models.TextField(default='', null=True, blank=True)
```


--- File: lotteharper-main/meetings/templates/meetings/email.html ---
```html
Hello {{ username }},

You have been scheduled by {{ meeting.created_by.profile.name }} to join a video meeting online with {{ site_name }}.
The meeting starts on {{ start_time }}. Please click the link below or paste it into the navbar to download the attached invite and add it to your calendar for reference by opening it on your device.

<a href="{{ calendar_link }}">{{ calendar_link }}</a>

The invite contains a link to a video meeting. Please click the link in the description of the invite in your calendar and join the meeting from your phone, tablet, or other device. The invite also contains a link to a QR code, which can be scanned by any smart device with a camera in order to open the meeting.

When the meeting starts, please click the link below or paste it into your navbar. The link is also in the invite.

<a href="{{ meeting_link }}">{{ meeting_link }}</a>

We are looking forward to seeing you at your scheduled meeting time.

Sincerely,
{{ site_name }}

```


--- File: lotteharper-main/meetings/templates/meetings/meeting.html ---
```html
{% extends 'base.html' %}
{% block head %}
<style>
body { margin: 0; background: #222; color: #fff; }
#none {
    display: flex;
    flex-wrap: wrap;
    flex-shrink: 0;
    justify-content: center;
    object-fit: cover;
    object-fit: cover;
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    gap: 2%;
}
#videos {
    display: block;
    width: 100%;
    height: 100%;
    overflow-y: auto;
    position: relative;
    vertical-align: top;
    vertical-align: left;
}
video {
    border-radius: 6px;
    vertical-align: top;
    background: #000;
}
.video {
    width: 100%;
    max-width: 100%;
    border-radius: 8px;
    display: block;
    vertical-align: top;
    aspect-ratio: 16 / 9;
}
@media (max-width: 767px) {
    /* CSS rules for mobile devices */
    .video {
        aspect-ratio: 4 / 3;
    }
}
.video-container {
    position: relative;
    display: inline-block;
    vertical-align: top;
    margin: 0.5% 0.25%;
}
@media (max-width: 767px) {
    .video-container {
        width: 98%;
    }
}
@media (min-width: 767px) {
    .video-container {
        width: 49%;
    }
}
.speaker-video {
    border: 4px solid gray;
}
#controls {
    position: absolute;
    bottom: 10px;
    left: 10px;
    z-index: 20;
}
button { margin: 0 5px; }
#fullscreenToggle {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 25;
}
#chatbox {
    overflow-y: auto;
    max-height: 300px;
}
.muted-icon {
    position: absolute;
    top: 8px;
    right: 8px;
    font-size: 2em;
    color: #fff;
    background: rgba(0,0,0,0.5);
    border-radius: 50%;
    z-index: 2;
    pointer-events: none;
}
.videooff-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 4em;
    color: #fff;
    background: rgba(0,0,0,0.7);
    border-radius: 50%;
    z-index: 2;
    pointer-events: none;
}
.video-name-overlay {
    position: absolute;
    bottom: 8px;
    right: 8px;
    padding: 2px 8px;
    background: rgba(0,0,0,0.7);
    color: #fff;
    border-radius: 8px;
    font-size: 1em;
    z-index: 3;
    pointer-events: none;
    max-width: 80%;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
}
</style>
{% endblock %}
{% block content %}
{% load app_filters %}
<i id="meeting-url" class="hide">{{ base_url }}{% url 'meetings:meeting' meeting_id %}</i>
    <div id="videos" class="videos">
    <button id="fullscreenToggle" class="btn btn-sm btn-outline-secondary" title="{{ 'Toggle Fullscreen'|etrans }}"><i class="bi bi-arrows-fullscreen" style="color: white !important;"></i></button>
    <div id="controls">
        <button id="videoBtn" class="btn btn-outline-secondary">{{ 'Toggle Video'|etrans }}</button>
        <button id="audioBtn" class="btn btn-outline-secondary">{{ 'Toggle Mic'|etrans }}</button>
        <button id="screenshareBtn" class="btn btn-outline-secondary">{{ 'Screenshare'|etrans }}</button>
        <button onclick="updateZoomMode(-1);" class="btn btn-outline-info">{{ 'Less'|etrans }}</button>
        <button onclick="updateZoomMode(1);" class="btn btn-outline-info">{{ 'More'|etrans }}</button>
        <button id="autofocusBtn" class="btn btn-outline-secondary">{{ 'Toggle Autofocus'|etrans }}</button>
        <button class="btn btn-outline-info btn-sm" onclick="copyToClipboard('meeting-url');" title="{{ 'Invite another participant to this meeting by copying the link'|etrans }}"><i class="bi bi-clipboard-plus"></i> {{ 'Copy link'|etrans }}</button>
    </div>
    <div class="video-container" id="localVideoContainer">
        <i class="bi bi-mic-mute muted-icon" id="muted-icon-local" style="display:none; color: white !important;"></i>
        <i class="bi bi-camera-video-off videooff-icon" id="videooff-icon-local" style="display:none; color: white !important;"></i>
        <div class="video-name-overlay" id="video-name-local">{% if request.user.is_authenticated %}{{ request.user.profile.name }}{% else %}Guest{% endif %}</div>
        <video class="video" id="localVideo" autoplay muted playsinline></video>
    </div>
    </div>
<div id="fullscreenElement">
</div>
<div id="chat-overlay">
    {% autoescape off %}<div id="chatbox">{% for message in meeting_id|meeting_messages|recent_stream_messages:3 %}<div class="bg-light text-dark"><b>{% if message.user %}@{{ message.user.profile.name }}{% if message.user == vendor %} ({{ 'Streamer'|etrans }}){% endif %}{% else %}{{ 'Guest'|etrans }}{% endif %}:</b> {{ message.id|meetingmessagetrans }}</div>{% endfor %}</div>{% endautoescape %}
    <div class="input-group mb-3">
        <input id="chatinput" type="text" class="form-control" placeholder="{{ 'Type your message here'|etrans }}" aria-label="{{ 'Message'|etrans }}" style="max-width: 75%;">
        <div class="input-group-append">
            <button class="btn btn-outline-secondary" type="button" id="button-addon2" onclick="sendChat();">{{ 'Send'|etrans }}</button>
        </div>
    </div>
</div>
<div>
<p><i>Additional settings</i></p>
<div style="display: inline-block;">
{% if request.GET.originalsound %}<a href="{{ request.path }}{{ 'originalsound='|urlparamedit }}" class="btn btn-sm btn-outline-primary" title="Original sound for musicians">Original sound for musicians (on)</a>{% else %}<a href="{{ request.path }}{{ 'originalsound=true'|urlparamedit }}?originalsound=true" title="Original sound for musicians" class="btn btn-sm btn-outline-primary">Original sound for musicians (off)</a>{% endif %}
{% if request.GET.light %}<a href="{{ request.path }}{{ 'light='|urlparamedit }}" class="btn btn-sm btn-outline-primary" title="Exit light mode">Exit light mode</a>{% else %}<a href="{{ request.path }}{{ 'light=true'|urlparamedit }}" title="Turn light mode on" class="btn btn-sm btn-outline-primary">Light mode</a>{% endif %}
{% if request.GET.dark %}<a href="{{ request.path }}{{ 'dark='|urlparamedit }}" class="btn btn-sm btn-outline-primary" title="Lighten things up">Exit dark mode</a>{% else %}<a href="{{ request.path }}{{ 'dark=true'|urlparamedit }}" title="Enter dark mode" class="btn btn-sm btn-outline-primary">Dark mode</a>{% endif %}
</div>
</div>
{% endblock %}
{% block javascript %}
var zoomMode = 4;
function updateZoomMode(zoomDiff) {
    zoomMode += zoomDiff;
    if(zoomMode < 3) zoomMode = 3;
    if(zoomMode > 6) zoomMode = 6;
    var videos = document.querySelectorAll('.video-container');
    const newWidth = new String(Math.floor(((7 - (zoomMode <= 3 ? 1 : zoomMode))/6.0)*100)-1) + '%';
    for(var x = 0; x < videos.length; x++) {
        vid = videos[x];
        vid.style.width = newWidth;
    }
/*    document.getElementById("videos").style.setProperty('--video-width', newWidth);*/
}
const meetingId = "{{ meeting_id }}";
const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
const wsUrl = `${wsScheme}://${window.location.host}:443/ws/meeting/${meetingId}/`;
var chatSocket;
var chatSocketReconnectTimeout;

let localStream = null;
let peers = {}; // peer_id -> RTCPeerConnection
let streams = {}; // peer_id -> MediaStream

const stunServers = [{urls: "stun:lotteh.com:3478"}]; // Pre-existing STUN
var socket;
var socketReconnectTimeout;
async function getMedia() {
    return await navigator.mediaDevices.getUserMedia({video: true, audio: {% if request.GET.originalsound %}true{% else %}{ echoCancellation: true, }{% endif %}});
}
var peerVolumes = {};
var sharingScreen = false;

function send(action, data={}, target=null) {
    if(socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action, data, target }));
    }
}

var samples = 0;
var totalVolume = 0;

let videoEnabled = true, audioEnabled = true, autofocusEnabled = true;
function updateVideoOffIcon(peer_id, enabled) {
    const videoElem = document.getElementById(peer_id == 'local' ? 'localVideo' : "video_" + peer_id);
    const iconElem = document.getElementById("videooff-icon-" + peer_id);
    if (!videoElem || !iconElem) return;
    if (!enabled) {
        iconElem.style.visibility = "visible";
        iconElem.style.display = "block";
    } else {
        iconElem.style.visibility = "hidden";
        iconElem.style.display = "none";
    }
}
function updateAudioOffIcon(peer_id, enabled) {
    const videoElem = document.getElementById(peer_id == 'local' ? 'localVideo' : "video_" + peer_id);
    const iconElem = document.getElementById("muted-icon-" + peer_id);
    if (!videoElem || !iconElem) return;
    if (!enabled) {
        iconElem.style.visibility = "visible";
        ico