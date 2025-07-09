import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from security.censor_video import censor_video_nude
from live.models import get_file_path, VideoRecording
p = VideoRecording.objects.order_by('-last_frame')[1].file.path
op = get_file_path(None, 'frame.mp4')
censor_video_nude(p, op, scale=0.2)
