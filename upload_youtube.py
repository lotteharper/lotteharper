import sys
to_upload = 1
if len(sys.argv) > 1: to_upload = int(sys.argv[1])
print('Uploading {} videos to YouTube'.format(to_upload))
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from django.conf import settings
from live.models import VideoRecording, VideoCamera
from live.models import get_file_path
import pytz, os, traceback
from django.conf import settings
from recordings.youtube import upload_youtube
from better_profanity import profanity
count = 0
for recording in VideoRecording.objects.filter(processed=True, uploaded=False).order_by('-last_frame'):
    cameras = VideoCamera.objects.filter(name=recording.camera, user=recording.user).order_by('-last_frame')
    print(recording)
#    print(cameras)
    camera = cameras.first()
    thumbnail = None
    from live.duration import get_duration
    # camera.upload and
    from live.upload import upload_recording
    recording = upload_recording(recording, camera)
    if recording:
        recording.save()
        if recording.uploaded:
            try:
                os.remove(recording.file.path)
            except: pass
            recording.file = None
        recording.processed = True
        recording.public = not recording.frames.filter(public=False).last()
        recording.save()
        for frame in recording.frames.all(): frame.delete_video()
    count+=1
    if count >= to_upload: break
