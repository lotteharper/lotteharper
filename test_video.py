import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from live.concat import concat
from live.models import VideoRecording
from django.conf import settings
from live.models import get_file_path
from live.anime import convert_video_anime
v = VideoRecording.objects.filter(processed=False).order_by('-last_frame')[int(sys.argv[1])]
path = os.path.join(settings.BASE_DIR, 'media', get_file_path(v, 'file.mp4'))
v.file=concat(v,path)
v.save()
path = os.path.join(settings.BASE_DIR, 'media', get_file_path(v, 'file.mp4'))
v.file = convert_video_anime(v.file.path,path)
v.save()
recording = v
towrite = recording.file_processed.storage.open(recording.file.path, mode='wb')
with recording.file.open('rb') as file:
    towrite.write(file.read())
towrite.close()
recording.file_processed = recording.file.path
recording.save()
print(v.file_processed.url)
