print('Removing empties from playlists, please wait.')
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from django.conf import settings
from recordings.youtube import remove_empty_videos_from_playlists
from django.contrib.auth.models import User
remove_empty_videos_from_playlists(User.objects.get(id=settings.MY_ID), email=None if len(sys.argv) < 3 else sys.argv[2])
