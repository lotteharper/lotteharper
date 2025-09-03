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
    from feed.tests import pediatric_identity_verified
    from django.shortcuts import get_object_or_404
    from users.models import Profile
    profile = get_object_or_404(Profile, name=camera_user, identity_verified=True, vendor=True)
    cameras = VideoCamera.objects.filter(user=profile.user, name=camera_name).order_by('-last_frame')
    model = profile.user
    camera = cameras.first()
    frame = None
    try:
        frame = camera.frames.order_by('time_captured')[index]
    except: pass
    if not frame:
        print('skip to last frame')
        frame = camera.frames.order_by('-time_captured').first()
    ext = frame.frame.name.split('.')[-1]
    return frame.get_local_url()

@sync_to_async
def get_camera_status(camera_user, camera_name):
    from live.models import VideoCamera
    camera = VideoCamera.objects.filter(name=camera_name, user__profile__name=camera_user).first()
    return '{},{},{}'.format('y' if camera.live else 'n', 'y' if camera.recording else 'n', 'y' if camera.muted else 'n')

@sync_to_async
def update_camera(self, user_id, camera_user, camera_name, camera_data, key=None):
    embed_logo = False
    from live.models import VideoCamera
    from live.models import get_file_path, VideoFrame, VideoRecording, Show
    import pytz, datetime, os, base64, asyncio, time
    from django.utils import timezone
    from django.conf import settings
    import urllib.parse
    from urllib.parse import parse_qs
    from feed.tests import pediatric_identity_verified
    from live.still import is_still
    from lotteh.celery import process_live, process_recording, delay_remove_frame
    from django.core.exceptions import PermissionDenied
    camera = None
    if key:
        camera = VideoCamera.objects.filter(user__profile__name=camera_user, name=camera_name, key=key).order_by('-last_frame').first()
        if camera and camera.user.profile.vendor != True: raise PermissionDenied()
    if user_id and not camera:
        camera = VideoCamera.objects.filter(user__id=int(user_id), name=camera_name).order_by('-last_frame').first()
        if camera and camera.user.profile.vendor != True: raise PermissionDenied()
    if not camera: raise PermissionDenied()
    if not pediatric_identity_verified(camera.user): raise PermissionDenied()
    camera.last_frame = timezone.now()
    camera_data = camera_data.split("&")
    timestamp = urllib.parse.unquote(camera_data[4].split('=', 1)[1])
    timestamp = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    videouid = urllib.parse.unquote(camera_data[5].split('=', 1)[1])
    frame_data = urllib.parse.unquote(camera_data[6].split('=', 1)[1]).split(',')[1]
    path = os.path.join(settings.MEDIA_ROOT, get_file_path(camera, 'frame.' + camera.mimetype.split(';')[0]))
    # In your consumer, for each received blob:
    with open(path, "wb") as file:
        bytes_data = base64.b64decode(frame_data)
        file.write(bytes_data)
        if False and self.stream_key and self.broadcast: ffmpeg_proc.stdin.write(bytes_data)
    file.close()
    is_frame_still, error = is_still(path)
#    new_path = os.path.join(settings.MEDIA_ROOT, get_file_path(camera, 'frame.' + camera.mimetype.split(';')[0]))
#    os.system('mp4fragment {} {}'.format(path, new_path)) #
#    os.remove(path)
#    path = new_path
    frame = VideoFrame.objects.create(user=camera.user, time_captured=timestamp, compressed=camera.user.vendor_profile.compress_video, confirmation_id=camera_data[3].split('=', 1)[1], frame=path, difference=error, adjust_pitch=camera.adjust_pitch, animate_video=camera.animate_video)
    camera.frame = path
    camera.save()
    if (not camera.recording):
        delay_remove_frame.apply_async([frame.id], countdown=(settings.LIVE_INTERVAL/1000) * 16)
    camera.mime = frame.frame.name.split('.')[1]
    camera.frames.add(frame)
    camera.frame_count = camera.frames.count()
    camera.save()
    if camera.recording: # and not is_frame_still:
        recordings = VideoRecording.objects.filter(user=camera.user, camera=camera.name, processing=False, camera_id=videouid, last_frame__gte=timezone.now() - datetime.timedelta(seconds=int(settings.LIVE_INTERVAL/1000) * 12)).order_by('-last_frame')
        recording = recordings.first()
        is_at_length = recordings.first() and (recording.frames.count() * (settings.LIVE_INTERVAL/1000.0) > (camera.video_length_minutes * 60.0))
        is_a_short = recordings.first() and camera.short_mode and (recording.frames.count() * (settings.LIVE_INTERVAL/1000.0) > settings.LIVE_SHORT_SECONDS)
        if (recordings.count() == 0) or is_at_length or is_a_short:
            recording = VideoRecording.objects.create(user=camera.user, camera=camera.name, last_frame=timestamp, camera_id=videouid)
        recording.frames.add(frame)
        recording.last_frame = timestamp
        recording.upload_email = camera.upload_email
        recording.save()
        process_recording.apply_async([recording.id, embed_logo], countdown=(settings.LIVE_INTERVAL/1000) * 16)
    process_live.apply_async([camera.id, frame.id], countdown=(settings.LIVE_INTERVAL/1000) * 4)
    return frame.confirmation_id

@sync_to_async
def get_user(id):
    try:
        user = User.objects.get(id=int(id))
    except: return False
#    if not (user.profile.vendor or user.is_superuser): return False
    return user

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

@sync_to_async
def get_auth(user_id, session_key):
    from security.models import UserSession
    sess = UserSession.objects.filter(user__id=user_id, session_key=session_key).order_by('-timestamp')
    for s in sess:
        if s.authorized: return True
    return False

# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer

@sync_to_async
def initiate_stream(self):
    from live.models import VideoCamera
    from verify.tests import pediatric_identity_verified
    from django.core.exceptions import PermissionDenied
    user_id = self.user_id
    camera_name = self.camera_name
    camera = None
    if user_id and not camera:
        camera = VideoCamera.objects.filter(user__id=int(user_id), name=camera_name).order_by('-last_frame').first()
        if camera and camera.user.profile.vendor != True: raise PermissionDenied()
    if not camera: raise PermissionDenied()
    if not pediatric_identity_verified(camera.user): raise PermissionDenied()
    from recordings.youtube import get_stream_key
    try:
        self.stream_key = get_stream_key(self.user_id, camera.upload_email, camera)
        print(self.stream_key)
    except:
        import traceback
        print(traceback.format_exc())
#    if self.stream_key:
#        import subprocess
#        ffmpeg_cmd = [
#            'ffmpeg', '-i', '-', '-f', 'flv', self.stream_key
#            'ffmpeg', '-re', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast',
#            '-b:v', '3000k', '-c:a', 'aac', '-ar', '44100', '-b:a', '128k',
#            '-f', 'flv',
#        ]
#        self.ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
import tempfile
import os
import subprocess
from channels.generic.websocket import AsyncWebsocketConsumer

class StreamConsumer(AsyncWebsocketConsumer):
    stream_key = None
    ffmpeg = None
    user_id = None
    buffer = None
    active = False
    async def connect(self):
        self.camera_user = self.scope['url_route']['kwargs']['username']
        self.camera_name = self.scope['url_route']['kwargs']['name']
        self.user_id = self.scope['user'].id
        return # remove when fixed
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'key' in query_params and query_params['key']: self.key = query_params['key'][0]
        self.user_id = self.scope['user'].id
        authorized = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
        if not authorized: return
        await initiate_stream(self)
        print('Initiating stream')
        # Replace with your RTMP URL from YouTube
        self.ffmpeg = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-f", "webm",           # Match client format
            "-i", "-",              # Read from stdin
            "-c:v", "copy",         # No re-encoding for video
            "-c:a", "aac",          # Encode audio
            "-b:a", "128k",
            "-ar", "44100",
            "-f", "flv",
            self.stream_key,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.active = True
        await self.accept()

    async def disconnect(self, close_code):
        self.active = False
        if self.ffmpeg and self.ffmpeg.stdin:
            try:
                self.ffmpeg.stdin.close()
            except Exception as e:
                print(f"Error closing ffmpeg stdin: {e}")
            await self.ffmpeg.wait()

    async def receive(self, text_data=None, bytes_data=None):
        """
        Immediately writes each segment to FFmpeg's stdin as it arrives.
        """
        if not self.active or not self.ffmpeg or not self.ffmpeg.stdin:
            return
        if bytes_data:
            try:
                self.ffmpeg.stdin.write(bytes_data)
                await self.ffmpeg.stdin.drain()
            except (BrokenPipeError, ConnectionResetError) as e:
                print(f"Broken pipe: {e}")
#                self.active = False
#                await self.close()
            except Exception as e:
                print(f"Error writing to ffmpeg stdin: {e}")
#                self.active = False
#                await self.close()

class CameraConsumer(AsyncWebsocketConsumer):
    camera_user = None
    camera_name = None
    key = None
    user_id = None
    nologo = False
    stream_key = None
    async def connect(self):
        self.camera_user = self.scope['url_route']['kwargs']['username']
        self.camera_name = self.scope['url_route']['kwargs']['name']
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'key' in query_params and query_params['key']: self.key = query_params['key'][0]
        self.user_id = self.scope['user'].id
#        auth2 = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
#        if not (auth and auth2): return
        authorized = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
        if not authorized: return
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text = await update_camera(self, self.user_id, self.camera_user, self.camera_name, text_data, self.key)
        try:
            await self.send(text_data=text)
        except: pass

    pass

remotes = {}

async def run_remote(self):
    global remotes
    while self.connected:
        if self.camera_user in remotes and self.camera_name in remotes[self.camera_user]:
            try:
                for id, sock in remotes[self.camera_user][self.camera_name].items():
                    if sock.connected:
                        text_data = await get_camera_status(self.camera_user, self.camera_name)
                        try:
                            await sock.send(text_data=text_data)
                        except: pass
                        await asyncio.sleep(1)
            except:
                import traceback
                print(traceback.format_exc())
#                print(text_data)
        await asyncio.sleep(5)

class RemoteConsumer(AsyncWebsocketConsumer):
    camera_user = None
    camera_name = None
    connected = False
    identifier = ''
    async def connect(self):
        self.camera_user = self.scope['url_route']['kwargs']['username']
        self.camera_name = self.scope['url_route']['kwargs']['name']
        import uuid
        self.identifier = str(uuid.uuid4())
        await self.accept()
        self.connected = True
        global remotes
        if not self.camera_user in remotes:
            remotes[self.camera_user] = {}
        if not self.camera_name in remotes[self.camera_user]:
            remotes[self.camera_user][self.camera_name] = {}
        remotes[self.camera_user][self.camera_name][self.identifier] = self
        await run_remote(self)

    async def disconnect(self, close_code):
        self.connected = False
        try:
            del remotes[self.camera_user][self.camera_name][self.identifier]
        except:
            import traceback
            print(traceback.format_exc())
        pass

    async def receive(self, text_data):
#        await self.send(text_data=text)
        pass

    pass

async def run_updates(self, camera_user, camera_name, index, req_user):
    text = await get_camera_data(camera_user, camera_name, index, req_user)
    try:
        await self.send(text_data=text)
    except: pass
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
        authorized = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
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

