import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

import PIL
from PIL import Image
from PIL.ExifTags import TAGS

from feed.models import Post
import traceback

def generate_thumbnail(post):
    post.image_thumbnail = None
    post.save()
    p = post
    p.get_image_thumb_url()
    if p.image_thumbnail and os.path.exists(p.image_thumbnail.path):
        towrite = p.image_thumbnail_bucket.storage.open(p.image_thumbnail.path, mode='wb')
        with p.image_thumbnail.open('rb') as file:
            towrite.write(file.read())
        towrite.close()
        p.image_thumbnail_bucket = p.image_thumbnail.path
    p.save()

def upload_image(post):
    p = post
    towrite = p.image_bucket.storage.open(p.image.path, mode='wb')
    with p.image.open('rb') as file:
        towrite.write(file.read())
    towrite.close()
    p.image_bucket = p.image.path
    p.save()


for post in Post.objects.filter(posted=True, published=True, uploaded=True).exclude(image=None).order_by('-date_posted'):
    try:
        if post.image:
            if post.image and not os.path.exists(post.image.path): post.download_photo()
            post = Post.objects.get(id=post.id)
            if post.image_original and not os.path.exists(post.image_original.path):
                post.download_original()
                if os.path.exists(post.image_original.path):
                    post = Post.objects.get(id=post.id)
                    try:
                        im = Image.open(post.image.path)
                        im.verify()
                        im.close()
                        im = Image.open(post.image.path)
                        im.transpose(PIL.Image.FLIP_LEFT_RIGHT)
                        im.close()
                        post.image = post.image_original.path
                        post.save()
                        upload_image(post)
                    except:
                        print('Invalid post - ' + str(post.id))
                        print(post.image.path)
                        if len(sys.argv) == 2: post.delete()
                        print(traceback.format_exc())
            post.save()
            post = Post.objects.get(id=post.id)
            if os.path.exists(post.image.path):
                try:
                    im = Image.open(post.image.path)
                    im.verify()
                    im.close()
                    im = Image.open(post.image.path)
                    im.transpose(PIL.Image.FLIP_LEFT_RIGHT)
                    im.close()
                except:
                    print('Invalid post - ' + str(post.id))
                    print(post.image.path)
                    if len(sys.argv) == 2: post.delete()
                    print(traceback.format_exc())
            else:
                print('Invalid post - ' + str(post.id))
                print(post.image)
                if len(sys.argv) == 2: post.delete()
            if post.image_thumbnail and not os.path.exists(post.image_thumbnail.path): post.download_thumbnail()
            post = Post.objects.get(id=post.id)
            if os.path.exists(post.image_thumbnail.path):
                try:
                    im = Image.open(post.image_thumbnail.path)
                    im.verify()
                    im.close()
                    im = Image.open(post.image_thumbnail.path)
                    im.transpose(PIL.Image.FLIP_LEFT_RIGHT)
                    im.close()
                except:
                    print('Invalid post - ' + str(post.id))
                    print(post.image_thumbnail.path)
                    if len(sys.argv) == 2: generate_thumbnail(post)
                    print(traceback.format_exc())
            else:
                print('Invalid post - ' + str(post.id))
                print(post.image_thumbnail)
                if len(sys.argv) == 2: generate_thumbnail(post)
    except:
        print('Invalid post - ' + str(post.id))
        print(post.image)
        if len(sys.argv) == 2: post.delete()
        print(traceback.format_exc())
