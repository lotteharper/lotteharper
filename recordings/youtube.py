#from allauth.socialaccount.models import SocialLogin, SocialToken, SocialApp
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

#    import google.oauth2.credentials
#    import google_auth_oauthlib.flow
#    print(token_url)
#    from django.urls import reverse
#    if True: # not creds.valid:
#        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(str(os.path.join(settings.BASE_DIR, 'client_secret.json')),
#        scopes=['https://www.googleapis.com/auth/youtube.force-ssl',
#            'https://www.googleapis.com/auth/youtube.upload',
#            'https://www.googleapis.com/auth/youtube',
#            'https://www.googleapis.com/auth/userinfo.email',
#            'openid',
#        ])
#        flow.redirect_uri = settings.BASE_URL + reverse('users:oauth')
#        creds = tools.run_flow(flow, store)
#    return creds

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

def upload_youtube(user, file_path, title, description, tags, category='22', privacy_status='public', thumbnail=None, age_restricted=False):
    # Video options
    from django.urls import reverse
    from django.conf import settings

    access_token = user.profile.token
    refresh_token = user.profile.refresh_token

    options = {
        "title" : title,
        "description" : description,
        "tags" : tags,
        "category" : category,
        "privacy" : privacy_status,
        "thumbnail" : thumbnail,
        "kids" : False,
    }
    if age_restricted: options["contentDetails"] = {"contentRating": {"ytRating": "ytAgeRestricted"}}

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

    def initialize_upload(youtube, options, the_file):
      body=dict(
        snippet=dict(
          title=options['title'],
          description=options['description'],
          tags=options['tags'],
          categoryId=options['category'],
          thumbnails=dict(
            default=dict(
              url=options['thumbnail']
            ),
          ) if options['thumbnail'] else None,
        ),
        status=dict(
          privacyStatus=options['privacy'],
          selfDeclaredMadeForKids=options['kids']
        )
      )

      # Call the API's videos.insert method to create and upload the video.
      insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(the_file, chunksize=-1, resumable=True)
      )

      resumable_upload(insert_request)

    # This method implements an exponential backoff strategy to resume a
    # failed upload.
    def resumable_upload(insert_request):
      response = None
      error = None
      retry = 0
      while response is None:
        try:
          status, response = insert_request.next_chunk()
          if response is not None:
            if 'id' in response:
              pass
            else:
              exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as e:
          print(traceback.format_exc())
          if e.resp.status in RETRIABLE_STATUS_CODES:
            error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                 e.content)
          else:
            raise
        except RETRIABLE_EXCEPTIONS as e:
          print(traceback.format_exc())
          error = "A retriable error occurred: %s" % e

        if error is not None:
          print(error)
          retry += 1
          if retry > MAX_RETRIES:
            exit("No longer attempting to retry.")

          max_sleep = 2 ** retry
          sleep_seconds = random.random() * max_sleep
          print("Sleeping %f seconds and then retrying..." % sleep_seconds)
          time.sleep(sleep_seconds)

    youtube = get_authenticated_service(user.email)
    try:
      initialize_upload(youtube, options, file_path)
    except HttpError as e:
      print(traceback.format_exc())
      print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
      raise Exception('An error has occured with upload, raising')
