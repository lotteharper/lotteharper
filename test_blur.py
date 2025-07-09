import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from security.censor_video import censor_video_nude_fast
from live.models import get_file_path, VideoRecording
from django.conf import settings
p = VideoRecording.objects.order_by('-last_frame')[1].file.path
op = os.path.join(settings.MEDIA_ROOT, get_file_path(None, 'frame.mp4'))
censor_video_nude_fast(p, op, scale=0.5)
p = Post.objects.create(file=op)
p.file_bucket.path
print(op)
