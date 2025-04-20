to_upload = 10
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
    print(recording.camera)
    print(cameras)
    camera = cameras.first()
    if camera.upload:
        try:
            if not (recording.file and os.path.exists(recording.file.path)):
                print('Getting file from bucket for upload')
                full_path = os.path.join(settings.BASE_DIR, 'media/', get_file_path(None, 'rec.mp4'))
                with recording.file_processed.storage.open(str(recording.file_processed.name), mode='rb') as bucket_file:
                    with open(full_path, "wb") as video_file:
                        video_file.write(bucket_file.read())
                    video_file.close()
                bucket_file.close()
                recording.file = full_path
                recording.save()
        except: print(traceback.format_exc())
        try:
            upload_youtube(camera.user, recording.file.path, profanity.censor(camera.title[:67-len(recording.last_frame.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%A %B %d, %Y %H:%M:%S'))]) + ' - ' + recording.last_frame.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%A %B %d, %Y %H:%M:%S'), profanity.censor(camera.description) + ' - ' + profanity.censor(recording.transcript[:4000 - 3]), [tag for tag in camera.tags.split(',')], category='22', privacy_status='public', age_restricted=not recording.public)
            recording.uploaded = True
        except:
            recording.uploaded = False
            print(traceback.format_exc())
        recording.save()
        count+=1
    if count >= to_upload: break
