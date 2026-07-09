print('Backup to Write-Once-Read-Many Mirror')
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from django.conf import settings
import datetime
import requests
import boto3
import os

# --- CONFIGURATION ---
GITHUB_OWNER = "lotteharper"
GITHUB_REPO = "lotteharper"
BRANCH = "main"  # Or specify a branch/tag/commit
ZIP_FILENAME = f"{GITHUB_REPO}.zip"

# --- STEP 1: Download GitHub Repo as ZIP ---
zip_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/archive/refs/heads/{BRANCH}.zip"
if not os.path.exists(ZIP_FILENAME):
    print('Downloading zip as none was found...')
    response = requests.get(zip_url)
    response.raise_for_status()
    with open(ZIP_FILENAME, "wb") as f:
        f.write(response.content)

from backup.models import PublicBackup, get_file_path

b = PublicBackup.objects.create()

def list_and_delete_oldest_s3_object(bucket_name):
    """
    List S3 objects in a bucket and delete the oldest one.
    Args:
        bucket_name: Name of the S3 bucket
    """
    # Initialize S3 client
    s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,)
    try:
        # List all objects in the bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in response:
            print(f"Bucket '{bucket_name}' is empty")
            return
        # Get all objects
        objects = response['Contents']
        print(f"\nObjects in bucket '{bucket_name}':")
        print(f"{'Key':<50} {'Last Modified':<30} {'Size (bytes)'}")
        print("-" * 90)
        for obj in objects:
            key = obj['Key']
            last_modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
            size = obj['Size']
            print(f"{key:<50} {last_modified:<30} {size}")
        # Find the oldest object
        oldest_object = min(objects, key=lambda x: x['LastModified'])
        oldest_key = oldest_object['Key']
        oldest_date = oldest_object['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n{'='*90}")
        print(f"Oldest object: {oldest_key}")
        print(f"Last modified: {oldest_date}")
        print(f"{'='*90}")
        if len(objects) > 6:
            s3_client.delete_object(Bucket=bucket_name, Key=oldest_key)
    except Exception as e:
        print(f"Error: {e}")

list_and_delete_oldest_s3_object('charlotteharper-backups')

out_path = os.path.join(settings.MEDIA_ROOT, get_file_path(b, 'backup.zip'))
towrite = b.file.storage.open(out_path, mode='wb')
with open(ZIP_FILENAME, 'rb') as file:
    towrite.write(file.read())
towrite.close()
b.file = out_path
b.save()

os.remove(ZIP_FILENAME)


print('Finished backup to S3')
