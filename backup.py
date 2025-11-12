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

out_path = os.path.join(settings.MEDIA_ROOT, get_file_path(b, 'backup.zip'))
towrite = b.file.storage.open(out_path, mode='wb')
with open(ZIP_FILENAME, 'rb') as file:
    towrite.write(file.read())
towrite.close()
b.file = out_path
b.save()

os.remove(ZIP_FILENAME)

print('Finished backup to S3')
