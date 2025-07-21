import google.oauth2.credentials
import google_auth_oauthlib.flow
from apiclient.discovery import build
from apiclient import errors
from django.conf import settings
from django.urls import reverse
import os

flows = {}

creds = {}

def get_creds(email):
    global creds
    return creds['email'] if 'email' in creds else None

def get_imgur_url():
    import uuid
    url = 'https://api.imgur.com/oauth2/authorize?client_id={}&response_type=token&state={}'.format(settings.IMGUR_ID, str(uuid.uuid4()))
    return url

def get_auth_url(request, email):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(str(os.path.join(settings.BASE_DIR, 'client_secret.json')),
    scopes=['https://www.googleapis.com/auth/youtube.force-ssl',
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid',
   ])
    flow.redirect_uri = settings.BASE_URL + reverse('users:oauth')
    authorization_url, state = None, None
    if email:
        authorization_url, state = flow.authorization_url(
            login_hint=email,
#            redirect_uri='https://lotteh.com/accounts/auth/callback/',
            prompt='consent')
    else:
        authorization_url, state = flow.authorization_url(
#            redirect_uri='https://lotteh.com/accounts/auth/callback/',
            prompt='consent')
    global flows
    flows[state] = flow
    return authorization_url, state

def get_user_info(credentials):
  """Send a request to the UserInfo API to retrieve the user's information.

  Args:
    credentials: oauth2client.client.OAuth2Credentials instance to authorize the
                 request.
  Returns:
    User information as a dict.
  """
  user_info_service = build(
      serviceName='oauth2', version='v2',
      credentials=credentials)
  user_info = None
  try:
    user_info = user_info_service.userinfo().get().execute()
  except (errors.HttpError, e):
    logging.error('An error occurred: %s', e)
  if user_info and user_info.get('id'):
    return user_info
  else:
    raise Exception()

def parse_callback_url(request, response):
#    print(str(request.body))
    global flows
#    flow = flows[request.GET.get('state')]
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(str(os.path.join(settings.BASE_DIR, 'client_secret.json')),
    scopes=['https://www.googleapis.com/auth/youtube.force-ssl',
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid',
    ])
#    print(token_url)
    flow.redirect_uri = settings.BASE_URL + reverse('users:oauth')
    from urllib.parse import unquote_plus
    import json
    flow.fetch_token(authorization_response=response) #json.dumps(request.GET.dict()))
    credentials = flow.credentials
    from recordings.youtube import save_credentials
    user_email = get_user_info(credentials)['email']
    from recordings.youtube import save_credentials
    save_credentials(credentials, user_email)
    global creds
    creds[user_email] = credentials
    return user_email, credentials.token, credentials.refresh_token

