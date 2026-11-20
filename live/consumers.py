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

import subprocess
import os

def stream_mp4_to_youtube(video_path, stream_url, stream_key):
    # Combine the base URL and the private stream key
    rtmp_destination = f"{stream_url}/{stream_key}"
    # Check if the local MP4 file exists before starting
    if not os.path.exists(video_path):
        print(f"Error: The file '{video_path}' was not found.")
        return
    # Build the FFmpeg command line arguments
    ffmpeg_command = [
        'ffmpeg',
        '-re',                        # Read input at native frame rate (essential for live streaming)
        '-i', video_path,             # Path to your local MP4 file
        '-c:v', 'libx264',            # Encode video to H.264 (YouTube standard)
        '-preset', 'veryfast',        # Balanced CPU usage preset for compression
        '-maxrate', '3000k',          # Cap the maximum video bitrate
        '-bufsize', '6000k',          # Buffer size constraint
        '-pix_fmt', 'yuv420p',        # Ensure pixel format compatibility
        '-g', '60',                   # Enforce a keyframe interval (GOP) every 2 seconds for 30fps
        '-c:a', 'aac',                # Encode audio to AAC format
        '-b:a', '128k',               # Set audio bitrate
        '-ar', '44100',               # Set audio sampling rate to 44.1 kHz
        '-f', 'flv',                  # Flash Video format container required for RTMP streaming
        rtmp_destination              # Target YouTube stream URL endpoint
    ]
    try:
        # Run the FFmpeg process through Python subprocess
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # Read and print the FFmpeg output logs in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        rc = process.poll()
        return rc
    except: pass


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
    try:
        frame = camera.frames.order_by('time_captured')[index]
    except IndexError:
        frame = None
    if not frame:
        frame = camera.frames.order_by('-time_captured').first()
    return frame.get_local_url() if frame else None

@sync_to_async
def get_camera_status(camera_user, camera_name):
    from live.models import VideoCamera
    camera = VideoCamera.objects.filter(name=camera_name, user__profile__name=camera_user).first()
    return '{},{},{}'.format('y' if camera.live else 'n', 'y' if camera.recording else 'n', 'y' if camera.muted else 'n')

def get_upload_camera(user_id, camera_user, camera_name, key):
    from live.models import VideoCamera
    from django.core.exceptions import PermissionDenied
    camera = VideoCamera.objects.filter(
        user__id=user_id, user__profile__name=camera_user, name=camera_name, key=key
    ).order_by('-last_frame').first()
    if not camera or not camera.user.profile.vendor:
        raise PermissionDenied()
    return camera

def save_camera_upload(self, user_id, camera_user, camera_name, key, timestamp, video_id, confirmation_id, content, camera=None):
    from live.video_upload import save_video_segment
    if camera is None:
        camera = get_upload_camera(user_id, camera_user, camera_name, key)
    frame = save_video_segment(camera, timestamp, video_id, confirmation_id, content)
    if camera.broadcast_youtube:
        if (not self.stream_url) or (not self.stream_key):
            from recordings.youtube import create_youtube_stream
            self.stream_url, self.stream_key = create_youtube_stream(camera.title, camera.description, camera.privacy_status, camera.user, email=camera.upload_email)
        threading.Thread(
            target=stream_mp4_to_youtube,
            args=(frame.frame.path, self.stream_url, self.stream_key),
            daemon=True,
        ).start()
    return frame.confirmation_id

@sync_to_async
def update_camera(self, user_id, camera_user, camera_name, camera_data, key=None):
    import base64
    import binascii
    from urllib.parse import parse_qs
    camera = get_upload_camera(user_id, camera_user, camera_name, key)
    try:
        params = parse_qs(camera_data, strict_parsing=True)
        values = {name: params[name][0] for name in ('timestamp', 'viduid', 'confirmation_id', 'frame')
                  if len(params[name]) == 1}
        header, encoded = values['frame'].split(',', 1)
        if not header.startswith('data:') or not header.endswith(';base64'):
            raise ValueError("Invalid video data URL")
        content = base64.b64decode(encoded, validate=True)
    except (KeyError, ValueError, binascii.Error) as exc:
        raise ValueError("Invalid video segment") from exc
    return save_camera_upload(self, user_id, camera_user, camera_name, key,
                              values['timestamp'], values['viduid'], values['confirmation_id'], content, camera)

update_camera_binary = sync_to_async(save_camera_upload)

@sync_to_async
def camera_upload_authorized(user_id, camera_user, camera_name, key):
    from live.models import VideoCamera
    return VideoCamera.objects.filter(
        user__id=user_id, user__profile__name=camera_user, name=camera_name,
        key=key, user__profile__vendor=True,
    ).exists()

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
#    if not pediatric_identity_verified(user): return False #raise PermissionDenied()
    for u in UserSession.objects.filter(user__id=user_id, session_key=session_key).order_by('-timestamp'):
        if u.expires > timezone.now() and (u.authorized and u.bypass) and not u.deauth:
            return True
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
    from recordings.youtube import get_stream_key
#    if not pediatric_identity_verified(camera.user): raise PermissionDenied()
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
    stream_url = None
    upload_file = None
    upload_metadata = None
    upload_size = 0
    async def connect(self):
        self.upload_file = None
        self.upload_metadata = None
        self.upload_size = 0
        self.camera_user = self.scope['url_route']['kwargs']['username']
        self.camera_name = self.scope['url_route']['kwargs']['name']
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'key' in query_params and query_params['key']: self.key = query_params['key'][0]
        self.user_id = self.scope['user'].id
        authorized = bool(self.user_id) and await get_auth(self.user_id, self.scope['session'].session_key)
        if not authorized or not self.key:
            print('Camera not authorized')
            await self.close(code=4403)
            return
#        broadcast, upload = await get_camera_upload(self)
#        if broadcast and not upload: await initiate_stream(self)
        await self.accept()

    async def disconnect(self, close_code):
        self.reset_upload()

    def reset_upload(self):
        if self.upload_file:
            self.upload_file.close()
        self.upload_file = None
        self.upload_metadata = None
        self.upload_size = 0

    async def receive(self, text_data=None, bytes_data=None):
        from django.core.exceptions import PermissionDenied
        import logging
        try:
            if bytes_data is not None:
                if not self.upload_file or not bytes_data or len(bytes_data) > 65536:
                    raise ValueError("Invalid video chunk")
                self.upload_size += len(bytes_data)
                if self.upload_size > self.upload_metadata['size']:
                    raise ValueError("Video segment exceeds declared size")
                self.upload_file.write(bytes_data)
                return
            if text_data is None:
                raise ValueError("Expected a text video segment")
            if text_data.startswith('{'):
                data = json.loads(text_data)
                if data.get('type') == 'segment_start':
                    if self.upload_file:
                        raise ValueError("Video segment already in progress")
                    size = data.get('size')
                    # Bound temporary storage per in-flight segment.
                    limit = getattr(settings, 'LIVE_VIDEO_MAX_SEGMENT_BYTES', 256 * 1024 * 1024)
                    if type(size) is not int or size <= 0 or size > limit:
                        raise ValueError("Invalid video segment size")
                    for field in ('timestamp', 'viduid', 'confirmation_id'):
                        if not isinstance(data.get(field), str) or not data[field] or len(data[field]) > 128:
                            raise ValueError("Invalid video segment metadata")
                    if not await camera_upload_authorized(self.user_id, self.camera_user, self.camera_name, self.key):
                        raise PermissionDenied()
                    self.upload_metadata = data
                    self.upload_file = tempfile.SpooledTemporaryFile(max_size=1024 * 1024)
                    await self.send(text_data=json.dumps({'ready': data['confirmation_id']}))
                    return
                if data.get('type') != 'segment_end' or not self.upload_file or self.upload_size != self.upload_metadata['size']:
                    raise ValueError("Incomplete video segment")
                metadata = self.upload_metadata
                self.upload_file.seek(0)
                content = await sync_to_async(self.upload_file.read, thread_sensitive=False)()
                self.reset_upload()
                text = await update_camera_binary(
                    self, self.user_id, self.camera_user, self.camera_name, self.key,
                    metadata['timestamp'], metadata['viduid'], metadata['confirmation_id'], content,
                )
            else:
                if self.upload_file:
                    raise ValueError("Video segment already in progress")
                text = await update_camera(self, self.user_id, self.camera_user, self.camera_name, text_data, self.key)
        except PermissionDenied:
            self.reset_upload()
            logging.getLogger(__name__).warning(
                "Camera upload rejected for user %s, camera %s/%s",
                self.user_id, self.camera_user, self.camera_name,
            )
            await self.close(code=4403)
            return
        except (ValueError, TypeError, AttributeError):
            self.reset_upload()
            await self.send(text_data=json.dumps({'error': 'Invalid video segment'}))
            return
        except Exception:
            self.reset_upload()
            logging.getLogger(__name__).exception("Failed to save video segment")
            await self.send(text_data=json.dumps({'error': 'Video segment upload failed'}))
            return
        await self.send(text_data=json.dumps({'confirmation_id': text}))

    pass

async def run_remote(self):
    while self.connected:
        text_data = await get_camera_status(self.camera_user, self.camera_name)
        await self.send(text_data=text_data)
        await asyncio.sleep(5)

async def run_socket_updates(consumer, updates):
    import logging
    try:
        await updates
    except asyncio.CancelledError:
        raise
    except Exception:
        logging.getLogger(__name__).exception("Live socket update failed")
        await consumer.close(code=1011)

class RemoteConsumer(AsyncWebsocketConsumer):
    camera_user = None
    camera_name = None
    connected = False
    async def connect(self):
        self.camera_user = self.scope['url_route']['kwargs']['username']
        self.camera_name = self.scope['url_route']['kwargs']['name']
        await self.accept()
        self.connected = True
        self.update_task = asyncio.create_task(run_socket_updates(self, run_remote(self)))

    async def disconnect(self, close_code):
        self.connected = False
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
            await asyncio.gather(self.update_task, return_exceptions=True)

    async def receive(self, text_data):
#        await self.send(text_data=text)
        pass

    pass

async def run_updates(self, camera_user, camera_name, index, req_user):
    text = await get_camera_data(camera_user, camera_name, index, req_user)
    if text is not None:
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
        try:
            index = int(self.index or 0)
            if index < 0:
                raise ValueError
        except ValueError:
            await self.close(code=4400)
            return
        await self.accept()
        self.connected = True
        self.update_task = asyncio.create_task(run_socket_updates(
            self, send_updates(self, self.camera_user, self.camera_name, index, self.scope['user'].id if self.user else None)
        ))

    async def disconnect(self, close_code):
        self.connected = False
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
            await asyncio.gather(self.update_task, return_exceptions=True)

    async def receive(self, text_data):

        pass

    pass
