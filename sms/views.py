from django.views.decorators.csrf import csrf_exempt

timeouts = {}

RATE_LIMIT = 5

@csrf_exempt
def sms(request):
    from django.conf import settings
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from django.shortcuts import render
    from django.contrib.auth.decorators import login_required
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.utils import timezone
    from django.contrib.auth.decorators import user_passes_test
    from vendors.tests import is_vendor
    from feed.tests import pediatric_identity_verified
    from django.http import HttpResponse
    from django.contrib.auth.models import User
    import threading, time
    from django.conf import settings
    from feed.templatetags.nts import number_to_string
    from chat.models import Message
    from users.tfa import send_user_text
    from users.logout import logout_user, logout_all
    from datetime import timedelta
    from twilio.twiml.voice_response import VoiceResponse, Gather
    from twilio.twiml.messaging_response import MessagingResponse
    global RATE_LIMIT
    global timeouts
    from twilio.rest import Client
    from_phone = User.objects.get(id=settings.MY_ID).profile.phone_number #'+14255358727'
    phone = request.POST.get('From', '')
    resp = MessagingResponse()
    if phone in timeouts and timeouts[phone] and timezone.now() - timeouts[phone] < timedelta(seconds=1):
        return HttpResponse(str(resp), content_type='text/xml')
    timeouts[phone] = timezone.now()
    message = request.POST.get('Body', None)
    m = ''
    if message:
        m = message.lower()
    user = None
    users = User.objects.filter(profile__phone_number=phone).order_by('-profile__last_seen')
    if users.count() > 0:
        user = users.first()
    if not user:
        if m.startswith('my email is'):
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            import re
            match = re.search(email_pattern, m[len('my email is'):])
            if match:
                e = match.group(0)
                from email_validator import validate_email
                valid = validate_email(e, check_deliverability=True)
                us = User.objects.filter(email=e).order_by('-profile__last_seen').first()
                if valid and (not us):
                    from django.utils.crypto import get_random_string
                    from users.username_generator import generate_username as get_random_username
                    user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                    user.profile.finished_signup = False
                    user.profile.phone_number = phone
                    user.profile.save()
                    from users.email import send_verification_email
                    send_verification_email(user)
                    resp.message(f"Thank you for creating an account.\nWe sent you a verification email, please check your email for an email from {settings.DOMAIN} and click the link in the email to verify your account. You have been assigned the randomly generated username {user.username}\nAfter verifying your email, please update it as appropriate using your email with this link {settings.BASE_URL}/accounts/password-reset/ before logging in with the link at {settings.BASE_URL}/accounts/login/ where you can change your username and display name as well as update your phone number through your email if needed.\nEnjoy the app! See you there.")
                else:
                    resp.message(f"Your email is already in the system.\nPlease login at {settings.BASE_URL}/accounts/login/ and make sure to reset your password if you need to at {settings.BASE_URL}/accounts/password-reset/\nYou can find your username in the password reset email. You can add a phone number to your profile by editing your profile at {settings.BASE_URL}/accounts/profile/")
            else:
                resp.message('Sorry, we didn\'t get your email address. Please send a message in the format "my email is " containing your email spaced appropriately, for example "my email is johnasample@{}". Be sure to check spelling and include the full address.'.format(settings.DOMAIN))
        else:
            resp.message('You need an account to message and call me. This site is age restricted, so do not message or call if you are under {} ({}). Join {} at {}/accounts/register/ ({}+) or send me a text with the text "my email is " with your email at the end, for example "my email is johnsample@{}" case insensitive to sign up. Be sure to answer your email and check for the email from {}.'.format(number_to_string(settings.MIN_AGE), settings.MIN_AGE, settings.SITE_NAME.capitalize(), settings.BASE_URL, settings.MIN_AGE, settings.DOMAIN, settings.SITE_NAME))
    elif m == 'stop':
        for u in users:
            u.profile.phone_number = '+1'
            u.save()
        resp.message('You are now unsubscribed.')
    elif m == 'logout':
        if user.is_superuser:
            logout_all()
            resp.message('You have logged all users out, {}'.format(User.objects.get(id=settings.MY_ID).profile.name))
        else:
            logout_user(user)
            resp.message('You have been logged out, {}'.format(User.objects.get(id=settings.MY_ID).profile.name))
    elif m == 'how are you':
        resp.message(User.objects.get(id=settings.MY_ID).profile.status)
    elif m == 'details':
        resp.message(settings.DOMAIN.capitalize() + " is a beauty and health blog. Visit today at {}".format(settings.BASE_URL))
    elif m == 'login':
        resp.message("Log in to {} here - {}".format(settings.DOMAIN.capitalize(), settings.BASE_URL + user.profile.create_face_url()))
    elif m == 'photo':
        extra = ''
        me = User.objects.get(id=settings.MY_ID)
        msg = resp.message("Here is the latest photo of me." + extra)
        if not (me in user.profile.subscriptions.all()):
            msg.media(settings.BASE_URL + User.objects.get(id=settings.MY_ID).profile.get_face_blur_url())
        else:
            msg.media(settings.BASE_URL + User.objects.get(id=settings.MY_ID).profile.get_public_image_url())
    else:
        resp.message('I\'m thinking about that. Give me a few seconds...')
        from lotteh.celery import reply_message_async
        reply_message_async.delay(phone, message)
    return HttpResponse(str(resp), content_type='text/xml')
