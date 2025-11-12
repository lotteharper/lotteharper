import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

count = 5
if len(sys.argv) > 1:
    try:
        count = int(sys.argv[1])
    except: pass

from django.conf import settings
from live.models import VideoRecording
vids = VideoRecording.objects.filter(user__id=settings.MY_ID).order_by('-last_frame')[:count]
for count,vid in enumerate(vids):
    print('#{} - {}\n'.format(count + 1, str(vid)))
