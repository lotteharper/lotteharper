import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from live.models import VideoRecording

v = VideoRecording.objects.order_by('-last_frame').first()
v.processing = False
v.save()
from lotteh.celery import process_recording
process_recording(v.id, False)
