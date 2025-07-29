def download_image_from_url(image_url, save_path):
    import requests
    """
    Downloads an image from a given URL and saves it to a specified local path.

    Args:
        image_url (str): The URL of the image to download.
        save_path (str): The local path where the image will be saved, including the filename and extension.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Image successfully downloaded to: {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")

def upload_recording(recording, camera):
    from django.conf import settings
    from live.duration import get_duration
    if get_duration(recording.file.path) > (7.5 if (settings.LIVE_INTERVAL/1000 * 1.5) <= 7.5 else (settings.LIVE_INTERVAL/1000 * 1.5)):
        from better_profanity import profanity
        import traceback
        import pytz
        transcript = '\nTranscript: ' if (recording.transcript and len(recording.transcript) > 0) else ''
        description = profanity.censor(camera.description) + transcript + profanity.censor(recording.transcript[:4000]) + '\nRecorded on ' + recording.last_frame.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%A %B %d, %Y at %H:%M:%S')
        title = profanity.censor(camera.title[:70])
        print(description)
#        frame = recording.frames.all()[int(recording.frames.count()/2)]
        print(recording.file.path)
        import os
        print(os.path.exists(recording.file.path))
        try:
            from recordings.youtube import upload_youtube
            id, recording = upload_youtube(
                camera.user,
                recording,
                recording.file.path,
                title,
                description,
                [profanity.censor(tag) for tag in camera.tags.split(',')],
                category=camera.category,
                privacy_status=camera.privacy_status if recording.public else 'private',
                age_restricted=not recording.public)
            from lotteh.celery import update_video_description
            update_video_description.apply_async(args=[camera.user.id, id, recording.thumbnail_url, description, title, camera.category], countdown=60*5)
            recording.title = title
            recording.description = description
            recording.category = camera.category
            recording.uploaded = True
        except:
            recording.uploaded = False
            print(traceback.format_exc())
        recording.save()
        return recording

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def load_credentials(filename):
    from django.conf import settings
    import os, pickle
    from oauth2client import file, client, tools
    filen = os.path.join(settings.BASE_DIR, 'keys/', filename)
    store = file.Storage(filen)
    with open(filen, 'rb') as f:
        creds = pickle.load(f)
    if creds.expired:
        creds.refresh(Request())
    return creds

def save_credentials(creds, filename):
    from django.conf import settings
    from oauth2client import file, client, tools
    import os, pickle
    filen = os.path.join(settings.BASE_DIR, 'keys/', filename)
    store = file.Storage(filen)
    store.put(creds)
    with open(filen, 'wb') as f:
        pickle.dump(creds, f)
    f.close()
    return

def update_description(user, video_id, new_description, current_title, current_category_id):
    from django.urls import reverse
    from django.conf import settings

    import httplib2
    import os
    import random
    import sys
    import time
    import traceback

    from apiclient.discovery import build
    from apiclient.errors import HttpError
    from apiclient.http import MediaFileUpload
    from oauth2client.client import flow_from_clientsecrets
    from oauth2client.file import Storage
    from oauth2client.tools import argparser, run_flow


    # Explicitly tell the underlying HTTP transport library not to retry, since
    # we are handling retry logic ourselves.
    httplib2.RETRIES = 1

    # Maximum number of times to retry before giving up.
    MAX_RETRIES = 10

    # Always retry when these exceptions are raised.
    RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)

    # Always retry when an apiclient.errors.HttpError with one of these status
    # codes is raised.
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

    # The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
    # the OAuth 2.0 information for this application, including its client_id and
    # client_secret. You can acquire an OAuth 2.0 client ID and client secret from
    # the Google API Console at
    # https://console.cloud.google.com/.
    # Please ensure that you have enabled the YouTube Data API for your project.
    # For more information about using OAuth2 to access the YouTube Data API, see:
    #   https://developers.google.com/youtube/v3/guides/authentication
    # For more information about the client_secrets.json file format, see:
    #   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    CLIENT_SECRETS_FILE = "client_secrets.json"

    # This OAuth 2.0 access scope allows an application to upload files to the
    # authenticated user's YouTube channel, but doesn't allow other types of access.
    YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    # This variable defines a message to display if the CLIENT_SECRETS_FILE is
    # missing.
    MISSING_CLIENT_SECRETS_MESSAGE = """
    WARNING: Please configure OAuth 2.0

    To make this sample run you will need to populate the client_secrets.json file
    found at:

       %s

    with information from the API Console
    https://console.cloud.google.com/

    For more information about the client_secrets.json file format, please visit:
    https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       CLIENT_SECRETS_FILE))

    VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


    def get_authenticated_service(email):
#      credentials = Credentials(
#          token=access_token,
#          refresh_token=refresh_token,
#          token_uri=settings.BASE_URL + reverse('users:oauth')
#      )
      from users.oauth import get_creds
      credentials = load_credentials(email)

      return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        credentials=credentials)

    youtube = get_authenticated_service(user.email)
    # Update the video's description
    body = {
        'id': video_id,
        'snippet': {
            'title': current_title, # Provide the current title
            'description': new_description,
            'categoryId': current_category_id # Provide the current category ID
        }
    }

    update_request = youtube.videos().update(
        part="snippet",
        body=body
    )
    update_response = update_request.execute()

    print(f"Video description updated successfully for video ID: {update_response['id']}")
