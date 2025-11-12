import json, threading
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from django.conf import settings
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

import subprocess

def push_stream(input_file, rtmp_url):
    return

    import subprocess
    import shlex
    import os
    # FFmpeg command
    # -re: Reads input at native frame rate, important for live streaming.
    # -i: Specifies the input file.
    # -c:v libx264 -preset veryfast -maxrate 3000k -bufsize 6000k: Video encoding settings.
    # -pix_fmt yuv420p: Pixel format for compatibility.
    # -g 50: GOP (Group of Pictures) size.
    # -c:a aac -b:a 128k -ar 44100: Audio encoding settings.
    # -f flv: Output format is Flash Video (FLV) for RTMP.
    # rtmp://...: Your full YouTube RTMP URL.
    ffmpeg_command = (
        f"ffmpeg -re -i \"{input_file}\" "
        "-c:v libx264 -preset veryfast -maxrate 3000k -bufsize 6000k "
        "-pix_fmt yuv420p -g 50 "
        "-c:a aac -b:a 128k -ar 44100 "
        "-f flv "
        f"\"{rtmp_url}\""
    )
    try:
        # Use shlex.split to handle spaces and quotes in file paths properly
        process = subprocess.Popen(shlex.split(ffmpeg_command))
        return process
    except:
        import traceback
        print(traceback.format_exc())
#    cmd = [
#        'ffmpeg',
#        '-re',                       # Read input in real time
#        '-i', input_file,            # Input file
#        '-ar', '44100',              # Set audio sample rate
#        '-c:v', 'libx264',           # Video codec
#        '-preset', 'veryfast',       # Encoding preset
#        '-maxrate', '3000k',         # Max bitrate for video
#        '-bufsize', '6000k',         # Video buffer size
#        '-c:a', 'aac',               # Audio codec
#        '-b:a', '128k',              # Audio bitrate
#        '-f', 'flv',                 # Output format
#        rtmp_url                     # RTMP destination
#    ]
#    return subprocess.Popen(cmd)

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
    camera.last_frame = timezone.now()
    camera_data = camera_data.split("&")
    timestamp = urllib.parse.unquote(camera_data[4].split('=', 1)[1])
    timestamp = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    videouid = urllib.parse.unquote(camera_data[5].split('=', 1)[1])
    frame_data = urllib.parse.unquote(camera_data[6].split('=', 1)[1]).split(',')[1]
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

    path = os.path.join(settings.MEDIA_ROOT, get_file_path(camera, 'frame.' + camera.mimetype.split(';')[0]))
    with open(path, "wb") as file:
        bytes_data = base64.b64decode(frame_data)
        file.write(bytes_data)
    file.close()
    is_frame_still, error = is_still(path)
    frame = VideoFrame.objects.create(user=camera.user, time_captured=timestamp, compressed=camera.user.vendor_profile.compress_video, confirmation_id=camera_data[3].split('=', 1)[1], frame=path, difference=error, adjust_pitch=camera.adjust_pitch, animate_video=camera.animate_video)
    if camera.recording:
        recording.frames.add(frame)
        recording.last_frame = timestamp
        recording.save()
    process_recording.apply_async([recording.id], countdown=(settings.LIVE_INTERVAL/1000) * 18)
    process_live.apply_async([camera.id, frame.id], countdown=settings.LIVE_INTERVAL)
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
    from feed.tests import pediatric_identity_verified
    from django.utils import timezone
    user = User.objects.get(id=int(user_id)) if user_id else None
    from security.models import UserSession
    if not pediatric_identity_verified(user): return False #raise PermissionDenied()
    for u in UserSession.objects.filter(user__id=user_id, session_key=session_key).order_by('-timestamp'):
        if u.expires > timezone.now() and (u.authorized and u.bypass) and not u.deauth:
            return True
    return False

# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer

@sync_to_async
def initiate_stream(self):
    from live.models import VideoCamera
    if not pediatric_identity_verified(camera.user): raise PermissionDenied()
    from verify.tests import pediatric_identity_verified
    from django.core.exceptions import PermissionDenied
    user_id = self.user_id
    camera_name = self.camera_name
    camera = None
    if user_id and not camera:
        camera = VideoCamera.objects.filter(user__id=int(user_id), name=camera_name).order_by('-last_frame').first()
        if camera and camera.user.profile.vendor != True: raise PermissionDenied()
    if not camera: raise PermissionDenied()
    from recordings.youtube import get_stream_key
    try:
        self.stream_key = get_stream_key(self.user_id, camera.upload_email, camera)
        print(self.stream_key)
    except:
        import traceback
        print(traceback.format_exc())


import tempfile
import os
import subprocess
from channels.generic.websocket import AsyncWebsocketConsumer

@sync_to_async
def get_camera_upload(self):
    from live.models import VideoCamera
    camera = VideoCamera.objects.filter(user__profile__name=self.camera_user, name=self.camera_name).order_by('-last_frame').first()
    return camera.broadcast, camera.upload

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
#        return # remove when fixed
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'key' in query_params and query_params['key']: self.key = query_params['key'][0]
        self.user_id = self.scope['user'].id
        authorized = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
        if not authorized:
            print('Unauthed live stream signaling consumer')
            return
        broadcast, upload = await get_camera_upload(self)
        if broadcast: await initiate_stream(self)
        print('Initiating stream')
        self.ffmpeg = await asyncio.create_subprocess_exec(
            'ffmpeg',
            '-re', '-i',
            'pipe:0', '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '3000k', '-maxrate', '3000k',
            '-bufsize', '6000k', '-pix_fmt', 'yuv420p', '-g', '50', '-c:a', 'aac', '-b:a', '160k',
            '-ac', '2',
            '-ar', '44100', '-f', 'flv',
#            'ffmpeg',
#            '-re',
#            '-i', 'pipe:0',
#            '-c:v', 'libx264',
#            '-preset', 'veryfast',
#            '-max_muxing_queue_size', '1024',
#            '-c:a', 'aac',
#            '-ar', '44100',
#            '-b:a', '128k',
#            '-f', 'flv',
            self.stream_key,
            stdin=subprocess.PIPE
        )
        # Replace with your RTMP URL from YouTube
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
        authorized = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
        if not authorized: return
        broadcast, upload = await get_camera_upload(self)
#        if broadcast and not upload: await initiate_stream(self)
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
cameras = {}

async def run_remote(self):
    global remotes
    global cameras
    from django.utils import timezone
    text_data = await get_camera_status(self.camera_user, self.camera_name)
    if not self.camera_user in cameras:
        cameras[self.camera_user] = {}
    if not self.camera_name in cameras[self.camera_user]:
        cameras[self.camera_user][self.camera_name] = (timezone.now(), text_data)
    for id, sock in remotes[self.camera_user][self.camera_name].items():
        if sock.connected:
            try:
                await sock.send(text_data=text_data)
            except: pass
            await asyncio.sleep(1)
    import datetime
    while self.connected:
        if self.camera_user in remotes and self.camera_name in remotes[self.camera_user]:
            last_update, text_data = cameras[self.camera_user][self.camera_name]
            if last_update < timezone.now() - datetime.timedelta(seconds=5):
                text_data = await get_camera_status(self.camera_user, self.camera_name)
                cameras[self.camera_user][self.camera_name] = (timezone.now(), text_data)
            try:
                for id, sock in remotes[self.camera_user][self.camera_name].items():
                    if sock.connected:
                        try:
                            await sock.send(text_data=text_data)
                        except: pass
                        await asyncio.sleep(1)
            except:
                import traceback
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

