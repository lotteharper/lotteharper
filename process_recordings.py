import os, sys
number = int(sys.argv[1]) if len(sys.argv) > 1 else 3
print(f"Processing {number} recordings manually")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from django.conf import settings
from lotteh.celery import process_recordings
process_recordings(num=number)
