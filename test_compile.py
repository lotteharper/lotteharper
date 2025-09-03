import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from feed.models import Post
Post.objects.get(id=105).compile_content()
