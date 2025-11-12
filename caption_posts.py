import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from feed.models import Post
from enhance.caption import caption_post
for post in Post.objects.filter(feed='private', public=True, private=False).exclude(image=None).order_by('-date_posted'):
    if len(post.content) < 100 or not post.content:
        post.content = ''
        post.save()
        caption_post(post)
