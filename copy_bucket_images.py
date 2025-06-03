import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from django.conf import settings
import boto3

session = boto3.Session(
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

s3 = session.client('s3')

# Replace with your actual bucket and prefix names
source_bucket = 'uglek'
source_prefix = 'home/team/lotteh'
destination_bucket = 'charlotteharper'
destination_prefix = 'home/team/lotteh'

next_token = ''

def should_copy(key):
    print('Should copy?')
    pref = ''
    print(pref + key)
    from feed.models import Post
    if p1 or p2 or p3 or p4 or p5 or p6:
        print('Copying')
        return True
    return False

#while True:
#   response = s3.list_objects_v2(
#       Bucket=source_bucket,
#       Prefix=source_prefix,
#       ContinuationToken=next_token
#   )
def copy_file(s3, key):
    key = key[1:]
    dest_key = key
    response = s3.copy_object(Bucket=destination_bucket, Key=dest_key, CopySource={'Bucket': source_bucket, 'Key': key})
    print(response)

from feed.models import Post
for post in Post.objects.all():
    if post.image_bucket: print(post.image_bucket.name)
    if post.image_bucket: copy_file(s3, post.image_bucket.name)
    if post.image_original_bucket: copy_file(s3, post.image_original_bucket.name)
    if post.image_censored_bucket: copy_file(s3, post.image_censored_bucket.name)
    if post.image_censored_thumbnail_bucket: copy_file(s3, post.image_censored_thumbnail_bucket.name)
    if post.image_public_bucket: copy_file(s3, post.image_public_bucket.name)
    if post.image_thumbnail_bucket: copy_file(s3, post.image_thumbnail_bucket.name)

print("Posts copied successfully!")
