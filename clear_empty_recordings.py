MIN_FRAMES = 10
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from django.conf import settings
from live.models import VideoRecording
from django.utils import timezone
import datetime
for v in VideoRecording.objects.filter(processing=True, processed=True, last_frame__lte=timezone.now()-datetime.timedelta(minutes=1)).order_by('-last_frame'):
    if v.duration < 10:
        print(f"Deleting {v.duration} second recording with id #{v.id}")
        v.delete()
