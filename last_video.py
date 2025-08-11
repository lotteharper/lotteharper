import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from django.conf import settings
from live.models import VideoRecording
v = VideoRecording.objects.filter(user__id=settings.MY_ID).order_by('-last_frame').first()
print('Last recording is {}'.format(str(v)))
