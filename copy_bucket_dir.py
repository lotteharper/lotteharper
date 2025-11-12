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
source_prefix = 'home/team/lotteh/media/profiles'
destination_bucket = 'charlotteharper'
destination_prefix = 'home/team/lotteh/media/profiles'

next_token = ''

while True:
   response = s3.list_objects_v2(
       Bucket=source_bucket,
       Prefix=source_prefix,
#       ContinuationToken=next_token
   )
   for object in response.get('Contents', []):
       copy_source = {
           'Bucket': source_bucket,
           'Key': object['Key']
       }
       destination_key = destination_prefix + object['Key'][len(source_prefix):]

       try:
           s3.copy_object(
               Bucket=destination_bucket,
               Key=destination_key,
               CopySource=copy_source
           )
           print(f"Copied {object['Key']} to {destination_key}")
       except Exception as e:
           print(f"Error copying {object['Key']}: {e}")

   next_token = response.get('NextContinuationToken')
   if not next_token:
       break

print("Directory copied successfully!")
