self the code. Then, enter the code and press enter.'|etrans }}</p>
            </fieldset>
            <div class="form-group">
                <button class="btn btn-outline-secondary" type="submit">{{ 'Enter code'|etrans }}</button>
            </div>
        </form>
{% endblock %}
{% block javascript %}
{% if autofocus %}
var codeInput = document.getElementById("id_code");
codeInput.focus();
{% endif %}
var sendTextCheckbox = document.getElementById("id_send_email");
var form = document.getElementById("tfa-form");
function updateURLParams(check) {
	const urlParams = new URLSearchParams(window.location.search);
        const text = urlParams.get('text');
	if(!text) {
		if(check) sendTextCheckbox.checked = true;
	} else {
		if(check) sendTextCheckbox.checked = false;
	}
    if(sendTextCheckbox.checked) {
		form.action = "{{ request.path }}{% if request.GET.next %}?next={{ request.GET.next }}{% endif %}"
		$(".form-check-label").html(" {{ 'Send email'|etrans }}");
    } else {
		form.action = "{{ request.path }}?text=t{% if request.GET.next %}&next={{ request.GET.next }}{% endif %}"
		$(".form-check-label").html(" {{ 'Send text message'|etrans }}");
	}
}
sendTextCheckbox.addEventListener('change', e => {
        updateURLParams(false);
});
updateURLParams(true);
{% endblock %}
```


--- File: lotteharper-main/users/templates/users/tfa_onboarding.html ---
```html
{% extends 'base.html' %}
{% block content %}
{% load crispy_forms_tags %}
{% load app_filters %}
        <form method="POST">
            {% csrf_token %}
            <fieldset class="form-group">
                <legend class="border-bottom mb-4">{{ 'Set Up Two Factor Authentication'|etrans }}</legend>
                {{ form|crispy }}
            </fieldset>
            <div class="form-group">
                <button class="btn btn-outline-secondary" type="submit">{{ 'Add phone number'|etrans }}</button>
            </div>
        </form>
{% endblock %}
```


--- File: lotteharper-main/users/templates/users/toggle_active.html ---
```html
<form style="display: inline-block;" action="{% url 'users:toggle-user-active' user.id %}" method="POST" class="publishForm">
<button class="btn btn-sm btn-outline-danger" type="submit">{% if user.is_active %}<i class="bi bi-eye-fill"></i>{% else %}<i class="bi bi-eye-slash-fill"></i>{% endif %}</button>
</form>
```


--- File: lotteharper-main/users/templates/users/toggle_gift.html ---
```html
<form style="display: inline-block;" action="{% url 'users:toggle-gift' user.id %}" method="POST" class="publishForm">
<button class="btn btn-sm btn-outline-success" type="submit">{% if not request.user in user.profile.subscriptions.all %}<i class="bi bi-gift-fill"></i> Gift{% else %}<i class="bi bi-gift"></i> End Gift{% endif %}</button>
</form>
```


--- File: lotteharper-main/users/templates/users/unsubscribe.html ---
```html
{% extends "base.html" %}
{% block content %}
{% load app_filters %}
<h1>{{ 'Success'|etrans }}</h1>
<h2>{{ 'You are now unsubscribed.'|etrans }}</h2>
<p>{{ 'To subscribe again, please click the button below.'|etrans }}</p>
<form method="POST" action="{{ feed }}">
{% csrf_token %}
<p><button type="submit" class="btn btn-outline-primary">{{ 'Resubscribe'|etrans }}</button></p>
</form>
<p>{{ 'Or, please'|etrans }} <a href="{% url 'users:profile' %}" title="Visit your profile">{{ 'visit your profile'|etrans }}</a>, {{ 'check the box, and submit.'|etrans }}</p>
<p><a href="{% url 'app:app' %}" class="btn btn-primary" title="See new posts"><i class="bi bi-globe"></i> {{ 'Explore'|etrans }}</a></p>
{% endblock %}
```


--- File: lotteharper-main/users/templates/users/user_confirm_delete.html ---
```html
{% extends "blog/base.html" %}
{% block content %}
    <div class="content-section">
        <form method="POST">
            {% csrf_token %}
            <fieldset class="form-group">
                <legend class="border-bottom mb-4">Delete User</legend>
                <h2>Are you sure you want to delete the user "@{{ object.username }}"</h2>
            </fieldset>
            <div class="form-group">
                <button class="btn btn-outline-danger" type="submit">Yes, Delete</button>
                <a class="btn btn-outline-secondary" href="{% url 'feed:profile' username=object.username %}">Cancel</a>
            </div>
        </form>
    </div>
{% endblock content %}
```


--- File: lotteharper-main/users/templates/users/_user.html ---
```html
{% load app_filters %}
<div>
<img src="{{ user.profile.get_image_url }}" alt="@{{ user.profile.name }}'s profile photo" width="120" height="120" align="left" style="margin-top:5px; margin-right:10px; margin-bottom:10px; border-radius: 50%;"/>
    <div class="article-metadata">
      <p class="mr-2">@{{ user.username }} - {{ user.profile.name }} ({{ user.profile.preferred_name }})</p>
      <small class="text-muted">Last seen {{ user.profile.last_seen|date:"F d, Y" }} {{ user.profile.last_seen|time:"H:i" }}</small>
      <small class="text-muted">Joined on {{ user.profile.date_joined|date:"F d, Y" }} {{ user.profile.date_joined|time:"H:i" }}</small>
      <small>{{ user.email }}</small>
      {% if user.profile.phone_number %}<small><i class="bi bi-phone-fill"></i>{{ user.profile.phone_number }}</small>{% endif %}
      {% if user.verifications.last %}
      <small>'{{ user.verifications.last.full_name }}'</small>
      <small><i class="bi bi-123"></i> {{ user.verifications.last.document_number }}</small>
      <small><i class="bi bi-calendar-heart-fill"></i> {{ user.verifications.last.birthdate }}</small>
      <a href="{{ user|document_front }}" class="btn btn-sm btn-outline-primary" title="ID front"><i class="bi bi-person-badge-fill"></i> ID front</a>
      <a href="{{ user|document_back }}" class="btn btn-sm btn-outline-primary" title="ID back"><i class="bi bi-upc-scan"></i> ID back</a>
      {% endif %}
      <small>#{{ user.id }}</small>
      <small>{% if user.profile.subscribed %}Subscribed{% else %}Not subscribed{% endif %}</small>
    </div>
    {% if not user.is_superuser %}
    <div style="float: right;">{% include 'users/toggle_active.html' %}</div>
    <div style="float: right;">{% include 'users/toggle_gift.html' %}</div>
    {% endif %}
    {% autoescape off %}    
    <p class="article-content">{{ user.bio }}</p>
    {% endautoescape %}
    <hr>
    <p>{% if user.profile.identity_verified %}Verified user.{% else %}Unverified user.{% endif %} Verifications: {{ user.verifications.count|nts }}</p>
</div>
```


--- File: lotteharper-main/users/templates/users/users.html ---
```html
{% extends 'base.html' %}
{% load app_filters %}
{% block style %}
{% for user in users %}
{% if user.vendor_profile.video_intro_font %}
@font-face { font-family: 'Vendor Specified ({{ user.profile.name }})'; src: url('{{ user.vendor_profile.video_intro_font.url }}'); }
{% endif %}
{% endfor %}
{% endblock %}
{% block content %}
<h1>All Registered Visitors</h1>
{% if request.GET.page == '1' or not request.GET.page %}
<small>{{ verified_users|nts|capitalize }} ({{ verified_users }}) people active, {{ verified_user_count|nts }} ({{ verified_user_count }}) verified.</small>
<p>{{ new_today|nts|capitalize }} new today, {{ new_this_month|nts }} new this month, {{ subscribers|nts }} subscribers, {{ all_users.count|nts }} total.</p>
<small>{{ active_today|nonts|capitalize }} active today, {{ active_this_week|nonts }} this week, {{ active_this_month|nonts }} this month, {{ active_this_year|nonts }} this year.</small>
{% endif %}
<hr style="color: red;">
{% for user in users %}
{% include 'users/_user.html' %}
{% include 'survey/_user.html' %}
<hr style="color: blue;">
{% endfor %}
{% include 'pagelinks.html' %}
{% endblock %}
```


--- File: lotteharper-main/users/templates/users/verification_email.html ---
```html
<h1>{{ the_site_name }} - Verify Your Email</h1>
<p>Dear {{ user.username }},</p>
<p>To verify your email, please <a href="{{ protocol }}://{{ domain }}{% url 'users:activate' uidb64=uid token=token %}">click here</a>.</p>

<p>Alternatively, you can paste the following link in your browser's address bar:</p>
<p>{{ protocol }}://{{ domain }}{% url 'users:activate' uidb64=uid token=token %}</p>

<p>If you created an account at checkout, you will need to set your password. Please <a href="{{ protocol }}://{{ domain }}{% url 'users:password_reset' %}" title="Password reset">visit this link to reset your password</a>.</p>

<p>The link will expire in 30 minutes.</p>
<p>If you have not requested a verification email you can simply ignore this email.</p>
<p>Seeing you there,</p>
<p>{{ model_name }}</p>
```


--- File: lotteharper-main/users/templates/users/verification_email.txt ---
```
Dear {{ user.username }},
To verify your email, click the following link:
{{ protocol }}://{{ domain }}{% url 'users:activate' uidb64=uid token=token %}

Alternatively, you can paste the following link in your browser's address bar:
{{ protocol }}://{{ domain }}{% url 'users:activate' uidb64=uid token=token %}

The link will expire in 30 minutes.
If you have not requested a verification email you can simply ignore this email.
Seeing you there with love,
{{ model_name }}
```


--- File: lotteharper-main/users/templates/users/verify.html ---
```html
{% extends 'base.html' %}
{% block content %}
{% load app_filters %}
    <h2>{{ 'Verify Your Email'|etrans }}</h2>
    <p>{{ 'Please check your email and click the link to verify your account. You need to verify your email before you can log in. This step helps keep the site only accessible by real people like you.'|etrans }}</p>
    <a href="{% url 'users:resend_activation' %}" title="{{ 'Resend activation email'|etrans }}" class="btn btn-info">{{ 'Resend Verification Email'|etrans }}</a>
{% endblock content %}
```


--- File: lotteharper-main/users/tests.py ---
```python
def is_superuser_or_vendor(user):
    return user.is_superuser or user.profile.vendor
```


--- File: lotteharper-main/users/tfa.py ---
```python
from django.utils import timezone
import random
import datetime
from django.conf import settings
from feed.middleware import get_current_request
from django.contrib import messages
from .email import send_html_email
import traceback
from .models import MFAToken

account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN
source_phone = settings.PHONE_NUMBER

async def send_rust_text(target_phone, text):
    value = await send_text(target_phone, text)

def split_text_parts(text, max_len=310, last_max_len=293):
    words = text.split()
    parts = []
    curr_part = []

    for word in words:
        # If adding the word exceeds limit for all except last
        tentative = ' '.join(curr_part + [word])
        # For all but last, use max_len; for last use last_max_len
        curr_max = last_max_len if len(parts) and len(' '.join(parts + [tentative])) <= last_max_len else max_len

        if len(tentative) > curr_max:
            # Finish current part and start a new one
            if curr_part:
                parts.append(' '.join(curr_part))
            curr_part = [word]
        else:
            curr_part.append(word)

    # Append any remaining words
    if curr_part:
        parts.append(' '.join(curr_part))

    # Now, if last part is too long, move words to previous
    while len(parts) > 1 and len(parts[-1]) >= last_max_len:
        # Move last word from penultimate to last
        last_words = parts[-1].split()
        prev_words = parts[-2].split()
        moved_word = prev_words.pop()
        parts[-2] = ' '.join(prev_words)
        parts[-1] = moved_word + ' ' + ' '.join(last_words)

    # Clean up any blanks
    parts = [part for part in parts if part.strip()]
    # Final check
    assert all(len(part) < max_len for part in parts[:-1]), "A non-last part exceeds 310 chars"
    assert len(parts[-1]) < last_max_len, "Last part exceeds 293 chars"

    return parts

async def send_text(target_phone, text):
    import asyncio, math
    from twilio.rest import Client
    try:
        client = Client(account_sid, auth_token)
        if len(target_phone) >= 11:
            split_text = split_text_parts(text)
            total_length = str(len(split_text))
            for x in range(len(split_text)):
                count = str(x+1)
                response_fragment = split_text[x]
                if len(response_fragment) < 294:
                    msg = ' ({})'.format(count + '/' + total_length)
                    message = client.messages.create(
                        to=target_phone,
                        from_=source_phone,
                        body=response_fragment + msg + ('...' if len(response_fragment) > 293 else '') + ' Text STOP to cancel.')
                else:
                    msg = ' ({})'.format(count + '/' + total_length)
                    message = client.messages.create(
                        to=target_phone,
                        from_=source_phone,
                        body=response_fragment + msg + ('...' if len(response_fragment) > 310 else ''))
                await asyncio.sleep(10)
    except:
        import traceback
        print(traceback.format_exc())

def get_num_length(num, length):
    n = ''
    for x in range(length):
        n = n + str(num)
    return int(n)

def send_verification_text(user, token):
    length = user.profile.verification_code_length
    from django.utils.crypto import get_random_string
    code = get_random_string(length=length, allowed_chars='0123456789' if length < 8 else '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' if length < 10 else '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ~`!@#$%^&*()_+{}|\\:;"\'<,>.?/')
    token.set_password(code)
    token.expires = timezone.now() + datetime.timedelta(minutes=settings.AUTH_VALID_MINUTES)
    token.save()
    send_user_text(user, "Your verification code for {} is {}".format(settings.SITE_NAME, str(code)))

def send_verification_email(user, token):
    length = user.profile.verification_code_length
    from django.utils.crypto import get_random_string
    code = get_random_string(length=length, allowed_chars='0123456789' if length < 8 else '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' if length < 10 else '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ~`!@#$%^&*()_+{}|\\:;"\'<,>.?/')
    token.set_password(code)
    token.expires = timezone.now() + datetime.timedelta(minutes=settings.AUTH_VALID_MINUTES)
    token.save()
    send_html_email(user, "You have requested a code to access your account. Your verification code for {} is {}".format(settings.SITE_NAME, str(code)), "<p>Dear {},</p><p>Your verification code for {} is {}. Use this code to securely access your account. This email is auto-generated. Please do not reply to this email. If you did not request this code, you can safely disregard this email.</p><h2>{}</h2><p>Sincerely, {}</p>".format(user.profile.name, settings.SITE_NAME, str(code), str(code), settings.SITE_NAME))

def send_user_text(user, text):
    send_text(user.profile.phone_number, text)

def check_verification_code(user, token, code):
    token.attempts = token.attempts + 1
    profile = user.profile
    result = (token != None and code != '' and token.check_password(str(code)) and (token.expires > timezone.now()) and token.attempts <= settings.MFA_TOKEN_ATTEMPTS)
    if token.attempts < 3 and result:
        profile.verification_code_length = 6
    elif token.attempts > 1 and not result:
        profile.verification_code_length = profile.verification_code_length + 2
        if profile.verification_code_length > settings.MFA_TOKEN_LENGTH: profile.verification_code_length = settings.MFA_TOKEN_LENGTH
    token.save()
    profile.save()
    return result

def check_verification_time(user, token):
    result = (token != None) and (token.expires > timezone.now()) and token.attempts <= settings.MFA_TOKEN_ATTEMPTS
    return result
```


--- File: lotteharper-main/users/tokens.py ---
```python
from django.contrib.auth.tokens import PasswordResetTokenGenerator
class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        import six
        return (
            six.text_type(user.pk) + six.text_type(timestamp)
        )
account_activation_token = TokenGenerator()
unsubscribe_token = TokenGenerator()
```


--- File: lotteharper-main/users/urls.py ---
```python
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name='users'

from .views import (
    UserDeleteView,
)

urlpatterns = [
    path('all/', views.users, name='all'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_visitor, name='logout'),
    path('tfa/<str:username>/<str:usertoken>/', views.tfa, name='tfa'),
    path('tfa/onboarding/', views.tfa_onboarding, name='tfa_onboarding'),
    path('login/passwordless/', views.passwordless_login, name='passwordless'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             html_email_template_name='users/password_reset_html_email.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    path('resend_activation/', views.resend_activation, name='resend_activation'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('verify/', views.verify, name='verify'),
    path('unsubscribe/<str:username>/<token>/', views.unsubscribe, name='unsubscribe'),
    path('profile/', views.profile, name='profile'),
    path('user/<int:pk>/delete/', UserDeleteView.as_view(template_name='blog/user_confirm_delete.html'), name='delete-user'),
    path('user/<int:pk>/active/', views.toggle_user_active, name='toggle-user-active'),
    path('user/<int:pk>/gift/', views.toggle_gift, name='toggle-gift'),
    path('auth/google/', views.google_pub_auth, name='google-auth'),
    path('auth/google/callback/', views.google_pub_auth_callback, name='google-auth-callback'),
    path('auth/youtube/', views.google_auth, name='youtube'),
    path('auth/callback/', views.google_auth_callback, name='oauth'),
    path('auth/imgur/', views.imgur_oauth, name='imgur'),
    path('auth/imgur/callback/', views.imgur_callback, name='imgur-callback')
]
```


--- File: lotteharper-main/users/username_generator.py ---
```python
def generate_username(input=''):
    ONE = ['happy', 'sexy', 'fun', 'beautiful', 'pretty', 'handsome', 'dirty', 'gorgeous', 'stunning', 'lovely', 'perfect', 'busty', 'famous', 'best', 'lovely', 'stunning']
    TWO = ['person', 'woman', 'girl', 'beauty', 'sweetheart', 'lover', 'fox', 'bear', 'cutie', 'beast', 'babe', 'bestie', 'legend', 'hottie', 'runt', 'human', 'being', 'soul', 'goddess', 'memer', 'puppy', 'kitty', 'pup', 'pip', 'package', 'system', 'device']
    from django.contrib.auth.models import User
    from users.models import Profile
    import random
    TRIES = (len(ONE)-1) * (len(TWO)-1) * 100
    username = None
    tries = 0
    seed = ''
    for char in input:
        seed = seed + str(int(ord(char) - 32/127*5))
    random.seed(hash(seed) * -1 if seed else random.randrange(100000, 999999))
    while not username:
        username = ONE[random.randrange(0, len(ONE)-1)] + TWO[random.randrange(0, len(TWO)-1)] + str(random.randrange(0, 99))
        tries = tries + 1
        if tries > TRIES: break
        if User.objects.filter(username=username).count() == 0 and Profile.objects.filter(name=username).count() == 0:
            return username
    return 'Guest' + str(random.randrange(100000, 999999))
```


--- File: lotteharper-main/users/utils.py ---
```python
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.conf import settings
from security.views import all_unexpired_sessions_for_user

def send_expiry_notifications():
    for user in User.objects.filter(is_active=True, profile__admin=True):
        for session in all_unexpired_sessions_for_user(user):
            if session.expire_date < timezone.now() + datetime.timedelta(minutes=60) and session.expire_date > timezone.now():
                payload = {
                    'head': 'Your session is about to expire on {}'.format(settings.SITE_NAME),
                    'body': 'This session will expire in {} minutes with {}'.format((session.expire_date - timezone.now()).minutes, settings.SITE_NAME),
                    'icon': settings.BASE_URL + settings.ICON_URL,
                    'url': settings.BASE_URL,
                }
                from webpush import send_user_notification
                try:
                    send_user_notification(user, payload=payload)
                except: pass
```


--- File: lotteharper-main/users/views.py ---
```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    UpdateView,
    DeleteView
)
from django.utils.decorators import method_decorator
from face.tests import is_superuser_or_vendor
from vendors.tests import is_vendor
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import cache_page, never_cache, cache_control

@login_required
@user_passes_test(is_vendor)
def imgur_oauth(request):
    from users.oauth import get_imgur_url
    from django.shortcuts import redirect
    return redirect(get_imgur_url())

@csrf_exempt
@login_required
@user_passes_test(is_vendor)
def imgur_callback(request):
    if request.method == 'POST':
        vp = request.user.vendor_profile
        vp.imgur_token = request.GET.get('access_token', '')
        vp.imgur_refresh = request.GET.get('refresh_token', '')
        vp.imgur_username = request.GET.get('account_username', '')
        from django.utils import timezone
        vp.imgur_time = timezone.now()
        vp.save()
        from django.http import HttpResponse
        return HttpResponse(200)
    from django.shortcuts import render
    return render(request, 'users/imgur.html', {'title': 'Imgur Authentication'})

@csrf_exempt
@login_required
@user_passes_test(is_superuser_or_vendor)
def google_auth(request):
    from django.shortcuts import redirect
    from users.oauth import get_auth_url
    import uuid
    url, state = get_auth_url(request, request.user.email if request.user.is_authenticated else None)
    print(state)
    request.session['state'] = state
    return redirect(url)

def google_pub_auth(request):
    from django.shortcuts import redirect
    from users.oauth import get_pub_auth_url
    import uuid
    url, state = get_pub_auth_url(request, request.user.email if request.user.is_authenticated else None)
    print(state)
    request.session['state'] = state
    return redirect(url)

@login_required
@user_passes_test(is_superuser_or_vendor)
def google_auth_callback(request):
    print(request.session.get('state'))
    from users.oauth import parse_callback_url
    from security.middleware import get_qs
    from django.shortcuts import redirect
    from django.conf import settings
    from django.urls import reverse
    authorization_code = None
    import json
    url_working = settings.BASE_URL + request.get_full_path().replace(' ', '%20')
    if request.method == 'POST':
        email, token, refresh = parse_callback_url(request, request.user.id, url_working)
        print(email)
        from django.contrib import messages
        messages.success(request, 'Successfully linked a YouTube account')
        return redirect(reverse('/'))
    from django.shortcuts import render
    return render(request, 'users/oauth.html', {'title': 'YouTube Auth'})

def google_pub_auth_callback(request):
    print(request.session.get('state'))
    from users.oauth import parse_pub_callback_url
    from security.middleware import get_qs
    from django.shortcuts import redirect
    from django.conf import settings
    from django.urls import reverse
    authorization_code = None
    import json
    url_working = settings.BASE_URL + request.get_full_path().replace(' ', '%20')
    if request.method == 'POST':
        email, name, picture, token, refresh = parse_pub_callback_url(request, url_working)
        from django.contrib.auth.models import User
        user = User.objects.filter(email=email).order_by('-profile__last_seen').first() if not request.user.is_authenticated else request.user
        if not user:
            from users.username_generator import generate_username as get_random_username
            from django.utils.crypto import get_random_string
            user = User.objects.create_user(email=e, username=get_random_username(email), password=get_random_string(length=8))
            profile = user.profile
            import random
            profile.name = name.split(' ')[0] + ('' + (random.randrange(1111,9999) if User.objects.filter(profile__name=name).exclude(id=user.id).count() > 0 else ''))
            profile.full_name = name
            profile.preferred_name = name.split(' ')[0]
            profile.image_offsite = picture
            profile.finished_signup = True
            profile.save()
            from django.contrib import messages
            messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
            from users.email import send_verification_email
            send_verification_email(user)
            send_registration_push(user)
        if not request.user.is_authenticated:
            from django.contrib.auth import login as auth_login
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        from django.contrib import messages
        messages.success(request, 'Successfully linked Google account')
        return redirect(reverse('/'))
    from django.shortcuts import render
    return render(request, 'users/oauth.html', {'title': 'Google Auth'})


def resolve_multiple_accounts(request, user):
    from .models import AccountLink
    if request.user.is_authenticated and not request.user.account_link.objects.filter(to_user=user):
        AccountLink.objects.create(from_user=request.user, to_user=user)

def password_reset(request, uidb64, token):
    from django.shortcuts import redirect, get_object_or_404
#    from django.contrib.auth.forms import SetPasswordForm
    from .forms import SetPasswordForm
    from django.contrib import messages
    from django.contrib.auth.models import User
    from django.utils.http import urlsafe_base64_decode
    user = get_object_or_404(User, id=urlsafe_base64_decode(uidb64))
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse
        if form.is_valid() and default_token_generator.check_token(user, token):
            user.profile.email_verified = True
            user.profile.finished_signup = True
            user.profile.save()
            user.save()
            form.save()
            messages.success(request, 'Your password has been reset.')
        elif not form.is_valid():
            messages.warning(request, 'Your passwords do not match, or do not meet the requirements. Please try again.')
            return redirect(request.path)
        else:
            messages.warning(request, 'Your password reset link has expired. Please create a new one.')
        return redirect(reverse('users:login'))
    from django.shortcuts import render
    return render(request, 'users/password_reset_confirm.html', {
        'title': 'Reset your Password',
        'form': SetPasswordForm(user)
    })

@csrf_exempt
@login_required
@user_passes_test(is_superuser_or_vendor)
def toggle_user_active(request, pk):
    from django.contrib.auth.models import User
    user = User.objects.get(id=pk)
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
    from django.http import HttpResponse
    return HttpResponse('<i class="bi bi-eye-fill"></i>' if user.is_active else '<i class="bi bi-eye-slash-fill"></i>')

@csrf_exempt
@login_required
@user_passes_test(is_superuser_or_vendor)
def toggle_gift(request, pk):
    from django.contrib.auth.models import User
    user = User.objects.get(id=pk)
    from django.conf import settings
    model = request.user
    profile = user.profile
    if request.method == 'POST':
        if model in profile.subscriptions.all():
            profile.subscriptions.remove(model)
        else:
            profile.subscriptions.add(model)
        profile.save()
    from django.http import HttpResponse
    return HttpResponse('<i class="bi bi-gift-fill"></i>' if model in user.profile.subscriptions.all() else '<i class="bi bi-gift"></i>')

@login_required
@user_passes_test(is_superuser_or_vendor)
def users(request):
    from django.shortcuts import render
    from django.contrib.auth.models import User
    from django.utils import timezone
    import datetime
    from django.core.paginator import Paginator
    from django.contrib import messages
    page = 1
    if(request.GET.get('page', '') != ''):
        page = int(request.GET.get('page', ''))
    u = User.objects.all().order_by('-profile__last_seen')
    p = Paginator(u, 30)
    if page > p.num_pages or page < 1:
        messages.warning(request, "The page you requested, " + str(page) + ", does not exist. You have been redirected to the first page.")
    context = {
        'title': 'All Accounts',
        'count': p.count,
        'page_obj': p.get_page(page),
        'current_page': page,
        'users': p.page(page),
    }
    if page == 1:
        all_users = User.objects.filter(is_active=True)
        active_today = User.objects.filter(is_active=True, profile__last_seen__gte=timezone.now()-datetime.timedelta(days=1)).count()
        active_this_week = User.objects.filter(is_active=True, profile__last_seen__gte=timezone.now()-datetime.timedelta(days=7)).count()
        active_this_month = User.objects.filter(is_active=True, profile__last_seen__gte=timezone.now()-datetime.timedelta(days=30)).count()
        active_this_year = User.objects.filter(is_active=True, profile__last_seen__gte=timezone.now()-datetime.timedelta(days=365)).count()
        new_today = User.objects.filter(is_active=True, date_joined__gte=timezone.now() - datetime.timedelta(hours=24)).count()
        new_this_month = User.objects.filter(is_active=True, date_joined__gte=timezone.now() - datetime.timedelta(hours=24*30)).count()
        subscribers = User.objects.filter(is_active=True, profile__subscribed=True).count()
        verified_users = User.objects.filter(is_active=True, profile__email_verified=True)
        verified_user_count = 0
        for user in verified_users:
            verified_user_count = verified_user_count + (1 if user.verifications.count() > 0 else 0)
        context.update({
            'all_users': all_users,
            'new_today': new_today,
            'new_this_month': new_this_month,
            'subscribers': subscribers,
            'active_today': active_today,
            'active_this_week': active_this_week,
            'active_this_month': active_this_month,
            'active_this_year': active_this_year,
            'verified_users': verified_users.count(),
            'verified_user_count': verified_user_count,
        } if page == 1 else {})
    return render(request, 'users/users.html', context)

def logout_visitor(request):
    from django.contrib import messages
    from django.shortcuts import render
    from django.conf import settings
    if request.GET.get('message', None):
        messages.success(request, request.GET.get('message'))
    from django.contrib.auth import logout
    if request.user.is_authenticated:
        from security.build import async_build_session
        async_build_session(request.user.id, request.session.session_key)
    logout(request)
    return render(request, 'users/logout.html', {'small': True, 'title': 'You have been logged out of {}'.format(settings.SITE_NAME)})

def passwordless_login(request):
    from .forms import PhoneNumberForm
    from django.shortcuts import render, redirect, get_object_or_404
    if request.method == 'POST':
        form = PhoneNumberForm(request.POST)
        phone_number = form.data['phone_number'].replace('-', '').replace('(','').replace(')','')
        user = User.objects.filter(profile__phone_number=phone_number).order_by('-profile__last_seen').first()
        if user and user.is_active:
            from users.tfa import send_user_text
            from django.contrib import messages
            from django.conf import settings
            send_user_text(user, 'Use the following link to log into your account: {}'.format(settings.BASE_URL) + user.profile.create_face_url() + ' - The link will expire in 3 minutes.')
            messages.success(request, 'A one time login link has been sent to your phone number, ' + phone_number + '.')
            from django.urls import reverse
            return redirect(reverse('landing:landing'))
        else: messages.warning(request, 'This account is not active or login has been disabled.')
    form = PhoneNumberForm(initial={'phone_number': '+1'})
    return render(request, 'users/send_auth_text.html', {'title': 'Authenticate with a text', 'form': form, 'small': True})


def tfa(request, username, usertoken):
    from django.conf import settings
    from .forms import PhoneNumberForm
    from django.shortcuts import render, redirect, get_object_or_404
    from django.urls import reverse
    from django.http import HttpResponseRedirect
    from .models import MFAToken
    from .forms import TfaForm
    from django.contrib.auth.models import User
    from django.utils import timezone
    from django.contrib import messages
    import datetime
    from django.core.exceptions import PermissionDenied
    token = MFAToken.objects.filter(uid=username, expires__gt=timezone.now() + datetime.timedelta(seconds=30)).order_by('-timestamp').last()
    if not token: token = MFAToken.objects.create(user=User.objects.filter(profile__uuid=username).first(), uid=username, expires=timezone.now() + datetime.timedelta(seconds=115))
    user = User.objects.filter(id=token.user.id).first()
    if not user and request.user.is_authenticated: return redirect(reverse('feed:home'))
    if not user: raise PermissionDenied()
    from django.contrib.auth import login as auth_login
    next = request.GET.get('next','')
    if not user.profile.enable_two_factor_authentication and user.is_active and user.profile.check_auth_token(usertoken):
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        user.profile.tfa_expires = timezone.now() + datetime.timedelta(minutes=settings.LOGIN_VALID_MINUTES)
        user.profile.save()
        return HttpResponseRedirect(next if next != '' else reverse('landing:landing'))
    if not user.profile.tfa_enabled:
        from .tfa import check_verification_time
        if not check_verification_time(user, token):
            user.profile.tfa_enabled = False
            user.profile.enable_two_factor_authentication = True
            user.profile.phone_number = '+1'
            user.profile.save()
            print('Logging in user')
            resolve_multiple_accounts(request, user)
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.warning(request, 'Please enter a valid phone number and verify it with a code.')
            return redirect(reverse('users:tfa_onboarding'))
    from security.security import fraud_detect
    if request.method == 'POST' and not fraud_detect(request, True):
        form = TfaForm(request.POST)
        code = str(form.data.get('code', None))
        if code and code != '' and code != None:
            token_validated = user.profile.check_auth_token(usertoken)
            p = user.profile
            is_verified = False
#            try:
            from .tfa import check_verification_code
            is_verified = check_verification_code(user, token, code)
            print('Is verified?')
#            except:
#                is_verified = False
            p.tfa_authenticated = is_verified
            if token_validated:
                if is_verified:
                    user.profile.tfa_enabled = True
                    user.profile.language_code = request.LANGUAGE_CODE
                    user.profile.save()
                    resolve_multiple_accounts(request, user)
                    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    face = user.faces.filter(session_key=None).last()
                    if face:
                        face.session_key = request.session.session_key
                        face.save()
                    p.tfa_expires = timezone.now() + datetime.timedelta(minutes=settings.LOGIN_VALID_MINUTES)
                    p.save()
                    messages.success(request, 'You have been authenticated. Welcome.')
                    qs = '?'
                    for key, value in request.GET.items():
                        qs = qs + key + '=' + value + '&'
                    red_path = '/' if not request.user.profile.vendor else reverse('go:go')
                    if next != '' and not (next.startswith('/accounts/logout/') or next.startswith('/accounts/login/') or next.startswith('/admin/login/') or next.startswith('/accounts/register/')):
                        return HttpResponseRedirect(next)
                    elif next.startswith('/accounts/logout/') or next.startswith('/accounts/login/') or next.startswith('/accounts/register/'):
                        return redirect(red_path)
                    elif request.META.get('HTTP_REFERER', '/').startswith('/accounts/login/'):
                        return redirect(red_path)
                    elif not next:
                        return redirect(red_path)
                    else:
                        return HttpResponseRedirect(reverse('verify:age') + '?next=' + request.META.get('HTTP_REFERER', red_path))
                else:
                    messages.warning(request, 'The code you entered was not recognized. Please try again.')
            elif not token_validated:
                messages.warning(request, 'The URL token has expired or was not recognized. Please try again.')
                from django.contrib.auth import logout
                logout(request)
                return redirect(reverse('users:login'))
            if p.tfa_attempts > 3:
                messages.warning(request, 'You have entered the incorrect code more than 3 times. please send yourself a new code.')
                p.verification_code = None
                p.save()
        elif user.profile.can_send_tfa < timezone.now():
            user.profile.tfa_attempts = 0
            user.profile.can_send_tfa = timezone.now() + datetime.timedelta(minutes=2)
            user.profile.save()
            from .mfa import send_verification_text, check_verification_code, send_user_text, send_text
            from .mfa import send_verification_email as send_tfa_verification_email
            if form.data.get('send_email', False):
                send_tfa_verification_email(user, token)
            else:
                send_verification_text(user, token)
            messages.success(request, "Please enter the code sent to your phone number or email. The code will expire in 3 minutes.")
        elif user.profile.can_send_tfa < timezone.now() + datetime.timedelta(seconds=115):
            messages.warning(request, 'You are sending too many two factor authentication codes. Wait a few minutes before sending another code.')
    form = TfaForm()
    hide_logo = None
    if user.profile.hide_logo:
        hide_logo = True
    if request.user.is_authenticated: return redirect(reverse('/'))
    return render(request, 'users/tfa.html', {'title': 'Enter Code', 'form': form, 'xsmall': True, 'user': user, 'hide_logo': hide_logo, 'accl_logout': user.profile.shake_to_logout, 'preload': False, 'autofocus': request.method == 'POST'})

@login_required
def tfa_onboarding(request):
    from .forms import PhoneNumberForm
    from django.shortcuts import redirect
    from django.contrib import messages
    if request.method == 'POST':
        form = PhoneNumberForm(request.POST)
        request.user.profile.phone_number = form.data['phone_number'].replace('-', '').replace('(','').replace(')','')
        request.user.profile.tfa_enabled = True
        request.user.profile.enable_two_factor_authentication = True
        request.user.profile.save()
        messages.success(request, 'You have added a phone number to your account.')
        user = request.user
        return redirect(user.profile.create_auth_url())
    form = PhoneNumberForm(initial={'phone_number': request.user.profile.phone_number if request.user.profile.phone_number else '+1'})
    from django.shortcuts import render
    return render(request, 'users/tfa_onboarding.html', {'title': 'Enter your phone number', 'form': form, 'small': True})

@never_cache
@login_required
def profile(request):
    oldusername = request.user.username
    p_form = None
    from .forms import UserUpdateForm, ProfileUpdateForm, NonVendorProfileUpdateForm
    from .models import Profile
    from django.contrib import messages
    from django.http import HttpResponse
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if request.user.profile.vendor:
            p_form = ProfileUpdateForm(request.POST,
                                       request.FILES,
                                       instance=request.user.profile, user=request.user)
        else:
            p_form = NonVendorProfileUpdateForm(request.POST,
                                       request.FILES,
                                       instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            d = Profile.objects.filter(user=request.user).values().first()
            d.update({'user': None, 'id': None, 'user_id': None})
            oldprofile = Profile(**d)
            newusername = p_form.data['name']
            uc = False
            if newusername != oldprofile.name:
                uc = check_username(newusername)
            if not uc and newusername != oldprofile.name:
                user = request.user
                user.profile.name = oldusername
                user.profile.save()
                messages.warning(request, f'Your username has not been accepted. Please select a more appropriate username.')
            elif not newusername: p_form.data['name'] = request.user.username
            new_phone_number = p_form.data['phone_number']
            u_form.save()
            new_mail_pass = None
            if p_form.cleaned_data.get('email_password'):
                new_mail_pass = p_form.cleaned_data.get('email_password')
            counter = 0
            for email in request.user.email_addresses.order_by('created_at'):
                email.email = p_form.cleaned_data.get('profile_email{}'.format(counter))
                email.save()
                counter+=1
            from users.models import EmailAddress
            if p_form.cleaned_data.get('profile_email{}'.format(counter)):
                EmailAddress.objects.create(user=request.user, email=p_form.cleaned_data.get('profile_email{}'.format(counter)))
            EmailAddress.objects.filter(user=request.user, email='').delete()
            profile = p_form.save(commit=False)
            profile.phone_number = profile.phone_number.replace('-', '').replace('(','').replace(')','')
            profile.save()
            if new_mail_pass:
                profile.set_mail_password(new_mail_pass)
            if oldprofile.image != profile.image:
                from feed.align import face_rotation
                try:
                    rot = face_rotation(profile.image.path)
                    if rot == -1:
                        profile.rotate_right()
                    elif rot == 1:
                        profile.rotate_left()
                    profile.rotate_align()
                except: print("Failed to rotate profile photo")
            if new_phone_number != oldprofile.phone_number and oldprofile.phone_number and len(oldprofile.phone_number) >= 11:
                profile.tfa_enabled = True
                profile.save()
                send_text(oldprofile.phone_number, 'Your phone number has been updated to ' + new_phone_number + '. Please refer to texts on that phone to log in. If you didnt make this change, please call us. - {}'.format(settings.SITE_NAME))
            if profile.enable_two_factor_authentication and profile.phone_number and len(profile.phone_number) < 11:
                profile.enable_two_factor_authentication = False
                messages.success(request, f'Two factor authentication can\'t be activated without entering a phone number. Please enter a phone number to enable two factor authentication.')
            profile.save()
            if new_phone_number != oldprofile.phone_number and new_phone_number and len(new_phone_number) >= 11:
                send_user_text(request.user, 'You have added this number to {} for two factor authentication. You can now use your number for two factor authentication. If you didnt make this change, please call us. - {}'.format(settings.SITE_NAME, settings.DOMAIN))
                profile.tfa_enabled = True
                profile.tfa_code_expires = timezone.now() + datetime.timedelta(minutes=3)
                profile.save()
                return redirect(profile.create_auth_url())
            messages.success(request, f'Your profile has been updated!')
            print('Profile updated')
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(reverse('users:profile'))
    else:
        u_form = UserUpdateForm(instance=request.user)
        if request.user.profile.vendor:
            initial = {'email_password': '', 'phone_number': request.user.profile.phone_number if request.user.profile.phone_number else '+1'}
            count = 0
            for email in request.user.email_addresses.order_by('created_at'):
                initial.update({'profile_email{}'.format(count): email.email})
                count+=1
            p_form = ProfileUpdateForm(instance=request.user.profile, initial=initial, user=request.user)
        else:
            p_form = NonVendorProfileUpdateForm(instance=request.user.profile, initial={'phone_number': request.user.profile.phone_number if request.user.profile.phone_number else '+1'})
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'title':'Update Your Profile',
        'medium': True,
        'webpush': {},
        'headjs': True,
    }
    from django.shortcuts import render
    return render(request, 'users/profile.html', context)


def check_username(username):
    from better_profanity import profanity
    return not profanity.contains_profanity(username)

def check_username_old(username):
    from django.conf import settings
    import requests, json
    lang = 'en'
    data = {
        'text': username,
        'mode': 'standard',
        'lang': lang,
        'api_user': settings.SIGHTENGINE_USER,
        'api_secret': settings.SIGHTENGINE_SECRET
    }
    r = requests.post('https://api.sightengine.com/1.0/text/check.json', data=data)
    output = json.loads(r.text)
    try:
        if output['profanity']['matches'] or output['link']['matches']:
            return False
    except: return False
    return True

def set_user_cookie(response):
    import datetime
    max_age = 60 * 60 * 24 * 365
    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
        "%a, %d-%b-%Y %H:%M:%S GMT",
    )
    response.set_cookie('user_signup', True, max_age=max_age, expires=expires)
    return response


def send_registration_push(user):
    from webpush import send_user_notification
    from django.conf import settings
    from django.urls import reverse
    from django.contrib.auth.models import User
    payload = {
        'head': 'Someone new signed up with {}'.format(settings.SITE_NAME),
        'body': 'Meet the new visitor, @{}, on {}'.format(user.username, settings.SITE_NAME),
        'icon': settings.BASE_URL + settings.ICON_URL,
        'url': settings.BASE_URL + reverse('users:all'),
    }
    try:
        send_user_notification(User.objects.get(id=settings.MY_ID), payload=payload)
    except: pass

#@cache_control(public=True)
@never_cache
def register(request):
    from security.apis import get_client_ip
    from django.contrib.auth.models import User
    from security.apis import check_raw_ip_risk
    from users.models import Profile
    from security.models import SecurityProfile
    from .email import send_verification_email
    from django.contrib import messages
    from users.username_generator import generate_username as get_random_username
    from security.apis import get_client_ip
    from email_validator import validate_email
    from .forms import UserRegisterForm
    from django.utils import timezone
    import datetime
    from django.shortcuts import render, redirect, get_object_or_404
    from django.urls import reverse
    from security.security import fraud_detect
    import traceback
    from django.conf import settings
    ip = get_client_ip(request)
    e = request.GET.get('u', None)
    user = None
    if e:
        try:
            valid = validate_email(e, check_deliverability=True)
            us = User.objects.filter(email=e).last()
            safe = not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True)
            if valid and not us and safe:
                from django.utils.crypto import get_random_string
                user = User.objects.create_user(email=e, username=get_random_username(e), password=get_random_string(length=8))
                if not hasattr(user, 'profile'):
                    profile = Profile.objects.get_or_createcreate(user=user)
                    profile.finished_signup = False
                    profile.save()
                    security_profile, created = SecurityProfile.objects.get_or_create(user=user)
                    security_profile.save()
                messages.success(request, 'You are now subscribed, check your email for a confirmation. When you get the chance, fill out the form below to make an account.')
                send_verification_email(user)
                send_registration_push(user)
            elif us.profile.finished_signup and safe:
                user = us
                messages.warning(request, 'You already have an account with us. Please log in below.')
                response = redirect(reverse('users:login'))
                set_user_cookie(response)
                return response
            elif not valid: messages.warning(request, 'The email you entered is not valid or not deliverable.')
            else: messages.warning(request, 'You are using a risky IP address. Please do not continue.')
            user = us
        except: print(traceback.format_exc())
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        # user rate limit
        can_register = User.objects.filter(date_joined__date=datetime.date.today()).count() < settings.NEW_USERS_PER_DAY
        if can_register and form.is_valid() and not check_raw_ip_risk(ip, soft=True, dummy=False, guard=True):
            user = User.objects.filter(username=form.cleaned_data.get('username'), email=form.cleaned_data.get('email')).first()
            if not user:
                user = User.objects.filter(email=form.cleaned_data.get('email')).first()
            birthday = None
            try:
                birthday = datetime.datetime.strptime(form.data.get('birthday', ''), '%Y-%m-%d')
            except:
                birthday = datetime.datetime.strptime(form.data.get('birthday', ''), '%m/%d/%Y')
            if not birthday:
                messages.warning(request, 'Your birthday was not interpreted properly. Please enter in the format Year-Month-Day')
                return redirect(reverse('users:register'))
            from verify.forms import get_past_date
            if birthday > get_past_date(age=settings.MIN_AGE):
                messages.warning(request, 'You are not old enough to use this site. Please do not return until {}'.format((birthday + relativedelta(years=settings.MIN_AGE)).strftime("%B %d, %Y")))
                return redirect(reverse('app:app'))
            if User.objects.filter(username=form.cleaned_data.get('username'), profile__finished_signup=True).count() > 0 or User.objects.filter(email=form.cleaned_data.get('email'), profile__finished_signup=True).count() > 0:
                messages.warning(request, 'You are already registered. Please log in.')
                return redirect(reverse('users:login'))
            sendemail = False
            if not User.objects.filter(email=form.cleaned_data.get('email'), profile__finished_signup=True).first(): sendemail = True
            u = user
            if not u:
                u = User.objects.create_user(username=form.cleaned_data.get('username'), email=form.cleaned_data.get('email'))
            u.set_password(form.clean_password2())
            uc = check_username(u.username)
            if not uc:
                messages.warning(request, f'Your username has not been accepted. Please select a more appropriate username.')
                u.delete()
                return redirect(reverse('misc:terms'))
            profile = u.profile
            profile.finished_signup = True
            profile.save()
            u.username = form.cleaned_data.get('username')
            u.save()
            if sendemail:
                send_verification_email(u)
                send_registration_push(u)

            messages.success(request, f'Your account has been created! Please check your email and verify your account.')
            response = redirect(reverse('verify:verify'))
            set_user_cookie(response)
            return response
        else:
            if not can_register:
                messages.warning(request, 'We have reached the limit of new accounts for the day. Please try to register again tomorrow.')
    else:
        arg = request.GET.get('u','')
        email = ''
        if not arg == '':
            email = arg
        if not email == '' and User.objects.filter(email=arg, profile__finished_signup=True).exists():
            messages.warning(request, f'You already have an account. Please log in instead.')
            return redirect(reverse('users:login'))
        elif email != '':
            messages.success(request, f'Please enter a username (can be your name) and a password, as well as check the box.')
        if user:
            form = UserRegisterForm(initial={'email': email})
        else:
            form = UserRegisterForm(initial={'email': email})
    import pytz
    available = settings.NEW_USERS_PER_DAY - User.objects.filter(date_joined__gte=datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1), datetime.time(9,0)).astimezone(pytz.timezone(settings.TIME_ZONE))).count()
    from django.shortcuts import render
    response = render(request, 'users/register.html', {'form': form, 'title':'Register', 'dontshowad': True, 'dontshowsidebar': True, 'small': True, 'available_accounts': available, 'email_query_delay': 90})
    if user:
        response = set_user_cookie(response)
    return response

#@cache_control(public=True)
@never_cache
def login(request):
    from django.conf import settings
    from security.apis import get_client_ip
    from django.contrib.auth.models import User
    from security.apis import check_raw_ip_risk, check_ip_risk
    from users.models import Profile
    from security.models import SecurityProfile, UserIpAddress
    from django.contrib import messages
    from users.username_generator import generate_username as get_random_username
    from security.apis import get_client_ip
    from email_validator import validate_email
    from django.contrib.auth.forms import AuthenticationForm
    import datetime
    from django.shortcuts import render, redirect, get_object_or_404
    from django.urls import reverse
    from django.utils import timezone
    from security.security import fraud_detect
    from django.contrib.auth import login as auth_login
    from security.models import UserLogin
    ip = get_client_ip(request)
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        print(username)
        the_user = None
        try:
            the_user = User.objects.get(username=username)
        except:
            the_user = None
        user = None
        disable_login = False
        if the_user:
            if not hasattr(the_user, 'security_profile'):
                SecurityProfile.objects.create(user=the_user)
            if not hasattr(the_user, 'profile'):
                Profile.objects.create(user=the_user)
        if hasattr(the_user, 'profile') and the_user.user_logins.filter(timestamp__lte=timezone.now(), timestamp__gte=timezone.now() - datetime.timedelta(seconds=15)).count() <= 20 and not disable_login:
            from django.contrib.auth import authenticate, logout
            user = authenticate(username=username,password=password)
            UserLogin.objects.create(user=user)
            print('User is')
            print(user)
            if not user and the_user:
                the_user.profile.save()
            else: print('successful login for user {}'.format(username))
        else: print('login rate limited for {}'.format(username))
        if user and hasattr(user, 'profile'):
            if user.is_active and user.profile.email_verified and user.user_logins.filter(timestamp__lte=timezone.now(), timestamp__gte=timezone.now() - datetime.timedelta(seconds=15)).count() <= 2:
                user.profile.can_login = timezone.now() - datetime.timedelta(seconds=15)
                user.profile.save()
                messages.success(request, f'Welcome back to ' + settings.SITE_NAME + ', ' + user.profile.preferred_name + '.' + (' Please complete authentication.' if user.profile.enable_two_factor_authentication else ''))
                profile = user.profile
                profile.verification_code = None
                if not (profile.tfa_enabled and profile.enable_two_factor_authentication): profile.language_code = request.LANGUAGE_CODE
                profile.save()
                next = request.GET.get('next', '')
                extra = ''
                qs = '?'
                for key, value in request.GET.items():
                    qs = qs + key + '=' + value + '&'
                if not profile.enable_facial_recognition_bypass:
                    response = redirect(user.profile.create_face_url() + qs)
                elif not user.profile.enable_two_factor_authentication:
                    from users.logout import logout_user
                    if settings.LIMIT_BYPASS_LOGIN: logout_user(user)
                    resolve_multiple_accounts(request, user)
                    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    response = redirect(reverse('app:app'))
                else:
                    response = redirect(user.profile.create_auth_url() + qs)
                response = set_user_cookie(response)
                return response
            elif not the_user.profile.email_verified:
                messages.warning(request, f'You tried to log in to your account, but have not yet verified your email. Please follow the link in your email to log in to your account, or request a new link by clicking the button below and entering your email. <a href="' + reverse('users:resend_activation') + '" title="Resend activation email">Resend Activation Email</a>')
                return redirect(reverse('users:verify'))
            else:
                messages.warning(request, 'You are trying to log in too much. Please wait another few seconds before logging in.')
                return redirect(reverse('users:login'))
        else:
            messages.warning(request, 'Your username or password is not correct, or you are trying to log in too much. Please wait another few seconds before logging in.')
            return redirect(reverse('users:login'))
    else:
        form = AuthenticationForm()
    title = 'Login'
    if request.GET.get('next', None):
        title = 'Log in to visit ' + request.GET.get('next', '')
    return render(request,'users/login.html', {'form':form, 'title': title, 'dontshowad': True, 'dontshowsidebar': True, 'small': True, 'email_query_delay': 15})

def activate(request, uidb64, token):
    from django.urls import reverse
    from django.contrib import messages
    from django.contrib.auth.models import User
    from security.apis import get_client_ip
    from security.apis import check_raw_ip_risk
    from .email import sendwelcomeemail
    from django.shortcuts import redirect
    from django.conf import settings
    from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
    from .tokens import account_activation_token
    from django.utils.encoding import force_str
    from users.models import Profile
    from security.models import SecurityProfile
    from barcode.tests import pediatric_document_scanned
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    ip = get_client_ip(request)
    if user.profile.email_verified and not pediatric_document_scanned(user):
        messages.success(request, 'You have already verified your email. Please continue to take a photo of your face and scan your ID.')
        return redirect(reverse('users:login') + '?next=' + reverse('barcode:scan'))
    elif user.profile.email_verified:
        messages.success(request, 'You have already verified your email. Please continue to login.')
        return redirect(reverse('users:login'))
    elif user is not None and account_activation_token.check_token(user, token) and not check_raw_ip_risk(ip):
        if not user.profile.email_verified:
            from .tfa import send_user_text
            send_user_text(User.objects.get(id=settings.MY_ID), 'Someone new has joined {}.'.format(settings.SITE_NAME))
        user.profile.email_verified = True
        user.profile.finished_signup = True
        user.profile.save()
        user.save()
        sendwelcomeemail(request, user)
        messages.success(request, f'Thanks for confirming your email! You can now log into your account, and a welcome email has been sent to you.')
        return redirect(user.profile.create_face_url() + '?next=' + reverse('barcode:scan'))
    else:
        messages.success(request, f'Your activation link has expired. Please request a new activation link.')
        return redirect(reverse('users:verify'))

def resend_activation(request):
    from .forms import ResendActivationEmailForm
    if request.method == 'POST':
        form = ResendActivationEmailForm(request.POST)
        email = request.POST['email']
        from django.contrib import messages
        from django.urls import reverse
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(email=email)
            from .email import send_verification_email
            send_verification_email(user)
            messages.success(request,'Your verification email sent. Please click the link in your email to verify your account.')
            return redirect(reverse('verify:verify'))
        except:
            messages.warning(request,f'Your email is not correct. Please try again.')
    else:
        form = ResendActivationEmailForm()
    from django.shortcuts import render
    return render(request,'users/resend_activation.html',{'form': form, 'title': 'Resend Activation', 'small': True})

#@cache_page(60*60*24*30*12)
def verify(request):
    from django.shortcuts import render
    return render(request, 'users/verify.html',{'title': 'Verify your email', 'small': True})

def unsubscribe(request, username, token):
    from django.urls import reverse
    from django.contrib import messages
    from django.shortcuts import get_object_or_404
    from django.contrib.auth.models import User
    user = User.objects.filter(username=username).first()
    if not user: user = get_object_or_404(User, profile_uuid=username)
    if request.method == 'POST' and ((request.user.is_authenticated and request.user == user) or user.profile.check_token(token)):
        profile = user.profile
        profile.subscribed = not profile.subscribed
        profile.save()
        messages.success(request, 'You have been {}'.format('resubscribed.' if profile.subscribed else 'unsubscribed.'))
        from django.shortcuts import redirect
        return redirect(reverse('app:app'))
    if request.method == 'GET' and ((request.user.is_authenticated and request.user == user) or user.profile.check_token(token)):
        # unsubscribe them
        profile = user.profile
        profile.subscribed = False
        profile.save()
        from django.shortcuts import render
        return render(request, 'users/unsubscribe.html', {'title': 'Unsubscribe', 'link': user.profile.create_unsubscribe_link()})
    # Otherwise redirect to login page
    from django.http import HttpResponseRedirect
    messages.warning(request,f'Your unsubscribe link has expired. Please log in to unsubscribe.')
    next_url = reverse('users:unsubscribe', kwargs={'username': username, 'token': token,})
    return HttpResponseRedirect('%s?next=%s' % (reverse('login'), next_url))


from django.contrib.auth.models import User

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    success_url = '/'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def test_func(self):
        user = self.get_object()
        if self.request.user != user and self.request.user.is_superuser:
            return True
        return False
```


--- File: lotteharper-main/users/welcome_email.html ---
```html
<h3>Welcome to {{ site_name }}</h3>
<p>Hello {{ username }},</p>
<p>We are happy to see you here! Thank you for joining {{ site_name }} and being a part of the fun. To get started, here are a few things you can do after you verify your identity.</p>
<ol>
    <li><a href="{{ base_url }}/" title="Use the app">Use the app</a>. This is the main page of {{ site_name }}</li>
    <li><a href="{{ base_url }}/feed/profile/{{ model_name }}/" title="See my profile">Visit my private {{ site_name }} profile</a>. This is a page for anyone wanting to get to know me.</li>
    <li><a href="{{ base_url }}/feed/profiles/" title="See all profiles currently on the site">More profiles</a>. You can find these people on the site, and see their content.</li>
    <li><a href="{{ base_url }}/feed/all/" title="See everything on {{ site_name }}">See all posts here</a>. This is the private front page of {{ site_name }}.</li>
</ol>
<p>There is even more on the site, so feel free to visit and see what you find. You can share the site with any of the social buttons on each page. I hope you enjoy your time with {{ site_name }}! Thanks for being here.</p>
<p>With much love,</p>
<p>{{ model_name }}</p>
<a href="{{ base_url }}" title="{{ site_name }}">{{ base_url }}</a>
```


--- File: lotteharper-main/vendors/admin.py ---
```python
from django.contrib import admin
from .models import VendorProfile
from simple_history.admin import SimpleHistoryAdmin
# Register your models here.
admin.site.register(VendorProfile, SimpleHistoryAdmin)
```


--- File: lotteharper-main/vendors/apps.py ---
```python
from django.apps import AppConfig


class VendorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendors'
```


--- File: lotteharper-main/vendors/forms.py ---
```python
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from .models import VendorProfile
from crypto.currencies import CRYPTO_CURRENCIES
import math


class SendBitcoinForm(forms.Form):
    amount = forms.FloatField()
    bitcoin_address = forms.CharField(min_length=27, max_length=34)

def sub_fee(fee):
    op = ''
    of = len(str(fee))%3
    op = op + str(fee)[0:of] + (',' if of > 0 else '')
    for f in range(math.floor(len(str(fee))/3)):
        op = op + str(fee)[3*f+of:3+3*f+of] + ','
    op = op[:-1]
    return op

def get_pricing():
    from lotteh.pricing import get_pricing_options
    choices = []
    for option in get_pricing_options(settings.PRICE_CHOICES):
        choices = choices + [[option, '${} / month'.format(sub_fee(option))]]
    return choices

class VendorProfileUpdateForm(forms.ModelForm):
    PRONOUNS_CHOICES = (
        ('Her', 'She/her/hers'),
        ('Him', 'He/him/his'),
        ('They', 'They/them/theirs'),
        ('Me', 'Just use "me"'),
    )
    pronouns = forms.CharField(widget=forms.Select(choices=PRONOUNS_CHOICES))
    SUBSCRIPTION_CHOICES = (
        ('5', '$5 / month'),
        ('10', '$10 / month'),
        ('15', '$15 / month'),
        ('20', '$20 / month'),
        ('25', '$25 / month'),
        ('50', '$50 / month'),
        ('100', '$100 / month'),
        ('200', '$200 / month'),
        ('500', '$500 / month'),
        ('1000', '$1,000 / month'),
        ('2000', '$2,000 / month'),
    )
    PHOTO_CHOICES = (
        ('5', '$5'),
        ('10', '$10'),
        ('20', '$20'),
        ('25', '$25'),
        ('50', '$50'),
        ('100', '$100'),
    )
    TRIAL_CHOICES = (
        ('0', 'None'),
        ('1', 'One Day'),
        ('2', 'Two Days'),
        ('3', 'Three days'),
        ('7', 'One Week'),
        ('14', 'Two Weeks'),
        ('30', 'One Month'),
        ('60', '60 Days'),
        ('90', '90 Days'),
    )
    CHOICES = list()
    for choice in CRYPTO_CURRENCIES:
        CHOICES.append((choice, choice))
    sync_podcasts = forms.BooleanField(initial=False, required=False)
    subscription_fee = forms.CharField(widget=forms.Select(choices=get_pricing()))
    payout_currency = forms.CharField(widget=forms.Select(choices=CHOICES))
    photo_tip = forms.CharField(widget=forms.Select(choices=PHOTO_CHOICES))
    free_trial = forms.CharField(widget=forms.Select(choices=TRIAL_CHOICES))
    payout_address = forms.CharField(max_length=300)
    logo_alpha = forms.FloatField(min_value=0.1, max_value=1)
    pitch_adjust = forms.IntegerField(required=False)
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(VendorProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['logo'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        self.fields['video_intro_font'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        from translate.translate import translate
        from feed.middleware import get_current_request
        r = get_current_request()
        self.fields['sync_podcasts'].label = translate(r, 'Sync podcasts with host?', src='en')
        self.fields['logo'].label = translate(r, 'Your square logo', src='en')
        self.fields['video_intro_font'].label = translate(r, 'A font for your video intro', src='en')
        self.fields['video_intro_text'].label = translate(r, 'Text for your video intro', src='en')
        self.fields['video_intro_color'].label = translate(r, 'A color for the intro text', src='en')
        self.fields['hide_profile'].label = translate(r, 'Hide your profile?', src='en')
        self.fields['activate_surrogacy'].label = translate(r, 'Activate contracts for GC/GS? (women only)', src='en')
        self.fields['pronouns'].label = translate(r, 'Please select your pronouns', src='en')
        self.fields['address'].label = translate(r, 'Enter your address', src='en')
        self.fields['insurance_provider'].label = translate(r, 'Your insurance provider', src='en')
        self.fields['video_link'].label = translate(r, 'A link to your video', src='en')
        self.fields['content_link'].label = translate(r, 'A link to your content', src='en')
        self.fields['video_embed'].label = translate(r, 'Your video for embedding', src='en')
        self.fields['playlist_embed'].label = translate(r, 'Your playlist for embedding', src='en')
        self.fields['pitch_adjust'].label = translate(r, 'Your pitch adjustment', src='en')
        self.fields['subscription_fee'].label = translate(r, 'Your subscription fee', src='en')
        self.fields['free_trial'].label = translate(r, 'Free trial options', src='en')
        self.fields['photo_tip'].label = translate(r, 'Default pricing', src='en')
        self.fields['logo_alpha'] = forms.FloatField(
            min_value=0.1,
            max_value=1,
            error_messages={
                'min_value': translate(r, 'Alpha cannot be less than 0.1', src='en'),
                'max_value': translate(r, 'Alpha cannot be greater than 1', src='en')
            })
        self.fields['logo_alpha'].label = translate(r, 'Video intro & logo alpha (0.1-1)', src='en')
        self.fields['payout_currency'].label = translate(r, 'Payout currency', src='en')
        self.fields['payout_address'].label = translate(r, 'Payout address', src='en')
        self.fields['bitcoin_address'].label = translate(r, 'Bitcoin (BTC) address', src='en')
        self.fields['ethereum_address'].label = translate(r, 'Ethereum (ETH) address', src='en')
        self.fields['usdcoin_address'].label = translate(r, 'USDCoin (USDC) address', src='en')
        self.fields['solana_address'].label = translate(r, 'Solana (SOL) address', src='en')
        self.fields['trump_address'].label = translate(r, 'Trump (TRUMP) address', src='en')
        self.fields['polygon_address'].label = translate(r, 'Polygon (POL) address', src='en')
        self.fields['avalanche_address'].label = translate(r, 'Avalanche (AVAX) address', src='en')
        self.fields['bitcoin_cash_address'].label = translate(r, 'Bitcoin Cash (BCH) address', src='en')
        self.fields['litecoin_address'].label = translate(r, 'Litcoin (LTC) address', src='en')
        self.fields['usdtether_address'].label = translate(r, 'USDTether (USDT) address', src='en')
        self.fields['dogecoin_address'].label = translate(r, 'DogeCoin (DOGE) address', src='en')
        self.fields['transistorfm_key'].label = translate(r, 'Transistor.fm API Key (for podcast upload)', src='en')
        self.fields['emergency_contact_1_name'].label = translate(r, 'Emergency contact 1 name', src='en')
        self.fields['emergency_contact_1_phone'].label = translate(r, 'Emergency contact 1 phone number including +1', src='en')
        self.fields['emergency_contact_2_name'].label = translate(r, 'Emergency contact 2 name', src='en')
        self.fields['emergency_contact_2_phone'].label = translate(r, 'Emergency contact 2 phone number including +1', src='en')

        from verify.tests import minor_identity_verified
        if not minor_identity_verified(user): self.fields.pop('activate_surrogacy')

    class Meta:
        model = VendorProfile
        fields = ['logo', 'video_intro_font', 'video_intro_text', 'video_intro_color', 'logo_alpha', 'hide_profile', 'activate_surrogacy', 'pronouns', 'address', 'insurance_provider', 'video_link', 'content_link', 'video_embed', 'playlist_embed', 'transistorfm_key', 'sync_podcasts', 'pitch_adjust', 'subscription_fee', 'free_trial', 'photo_tip', 'payout_currency', 'payout_address', 'bitcoin_address', 'ethereum_address', 'usdcoin_address', 'solana_address', 'trump_address', 'polygon_address', 'avalanche_address', 'bitcoin_cash_address', 'litecoin_address', 'usdtether_address', 'dogecoin_address', 'emergency_contact_1_name', 'emergency_contact_1_phone', 'emergency_contact_2_name', 'emergency_contact_2_phone']
        labels = {
            'usdcoin_address': 'USDCoin address',
            'usdtether_address': 'USD Tether address',
            'bitcoincash_address': 'Bitcoin Cash address',
            'trump_address': 'TRUMP address',
        }
        widgets = {
            'video_intro_color': forms.TextInput(attrs={'type': 'color'}),
        }
```


--- File: lotteharper-main/vendors/__init__.py ---
```python
```


--- File: lotteharper-main/vendors/migrations/0001_initial.py ---
```python
# Generated by Django 4.2.5 on 2023-10-04 16:02

import address.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('address', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_onboarded', models.BooleanField(default=False)),
                ('pronouns', models.CharField(default='They', max_length=50)),
                ('subscription_fee', models.CharField(blank=True, default='50', max_length=50, null=True)),
                ('photo_tip', models.CharField(blank=True, default='5', max_length=10, null=True)),
                ('compress_video', models.BooleanField(default=False)),
                ('payout_currency', models.CharField(blank=True, default='BTC', max_length=10, null=True)),
                ('payout_address', models.CharField(blank=True, default='', max_length=300, null=True)),
                ('pitch_adjust', models.IntegerField(default=0)),
                ('address', address.models.AddressField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='address.address')),
                ('subscriptions', models.ManyToManyField(blank=True, related_name='vendor_subscriptions', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vendor_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0002_vendorprofile_activate_surrogacy.py ---
```python
# Generated by Django 4.2.6 on 2023-11-13 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorprofile',
            name='activate_surrogacy',
            field=models.BooleanField(default=False),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0003_vendorprofile_free_trial.py ---
```python
# Generated by Django 4.2.6 on 2023-12-09 23:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0002_vendorprofile_activate_surrogacy'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorprofile',
            name='free_trial',
            field=models.CharField(blank=True, default='30', max_length=10, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0004_vendorprofile_pornhub_link.py ---
```python
# Generated by Django 5.0.1 on 2024-01-31 05:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0003_vendorprofile_free_trial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorprofile',
            name='pornhub_link',
            field=models.CharField(default='', max_length=500),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0005_vendorprofile_onlyfans_link.py ---
```python
# Generated by Django 5.0.1 on 2024-03-10 20:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0004_vendorprofile_pornhub_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorprofile',
            name='onlyfans_link',
            field=models.CharField(default='', max_length=500),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0006_vendorprofile_insurance_provider.py ---
```python
# Generated by Django 5.0.1 on 2024-03-10 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0005_vendorprofile_onlyfans_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorprofile',
            name='insurance_provider',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0007_historicalvendorprofile.py ---
```python
# Generated by Django 5.0.7 on 2024-08-20 23:06

import address.models
import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0003_auto_20200830_1851'),
        ('vendors', '0006_vendorprofile_insurance_provider'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalVendorProfile',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('is_onboarded', models.BooleanField(default=False)),
                ('pronouns', models.CharField(default='They', max_length=50)),
                ('pornhub_link', models.CharField(default='', max_length=500)),
                ('onlyfans_link', models.CharField(default='', max_length=500)),
                ('subscription_fee', models.CharField(blank=True, default='50', max_length=50, null=True)),
                ('photo_tip', models.CharField(blank=True, default='5', max_length=10, null=True)),
                ('free_trial', models.CharField(blank=True, default='30', max_length=10, null=True)),
                ('compress_video', models.BooleanField(default=False)),
                ('activate_surrogacy', models.BooleanField(default=False)),
                ('payout_currency', models.CharField(blank=True, default='BTC', max_length=10, null=True)),
                ('payout_address', models.CharField(blank=True, default='', max_length=300, null=True)),
                ('pitch_adjust', models.IntegerField(default=0)),
                ('insurance_provider', models.CharField(blank=True, default='', max_length=300, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('address', address.models.AddressField(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='address.address')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical vendor profile',
                'verbose_name_plural': 'historical vendor profiles',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0008_historicalvendorprofile_hide_profile_and_more.py ---
```python
# Generated by Django 5.0.7 on 2024-08-24 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0007_historicalvendorprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='hide_profile',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='hide_profile',
            field=models.BooleanField(default=False),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0009_rename_onlyfans_link_historicalvendorprofile_content_link_and_more.py ---
```python
# Generated by Django 5.1.3 on 2024-11-17 22:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0008_historicalvendorprofile_hide_profile_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='historicalvendorprofile',
            old_name='onlyfans_link',
            new_name='content_link',
        ),
        migrations.RenameField(
            model_name='historicalvendorprofile',
            old_name='pornhub_link',
            new_name='video_link',
        ),
        migrations.RenameField(
            model_name='vendorprofile',
            old_name='onlyfans_link',
            new_name='content_link',
        ),
        migrations.RenameField(
            model_name='vendorprofile',
            old_name='pornhub_link',
            new_name='video_link',
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0010_historicalvendorprofile_imgur_refresh_and_more.py ---
```python
# Generated by Django 5.1.3 on 2024-12-01 04:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0009_rename_onlyfans_link_historicalvendorprofile_content_link_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='imgur_refresh',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='imgur_token',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='imgur_username',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='imgur_refresh',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='imgur_token',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='imgur_username',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0011_historicalvendorprofile_imgur_time_and_more.py ---
```python
# Generated by Django 5.1.3 on 2024-12-01 04:39

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0010_historicalvendorprofile_imgur_refresh_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='imgur_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='imgur_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0012_historicalvendorprofile_bitcoin_address_and_more.py ---
```python
# Generated by Django 5.1.4 on 2025-01-18 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0011_historicalvendorprofile_imgur_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='bitcoin_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='ethereum_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='bitcoin_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='ethereum_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0013_historicalvendorprofile_logo_vendorprofile_logo.py ---
```python
# Generated by Django 5.1.6 on 2025-03-07 02:25

import vendors.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0012_historicalvendorprofile_bitcoin_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='logo',
            field=models.TextField(default='static/lotteh.png', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='logo',
            field=models.ImageField(default='static/lotteh.png', null=True, upload_to=vendors.models.get_logo_path),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0014_historicalvendorprofile_avalanche_address_and_more.py ---
```python
# Generated by Django 5.1.7 on 2025-03-25 01:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0013_historicalvendorprofile_logo_vendorprofile_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='avalanche_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='polygon_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='solana_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='stellarlumens_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='usdcoin_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='avalanche_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='polygon_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='solana_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='stellarlumens_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='usdcoin_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0015_historicalvendorprofile_video_intro_font_and_more.py ---
```python
# Generated by Django 5.1.7 on 2025-04-09 06:39

import vendors.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0014_historicalvendorprofile_avalanche_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='video_intro_font',
            field=models.TextField(default='', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='video_intro_text',
            field=models.CharField(default='Lotte Harper', max_length=50),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='video_intro_font',
            field=models.ImageField(default='', null=True, upload_to=vendors.models.get_font_path),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='video_intro_text',
            field=models.CharField(default='Lotte Harper', max_length=50),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0016_historicalvendorprofile_video_intro_color_and_more.py ---
```python
# Generated by Django 5.1.7 on 2025-04-09 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0015_historicalvendorprofile_video_intro_font_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='video_intro_color',
            field=models.CharField(default='#FFFFFF', max_length=7),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='video_intro_color',
            field=models.CharField(default='#FFFFFF', max_length=7),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0017_alter_historicalvendorprofile_video_intro_font_and_more.py ---
```python
# Generated by Django 5.1.7 on 2025-04-09 10:10

import vendors.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0016_historicalvendorprofile_video_intro_color_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalvendorprofile',
            name='video_intro_font',
            field=models.TextField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='vendorprofile',
            name='video_intro_font',
            field=models.ImageField(blank=True, default='', null=True, upload_to=vendors.models.get_font_path),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0018_alter_vendorprofile_video_intro_font.py ---
```python
# Generated by Django 5.2 on 2025-04-13 09:19

import vendors.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0017_alter_historicalvendorprofile_video_intro_font_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendorprofile',
            name='video_intro_font',
            field=models.FileField(blank=True, default='', null=True, upload_to=vendors.models.get_font_path),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0019_historicalvendorprofile_video_embed_and_more.py ---
```python
# Generated by Django 5.2 on 2025-04-27 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0018_alter_vendorprofile_video_intro_font'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='video_embed',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='video_playlist_embed',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='video_embed',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='video_playlist_embed',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0020_rename_video_playlist_embed_historicalvendorprofile_playlist_embed_and_more.py ---
```python
# Generated by Django 5.2 on 2025-04-27 23:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0019_historicalvendorprofile_video_embed_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='historicalvendorprofile',
            old_name='video_playlist_embed',
            new_name='playlist_embed',
        ),
        migrations.RenameField(
            model_name='vendorprofile',
            old_name='video_playlist_embed',
            new_name='playlist_embed',
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0021_alter_historicalvendorprofile_playlist_embed_and_more.py ---
```python
# Generated by Django 5.2 on 2025-04-27 23:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0020_rename_video_playlist_embed_historicalvendorprofile_playlist_embed_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalvendorprofile',
            name='playlist_embed',
            field=models.CharField(blank=True, default='', max_length=1500, null=True),
        ),
        migrations.AlterField(
            model_name='historicalvendorprofile',
            name='video_embed',
            field=models.CharField(blank=True, default='', max_length=1500, null=True),
        ),
        migrations.AlterField(
            model_name='vendorprofile',
            name='playlist_embed',
            field=models.CharField(blank=True, default='', max_length=1500, null=True),
        ),
        migrations.AlterField(
            model_name='vendorprofile',
            name='video_embed',
            field=models.CharField(blank=True, default='', max_length=1500, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0022_historicalvendorprofile_bitcoin_cash_address_and_more.py ---
```python
# Generated by Django 5.2 on 2025-05-05 01:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0021_alter_historicalvendorprofile_playlist_embed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='bitcoin_cash_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='litecoin_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='tronix_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='trump_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='usdtether_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='bitcoin_cash_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='litecoin_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='tronix_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='trump_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='usdtether_address',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0023_rename_tronix_address_historicalvendorprofile_dogecoin_address_and_more.py ---
```python
# Generated by Django 5.2 on 2025-05-05 02:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0022_historicalvendorprofile_bitcoin_cash_address_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='historicalvendorprofile',
            old_name='tronix_address',
            new_name='dogecoin_address',
        ),
        migrations.RenameField(
            model_name='vendorprofile',
            old_name='tronix_address',
            new_name='dogecoin_address',
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0024_historicalvendorprofile_logo_alpha_and_more.py ---
```python
# Generated by Django 5.2.3 on 2025-06-30 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0023_rename_tronix_address_historicalvendorprofile_dogecoin_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='logo_alpha',
            field=models.FloatField(default=0.8),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='logo_alpha',
            field=models.FloatField(default=0.8),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0025_historicalvendorprofile_transistorfm_key_and_more.py ---
```python
# Generated by Django 5.2.6 on 2025-10-08 00:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0024_historicalvendorprofile_logo_alpha_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='transistorfm_key',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='transistorfm_key',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/0026_historicalvendorprofile_emergency_contact_1_name_and_more.py ---
```python
# Generated by Django 5.2.8 on 2026-03-18 03:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0025_historicalvendorprofile_transistorfm_key_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='emergency_contact_1_name',
            field=models.CharField(blank=True, default='', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='emergency_contact_1_phone',
            field=models.CharField(blank=True, default='', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='emergency_contact_2_name',
            field=models.CharField(blank=True, default='', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='historicalvendorprofile',
            name='emergency_contact_2_phone',
            field=models.CharField(blank=True, default='', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='emergency_contact_1_name',
            field=models.CharField(blank=True, default='', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='emergency_contact_1_phone',
            field=models.CharField(blank=True, default='', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='emergency_contact_2_name',
            field=models.CharField(blank=True, default='', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='emergency_contact_2_phone',
            field=models.CharField(blank=True, default='', max_length=64, null=True),
        ),
    ]
```


--- File: lotteharper-main/vendors/migrations/__init__.py ---
```python
```


--- File: lotteharper-main/vendors/models.py ---
```python
from simple_history.models import HistoricalRecords
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from address.models import AddressField

def get_image_path(instance, filename):
    import uuid, os
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('verification/', filename)

def get_logo_path(instance, filename):
    import uuid, os
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('logo/', filename)

def get_font_path(instance, filename):
    import uuid, os
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('font/', filename)

from django.contrib.auth.models import User
from django.conf import settings

class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='vendor_profile')
    subscriptions = models.ManyToManyField(User, related_name='vendor_subscriptions', blank=True)
    is_onboarded = models.BooleanField(default=False)
    pronouns = models.CharField(max_length=50,default='They')
    video_intro_text = models.CharField(max_length=50,default=settings.SITE_NAME)
    video_intro_color = models.CharField(max_length=7,default='#FFFFFF')
    video_link = models.CharField(max_length=500,default='')
    content_link = models.CharField(max_length=500,default='')
    imgur_token = models.CharField(max_length=100, default='', null=True, blank=True)
    imgur_refresh = models.CharField(max_length=100, default='', null=True, blank=True)
    imgur_username = models.CharField(max_length=100, default='', null=True, blank=True)
    imgur_time = models.DateTimeField(default=timezone.now)
    subscription_fee = models.CharField(max_length=50,default='50', null=True, blank=True)
    photo_tip = models.CharField(max_length=10, default='5', null=True, blank=True)
    free_trial = models.CharField(max_length=10, default=settings.DEFAULT_MODEL_TRIAL_DAYS, null=True, blank=True)
    compress_video = models.BooleanField(default=False)
    activate_surrogacy = models.BooleanField(default=False)
    hide_profile = models.BooleanField(default=False)
    payout_currency = models.CharField(max_length=10, default='BTC', null=True, blank=True)
    payout_address = models.CharField(max_length=300, default='', null=True, blank=True)
    bitcoin_address = models.CharField(max_length=300, default='', null=True, blank=True)
    ethereum_address = models.CharField(max_length=300, default='', null=True, blank=True)
    usdcoin_address = models.CharField(max_length=300, default='', null=True, blank=True)
    solana_address = models.CharField(max_length=300, default='', null=True, blank=True)
    trump_address = models.CharField(max_length=300, default='', null=True, blank=True)
    polygon_address = models.CharField(max_length=300, default='', null=True, blank=True)
    stellarlumens_address = models.CharField(max_length=300, default='', null=True, blank=True)
    avalanche_address = models.CharField(max_length=300, default='', null=True, blank=True)
    bitcoin_cash_address = models.CharField(max_length=300, default='', null=True, blank=True)
    litecoin_address = models.CharField(max_length=300, default='', null=True, blank=True)
#    tronix_address = models.CharField(max_length=300, default='', null=True, blank=True)
    usdtether_address = models.CharField(max_length=300, default='', null=True, blank=True)
    dogecoin_address = models.CharField(max_length=300, default='', null=True, blank=True)
    transistorfm_key = models.CharField(max_length=100, default='', null=True, blank=True)
    pitch_adjust = models.IntegerField(default=0)
    address = AddressField(null=True, blank=True)
    insurance_provider = models.CharField(max_length=300, default='', null=True, blank=True)
    video_embed = models.CharField(max_length=1500, default='', null=True, blank=True)
    playlist_embed = models.CharField(max_length=1500, default='', null=True, blank=True)
    logo = models.ImageField(null=True, default='static/lotteh.png', upload_to=get_logo_path)
    logo_alpha = models.FloatField(default=settings.DEFAULT_CAMERA_ALPHA)
    video_intro_font = models.FileField(null=True, blank=True, default='', upload_to=get_font_path)
    emergency_contact_1_phone = models.CharField(max_length=64, null=True, blank=True, default='')
    emergency_contact_2_phone = models.CharField(max_length=64, null=True, blank=True, default='')
    emergency_contact_1_name = models.CharField(max_length=64, null=True, blank=True, default='')
    emergency_contact_2_name = models.CharField(max_length=64, null=True, blank=True, default='')
    history = HistoricalRecords()

    def __str__(self):
        return self.user.profile.name

    def delete(self):
        print('Cannot delete vendor profile')

    def save(self, *args, **kwargs):
        super(VendorProfile, self).save(*args, **kwargs)
```


--- File: lotteharper-main/vendors/templates/vendors/send_bitcoin.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block content %}
<div id="container rounded bg-white shadow col-md-6 mx-auto">
<h1>Crypto</h1>
<legend>Balances</legend>
<p style="white-space: pre-wrap;">{{ info|jsonprint }}</p>
</div>
{% endblock %}
```


--- File: lotteharper-main/vendors/templates/vendors/vendor_preferences.html ---
```html
{% extends 'base.html' %}
{% block head %}
{% if vendor.vendor_profile.video_intro_font %}
<style>
@font-face { font-family: 'VendorSpecified'; src: url('{{ vendor.vendor_profile.video_intro_font.url }}'); }
</style>
{% endif %}
{% endblock %}
{% load crispy_forms_tags %}
{% load feed_filters %}
{% block javascripts %}
{% autoescape off %}
{{ form.media|removejsig }}
{% endautoescape %}
{% endblock %}
{% block content %}
        <legend class="border-bottom mb-4">{{ 'Vendor Settings'|etrans }}</legend>
        <p><img alt="{{ 'Your saved logo used in videos and email'|etrans }}" src="{{ vendor.vendor_profile.logo.url }}" style="width: 30%; max-width: 150px; height: auto;"> - <b>"{{ vendor.profile.name }}"</b> ({{ vendor.verifications.last.full_name }}) <i>{% if vendor == my_profile.user %} - {{ 'Author'|etrans }}{% endif %}{% if vendor.profile.admin %} - {{ 'Admin'|etrans }}{% endif %}</i></p>
        <h2 style="{% if vendor.vendor_profile.video_intro_font %}font-family: 'VendorSpecified';{% endif %} color: {{ vendor.vendor_profile.video_intro_color }} !important; text-color: {{ vendor.vendor_profile.video_intro_color }} !important;{% if darkmode and vendor.vendor_profile.video_intro_color|blenddark %}background-color: white;{% elif vendor.vendor_profile.video_intro_color|blendbright and not darkmode %}background-color: black;{% endif %}">{{ vendor.vendor_profile.video_intro_text }}</h2>
        <hr>
        {% if True or payment_processor == 'stripe' %}	<a class="btn btn-outline-danger" title="{{ 'Connect your bank account or debit card to get paid'|etrans }}" href="{% url 'payments:create-link' %}">{{ 'Payouts'|etrans }}</a>{% endif %}
        <form method="POST" enctype="multipart/form-data">
            {% csrf_token %}
            <fieldset class="form-group">
                {{ form|crispy }}
            </fieldset>
    	    <p>{{ 'Please be sure all details are correct before proceeding.'|etrans }}</p>
            <div class="form-group">
                <button class="btn btn-outline-info" type="submit">{{ 'Submit'|etrans }}</button>
            </div>
        </form>
{% endblock content %}
```


--- File: lotteharper-main/vendors/tests.py ---
```python
def is_vendor(user):
    return user.profile.vendor
```


--- File: lotteharper-main/vendors/urls.py ---
```python
from django.urls import path

from . import views

app_name='vendors'

urlpatterns = [
    path('onboarding/', views.onboarding, name='onboarding'),
    path('preferences/', views.vendor_preferences, name='preferences'),
    path('crypto/', views.send_bitcoin, name='send-bitcoin'),
    path('adult/video/<str:username>/', views.video, name='video'),
    path('adult/content/<str:username>/', views.content, name='content'),
]
```


--- File: lotteharper-main/vendors/views.py ---
```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import pediatric_identity_verified, minor_identity_verified
from barcode.tests import minor_document_scanned, pediatric_document_scanned

def video(request, username):
    from .models import VendorProfile
    from django.shortcuts import redirect
    from django.contrib import messages
    from security.apis import get_client_ip, check_raw_ip_risk
    if not request.COOKIES.get('age_verified', None) or check_raw_ip_risk(get_client_ip(request), True, False):
        messages.warning(request, 'You may not visit this link, as per the site policies.')
        return redirect(reverse('misc:terms'))
    profile = VendorProfile.objects.filter(user__profile__name=username).first()
    return redirect('/' if not profile.video_link else profile.video_link)

def content(request, username):
    from .models import VendorProfile
    from django.shortcuts import redirect
    from django.contrib import messages
    from security.apis import get_client_ip, check_raw_ip_risk
    if not request.COOKIES.get('age_verified', None) or check_raw_ip_risk(get_client_ip(request), True, False):
        messages.warning(request, 'You may not visit this link, as per the site policies.')
        return redirect(reverse('misc:terms'))
    profile = VendorProfile.objects.filter(user__profile__name=username).first()
    return redirect('/' if not profile.content_link else profile.content_link)

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def send_bitcoin(request):
    from .models import VendorPaymentsProfile
    from django.shortcuts import render
    profile, created = VendorPaymentsProfile.objects.get_or_create(vendor=request.user)
    return render(request, 'vendors/send_bitcoin.html', {'title': 'Crypto', 'info': profile.get_crypto_balances()})

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def onboarding(request):
    from django.shortcuts import redirect
    from django.urls import reverse
    from payments.models import VendorProfile
    if not hasattr(request.user, 'vendor_profile'):
        v = VendorProfile.objects.create(user=request.user)
        v.save()
        request.user.profile.vendor = True
        request.user.profile.save()
    from django.shortcuts import render
    return redirect(reverse('feed:profile', kwargs={'username': request.user.username}))

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
def vendor_preferences(request):
    from django.shortcuts import redirect
    from django.urls import reverse
    from payments.models import VendorPaymentsProfile
    from .forms import VendorProfileUpdateForm
    from .models import VendorProfile
    from django.contrib import messages
    v, created = VendorProfile.objects.get_or_create(user=request.user)
    v.save()
    form = VendorProfileUpdateForm(instance=v, user=request.user)
    if request.method == 'POST':
        form = VendorProfileUpdateForm(request.POST, request.FILES, instance=request.user.vendor_profile, user=request.user)
        if form.is_valid():
            form.instance.user = request.user
            tfm_key = form.cleaned_data.get('transistorfm_key')
            if form.cleaned_data.get('sync_podcasts') or (tfm_key != request.user.vendor_profile.transistorfm_key):
                from live.podcast import update_user_podcasts
                update_user_podcasts(request.user)
            from payments.apis import validate_address
            accepted = True
            import coinaddrvalidator as crv
            from payments.apis import validate_address
            try:
                if form.cleaned_data.get('payout_address') and not crv.validate(form.cleaned_data.get('payout_currency').lower(), form.cleaned_data.get('payout_address')).valid:
                    form.instance.payout_address = ''
                    messages.warning(request, 'This crypto address could not be accepted. Please check the address and the currency.')
                    accepted = False
            except:
                form.instance.payout_address = ''
                messages.warning(request, 'This crypto address could not be accepted. Please check the address and the currency.')
                accepted = False
            cloc = {'btc': 'bitcoin', 'eth': 'ethereum', 'xlm': 'stellarlumens', 'bch': 'bitcoin-cash', 'ltc': 'litecoin', 'doge': 'dogecoin'}
            cnet = {'usdc': 'usdcoin', 'sol': 'solana', 'matic': 'polygon', 'avax': 'avalanche', 'trump': 'trump', 'usdt': 'usdtether'}
            for key, val in cloc.items():
                try:
                    if form.cleaned_data.get('{}_address'.format(val)) and not crv.validate(key, form.cleaned_data.get('{}_address'.format(val))).valid:
                        exec("form.instance.{}_address = ''".format(val.replace('-', '_')))
                        messages.warning(request, 'This {} address could not be accepted. Please check the address and the currency.'.format(val))
                        accepted = False
                except:
                    exec("form.instance.{}_address = ''".format(val.replace('-', '_')))
                    messages.warning(request, 'This {} address could not be accepted. Please check the address and the currency.'.format(val))
                    accepted = False
            for key, val in cnet.items():
                try:
                    if form.cleaned_data.get('{}_address'.format(val)) and not validate_address(key, form.cleaned_data.get('{}_address'.format(val))):
                        exec("form.instance.{}_address = ''".format(val))
                        messages.warning(request, 'This {} address could not be accepted. Please check the address and the currency.'.format(val))
                        accepted = False
                except:
                    exec("form.instance.{}_address = ''".format(val))
                    messages.warning(request, 'This {} address could not be accepted. Please check the address and the currency.'.format(val))
                    accepted = False
            for char in form.instance.video_intro_color[1:]:
                if char.upper() not in "0123456789ABCDEF":
                    messages.warning(request, 'This color could not be accepted. Please use a hexadecimal color in the form #ABCDEF')
                    form.instance.video_intro_color = '#FFFFFF'
                    accepted = False
            if not form.instance.video_intro_color[0] == '#':
                messages.warning(request, 'This color could not be accepted. Please use a hexadecimal color in the form #ABCDEF')
                form.instance.video_intro_color = '#FFFFFF'
                accepted = False
            from fontTools.ttLib import TTFont
            def validate_ttf(file_path):
                """
                Validates a TTF file.

                Args:
                    file_path (str): The path to the TTF file.

                Returns:
                    bool: True if the TTF file is valid, False otherwise.
                """
                try:
                    font = TTFont(file_path)
                    font.close()
                    return True
                except Exception as e:
                    print(f"Error validating TTF file: {e}")
                    return False
            if form.instance.video_intro_font and not (form.instance.video_intro_font.name.rsplit('.', 1)[1] == 'ttf'):
                messages.warning(request, 'The font you uploaded is not valid because the extension is wrong. Please upload a valid OpenType font in .ttf format.')
                accepted = False
#            if form.instance.activate_surrogacy and not minor_document_scanned(request.user): form.instance.activate_surrogacy = False
            p = form.save()
            if p.video_intro_font and not (p.video_intro_font.name.rsplit('.', 1)[1] == 'ttf' and validate_ttf(p.video_intro_font.path)):
                messages.warning(request, 'The font you uploaded is not valid. Please upload a valid OpenType font in .ttf format.')
                accepted = False
            if accepted:
                p.user.profile.vendor = True
                p.user.profile.save()
                messages.success(request, 'Vendor profile updated.')
                return redirect(reverse('go:go'))
    from django.conf import settings
    from django.shortcuts import render
    return render(request, 'vendors/vendor_preferences.html', {'title': 'Vendor Preferences','form': form, 'payment_processor': settings.PAYMENT_PROCESSOR, 'vendor': request.user})

```


--- File: lotteharper-main/verify/admin.py ---
```python
from django.contrib import admin
from .models import IdentityDocument
from simple_history.admin import SimpleHistoryAdmin
# Register your models here.
admin.site.register(IdentityDocument, SimpleHistoryAdmin)
```


--- File: lotteharper-main/verify/apps.py ---
```python
from django.apps import AppConfig

class VerifyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'verify'

    def ready(self):
        # Makes sure all signal handlers are connected
        from verify import handlers  # noqa
```


--- File: lotteharper-main/verify/barcode.py ---
```python
def barcode_valid(verification):
    import re, os
    from django.conf import settings
    from .process_barcode import process
    from .forensics import text_matches_name, text_matches_birthday, text_has_valid_birthday_and_expiry
    from barcode.idscan import scan_id
    from .idscan import decode_barcode
#    if not scan_id(verification.document_back.path, verification):
#        return False
    from PIL import Image
    if not verification.document_back.name.split('.')[-1] == 'png':
        img = Image.open(verification.document_back.path)
        verification.document_back = str(verification.document_back.path) + '.png'
        img.save(verification.document_back.path, 'PNG')
        verification.save()
    if not verification.document_back_isolated:
        from verify.models import get_document_path
        new_path = os.path.join(settings.MEDIA_ROOT, get_document_path(verification, verification.document_back.name))
        from barcode.isolate import write_isolated
        write_isolated(verification.document_back.path, new_path)
        verification.document_back_isolated = new_path
        verification.save()
    import zxing
    reader = zxing.BarCodeReader()
    barcodes_raw = str(reader.decode(verification.document_back_isolated.path))
    print(barcodes_raw)
    matches = re.findall("raw='([^']+)'", str(barcodes_raw))
    fmatch = re.findall("format='([\w+]+)'", str(barcodes_raw))
    if not 'PDF_417' in fmatch:
        print(fmatch)
        print('Barcode format mismatch')
        return False
    match = ''
    for m in matches:
        print(m)
        if len(m) > len(match):
            match = m
    print(match)
    verification.barcode_data = match
    verification.barcode_data_processed = process(match)
    verification.save()
    if not match:
        return False
    if settings.USE_IDWARE and not decode_barcode(match, verification): return False
    processed = verification.barcode_data_processed
    if not text_matches_name(processed, verification.full_name) or not text_matches_birthday(processed, verification.birthday.strftime('%m/%d/%Y').replace('/', '')):
        print('mismatch')
        return False
    if not verification.document_number or len(verification.document_number) < 8 or not verification.document_number in processed:
        print('Number not found on document')
        return False
    return text_has_valid_birthday_and_expiry(verification.barcode_data_processed, '')
```


--- File: lotteharper-main/verify/blur_detection.py ---
```python
import cv2

def variance_of_laplacian(image):
    return cv2.Laplacian(image, cv2.CV_64F).var()

def detect_blur(imagePath):
    image = cv2.imread(imagePath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    fm = variance_of_laplacian(gray)
    # check image quality
    print('Variance of laplacian is ' + str(fm))
    height, width, dim = image.shape
    if fm < width/3000 * 5:
        return True
    return False
```


--- File: lotteharper-main/verify/forensics.py ---
```python
from verify.forms import get_past_date
from datetime import datetime
from django.utils import timezone
from django.conf import settings
import pytz, re

tz = pytz.timezone(settings.TIME_ZONE)

def text_has_valid_expiry(image_text, seperator='/'):
    expiry_valid = False
    matches = []
    if seperator == '/':
        matches = re.findall('[\d+]+/[\d+]+/[\d+]+'.format(seperator, seperator), image_text)
        if len(matches) < 2:
            matches = re.findall('[\d+]+-[\d+]+-[\d+]+'.format(seperator, seperator), image_text)
    else:
        matches = re.findall('[0-9][0-9][0-9][0-9][1-2][0-9][0-9][0-9]', image_text)
    s = seperator
    expiry = None
    for match in matches:
        print(match)
        if seperator == '' and not len(match) == 8:
            continue
        if seperator == '':
            match = match[0:2] + s + match[2:4] + s + match[4:8]
        date_on_id = None
        try:
            date_on_id = datetime.strptime(match, '%m{}%d{}%Y'.format(s,s)).replace(tzinfo=tz)
        except:
            try:
                date_on_id = datetime.strptime(match, '%d{}%m{}%Y'.format(s,s)).replace(tzinfo=tz)
            except:
                pass
        if not date_on_id: continue
        print(str(date_on_id))
        if date_on_id > timezone.now().replace(tzinfo=tz):
            expiry_valid = True
            expiry = date_on_id
    if expiry_valid:
        return expiry
    return False

def text_has_valid_birthday_and_expiry(image_text, seperator='/'):
    bday_valid = False
    expiry_valid = False
    matches = []
    if seperator == '/':
        matches = re.findall('[\d+]+/[\d+]+/[\d+]+'.format(seperator, seperator), image_text)
        if len(matches) < 2:
            matches = re.findall('[\d+]+-[\d+]+-[\d+]+'.format(seperator, seperator), image_text)
    else:
        matches = re.findall('[0-9][0-9][0-9][0-9][1-2][0-9][0-9][0-9]', image_text)
    s = seperator
    bday = None
    expiry = None
    bday = get_past_date().replace(tzinfo=tz)
    for match in matches:
        print(match)
        if seperator == '' and not len(match) == 8:
            continue
        if seperator == '':
            match = match[0:2] + s + match[2:4] + s + match[4:8]
        date_on_id = None
        try:
            date_on_id = datetime.strptime(match, '%m{}%d{}%Y'.format(s,s)).replace(tzinfo=tz)
        except:
            try:
                date_on_id = datetime.strptime(match, '%d{}%m{}%Y'.format(s,s)).replace(tzinfo=tz)
            except:
                pass
        if not date_on_id: continue
        print(str(date_on_id))
        if date_on_id < bday:
            bday_valid = True
            bday = date_on_id
        if date_on_id > timezone.now().replace(tzinfo=tz):
            expiry_valid = True
            expiry = date_on_id
    if bday_valid and expiry_valid:
        return (bday, expiry)
    return False

def text_matches_name(image_text, name):
    split = name.lower().split(" ")
    image_text = image_text.lower()
    for text in split:
        if not text in image_text:
            print("Id name mismatch " + name + " " + image_text)
            return False
    print('ID name matches')
    return True

def text_matches_birthday(image_text, birthday):
    if not birthday in image_text:
        print("Id birthday mismatch " + birthday)
        return False
    return True
```


--- File: lotteharper-main/verify/forms.py ---
```python
from django import forms
from .models import IdentityDocument
from jsignature.forms import JSignatureField, JSignatureWidget

def get_past_date(age=None):
    import datetime
    from dateutil.relativedelta import relativedelta
    from django.conf import settings
    return datetime.datetime.now() - relativedelta(years=settings.MIN_AGE if not age else age)

from feed.middleware import get_current_user

class VerificationForm(forms.ModelForm):
    document_number = forms.CharField(widget=forms.TextInput())
    birthday = forms.DateField(initial=get_past_date, widget=forms.DateInput(attrs={'type': 'date'}))
    signature = JSignatureField(widget=JSignatureWidget(jsignature_attrs={'color': '#ff0000' if get_current_user() and not get_current_user().profile.vendor else '#000000'}))
    i_am_a = forms.CharField()
    seeking = forms.CharField()
    attest = forms.BooleanField()
    def __init__(self, *args, **kwargs):
        super(VerificationForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['document'].required = True
        self.fields['address'].required = True
        self.fields['document_number'].required = True
        self.fields['document_back'].required = True
        self.fields['full_name'].required = True
        self.fields['document'].label = translate(r, 'Upload a photo of your drivers license or state ID document clearly showing your full name and date of birth.')
        self.fields['address'].label = translate(r, 'Let me know where you live')
        self.fields['full_name'].label = translate(r, 'Please tell me your full name, first, middle and last name.')
        self.fields['document_number'].label = translate(r, 'The ID number on your document')
        self.fields['document_back'].label = translate(r, 'Upload a photo of the back of your ID document clearly showing the PDF417 barcode.')
        self.fields['birthday'].label = translate(r, 'Tell me your birthday (as the day is shown on your ID)')
        self.fields['birthday'].initial = get_past_date()
        self.fields['attest'].label = translate(r, 'I confirm and attest to my own good character and compliance with the law as well as the policies listed on this website.')
        self.fields['i_am_a'].label = translate(r, 'I am a', src='en')
        self.fields['seeking'].label = translate(r, 'Seeking', src='en')
        self.fields['signature'].label = translate(r, 'Your signature', src='en')
        i = [['woman','woman'], ['man','man'], ['other', 'other'], ['heat','heat']]
        s = [['woman','woman'], ['man','man'],  ['other', 'other'], ['missile','missile']]
        for c in i:
            c[1] = translate(r, c[1], src='en').capitalize()
        for c in s:
            c[1] = translate(r, c[1], src='en').capitalize()
        self.fields['i_am_a'].widget = forms.Select(choices=i)
        self.fields['seeking'].widget = forms.Select(choices=s)
        if get_current_request().GET.get('camera'):
            self.fields['document'].widget.attrs.update({'capture': 'environment'})
            self.fields['document_back'].widget.attrs.update({'capture': 'environment'})
        self.fields['document'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
        self.fields['document_back'].widget.attrs.update({'style': 'width:100%;padding:25px;border-style:dashed;border-radius:10px;'})
    class Meta:
        model = IdentityDocument
        fields = ['full_name','birthday','address','document_number','document','document_back', 'i_am_a', 'seeking', 'signature', 'attest']
        widgets = {
            'birthday': forms.DateInput(),
            'document_number': forms.Textarea(attrs={'rows': 1}),
        }
```


--- File: lotteharper-main/verify/handlers.py ---
```python
from corsheaders.signals import check_request_enabled

def cors_allow_api_to_everyone(sender, request, **kwargs):
    return request.path.startswith("/verify/api/")
```


--- File: lotteharper-main/verify/idscan.py ---
```python
import requests
import json
from django.conf import settings
import base64
import codecs
from io import BytesIO
from PIL import Image
from verify.forms import get_past_date
from datetime import datetime
from django.utils import timezone
import pytz
utc=pytz.timezone(settings.TIME_ZONE)
#pytz.UTC

def decode_barcode(barcode_data, instance):
    api_url = "https://app1.idware.net/DriverLicenseParserRest.svc/Parse"
    message = barcode_data.encode('utf-8')
    base64_bytes = base64.b64encode(message)
    encoded_string = base64_bytes.decode('utf-8')
    todo = {"authKey": settings.IDSCAN_AUTH_KEY, "text": encoded_string}
    headers =  {"Content-Type":"text/json", "Cache-Control": "no-cache"}
    response = requests.post(api_url, data=json.dumps(todo), headers=headers)
    decoded_data=codecs.decode(response.text.encode(), 'utf-8-sig')
    instance.idscan_text = str(decoded_data)
    instance.idscan = str(decoded_data)
    instance.save()
    print(instance.idscan_text)
    response = json.loads(instance.idscan_text)
    result = response['ParseResult']
    document = result[list(result.keys())[0]]
    if list(result.keys())[0] in settings.BANNED_ID_TYPES: return False
    exp_date = document['ExpirationDate']
    exp_date = datetime.strptime(exp_date, '%Y-%m-%d').replace(tzinfo=utc)
    if exp_date < timezone.now():
        return False
    birthday = document['Birthdate']
    birthday = datetime.strptime(birthday, '%Y-%m-%d').replace(tzinfo=utc)
    subject = document['Subject'] if 'Subject' in document else None
    if settings.REQUIRE_SUBJECTION and subject and not (subject == 'Y' or subject == 'y'): return False
    if birthday > get_past_date().replace(tzinfo=utc):
        return False
    if result['Success'] and int(result['Confidence']) > settings.MIN_CONFIDENCE:
        return True
    return False
```


--- File: lotteharper-main/verify/__init__.py ---
```python
```


--- File: lotteharper-main/verify/migrations/0001_initial.py ---
```python
# Generated by Django 4.2.5 on 2023-10-04 16:02

import address.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import jsignature.fields
import verify.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('address', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IdentityDocument',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('full_name', models.CharField(default='', max_length=100)),
                ('document', models.ImageField(null=True, upload_to=verify.models.get_document_path)),
                ('document_back', models.ImageField(null=True, upload_to=verify.models.get_document_path)),
                ('signature', jsignature.fields.JSignatureField(null=True)),
                ('document_number', models.TextField(blank=True, default='', null=True)),
                ('document_ocr', models.TextField(blank=True, default='', null=True)),
                ('barcode_data', models.TextField(blank=True, default='', null=True)),
                ('barcode_data_processed', models.TextField(blank=True, default='', null=True)),
                ('idscan', models.TextField(blank=True, default='', null=True)),
                ('idscan_text', models.TextField(blank=True, default='', null=True)),
                ('birthday', models.DateTimeField(default=django.utils.timezone.now)),
                ('submitted', models.DateTimeField(default=django.utils.timezone.now)),
                ('birthdate', models.DateTimeField(default=django.utils.timezone.now)),
                ('expiry', models.DateTimeField(default=django.utils.timezone.now)),
                ('expire_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('verified', models.BooleanField(default=False)),
                ('address', address.models.AddressField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='address.address')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='verifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/verify/migrations/0002_veriflow.py ---
```python
# Generated by Django 5.0.6 on 2024-07-06 01:12

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('barcode', '0001_initial'),
        ('face', '0003_facetoken'),
        ('verify', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VeriFlow',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('uid', models.CharField(default=uuid.uuid4, max_length=100)),
                ('next', models.CharField(blank=True, default=uuid.uuid4, max_length=300, null=True)),
                ('face', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='face.face')),
                ('scans', models.ManyToManyField(to='barcode.documentscan')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='veriflows', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/verify/migrations/0003_identitydocument_document_back_isolated.py ---
```python
# Generated by Django 5.0.7 on 2024-08-16 01:56

import verify.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verify', '0002_veriflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='identitydocument',
            name='document_back_isolated',
            field=models.ImageField(null=True, upload_to=verify.models.get_document_path),
        ),
    ]
```


--- File: lotteharper-main/verify/migrations/0004_identitydocument_document_isolated.py ---
```python
# Generated by Django 5.0.7 on 2024-08-16 02:29

import verify.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verify', '0003_identitydocument_document_back_isolated'),
    ]

    operations = [
        migrations.AddField(
            model_name='identitydocument',
            name='document_isolated',
            field=models.ImageField(null=True, upload_to=verify.models.get_document_path),
        ),
    ]
```


--- File: lotteharper-main/verify/migrations/0005_identitydocument_subjective.py ---
```python
# Generated by Django 5.2.3 on 2025-07-15 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verify', '0004_identitydocument_document_isolated'),
    ]

    operations = [
        migrations.AddField(
            model_name='identitydocument',
            name='subjective',
            field=models.BooleanField(default=False),
        ),
    ]
```


--- File: lotteharper-main/verify/migrations/__init__.py ---
```python
```


--- File: lotteharper-main/verify/models.py ---
```python
from simple_history.models import HistoricalRecords
from django.db import models
from jsignature.fields import JSignatureField
from address.models import AddressField

def get_document_path(instance, filename):
    import uuid, os, datetime
    from feed.middleware import get_current_user
    ext = filename.split('.')[-1]
    filename = "%s.%s" % ('{}-{}-{}'.format(uuid.uuid4(), instance.submitted.strftime("%Y%m%d-%H%M%S"), get_current_user().id if get_current_user() else 0), ext)
    return os.path.join('documents/', filename)

def get_signature_path(instance, filename):
    import uuid, os
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('signature/', filename)

def get_past_date():
    from dateutil.relativedelta import relativedelta
    from django.conf import settings
    from django.utils import timezone
    return timezone.now() - relativedelta(years=settings.MIN_AGE)

def get_past_day():
    from dateutil.relativedelta import relativedelta
    from django.conf import settings
    from django.utils import timezone
    return timezone.now() - relativedelta(years=settings.MIN_AGE)

import uuid
from django.contrib.auth.models import User

from barcode.models import DocumentScan
from face.models import Face

class VeriFlow(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='veriflows')
    uid = models.CharField(default=uuid.uuid4, max_length=100)
    face = models.ForeignKey(Face, on_delete=models.DO_NOTHING, null=True, blank=True)
    scans = models.ManyToManyField(DocumentScan)
    next = models.CharField(default=uuid.uuid4, max_length=300, null=True, blank=True)

    def is_valid(self):
        return self.face.authorized and self.scans.filter(side=True, succeeded=True).count() > 0 and self.scans.filter(side=False, succeeded=True).count() > 0

from django.utils import timezone

class IdentityDocument(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='verifications')
    full_name = models.CharField(default='', max_length=100)
    address = AddressField(null=True, blank=True)
    document = models.ImageField(upload_to=get_document_path, null=True)
    document_isolated = models.ImageField(upload_to=get_document_path, null=True)
    document_back = models.ImageField(upload_to=get_document_path, null=True)
    document_back_isolated = models.ImageField(upload_to=get_document_path, null=True)
    signature = JSignatureField(null=True)
    document_number = models.TextField(default='', null=True, blank=True)
    document_ocr = models.TextField(default='', null=True, blank=True)
    barcode_data = models.TextField(default='', null=True, blank=True)
    barcode_data_processed = models.TextField(default='', null=True, blank=True)
    idscan = models.TextField(default='', null=True, blank=True)
    idscan_text = models.TextField(default='', null=True, blank=True)
    birthday = models.DateTimeField(default=timezone.now)
    submitted = models.DateTimeField(default=timezone.now)
    birthdate = models.DateTimeField(default=timezone.now)
    expiry = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField(default=timezone.now)
    verified = models.BooleanField(default=False)
    subjective = models.BooleanField(default=False)

    def get_base64_front(self, key):
        import urllib.parse
        import base64
        from security.crypto import encrypt_cbc
        with open(self.document_isolated.path, 'rb') as file:
            image1 = base64.b64encode(file.read()).decode('utf-8')
        return urllib.parse.quote_plus(encrypt_cbc(image1, key))

    def get_base64_back(self, key):
        import urllib.parse
        import base64
        from security.crypto import encrypt_cbc
        with open(self.document_back_isolated.path, 'rb') as file:
            image2 = base64.b64encode(file.read()).decode('utf-8')
        return urllib.parse.quote_plus(encrypt_cbc(image2, key))

    def save(self, *args, **kwargs):
        this = IdentityDocument.objects.filter(id=self.id).first()
        if this and this.verified:
#            return
            if len(self.barcode_data) < len(this.barcode_data):
                return
            if len(self.barcode_data_processed) < len(this.barcode_data_processed):
                return
            if not self.document or not self.document_back:
                return
        super(IdentityDocument, self).save(*args, **kwargs)

    def __str__(self):
        return self.full_name + ' documented ' + self.birthday.strftime('%m/%d/%Y')

    def delete(self):
        pass
```


--- File: lotteharper-main/verify/ocr.py ---
```python
def get_image_text(path, lang='eng'):
    import cv2
    import pytesseract
    from PIL import Image
    print('Trying to tesseract (ocr) image')
    image = Image.open(path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
        image.save(path)
#    img_cv = cv2.imread(path)
#    mode = Image.open(path).mode[0]
#    img = img_cv
#    if mode == 'B':
#        img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    text = pytesseract.image_to_string(image, lang=lang)
    print(text)
    return text
```


--- File: lotteharper-main/verify/pdf417dict.py ---
```python
codewords_tbl = [['31111136', '41111144', '51111152', '31111235', '41111243', '51111251', '21111326', '31111334', '21111425', '11111516', '21111524', '11111615', '21112136', '31112144', '41112152', '21112235', '31112243', '41112251', '11112326', '21112334', '11112425', '11113136', '21113144', '31113152', '11113235', '21113243', '31113251', '11113334', '21113342', '11114144', '21114152', '11114243', '21114251', '11115152', '51116111', '31121135', '41121143', '51121151', '21121226', '31121234', '41121242', '21121325', '31121333', '11121416', '21121424', '31121432', '11121515', '21121523', '11121614', '21122135', '31122143', '41122151', '11122226', '21122234', '31122242', '11122325', '21122333', '31122341', '11122424', '21122432', '11123135', '21123143', '31123151', '11123234', '21123242', '11123333', '21123341', '11124143', '21124151', '11124242', '11124341', '21131126', '31131134', '41131142', '21131225', '31131233', '41131241', '11131316', '21131324', '31131332', '11131415', '21131423', '11131514', '11131613', '11132126', '21132134', '31132142', '11132225', '21132233', '31132241', '11132324', '21132332', '11132423', '11132522', '11133134', '21133142', '11133233', '21133241', '11133332', '11134142', '21141125', '31141133', '41141141', '11141216', '21141224', '31141232', '11141315', '21141323', '31141331', '11141414', '21141422', '11141513', '21141521', '11142125', '21142133', '31142141', '11142224', '21142232', '11142323', '21142331', '11142422', '11142521', '21143141', '11143331', '11151116', '21151124', '31151132', '11151215', '21151223', '31151231', '11151314', '21151322', '11151413', '21151421', '11151512', '11152124', '11152223', '11152322', '11161115', '31161131', '21161222', '21161321', '11161511', '32111135', '42111143', '52111151', '22111226', '32111234', '42111242', '22111325', '32111333', '42111341', '12111416', '22111424', '12111515', '22112135', '32112143', '42112151', '12112226', '22112234', '32112242', '12112325', '22112333', '12112424', '12112523', '12113135', '22113143', '32113151', '12113234', '22113242', '12113333', '12113432', '12114143', '22114151', '12114242', '12115151', '31211126', '41211134', '51211142', '31211225', '41211233', '51211241', '21211316', '31211324', '41211332', '21211415', '31211423', '41211431', '21211514', '31211522', '22121126', '32121134', '42121142', '21212126', '22121225', '32121233', '42121241', '21212225', '31212233', '41212241', '11212316', '12121415', '22121423', '32121431', '11212415', '21212423', '11212514', '12122126', '22122134', '32122142', '11213126', '12122225', '22122233', '32122241', '11213225', '21213233', '31213241', '11213324', '12122423', '11213423', '12123134', '22123142', '11214134', '12123233', '22123241', '11214233', '21214241', '11214332', '12124142', '11215142', '12124241', '11215241', '31221125', '41221133', '51221141', '21221216', '31221224', '41221232', '21221315', '31221323', '41221331', '21221414', '31221422', '21221513', '21221612', '22131125', '32131133', '42131141', '21222125', '22131224', '32131232', '11222216', '12131315', '31222232', '32131331', '11222315', '12131414', '22131422', '11222414', '21222422', '22131521', '12131612', '12132125', '22132133', '32132141', '11223125', '12132224', '22132232', '11223224', '21223232', '22132331', '11223323', '12132422', '12132521', '12133133', '22133141', '11224133', '12133232', '11224232', '12133331', '11224331', '11225141', '21231116', '31231124', '41231132', '21231215', '31231223', '41231231', '21231314', '31231322', '21231413', '31231421', '21231512', '21231611', '12141116', '22141124', '32141132', '11232116', '12141215', '22141223', '32141231', '11232215', '21232223', '31232231', '11232314', '12141413', '22141421', '11232413', '21232421', '11232512', '12142124', '22142132', '11233124', '12142223', '22142231', '11233223', '21233231', '11233322', '12142421', '11233421', '11234132', '11234231', '21241115', '31241123', '41241131', '21241214', '31241222', '21241313', '31241321', '21241412', '21241511', '12151115', '22151123', '32151131', '11242115', '12151214', '22151222', '11242214', '21242222', '22151321', '11242313', '12151412', '11242412', '12151511', '12152123', '11243123', '11243222', '11243321', '31251122', '31251221', '21251411', '22161122', '12161213', '11252213', '11252312', '11252411', '23111126', '33111134', '43111142', '23111225', '33111233', '13111316', '23111324', '33111332', '13111415', '23111423', '13111514', '13111613', '13112126', '23112134', '33112142', '13112225', '23112233', '33112241', '13112324', '23112332', '13112423', '13112522', '13113134', '23113142', '13113233', '23113241', '13113332', '13114142', '13114241', '32211125', '42211133', '52211141', '22211216', '32211224', '42211232', '22211315', '32211323', '42211331', '22211414', '32211422', '22211513', '32211521', '23121125', '33121133', '43121141', '22212125', '23121224', '33121232', '12212216', '13121315', '32212232', '33121331', '12212315', '22212323', '23121422', '12212414', '13121513', '12212513', '13122125', '23122133', '33122141', '12213125', '13122224', '32213141', '12213224', '22213232', '23122331', '12213323', '13122422', '12213422', '13123133', '23123141', '12214133', '13123232', '12214232', '13123331', '13124141', '12215141', '31311116', '41311124', '51311132', '31311215', '41311223', '51311231', '31311314', '41311322', '31311413', '41311421', '31311512', '22221116', '32221124', '42221132', '21312116', '22221215', '41312132', '42221231', '21312215', '31312223', '41312231', '21312314', '22221413', '32221421', '21312413', '31312421', '22221611', '13131116', '23131124', '33131132', '12222116', '13131215', '23131223', '33131231', '11313116', '12222215', '22222223', '32222231', '11313215', '21313223', '31313231', '23131421', '11313314', '12222413', '22222421', '11313413', '13131611', '13132124', '23132132', '12223124', '13132223', '23132231', '11314124', '12223223', '22223231', '11314223', '21314231', '13132421', '12223421', '13133132', '12224132', '13133231', '11315132', '12224231', '31321115', '41321123', '51321131', '31321214', '41321222', '31321313', '41321321', '31321412', '31321511', '22231115', '32231123', '42231131', '21322115', '22231214', '41322131', '21322214', '31322222', '32231321', '21322313', '22231412', '21322412', '22231511', '21322511', '13141115', '23141123', '33141131', '12232115', '13141214', '23141222', '11323115', '12232214', '22232222', '23141321', '11323214', '21323222', '13141412', '11323313', '12232412', '13141511', '12232511', '13142123', '23142131', '12233123', '13142222', '11324123', '12233222', '13142321', '11324222', '12233321', '13143131', '11325131', '31331114', '41331122', '31331213', '41331221', '31331312', '31331411', '22241114', '32241122', '21332114', '22241213', '32241221', '21332213', '31332221', '21332312', '22241411', '21332411', '13151114', '23151122', '12242114', '13151213', '23151221', '11333114', '12242213', '22242221', '11333213', '21333221', '13151411', '11333312', '12242411', '11333411', '12243122', '11334122', '11334221', '41341121', '31341311', '32251121', '22251212', '22251311', '13161113', '12252113', '11343113', '13161311', '12252311', '24111125', '14111216', '24111224', '14111315', '24111323', '34111331', '14111414', '24111422', '14111513', '24111521', '14112125', '24112133', '34112141', '14112224', '24112232', '14112323', '24112331', '14112422', '14112521', '14113133', '24113141', '14113232', '14113331', '14114141', '23211116', '33211124', '43211132', '23211215', '33211223', '23211314', '33211322', '23211413', '33211421', '23211512', '14121116', '24121124', '34121132', '13212116', '14121215', '33212132', '34121231', '13212215', '23212223', '33212231', '13212314', '14121413', '24121421', '13212413', '23212421', '14121611', '14122124', '24122132', '13213124', '14122223', '24122231', '13213223', '23213231', '13213322', '14122421', '14123132', '13214132', '14123231', '13214231', '32311115', '42311123', '52311131', '32311214', '42311222', '32311313', '42311321', '32311412', '32311511', '23221115', '33221123', '22312115', '23221214', '33221222', '22312214', '32312222', '33221321', '22312313', '23221412', '22312412', '23221511', '22312511', '14131115', '24131123', '13222115', '14131214', '33222131', '12313115', '13222214', '23222222', '24131321', '12313214', '22313222', '14131412', '12313313', '13222412', '14131511', '13222511', '14132123', '24132131', '13223123', '14132222', '12314123', '13223222', '14132321', '12314222', '13223321', '14133131', '13224131', '12315131', '41411114', '51411122', '41411213', '51411221', '41411312', '41411411', '32321114', '42321122', '31412114', '41412122', '42321221', '31412213', '41412221', '31412312', '32321411', '31412411', '23231114', '33231122', '22322114', '23231213', '33231221', '21413114', '22322213', '32322221', '21413213', '31413221', '23231411', '21413312', '22322411', '21413411', '14141114', '24141122', '13232114', '14141213', '24141221', '12323114', '13232213', '23232221', '11414114', '12323213', '22323221', '14141411', '11414213', '21414221', '13232411', '11414312', '14142122', '13233122', '14142221', '12324122', '13233221', '11415122', '12324221', '11415221', '41421113', '51421121', '41421212', '41421311', '32331113', '42331121', '31422113', '41422121', '31422212', '32331311', '31422311', '23241113', '33241121', '22332113', '23241212', '21423113', '22332212', '23241311', '21423212', '22332311', '21423311', '14151113', '24151121', '13242113', '23242121', '12333113', '13242212', '14151311', '11424113', '12333212', '13242311', '11424212', '12333311', '11424311', '13243121', '11425121', '41431211', '31432112', '31432211', '22342112', '21433112', '21433211', '13252112', '12343112', '11434112', '11434211', '15111116', '15111215', '25111223', '15111314', '15111413', '15111512', '15112124', '15112223', '15112322', '15112421', '15113132', '15113231', '24211115', '24211214', '34211222', '24211313', '34211321', '24211412', '24211511', '15121115', '25121123', '14212115', '24212123', '25121222', '14212214', '24212222', '14212313', '24212321', '14212412', '15121511', '14212511', '15122123', '25122131', '14213123', '24213131', '14213222', '15122321', '14213321', '15123131', '14214131', '33311114', '33311213', '33311312', '33311411', '24221114', '23312114', '33312122', '34221221', '23312213', '33312221', '23312312', '24221411', '23312411', '15131114', '14222114', '15131213', '25131221', '13313114', '14222213', '15131312', '13313213', '14222312', '15131411', '13313312', '14222411', '15132122', '14223122', '15132221', '13314122', '14223221', '13314221', '42411113', '42411212', '42411311', '33321113', '32412113', '42412121', '32412212', '33321311', '32412311', '24231113', '34231121', '23322113', '33322121', '22413113', '23322212', '24231311', '22413212', '23322311', '22413311', '15141113', '25141121', '14232113', '24232121', '13323113', '14232212', '15141311', '12414113', '13323212', '14232311', '12414212', '13323311', '15142121', '14233121', '13324121', '12415121', '51511112', '51511211', '42421112', '41512112', '42421211', '41512211', '33331112', '32422112', '33331211', '31513112', '32422211', '31513211', '24241112', '23332112', '24241211', '22423112', '23332211', '21514112'], ['51111125', '61111133', '41111216', '51111224', '61111232', '41111315', '51111323', '61111331', '41111414', '51111422', '41111513', '51111521', '41111612', '41112125', '51112133', '61112141', '31112216', '41112224', '51112232', '31112315', '41112323', '51112331', '31112414', '41112422', '31112513', '41112521', '31112612', '31113125', '41113133', '51113141', '21113216', '31113224', '41113232', '21113315', '31113323', '41113331', '21113414', '31113422', '21113513', '31113521', '21113612', '21114125', '31114133', '41114141', '11114216', '21114224', '31114232', '11114315', '21114323', '31114331', '11114414', '21114422', '11114513', '21114521', '11115125', '21115133', '31115141', '11115224', '21115232', '11115323', '21115331', '11115422', '11116133', '21116141', '11116232', '11116331', '41121116', '51121124', '61121132', '41121215', '51121223', '61121231', '41121314', '51121322', '41121413', '51121421', '41121512', '41121611', '31122116', '41122124', '51122132', '31122215', '41122223', '51122231', '31122314', '41122322', '31122413', '41122421', '31122512', '31122611', '21123116', '31123124', '41123132', '21123215', '31123223', '41123231', '21123314', '31123322', '21123413', '31123421', '21123512', '21123611', '11124116', '21124124', '31124132', '11124215', '21124223', '31124231', '11124314', '21124322', '11124413', '21124421', '11124512', '11125124', '21125132', '11125223', '21125231', '11125322', '11125421', '11126132', '11126231', '41131115', '51131123', '61131131', '41131214', '51131222', '41131313', '51131321', '41131412', '41131511', '31132115', '41132123', '51132131', '31132214', '41132222', '31132313', '41132321', '31132412', '31132511', '21133115', '31133123', '41133131', '21133214', '31133222', '21133313', '31133321', '21133412', '21133511', '11134115', '21134123', '31134131', '11134214', '21134222', '11134313', '21134321', '11134412', '11134511', '11135123', '21135131', '11135222', '11135321', '11136131', '41141114', '51141122', '41141213', '51141221', '41141312', '41141411', '31142114', '41142122', '31142213', '41142221', '31142312', '31142411', '21143114', '31143122', '21143213', '31143221', '21143312', '21143411', '11144114', '21144122', '11144213', '21144221', '11144312', '11144411', '11145122', '11145221', '41151113', '51151121', '41151212', '41151311', '31152113', '41152121', '31152212', '31152311', '21153113', '31153121', '21153212', '21153311', '11154113', '21154121', '11154212', '11154311', '41161112', '41161211', '31162112', '31162211', '21163112', '21163211', '42111116', '52111124', '62111132', '42111215', '52111223', '62111231', '42111314', '52111322', '42111413', '52111421', '42111512', '42111611', '32112116', '42112124', '52112132', '32112215', '42112223', '52112231', '32112314', '42112322', '32112413', '42112421', '32112512', '32112611', '22113116', '32113124', '42113132', '22113215', '32113223', '42113231', '22113314', '32113322', '22113413', '32113421', '22113512', '22113611', '12114116', '22114124', '32114132', '12114215', '22114223', '32114231', '12114314', '22114322', '12114413', '22114421', '12114512', '12115124', '22115132', '12115223', '22115231', '12115322', '12115421', '12116132', '12116231', '51211115', '61211123', '11211164', '51211214', '61211222', '11211263', '51211313', '61211321', '11211362', '51211412', '51211511', '42121115', '52121123', '62121131', '41212115', '42121214', '61212131', '41212214', '51212222', '52121321', '41212313', '42121412', '41212412', '42121511', '41212511', '32122115', '42122123', '52122131', '31213115', '32122214', '42122222', '31213214', '41213222', '42122321', '31213313', '32122412', '31213412', '32122511', '31213511', '22123115', '32123123', '42123131', '21214115', '22123214', '32123222', '21214214', '31214222', '32123321', '21214313', '22123412', '21214412', '22123511', '21214511', '12124115', '22124123', '32124131', '11215115', '12124214', '22124222', '11215214', '21215222', '22124321', '11215313', '12124412', '11215412', '12124511', '12125123', '22125131', '11216123', '12125222', '11216222', '12125321', '11216321', '12126131', '51221114', '61221122', '11221163', '51221213', '61221221', '11221262', '51221312', '11221361', '51221411', '42131114', '52131122', '41222114', '42131213', '52131221', '41222213', '51222221', '41222312', '42131411', '41222411', '32132114', '42132122', '31223114', '32132213', '42132221', '31223213', '41223221', '31223312', '32132411', '31223411', '22133114', '32133122', '21224114', '22133213', '32133221', '21224213', '31224221', '21224312', '22133411', '21224411', '12134114', '22134122', '11225114', '12134213', '22134221', '11225213', '21225221', '11225312', '12134411', '11225411', '12135122', '11226122', '12135221', '11226221', '51231113', '61231121', '11231162', '51231212', '11231261', '51231311', '42141113', '52141121', '41232113', '51232121', '41232212', '42141311', '41232311', '32142113', '42142121', '31233113', '32142212', '31233212', '32142311', '31233311', '22143113', '32143121', '21234113', '31234121', '21234212', '22143311', '21234311', '12144113', '22144121', '11235113', '12144212', '11235212', '12144311', '11235311', '12145121', '11236121', '51241112', '11241161', '51241211', '42151112', '41242112', '42151211', '41242211', '32152112', '31243112', '32152211', '31243211', '22153112', '21244112', '22153211', '21244211', '12154112', '11245112', '12154211', '11245211', '51251111', '42161111', '41252111', '32162111', '31253111', '22163111', '21254111', '43111115', '53111123', '63111131', '43111214', '53111222', '43111313', '53111321', '43111412', '43111511', '33112115', '43112123', '53112131', '33112214', '43112222', '33112313', '43112321', '33112412', '33112511', '23113115', '33113123', '43113131', '23113214', '33113222', '23113313', '33113321', '23113412', '23113511', '13114115', '23114123', '33114131', '13114214', '23114222', '13114313', '23114321', '13114412', '13114511', '13115123', '23115131', '13115222', '13115321', '13116131', '52211114', '62211122', '12211163', '52211213', '62211221', '12211262', '52211312', '12211361', '52211411', '43121114', '53121122', '42212114', '43121213', '53121221', '42212213', '52212221', '42212312', '43121411', '42212411', '33122114', '43122122', '32213114', '33122213', '43122221', '32213213', '42213221', '32213312', '33122411', '32213411', '23123114', '33123122', '22214114', '23123213', '33123221', '22214213', '32214221', '22214312', '23123411', '22214411', '13124114', '23124122', '12215114', '13124213', '23124221', '12215213', '22215221', '12215312', '13124411', '12215411', '13125122', '12216122', '13125221', '12216221', '61311113', '11311154', '21311162', '61311212', '11311253', '21311261', '61311311', '11311352', '11311451', '52221113', '62221121', '12221162', '51312113', '61312121', '11312162', '12221261', '51312212', '52221311', '11312261', '51312311', '43131113', '53131121', '42222113', '43131212', '41313113', '51313121', '43131311', '41313212', '42222311', '41313311', '33132113', '43132121', '32223113', '33132212', '31314113', '32223212', '33132311', '31314212', '32223311', '31314311', '23133113', '33133121', '22224113', '23133212', '21315113', '22224212', '23133311', '21315212', '22224311', '21315311', '13134113', '23134121', '12225113', '13134212', '11316113', '12225212', '13134311', '11316212', '12225311', '11316311', '13135121', '12226121', '61321112', '11321153', '21321161', '61321211', '11321252', '11321351', '52231112', '12231161', '51322112', '52231211', '11322161', '51322211', '43141112', '42232112', '43141211', '41323112', '42232211', '41323211', '33142112', '32233112', '33142211', '31324112', '32233211', '31324211', '23143112', '22234112', '23143211', '21325112', '22234211', '21325211', '13144112', '12235112', '13144211', '11326112', '12235211', '11326211', '61331111', '11331152', '11331251', '52241111', '51332111', '43151111', '42242111', '41333111', '33152111', '32243111', '31334111', '23153111', '22244111', '21335111', '13154111', '12245111', '11336111', '11341151', '44111114', '54111122', '44111213', '54111221', '44111312', '44111411', '34112114', '44112122', '34112213', '44112221', '34112312', '34112411', '24113114', '34113122', '24113213', '34113221', '24113312', '24113411', '14114114', '24114122', '14114213', '24114221', '14114312', '14114411', '14115122', '14115221', '53211113', '63211121', '13211162', '53211212', '13211261', '53211311', '44121113', '54121121', '43212113', '44121212', '43212212', '44121311', '43212311', '34122113', '44122121', '33213113', '34122212', '33213212', '34122311', '33213311', '24123113', '34123121', '23214113', '24123212', '23214212', '24123311', '23214311', '14124113', '24124121', '13215113', '14124212', '13215212', '14124311', '13215311', '14125121', '13216121', '62311112', '12311153', '22311161', '62311211', '12311252', '12311351', '53221112', '13221161', '52312112', '53221211', '12312161', '52312211', '44131112', '43222112', '44131211', '42313112', '43222211', '42313211', '34132112', '33223112', '34132211', '32314112', '33223211', '32314211', '24133112', '23224112', '24133211', '22315112', '23224211', '22315211', '14134112', '13225112', '14134211', '12316112', '13225211', '12316211', '11411144', '21411152', '11411243', '21411251', '11411342', '11411441', '62321111', '12321152', '61412111', '11412152', '12321251', '11412251', '53231111', '52322111', '51413111', '44141111', '43232111', '42323111', '41414111', '34142111', '33233111', '32324111', '31415111', '24143111', '23234111', '22325111', '21416111', '14144111', '13235111', '12326111', '11421143', '21421151', '11421242', '11421341', '12331151', '11422151', '11431142', '11431241', '11441141', '45111113', '45111212', '45111311', '35112113', '45112121', '35112212', '35112311', '25113113', '35113121', '25113212', '25113311', '15114113', '25114121', '15114212', '15114311', '15115121', '54211112', '14211161', '54211211', '45121112', '44212112', '45121211', '44212211', '35122112', '34213112', '35122211', '34213211', '25123112', '24214112', '25123211', '24214211', '15124112', '14215112', '15124211', '14215211', '63311111', '13311152', '13311251', '54221111', '53312111', '45131111', '44222111', '43313111', '35132111', '34223111', '33314111', '25133111', '24224111', '23315111', '15134111', '14225111', '13316111', '12411143', '22411151', '12411242', '12411341', '13321151', '12412151', '11511134', '21511142', '11511233', '21511241', '11511332', '11511431', '12421142', '11512142', '12421241', '11512241', '11521133', '21521141', '11521232', '11521331', '12431141', '11522141', '11531132', '11531231', '11541131', '36112112', '36112211', '26113112', '26113211', '16114112', '16114211', '45212111', '36122111', '35213111', '26123111', '25214111', '16124111', '15215111', '14311151', '13411142', '13411241', '12511133', '22511141', '12511232', '12511331', '13421141', '12512141', '11611124', '21611132', '11611223', '21611231', '11611322', '11611421', '12521132', '11612132', '12521231', '11612231', '11621123', '21621131', '11621222', '11621321', '12531131', '11622131', '11631122', '11631221', '14411141', '13511132', '13511231', '12611123', '22611131', '12611222', '12611321', '13521131', '12612131', '12621122', '12621221'], ['21111155', '31111163', '11111246', '21111254', '31111262', '11111345', '21111353', '31111361', '11111444', '21111452', '11111543', '61112114', '11112155', '21112163', '61112213', '11112254', '21112262', '61112312', '11112353', '21112361', '61112411', '11112452', '51113114', '61113122', '11113163', '51113213', '61113221', '11113262', '51113312', '11113361', '51113411', '41114114', '51114122', '41114213', '51114221', '41114312', '41114411', '31115114', '41115122', '31115213', '41115221', '31115312', '31115411', '21116114', '31116122', '21116213', '31116221', '21116312', '11121146', '21121154', '31121162', '11121245', '21121253', '31121261', '11121344', '21121352', '11121443', '21121451', '11121542', '61122113', '11122154', '21122162', '61122212', '11122253', '21122261', '61122311', '11122352', '11122451', '51123113', '61123121', '11123162', '51123212', '11123261', '51123311', '41124113', '51124121', '41124212', '41124311', '31125113', '41125121', '31125212', '31125311', '21126113', '31126121', '21126212', '21126311', '11131145', '21131153', '31131161', '11131244', '21131252', '11131343', '21131351', '11131442', '11131541', '61132112', '11132153', '21132161', '61132211', '11132252', '11132351', '51133112', '11133161', '51133211', '41134112', '41134211', '31135112', '31135211', '21136112', '21136211', '11141144', '21141152', '11141243', '21141251', '11141342', '11141441', '61142111', '11142152', '11142251', '51143111', '41144111', '31145111', '11151143', '21151151', '11151242', '11151341', '11152151', '11161142', '11161241', '12111146', '22111154', '32111162', '12111245', '22111253', '32111261', '12111344', '22111352', '12111443', '22111451', '12111542', '62112113', '12112154', '22112162', '62112212', '12112253', '22112261', '62112311', '12112352', '12112451', '52113113', '62113121', '12113162', '52113212', '12113261', '52113311', '42114113', '52114121', '42114212', '42114311', '32115113', '42115121', '32115212', '32115311', '22116113', '32116121', '22116212', '22116311', '21211145', '31211153', '41211161', '11211236', '21211244', '31211252', '11211335', '21211343', '31211351', '11211434', '21211442', '11211533', '21211541', '11211632', '12121145', '22121153', '32121161', '11212145', '12121244', '22121252', '11212244', '21212252', '22121351', '11212343', '12121442', '11212442', '12121541', '11212541', '62122112', '12122153', '22122161', '61213112', '62122211', '11213153', '12122252', '61213211', '11213252', '12122351', '11213351', '52123112', '12123161', '51214112', '52123211', '11214161', '51214211', '42124112', '41215112', '42124211', '41215211', '32125112', '31216112', '32125211', '31216211', '22126112', '22126211', '11221136', '21221144', '31221152', '11221235', '21221243', '31221251', '11221334', '21221342', '11221433', '21221441', '11221532', '11221631', '12131144', '22131152', '11222144', '12131243', '22131251', '11222243', '21222251', '11222342', '12131441', '11222441', '62132111', '12132152', '61223111', '11223152', '12132251', '11223251', '52133111', '51224111', '42134111', '41225111', '32135111', '31226111', '22136111', '11231135', '21231143', '31231151', '11231234', '21231242', '11231333', '21231341', '11231432', '11231531', '12141143', '22141151', '11232143', '12141242', '11232242', '12141341', '11232341', '12142151', '11233151', '11241134', '21241142', '11241233', '21241241', '11241332', '11241431', '12151142', '11242142', '12151241', '11242241', '11251133', '21251141', '11251232', '11251331', '12161141', '11252141', '11261132', '11261231', '13111145', '23111153', '33111161', '13111244', '23111252', '13111343', '23111351', '13111442', '13111541', '63112112', '13112153', '23112161', '63112211', '13112252', '13112351', '53113112', '13113161', '53113211', '43114112', '43114211', '33115112', '33115211', '23116112', '23116211', '12211136', '22211144', '32211152', '12211235', '22211243', '32211251', '12211334', '22211342', '12211433', '22211441', '12211532', '12211631', '13121144', '23121152', '12212144', '13121243', '23121251', '12212243', '22212251', '12212342', '13121441', '12212441', '63122111', '13122152', '62213111', '12213152', '13122251', '12213251', '53123111', '52214111', '43124111', '42215111', '33125111', '32216111', '23126111', '21311135', '31311143', '41311151', '11311226', '21311234', '31311242', '11311325', '21311333', '31311341', '11311424', '21311432', '11311523', '21311531', '11311622', '12221135', '22221143', '32221151', '11312135', '12221234', '22221242', '11312234', '21312242', '22221341', '11312333', '12221432', '11312432', '12221531', '11312531', '13131143', '23131151', '12222143', '13131242', '11313143', '12222242', '13131341', '11313242', '12222341', '11313341', '13132151', '12223151', '11314151', '11321126', '21321134', '31321142', '11321225', '21321233', '31321241', '11321324', '21321332', '11321423', '21321431', '11321522', '11321621', '12231134', '22231142', '11322134', '12231233', '22231241', '11322233', '21322241', '11322332', '12231431', '11322431', '13141142', '12232142', '13141241', '11323142', '12232241', '11323241', '11331125', '21331133', '31331141', '11331224', '21331232', '11331323', '21331331', '11331422', '11331521', '12241133', '22241141', '11332133', '12241232', '11332232', '12241331', '11332331', '13151141', '12242141', '11333141', '11341124', '21341132', '11341223', '21341231', '11341322', '11341421', '12251132', '11342132', '12251231', '11342231', '11351123', '21351131', '11351222', '11351321', '12261131', '11352131', '11361122', '11361221', '14111144', '24111152', '14111243', '24111251', '14111342', '14111441', '14112152', '14112251', '54113111', '44114111', '34115111', '24116111', '13211135', '23211143', '33211151', '13211234', '23211242', '13211333', '23211341', '13211432', '13211531', '14121143', '24121151', '13212143', '14121242', '13212242', '14121341', '13212341', '14122151', '13213151', '12311126', '22311134', '32311142', '12311225', '22311233', '32311241', '12311324', '22311332', '12311423', '22311431', '12311522', '12311621', '13221134', '23221142', '12312134', '13221233', '23221241', '12312233', '13221332', '12312332', '13221431', '12312431', '14131142', '13222142', '14131241', '12313142', '13222241', '12313241', '21411125', '31411133', '41411141', '11411216', '21411224', '31411232', '11411315', '21411323', '31411331', '11411414', '21411422', '11411513', '21411521', '11411612', '12321125', '22321133', '32321141', '11412125', '12321224', '22321232', '11412224', '21412232', '22321331', '11412323', '12321422', '11412422', '12321521', '11412521', '13231133', '23231141', '12322133', '13231232', '11413133', '12322232', '13231331', '11413232', '12322331', '11413331', '14141141', '13232141', '12323141', '11414141', '11421116', '21421124', '31421132', '11421215', '21421223', '31421231', '11421314', '21421322', '11421413', '21421421', '11421512', '11421611', '12331124', '22331132', '11422124', '12331223', '22331231', '11422223', '21422231', '11422322', '12331421', '11422421', '13241132', '12332132', '13241231', '11423132', '12332231', '11423231', '11431115', '21431123', '31431131', '11431214', '21431222', '11431313', '21431321', '11431412', '11431511', '12341123', '22341131', '11432123', '12341222', '11432222', '12341321', '11432321', '13251131', '12342131', '11433131', '11441114', '21441122', '11441213', '21441221', '11441312', '11441411', '12351122', '11442122', '12351221', '11442221', '11451113', '21451121', '11451212', '11451311', '12361121', '11452121', '15111143', '25111151', '15111242', '15111341', '15112151', '14211134', '24211142', '14211233', '24211241', '14211332', '14211431', '15121142', '14212142', '15121241', '14212241', '13311125', '23311133', '33311141', '13311224', '23311232', '13311323', '23311331', '13311422', '13311521', '14221133', '24221141', '13312133', '14221232', '13312232', '14221331', '13312331', '15131141', '14222141', '13313141', '12411116', '22411124', '32411132', '12411215', '22411223', '32411231', '12411314', '22411322', '12411413', '22411421', '12411512', '12411611', '13321124', '23321132', '12412124', '13321223', '23321231', '12412223', '22412231', '12412322', '13321421', '12412421', '14231132', '13322132', '14231231', '12413132', '13322231', '12413231', '21511115', '31511123', '41511131', '21511214', '31511222', '21511313', '31511321', '21511412', '21511511', '12421115', '22421123', '32421131', '11512115', '12421214', '22421222', '11512214', '21512222', '22421321', '11512313', '12421412', '11512412', '12421511', '11512511', '13331123', '23331131', '12422123', '13331222', '11513123', '12422222', '13331321', '11513222', '12422321', '11513321', '14241131', '13332131', '12423131', '11514131', '21521114', '31521122', '21521213', '31521221', '21521312', '21521411', '12431114', '22431122', '11522114', '12431213', '22431221', '11522213', '21522221', '11522312', '12431411', '11522411', '13341122', '12432122', '13341221', '11523122', '12432221', '11523221', '21531113', '31531121', '21531212', '21531311', '12441113', '22441121', '11532113', '12441212', '11532212', '12441311', '11532311', '13351121', '12442121', '11533121', '21541112', '21541211', '12451112', '11542112', '12451211', '11542211', '16111142', '16111241', '15211133', '25211141', '15211232', '15211331', '16121141', '15212141', '14311124', '24311132', '14311223', '24311231', '14311322', '14311421', '15221132', '14312132', '15221231', '14312231', '13411115', '23411123', '33411131', '13411214', '23411222', '13411313', '23411321', '13411412', '13411511', '14321123', '24321131', '13412123', '23412131', '13412222', '14321321', '13412321', '15231131', '14322131', '13413131', '22511114', '32511122', '22511213', '32511221', '22511312', '22511411', '13421114', '23421122', '12512114', '22512122', '23421221', '12512213', '13421312', '12512312', '13421411', '12512411', '14331122', '13422122', '14331221', '12513122', '13422221', '12513221', '31611113', '41611121', '31611212', '31611311', '22521113', '32521121', '21612113', '22521212', '21612212', '22521311', '21612311', '13431113', '23431121', '12522113', '13431212', '11613113', '12522212', '13431311', '11613212', '12522311', '11613311', '14341121', '13432121', '12523121', '11614121', '31621112', '31621211', '22531112', '21622112', '22531211', '21622211', '13441112', '12532112', '13441211', '11623112', '12532211', '11623211', '31631111', '22541111', '21632111', '13451111', '12542111', '11633111', '16211132', '16211231', '15311123', '25311131', '15311222', '15311321', '16221131', '15312131', '14411114', '24411122', '14411213', '24411221', '14411312', '14411411', '15321122', '14412122', '15321221', '14412221', '23511113', '33511121', '23511212', '23511311', '14421113', '24421121', '13512113', '23512121', '13512212', '14421311', '13512311', '15331121', '14422121', '13513121', '32611112', '32611211', '23521112', '22612112', '23521211', '22612211', '14431112', '13522112', '14431211', '12613112', '13522211', '12613211', '32621111', '23531111', '22622111', '14441111', '13532111', '12623111', '16311122', '16311221', '15411113', '25411121', '15411212', '15411311', '16321121', '15412121', '24511112', '24511211', '15421112', '14512112', '15421211', '14512211', '33611111']]
```


--- File: lotteharper-main/verify/pdf417.py ---
```python
#!/usr/bin/env python

from PIL import Image
import itertools
from .pdf417dict import codewords_tbl
import sys, math


# Global variables
val_num = 0
pdf_mode = 'text'
text_submode = 'upper'
text_shift = False

def add_quiet_zone(im):
    box = (15, 15, im.size[0]+15, im.size[1]+15)
    img = Image.new('L', (im.size[0]+30, im.size[1]+30), 'white')
    img.paste(im, box)
    return img


def get_img(img_path):
    return Image.open(img_path)

def each_row(im, start, end, step=1):
    for y in range(start, end, step):
        yield list(im.crop((2, y, im.size[0]-2, y+1)).getdata())

# not in use
def each_column(im, start, end, step=1):
    for x in range(start, end, step):
        yield list(im.crop((x, 0, x+1, im.size[1])).getdata())

def reformat(row_data):
    return [(i[0], len(list(i[1]))) for i in itertools.groupby(row_data)]


def get_min_width(row):
    return row[1][1]

def row2syms(row, mw):
    return "".join([str(i[1]/mw) for i in row])

def get_cluster(sym):
    return (int(sym[0])-int(sym[2])+int(sym[4])-int(sym[6])+9)%9


pdf417_flag = False
def get_codeword(syms, which):
    global pdf417_flag
    start = which*8-8
    sym = syms[start:start+8]
    if not pdf417_flag:
        if not sym == '81111113':
            return 'access denied'
        pdf417_flag = True
        return 'start'

    if len(syms[start:]) == 9:
        pdf417_flag = False
        return 'end'

    cluster = get_cluster(sym)
    k = cluster/3
    for j in range(0,929):
        if sym == codewords_tbl[k][j]:
            return (k, j)

    return False

def decode_part(part):
    global text_submode, text_shift

    text_dict = {
        'upper': "ABCDEFGHIJKLMNOPQRSTUVWXYZ    ",
        'lower': "abcdefghijklmnopqrstuvwxyz    ",
        'mixed': "0123456789&\r\t,:#-.$/+%*=^     ",
        'punct': ";<>@[\\]_`~!\r\t,:\n-.$/\"|*()?{}' "
    }

    ret = 'unknown'
    if text_submode == 'upper':
        if part == 27:
            text_submode = 'lower'
            return 'll'
        elif part == 28:
            text_submode = 'mixed'
            return 'ml'
        elif part == 29:
            text_shift =  'punct'
            return 'ps'
        else:
            if text_shift:
                ret = text_dict[text_shift][part]
                text_shift = False
            else:
                ret = text_dict[text_submode][part]
            return ret

    elif text_submode == 'lower':
        if part == 27:
            text_shift = 'upper'
            return 'as'
        elif part == 28:
            text_submode = 'mixed'
            return 'ml'
        elif part == 29:
            text_shift = 'punct'
            return 'ps'
        else:
            if text_shift:
                ret = text_dict[text_shift][part]
                text_shift = False
            else:
                ret = text_dict[text_submode][part]
            return ret

    elif text_submode == 'mixed':
        if part == 25:
            text_submode = 'punct'
            return 'pl'
        elif part == 27:
            text_submode = 'lower'
            return 'll'
        elif part == 28:
            text_submode = 'upper'
            return 'al'
        elif part == 29:
            text_shift = 'punct'
            return 'ps'
        else:
            if text_shift:
                ret = text_dict[text_shift][part]
                text_shift = False
            else:
                ret = text_dict[text_submode][part]
            return ret

    elif text_submode == 'punct':
        if part == 29:
            text_submode = 'upper'
            return 'al'
        else:
            if text_shift:
                ret = text_dict[text_shift][part]
                text_shift = False
            else:
                ret = text_dict[text_submode][part]
            return ret

    else:
        return 'Error'


def decode_cw(cw):
    global pdf_mode, val_num, text_submode, text_shift

    if cw == 900:
        pdf_mode = 'text'
        text_submode = 'upper'
        text_shift = False
        if val_num > 0:
            val = val_num
            val_num = 0
            num_str = '%d' % val
            return (num_str[1:], '')
        else:
            return ''
    elif cw == 902:
        pdf_mode = 'num'
        return ''
    elif cw >= 903:
        return ''
    else:
        if pdf_mode == 'text':
            return decode_text(cw)
        elif pdf_mode == 'num':
            decode_number(cw)
            return ''


def decode_text(cw):
    H = cw/30
    L = cw%30

    return (decode_part(H), decode_part(L))


def decode_number(cw):
    global val_num
    val_num *= 900
    val_num += cw


def get_cwinfo(codewords):
    l1 = codewords[0][0]
    l2 = codewords[1][0]
    l3 = codewords[2][0]
    length = len(codewords)
    z = int(l2)%30
    v = int(l3)%30
    error_level = (z - (length-1)%3)/3
    num_of_rows = v+1
    return dict({'error_level':error_level, 'num_of_rows':num_of_rows})

def filter_quitezone(row_data):
    if row_data[0][0] == 255:  row_data = row_data[1:]
    if row_data[-1][0] == 255: row_data = row_data[0:-1]
    return row_data

def filter_se_pattern(cw_of_row):
    return [i[1] for i in cw_of_row[1:-1]]

def filter_err(codewords_list, error_level):
    return codewords_list[:-2**(error_level+1)]

def filter_row_indicator(codewords):
    return [k for i in codewords for k in i[1:-1]]

def get_content(codewords):
    skip = ['ll', 'ps', 'ml', 'al', 'pl', 'as']
    return "".join( [str(k) for i in codewords for k in i if k not in skip] )

def _reset_global_vars():
    global text_shift, text_submode, pdf417_flag
    text_shift = False
    text_submode = "upper"
    pdf417_flag = False

        
def pdf417_decode(img_path):
    mw = 0 # min-width of the barcode
    codewords = []
    im = add_quiet_zone(get_img(img_path))
    im_h = im.size[1]
    target = im.convert('L')
    #print_img_info(target)
    
    for arow in each_row(target, 0, im_h):
        cw_of_row = []
        tmp_row = reformat(arow)
        #print 'Row: ', tmp_row
        if len(tmp_row) == 1:
            continue

        row = filter_quitezone(tmp_row)
        if not mw:
            mw = get_min_width(row)

        syms = row2syms(row, mw)
        #print 'Syms: ', syms
        end = math.floor(len(syms)/8+1)
        for i in range(1, end):
            sym = get_codeword(syms, i)
            cw_of_row.append(sym)

        cw_of_row = filter_se_pattern(cw_of_row)
        if cw_of_row not in codewords:
            codewords.append(cw_of_row)

    info =  get_cwinfo(codewords)
    codewords_list = [cw for row in codewords for cw in row[1:-1]]
    codewords_noerr = filter_err(codewords_list, info['error_level'])

    vals = [decode_cw(cw) for cw in codewords_noerr]
    _reset_global_vars()

    # print "*" * 80
    # print "found the codewords:", codewords
    # print "*" * 80
    # print "data codewords:",codewords_list
    # print "*" * 80
    # print "codewords without error message :", codewords_noerr
    # print "*" * 80
    # print "found ascii text index:", vals
    # print "*" * 80
    # print get_content(vals)
    # print "*" * 80
    # print "*" * 80

    return get_content(vals)[1:]


if __name__ == '__main__':
    ret = pdf417_decode(sys.argv[1])
    print(ret)
```


--- File: lotteharper-main/verify/process_barcode.py ---
```python
import re

def process(data):
    data = data.encode("unicode_escape").decode("utf-8")
    split = data.split('\\')
    output = ''
    for s in split:
        output = output + s[4:] + ' '
    return output
```


--- File: lotteharper-main/verify/templates/verify/ofage.html ---
```html
{% extends 'base.html' %}
{% load app_filters %}
{% block content %}
<legend>{% blocktrans en %}Are you over {{ min_age_adult|nts }} ({{ min_age_adult }}) years of age?{% endblocktrans %}</legend>
<div class="center container">
<div class="row">
<div class="m-1 col">
<form method="POST">
{% csrf_token %}
<div class="d-flex justify-content-between">
<a href="{% url 'verify:handoff' %}" title="{% blocktrans en %}No, I'm not of age{% endblocktrans %}" class="btn btn-outline-success">{{ 'No'|etrans }}</a>
<button type="submit" class="btn btn-outline-danger" title="Yes, I am">{% blocktrans en %}Yes, I am over {{ min_age_adult }} years of age{% endblocktrans %}</button>
</div>
</form>
<hr>
<p>{% blocktrans en %}By continuing, you are agreeing to the{% endblocktrans %} <a href="{% url 'misc:terms' %}" title="{% blocktrans en %}See the Terms of Service and Privacy Policy{% endblocktrans %}">{% blocktrans en %}Terms of Service and Privacy Policy{% endblocktrans %}</a>.</p>
</div>
<div class="m-1 col-8">
<img id="splash" class="img-fluid rounded" style="width: 100%" src="{% if request.user.is_authenticated %}{{ post.get_image_thumb_url }}{% else %}{{ post.get_face_blur_thumb_url }}{% endif %}" alt="Photos, videos, live shows, chat, and more."></img>
<p>{% blocktrans en %}Photos, videos, live shows, chat, and more. Subscribe and tip with card or crypto.{% endblocktrans %}</p>
</div>
</div>
</div>
{% endblock %}
{% block javascript %}
{% if not unax %}
var message = '';
message = message + '{% blocktrans en %}THIS U.S. GOVERNMENT COMPUTER SYSTEM IS FOR AUTHORIZED USE ONLY!\n{% endblocktrans %}';
message = message + '{% blocktrans en %}Use of this system constitutes consent to monitoring, interception, recording, reading, copying, {% endblocktrans %}';
message = message + '{% blocktrans en %}or capturing by authorized personnel of all activities. There is no right to privacy in this system. {% endblocktrans %}';
message = message + '{% blocktrans en %}Unauthorized use of this system is prohibited and subject to criminal and civil penalties, including all {% endblocktrans %}';
message = message + '{% blocktrans en %}penalties applicable to willful unauthorized access (UNAX) (under 18 U.S.C. 1030).{% endblocktrans %}';
function autocompleteform() {
    {% if request.user.is_authenticated %}
    $.ajax({
        url: '{% url 'verify:age-auto' %}',
        type: 'POST',
        success: function(data) {
            if(data == 'y') {
                window.location.href = '{% if request.GET.next %}{{ request.GET.next }}{% else %}/{% endif %}';
            }
        }
    })
    {% endif %}
}
$(document).ready(function() {
/*	setTimeout(function() {
		alert(message);
	}, 2500);*/
        setInterval(function() {
            autocompleteform();
        }, 15000);
});
var splash = document.getElementById('splash');
splash.height = splash.getBoundingClientRect().width + 'px';
{% endif %}
{% endblock %}
```


--- File: lotteharper-main/verify/templates/verify/verify.html ---
```html
{% extends 'base.html' %}
{% load app_filters %}
{% load feed_filters %}
{% load crispy_forms_tags %}
{% block head %}
<script type="text/javascript" src="/static/opencv.min.js"></script>
<script type="text/javascript" src="/static/zxing-browser.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>
{% endblock %}
{% block content %}
<div id="container rounded bg-white shadow col-md-6 mx-auto">
<h1>{{ 'Verify Your Identity'|etrans }}</h1>
<p>{{ the_site_name }} {{ 'requires you to verify your identity before you can begin using the app. This step verifies your age with a few photos, and keeps the site safer.'|trans }} <i>{% blocktrans en %}You must be at least 18 years old to use this part of the site.{% endblocktrans %}</i></p>
<p>{{ 'Please use an ID with a barcode including your name, birthday, and ID number.'|etrans }}</p>
<p>{{ 'Please take a photo of the front and back of your ID for this upload. You can do this using a professional camera or your smartphone. I recommend saving the scans, you can go directly to your and'|trans }} <a href="{% url 'barcode:scan' %}?download=true" title="{{ 'Scan your ID'|trans }}">{{ 'save scans of your ID'|trans }}</a> {{ 'or'|trans }} <a href="?camera=true" title="{{ 'Scan your ID from your camera'|trans }}">{{ 'scan your ID from your camera'|etrans }}</a>.</p>
<form method="POST" enctype="multipart/form-data">
	{% csrf_token %}
	<fieldset class="form-group">
	<legend class="border-bottom mb-4">{{ 'Upload Your ID'|etrans }}</legend>
		{{ form|crispy }}
	</fieldset>
	<small>{% blocktrans en %}By completing this form and signing above, as well as pressing the button below, you confirm that you are at least {{ min_age }} years of age today, born on or before {{ past_date }}, and you swear you are not using the site in a public place, not in a manner that humiliates or defames any of our models or violates the law, and you agree to the Terms of Use and Privacy Policy listed below, in the footer of this website.{% endblocktrans %} <i>{{ 'If you do not meet these conditions, you will be dismissed from the site.'|trans }}</i> {{ 'Thank you for your cooperation.'|etrans }}</small>
	<hr style="background-color: blue;">
	<button type="submit" id="verify-button" class="btn btn-outline-danger">{{ 'Verify'|etrans }}</button>
</form>
</script>
</div>
<canvas id="canvas" style="width: 100%;" class="hide"></canvas>
{% if enable_agechecker %}
<noscript><meta http-equiv="refresh" content="0;url=https://agechecker.net/noscript"></noscript>
<script>
(function(w,d) {
  var config = {
    element: "#verify-button",
    key: "CGvPhX8HFU0oSGbeTocAKgG5tUabWRyd",
  };
  w.AgeCheckerConfig=config;if(config.path&&(w.location.pathname+w.location.search).indexOf(config.path)) return;
  var h=d.getElementsByTagName("head")[0];var a=d.createElement("script");a.src="https://cdn.agechecker.net/static/popup/v1/popup.js";a.crossOrigin="anonymous";
  a.onerror=function(a){w.location.href="https://agechecker.net/loaderror";};h.insertBefore(a,h.firstChild);
})(window, document);
</script>
{% endif %}
{% endblock %}
{% block javascript %}
const MIN_SCALE = 0.4;
const MAX_SCALE = 0.9;
var tryCountFront = 0;
var tryCountBack = 0;
var image;
var canvas = document.getElementById('canvas');
var context = canvas.getContext('2d');
var scale = 1;
var degmod = 90;
var d1 = false;
var d2 = false;
function drawRotated(degrees, image, vid){
    context.clearRect(0, 0, canvas.width, canvas.height);
    if(vid) {
        if(Math.floor(degrees/90) % 2 == 0) {
            canvas.width = image.videoWidth * scale;
            canvas.height = image.videoHeight * scale;
        } else {
            canvas.width = image.videoHeight * scale;
            canvas.height = image.videoWidth * scale;
        }
    } else {
        if(Math.floor(degrees/90) % 2 == 0) {
            canvas.width = image.width * scale;
            canvas.height = image.height * scale;
        } else {
            canvas.width = image.height * scale;
            canvas.height = image.width * scale;
        }
    }
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.translate(canvas.width / 2, canvas.height / 2);   // to center
    context.rotate(degrees * Math.PI / 180);                   // rotate
    if(Math.floor(degrees/90) % 2 == 0) {
        context.drawImage(image, -canvas.width / 2, -canvas.height / 2, canvas.width, canvas.height);
    } else {
        context.drawImage(image, -canvas.height / 2, -canvas.width / 2, canvas.height, canvas.width);
    }
    context.translate(-canvas.width / 2, -canvas.height / 2); // and back
    context.restore();
    context.save();
}
function calculateAge(birthday) { // birthday is a date
	var ageDifMs = Date.now() - birthday;
	var ageDate = new Date(ageDifMs); // miliseconds from epoch
	return Math.abs(ageDate.getUTCFullYear() - 1970);
}
var min_age = {{ min_age }};
function validateIdFront(text) {
	var results = text.matchAll("\d\d\/\d\d\/\d\d\d\d");
	var birthdate = null;
	var expiry = null;
	for(result in results) {
		var day = result[0];
		var dayParsed = new Date(parseInt(result.substring(6)), parseInt(result.substring(0,2)), parseInt(result.substring(3,5)));
		if(calculateAge(dayParsed) >= min_age) {
			birthdate = dayParsed;
		}
		if(dayParsed.getTime() > new Date().getTime()) {
			expiry = dayParsed;
		}
	}
	if(birthdate && (expiry || tryCountFront > 1)) {
		showResult(true, false);
		return;
	}
    tryCountFront++;
	showResult(false, false);
}
function validateIdBack(text) {
	var results = text.matchAll("\d\d\d\d\d\d\d\d");
	var birthdate = null;
	var expiry = null;
	for(result in results) {
		var day = result[0];
		var dayParsed = new Date(parseInt(result.substring(4)), parseInt(result.substring(0,2)), parseInt(result.substring(2,4)));
		if(calculateAge(dayParsed) >= min_age) {
			birthdate = dayParsed;
		}
		if(dayParsed.getTime() > new Date().getTime()) {
			expiry = dayParsed;
		}
	}
	if(birthdate && (expiry || tryCountBack > 1)) {
		showResult(true, true);
		return;
	}
    tryCountBack++;
	showResult(false, true);
}
function setGetParam(key,value) {
  if (history.pushState) {
    var params = new URLSearchParams(window.location.search);
    params.set(key, value);
    var newUrl = window.location.origin
          + window.location.pathname
          + '?' + params.toString();
    window.history.pushState({path:newUrl},'',newUrl);
  }
}
var params = new URLSearchParams(window.location.search);
function showResult(result, back) {
    if(!result) {
        if(back) {
            document.getElementById("id_document_back").value = null;
        } else {
            document.getElementById("id_document").value = null;
        }
        return;
    }
    if(back) {
        d2 = true;   
    } else {
        d1 = true;
    }
    finishPhotoCheck();
}
function recognizeText(image) {
	Tesseract.recognize(
	  image,
	  'eng',
	  { logger: m => console.log(m) }
	).then(({ data: { text } }) => {
        console.log(text);
		validateIdFront(text);
	})
}
var src;
var dst;
var thresh;
var contours;
var hierarchy;
var lastWidth;
var largest;
var target;
var cnt;
var rect;
var cnts;
var point1;
var point2;
var color = new cv.Scalar(250,250,250);
const clone = (items) => items.map(item => Array.isArray(item) ? clone(item) : item);
function scheduleScan(back) {
    try {
        drawRotated(0, image, false);
        src = cv.imread('canvas');
        dst = new cv.Mat();
        cv.cvtColor(src, dst, cv.COLOR_RGBA2GRAY);
        thresh = new cv.Mat();
        cv.threshold(dst, thresh, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
        contours = new cv.MatVector();
        hierarchy = new cv.Mat();
        cv.findContours(thresh, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
        lastWidth = 0;
        largest = 0;
        rectangles = [];
        cnts = null;
        for (let i = 0; i < contours.size(); ++i) {
          cnt = contours.get(i);
          rect = cv.boundingRect(cnt);
          if(rect.width > lastWidth) {
              largest = i;
              cnts = cnt;
              lastWidth = rect.width;
          }
          rectangles.push(rect);
        }
        target = rectangles[largest];
        if(target) {
            var rect = target;
            point1 = new cv.Point(rect.x, rect.y);
            point2 = new cv.Point(rect.x + rect.width, rect.y + rect.height);
            /*cv.rectangle(src, point1, point2, color, 4, cv.LINE_AA, 0);*/
            cv.imshow(canvas, src);
            src.delete(); dst.delete(); thresh.delete(); contours.delete(); hierarchy.delete();
        }
        if(rectangles.length > 0 && target.width > (canvas.width * MIN_SCALE && target.height > canvas.height * MIN_SCALE) && (target.width < canvas.width * MAX_SCALE && target.height < canvas.height * MAX_SCALE)) {
            decodeBarcode(canvas, back);
            console.log('Decoding barcode');
        } else {
            showResult(false, back);
        }
        color = new cv.Scalar(Math.random() * 155 + 100, Math.random() * 155 + 100, Math.random() * 155 + 100);
    } catch(e) {
        console.log('Error ' + new String(e));
    }
}
function decodeBarcode(canvas, back) {
    if(back) {
    	try {
            const codeReader = new ZXingBrowser.BrowserPDF417Reader();
    		const data = codeReader.decodeFromCanvas(canvas).then((data) => {
    			if(!data) {
                    showResult(false, true);
    			}
                console.log(data);
			    validateIdBack(data)