import json, threading
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from django.conf import settings
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

@sync_to_async
def get_camera_data(camera_user, camera_name, index, request_user):
    from live.models import VideoCamera
    from live.models import get_file_path, VideoFrame, VideoRecording, Show
    import pytz, datetime
    from django.utils import timezone
    from django.conf import settings
    import base64, asyncio
    import urllib.parse
    from urllib.parse import parse_qs
    from feed.tests import identity_really_verified
    from django.shortcuts import get_object_or_404
    from users.models import Profile
    profile = get_object_or_404(Profile, name=camera_user, identity_verified=True, vendor=True)
    cameras = VideoCamera.objects.filter(user=profile.user, name=camera_name).order_by('-last_frame')
    model = profile.user
    camera = cameras.first()
    # , public=True if profile.user.id != request_user else None
    frame = None
    try:
        frame = camera.frames.order_by('time_captured')[index]
    except: pass
    if not frame:
        print('skip to last frame')
        frame = camera.frames.order_by('-time_captured').first()
    ext = frame.frame.name.split('.')[-1]
    return frame.get_local_url()
#    header = 'data:video/{};base64,'.format(ext)
    print('Getting camera data')
#    with open(frame.frame.path, 'rb') as file:
#        return header + base64.b64encode(file.read()).decode('utf-8')

@sync_to_async
def get_camera_status(camera_user, camera_name):
    from live.models import VideoCamera
    return '{},{},{}'.format('y' if VideoCamera.objects.filter(name=camera_name, user__profile__name=camera_user).first().live else 'n', 'y' if VideoCamera.objects.filter(name=camera_name, user__profile__name=camera_user).first().recording else 'n', 'y' if VideoCamera.objects.filter(name=camera_name, user__profile__name=camera_user).first().muted else 'n')

@sync_to_async
def update_camera(user_id, camera_user, camera_name, camera_data, key=None):
    embed_logo = False
    from live.models import VideoCamera
    from live.models import get_file_path, VideoFrame, VideoRecording, Show
    import pytz, datetime, os, base64, asyncio, time
    from django.utils import timezone
    from django.conf import settings
    import urllib.parse
    from urllib.parse import parse_qs
    from feed.tests import identity_really_verified
    from live.still import is_still
    from lotteh.celery import process_live, process_recording, delay_remove_frame
    from django.core.exceptions import PermissionDenied
    camera = None
    if key:
        camera = VideoCamera.objects.filter(user__profile__name=camera_user, name=camera_name, key=key).order_by('-last_frame').first()
#        print('Camera is ' + str(camera))
        if camera and camera.user.profile.vendor != True: raise PermissionDenied()
    if user_id and not camera:
        camera = VideoCamera.objects.filter(user__id=int(user_id), name=camera_name).order_by('-last_frame').first()
#        print('Camera is ' + str(camera))
        if camera and camera.user.profile.vendor != True: raise PermissionDenied()
    if not camera: raise PermissionDenied()
    if not identity_really_verified(camera.user): raise PermissionDenied()
    camera.last_frame = timezone.now()
    camera_data = camera_data.split("&")
    timestamp = urllib.parse.unquote(camera_data[4].split('=', 1)[1])
#    print(timestamp)
    timestamp = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
#    timestamp += datetime.timedelta(minutes=1)
    videouid = urllib.parse.unquote(camera_data[5])
#    timestamp = datetime.datetime.utcfromtimestamp(timestamp / 1000) - datetime.timedelta(hours=7) #, tz=pytz.UTC)
    frame_data = urllib.parse.unquote(camera_data[6].split('=', 1)[1]).split(',')[1]
    path = os.path.join(settings.MEDIA_ROOT, get_file_path(camera, 'frame.' + camera.mimetype.split(';')[0]))
    with open(path, "wb") as file:
        file.write(base64.b64decode(frame_data))
    file.close()
    is_frame_still, error = is_still(path)
#    new_path = os.path.join(settings.MEDIA_ROOT, get_file_path(camera, 'frame.' + camera.mimetype.split(';')[0]))
#    os.system('mp4fragment {} {}'.format(path, new_path)) #
#    os.remove(path)
#    path = new_path
    frame = VideoFrame.objects.create(user=camera.user, time_captured=timestamp, compressed=camera.user.vendor_profile.compress_video, confirmation_id=camera_data[3].split('=', 1)[1], frame=path, difference=error, adjust_pitch=camera.adjust_pitch, animate_video=camera.animate_video)
    camera.frame = path
    camera.save()
    recording = None
    if camera.recording and not is_frame_still:
        show = Show.objects.filter(start__lte=timezone.now() + datetime.timedelta(minutes=settings.LIVE_SHOW_LENGTH_MINUTES), start__gte=timezone.now()).first()
        recordings = VideoRecording.objects.filter(user=camera.user, camera=camera.name, processing=False, camera_id=videouid).order_by('-last_frame')
# , public=False if Show.objects.filter(start__lte=timestamp + datetime.timedelta(minutes=settings.LIVE_SHOW_LENGTH_MINUTES), start__gte=timezone.now()).count() > 0 else True, recipient=show.user if show else None
        if recordings.count() == 0:
            recording = VideoRecording.objects.create(user=camera.user, camera=camera.name, last_frame=timestamp, camera_id=videouid)
            recording.save()
        else:
            recording = recordings.first()
#, public=False if Show.objects.filter(start__lte=timezone.now() + datetime.timedelta(minutes=settings.LIVE_SHOW_LENGTH_MINUTES), start__gte=timezone.now()).count() > 0 else True, recipient=show.user if show else None
        if recording.last_frame < timezone.now() - datetime.timedelta(seconds=int(settings.LIVE_INTERVAL/1000) * 5) or (recording.frames.order_by('time_captured').first() and ((recording.last_frame - recording.frames.order_by('time_captured').first().time_captured).total_seconds() > settings.RECORDING_LENGTH_SECONDS)) or (camera.short_mode and (recording.frames.order_by('time_captured').first() and ((recording.last_frame - recording.frames.order_by('time_captured').first().time_captured).total_seconds() > settings.LIVE_SHORT_SECONDS))):
            recording = VideoRecording.objects.create(user=camera.user, camera=camera.name, last_frame=timestamp, camera_id=videouid)
            recording.save()
    if is_frame_still or (not camera.recording):
        delay_remove_frame.apply_async([frame.id], countdown=(settings.LIVE_INTERVAL/1000) * 16)
    camera.mime = frame.frame.name.split('.')[1]
    camera.frames.add(frame)
    camera.frame_count = camera.frames.count()
    camera.save()
    if camera.recording and recording and not is_frame_still:
        recording.frames.add(frame)
        recording.last_frame = timestamp
        recording.save()
#        print('recording')
        process_recording.apply_async([recording.id, embed_logo], countdown=(settings.LIVE_INTERVAL/1000) * 16)
#    else: print('Not saving frame')
    process_live.apply_async([camera.id, frame.id], countdown=(settings.LIVE_INTERVAL/1000) * 12)
    return frame.confirmation_id

@sync_to_async
def get_user(id):
    try:
        user = User.objects.get(id=int(id))
    except: return False
#    if not (user.profile.vendor or user.is_superuser): return False
    return True

#@sync_to_async
#def get_auth(user_id, session_key):
#    from security.tests import face_mrz_or_nfc_verified_session_key
#    user = User.objects.get(id=int(user_id)) if user_id else None
#    return face_mrz_or_nfc_verified_session_key(user, session_key)

@sync_to_async
def get_auth(user_id, session_key):
    from security.models import UserSession
    sess = UserSession.objects.filter(user__id=user_id, session_key=session_key).order_by('-timestamp')
    for s in sess:
        if s.authorized: return True
    return False

class CameraConsumer(AsyncWebsocketConsumer):
    camera_user = None
    camera_name = None
    key = None
    user_id = None
    nologo = False
    async def connect(self):
        self.camera_user = self.scope['url_route']['kwargs']['username']
        self.camera_name = self.scope['url_route']['kwargs']['name']
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'key' in query_params and query_params['key']: self.key = query_params['key'][0]
        self.user_id = self.scope['user'].id
#        auth2 = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
#        if not (auth and auth2): return
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text = await update_camera(self.user_id, self.camera_user, self.camera_name, text_data, self.key)
        await self.send(text_data=text)

    pass

remotes = {}

async def run_remote(self):
    global remotes
    while self.connected:
        text_data = await get_camera_status(self.camera_user, self.camera_name)
        if self.camera_user in remotes and self.camera_name in remotes[self.camera_user]:
            for sock in remotes[self.camera_user][self.camera_name]:
                if sock != self: await sock.send(text_data=text_data)
#                print(text_data)
        asyncio.sleep(3)

class RemoteConsumer(AsyncWebsocketConsumer):
    camera_user = None
    camera_name = None
    connected = False
    async def connect(self):
        self.camera_user = self.scope['url_route']['kwargs']['username']
        self.camera_name = self.scope['url_route']['kwargs']['name']
        await self.accept()
        self.connected = True
        global remotes
        if not self.camera_user in remotes:
            remotes[self.camera_user] = {}
        if not self.camera_name in remotes[self.camera_user]:
            remotes[self.camera_user][self.camera_name] = []
        remotes[self.camera_user][self.camera_name]+=[self]
        await run_remote(self)

    async def disconnect(self, close_code):
        self.connected = False
        pass

    async def receive(self, text_data):
#        await self.send(text_data=text)
        pass

    pass

async def run_updates(self, camera_user, camera_name, index, req_user):
    text = await get_camera_data(camera_user, camera_name, index, req_user)
    await self.send(text_data=text)
    await asyncio.sleep(settings.LIVE_INTERVAL/1000)

async def send_updates(self, camera_user, camera_name, index, req_user):
    i = index
    while self.connected:
        await run_updates(self, camera_user, camera_name, i, req_user)
        i += 1

class VideoConsumer(AsyncWebsocketConsumer):
    user = None
    camera_user = None
    camera_name = None
    key = None
    index = None
    connected = False
    async def connect(self):
        try:
            self.user = await get_user(self.scope['user'].id)
        except: pass
        self.camera_user = self.scope['url_route']['kwargs']['username']
        self.camera_name = self.scope['url_route']['kwargs']['name']
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'key' in query_params and query_params['key']: self.key = query_params['key'][0]
        if 'index' in query_params and query_params['index']: self.index = query_params['index'][0]
        await self.accept()
        index = int(self.index)
        self.connected = True
        await send_updates(self, self.camera_user, self.camera_name, index, self.scope['user'].id if self.user else None)

    async def disconnect(self, close_code):
        self.connected = False
        pass

    async def receive(self, text_data):

        pass
    pass

