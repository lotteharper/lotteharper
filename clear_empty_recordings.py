MIN_FRAMES = 10
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from django.conf import settings
from live.models import VideoRecording
for v in VideoRecording.objects.filter(processed=True):
    if v.frames.count() < MIN_FRAMES:
        print('Deleting recording with {} frames'.format(v.frames.count()))
        v.delete()
