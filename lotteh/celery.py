from __future__ import absolute_import
from django.conf import settings
from celery import Celery
import os
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
app = Celery('lotteh')
import django
django.setup()
# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
from celery.schedules import crontab

from django.contrib.auth.models import User

me = None
try:
    me = User.objects.get(id=settings.MY_ID) if User.objects.count() > 1 else None
except: pass

import asyncio
from celery import shared_task

@shared_task
def do_async_stuff():
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(async_func())
    loop.close()
    return result

@app.task
def delete_recording_video_file(recording_id):
    from live.models import VideoRecording
    recording = VideoRecording.objects.filter(id=recording_id).first()
    if recording:
        try:
            os.remove(recording.file.path)
        except: pass
        try:
            os.remove(recording.file_processed.path)
        except: pass

#def do_async_stuff():

from asgiref.sync import sync_to_async

@sync_to_async
def reply_message(phone, message, user_id):
    from django.contrib.auth.models import User
    user = User.objects.filter(id=int(user_id)).first() if user_id else None
    preferred_language = user.profile.preferred_language if user else settings.DEFAULT_LANG
    lang = preferred_language
    from voice.ai import get_ai_response
    response = get_ai_response(message, lang)
    from users.tfa import send_text
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(send_text(phone, response))
    loop.close()

@shared_task
def reply_message_async(phone, message, user_id):
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(reply_message(phone, message, user_id))
    loop.close()
    return result

#@app.task
#def reply_message_async(phone, message, user_id):

@app.task
def update_video_description(user_id, recording_id, video_id, thumbnail_url, original_description, original_title, original_category_id, prompt):
    from live.process import update_video_description
    update_video_description(user_id, recording_id, video_id, thumbnail_url, original_description, original_title, original_category_id, prompt)

@app.task
def async_check_upload(post_id):
    from feed.models import Post
    from feed.upload import check_offsite
    check_offsite(Post.objects.get(id=post_id))

@app.task
def async_get_sun(user_id, user_is_authenticated, ip):
    from feed.sun import get_sun
    get_sun(user_id, user_is_authenticated, ip)

@app.task
def async_user_tasks(user_is_authenticated, user_id, ip, language_code):
    from users.tasks import user_tasks
    user_tasks(user_is_authenticated, user_id, ip, language_code)

@app.task
def async_process_user_request(ip, user_id, session_key, user_is_authenticated, path, content_length, http_referrer, querystring, method, index):
    from security.risk import process_user_request
    process_user_request(ip, user_id, session_key, user_is_authenticated, path, content_length, http_referrer, querystring, method, index)

@app.task
def async_verify_payments():
    from payments.verify import verify_payments
    verify_payments()


@app.task
def async_sessions():
    from security.build import async_build_sessions, delete_old_sessions
    async_build_sessions()
    from django.conf import settings
    delete_old_sessions(minutes=settings.LOGIN_VALID_MINUTES)

@app.task
def update_auctions():
    from feed.auctions import update_auctions
    update_auctions()


@app.task
def automatic_backup():
    from web.generate import generate_site
    from shell.execute import run_command
    generate_site()
    print(run_command('sudo backup'))

@app.task
def upload_post(post_id):
    from feed.models import Post
    self = Post.objects.get(id=post_id)
    self.upload()

@app.task
def write_post_book(post_id):
    from feed.models import Post
    self = Post.objects.get(id=post_id)
    from feed.books import generate_post_book
    self.compile_content()
    self.file = generate_post_book(self)
    self.save()
    towrite = self.file_bucket.storage.open(self.file.path, mode='wb')
    with self.file.open('rb') as file:
        towrite.write(file.read())
    self.file_bucket = self.file.path
    towrite.close()
    self.save()

@app.task
def remove_duplicates(post_id):
    pass

@app.task
def delay_delete_session(id):
    from security.models import SessionDedup
    SessionDedup.objects.get(id=id).delete()

@app.task
def notify_expiry():
    from users.utils import send_expiry_notifications
    send_expiry_notifications()

#@app.task
#def update_dovecot():
#    from mail.views import write_dovecot
#    write_dovecot()

@app.task
def update_file(path, new_text, shell_user):
    from pathlib import Path
    import os
    from shell.execute import run_command
    from shell.models import SavedFile
    status = None
    owner = None
    group = None
    path_exists = os.path.exists(path)
    if path_exists:
        status = os.stat(path)
        path = Path(str(path))
        owner = path.owner()
        group = path.group()
        run_command('sudo chmod a+rw ' + str(path))
    with open(path, 'w') as f:
        f.writelines(new_text)
    if path_exists:
        run_command('sudo chmod a-rw ' + str(path))
        run_command('sudo chown {}:{}'.format(owner, group) + ' ' + str(path))
        run_command('sudo chmod ' + oct(status.st_mode)[-3:] + ' ' + str(path))
    for file in SavedFile.objects.filter(path=str(path), current=True):
        file.current = False
        file.save()
    file = SavedFile.objects.create(user=User.objects.get(id=shell_user), path=str(path), content=new_text, current=True)
    file.save()

@app.task
def async_geolocation(ip_obj, ip):
    from security.geolocation import get_ip_location, get_country
    from security.models import UserIpAddress
    ip_obj = UserIpAddress.objects.filter(id=ip_obj).last()
    ip_obj.latitude, ip_obj.longitude = get_ip_location(ip)
    ip_obj.country = get_country(ip_obj.latitude, ip_obj.longitude)
    ip_obj.save()

@app.task
def remove_if_nude(scan_id):
    from barcode.models import DocumentScan
    scan = DocumentScan.objects.get(id=scan_id)
    from feed.nude import is_nude_fast
    if is_nude_fast(scan.document.path):
        scan.delete()

@app.task
def notify_mail_update():
    from mail.views import update_notify
    update_notify()

@app.task
def send_scheduled_emails():
    from django.utils import timezone
    from retargeting.models import ScheduledEmail
    emails = ScheduledEmail.objects.filter(send_at__lte=timezone.now(), sent=False)
    for email in emails:
        email.send()
        email.sent = True
        email.save()

@app.task
def send_scheduled_user_emails():
    from django.utils import timezone
    from retargeting.models import ScheduledUserEmail
    emails = ScheduledUserEmail.objects.filter(send_at__lte=timezone.now(), sent=False)
    count = 0
    for email in emails:
        count = count + 1
        if count > 3: return
        email.send()
        email.sent = True
        email.save()

@app.task
def send_idscan_emails():
    from barcode.email import send_routine_email
    send_routine_email()

@app.task
def push_notification():
    from notifications.push import routine_push
    routine_push()

@app.task
def process_live(camera_id, frame_id):
    from live.process import process_live
    process_live(camera_id, frame_id)

@app.task
def routine_safe_reload():
    from shell.reload import safe_reload
    safe_reload()

@app.task
def delay_delete_post(id):
    from feed.models import Post
    Post.objects.get(id=id).delete()

@app.task
def delay_remove_frame(id):
    from live.models import VideoFrame
    VideoFrame.objects.get(id=id).delete()

@app.task
def crypto_trading_bots():
    from crypto.models import Bot
    from crypto.bot import run_bot_once
    for bot in Bot.objects.filter(live=True, investment_amount_usd__gt=0):
        try:
            run_bot_once(bot.id)
        except: pass

@app.task
def rekey_cameras():
    from live.models import VideoCamera
    import datetime as dt
    from django.utils import timezone
    for camera in VideoCamera.objects.filter(updated__lte=timezone.now() - dt.timedelta(seconds=60)):
        camera.key = ''
        camera.save()

@app.task
def clear_shell_logins():
    from shell.models import ShellLogin
    import datetime as dt
    from django.utils import timezone
    for login in ShellLogin.objects.all():
        if login.time + dt.timedelta(minutes=10) < timezone.now():
            login.delete()

@app.task
def logout_fraudulent_connections():
    from shell.logout import logout_malicious_users
    logout_malicious_users()

@app.task
def delay_remove(filename):
    import os
    os.remove(filename)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.task
def show_reminder_text():
    from live.models import Show
    from django.utils import timezone
    import datetime
    from users.tfa import send_user_text
    shows = Show.objects.filter(start__lte=timezone.now() + datetime.timedelta(minutes=65), start__gte=timezone.now() - datetime.timedelta(minutes=5))
    for show in shows:
        send_user_text(show.model, 'Remember to log in to your live show with {} starting {}'.format(show.user, show.start.strftime('%m/%d/%Y %H:%M:%S')))
        send_user_text(show.user, 'Remember to log in to your live show with {} starting {}. Here is a link: {}'.format(show.model, show.start.strftime('%m/%d/%Y %H:%M:%S'), settings.BASE_URL + reverse('live:livevideo', kwargs={'username': model.profile.name})))

@app.task
def reload_server():
    import requests
    from django.conf import settings
    op = None
    try:
        op = requests.get(settings.BASE_URL, timeout=15)
    except:
        op = None
    if not op:
        from shell.restart import start_server_safe
        start_server_safe()

@app.task
def pend_id_verification(user_id):
    from django.contrib.auth.models import User
    u = User.objects.get(id=user_id)
    u.profile.identity_verified = True
    u.profile.identity_verifying = False
    u.save()

@app.task
def update_subscriptions():
    pass
#    sub_update()

def send_text(text):
    from django.conf import settings
    from django.contrib.auth.models import User
    from users.tfa import send_user_text
    send_user_text(User.objects.get(id=settings.MY_ID), text)

reminders = ['first','second','third']

@app.task
def process_recording(id):
    from live.process import process_recording
    process_recording(id)

@app.task
def process_recordings(num=None):
    from live.models import VideoRecording, VideoCamera
    import datetime
    from django.utils import timezone
    for recording in VideoRecording.objects.filter(processed=False, last_frame__lte=timezone.now() - datetime.timedelta(seconds=60)).order_by('-last_frame')[:num if num else 3]:
        camera = VideoCamera.objects.filter(user=recording.user, name=recording.camera).order_by('-last_frame').first()
        try:
            process_recording(recording.id)
        except:
            import traceback
            print(traceback.format_exc())

@app.task
def validate_bitcoin_payment(uid, mid, balance, transaction_id, fee, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if not model in user.profile.subscriptions.all() and model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from users.tfa import send_user_text
        send_user_text(model, '{} has sucessfully subscribed to your profile with crypto, {}.'.format(user.profile.name, model.profile.preferred_name))
        user.profile.subscriptions.add(model)
        user.profile.save()
        from payments.models import Subscription
        Subscription.objects.create(user=user, model=model, expire_date = timezone.now() + datetime.timedelta(days=30), fee=fee)

@app.task
def validate_surrogacy_payment(uid, mid, balance, transaction_id, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from users.tfa import send_user_text
        send_user_text(model, '{} has sucessfully paid for a surrogacy plan with crypto, {}.'.format(user.profile.name, model.profile.preferred_name))
        mother = model
        send_user_text(mother, '{} (@{}) has purchased a surrogacy plan with you. Please update them with details.'.format(user.verifications.last().full_name, user.username))
        from payments.surrogacy import save_and_send_agreement
        save_and_send_agreement(mother, user)

@app.task
def validate_photo_payment(uid, mid, balance, transaction_id, post_id, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from feed.models import Post
        p = Post.objects.get(id=post_id)
        if p.recipient == user or user in p.paid_users.all(): return
        if not p.paid_file:
            p.recipient = user
        else:
            p.paid_users.add(user)
            p.save()
        from feed.email import send_photo_email
        if not p.private: send_photo_email(user, p)
        from barcode.tests import minor_document_scanned
        if p.private and minor_document_scanned(user): send_photo_email(user, p)

@app.task
def validate_cart_payment(uid, mid, balance, transaction_id, cart, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from payments.cart import process_cart_purchase
        process_cart_purchase(user, cart, private=True)

@app.task
def validate_invoice_payment(uid, mid, balance, transaction_id, invoice_id, crypto, network):
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    if model.vendor_payments_profile.validate_crypto_transaction(user, balance, transaction_id, crypto, network):
        from payments.invoice import process_invoice
        process_invoice(invoice)

@app.task
def validate_tip_payment(uid, mid, balance, transaction_id, crypto, network):
    from django.conf import settings
    from django.contrib.auth.models import User
    user = User.objects.get(id=uid)
    model = User.objects.get(id=mid)
    import sys
    tip = model.vendor_payments_profile.validate_crypto_transaction(user, 0.01, transaction_id, crypto, network, True)
    if tip:
        print('sending tip email')
        from payments.email import send_tip_email
        send_tip_email(user, model, tip, crypto, network)


@app.task
def remove_secure(path):
    import os
    os.remove(path)

@app.task
def birth_control_reminder_text(uid):
    from django.contrib.auth.models import User
    import pytz
    from django.utils import timezone
    from users.tfa import send_user_text
    from django.conf import settings
    user = User.objects.filter(id=uid).first()
    if user:
        if (not user.birthcontrol_profile.took_birth_control_today()) and user.birthcontrol_profile.send_pill_reminder:
            profile = user.birthcontrol_profile
            if profile.reminders >= len(reminders):
                profile.reminders = 0
                profile.save()
            send_user_text(user, 'It\'s time to take your your {} birth control pill and input notes, {}. This is your {} reminder {}/birthcontrol/take/'.format(timezone.now().strftime("%A"), user.profile.preferred_name, reminders[profile.reminders], settings.BASE_URL))
            profile.reminders = profile.reminders + 1
            profile.save()

@app.task
def birth_control_text(uid):
    from django.contrib.auth.models import User
    import pytz
    from django.utils import timezone
    from users.tfa import send_user_text
    from django.conf import settings
    user = User.objects.filter(id=uid).first()
    if user:
        if not user.birthcontrol_profile.took_birth_control_today() and user.birthcontrol_profile.send_pill_reminder:
            send_user_text(user, 'Make sure to take your {} birth control pill and input notes, {}. {}/birthcontrol/take/'.format(timezone.now().strftime("%A"), user.profile.preferred_name, settings.BASE_URL))

@app.task
def sleep_reminder_text(uid):
    from django.contrib.auth.models import User
    import pytz
    from users.tfa import send_user_text
    from django.conf import settings
    from django.utils import timezone
    user = User.objects.filter(id=uid).first()
    if user:
        pill_reminder_time = user.birthcontrol_profile.reminder_time
        pill_reminder_hour = pill_reminder_time.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%-I%p')
        if user.birthcontrol_profile.send_sleep_reminder:
            send_user_text(user, 'Remember to go to sleep, {}. Sleep is healthy and it\'s already almost midnight. You wake up at {} tomorrow.'.format(user.profile.preferred_name, pill_reminder_hour))

#@app.task
#def logout_sessions():
#    for user in User.objects.all():
#        if user.is_authenticated and user.profile.tfa_expires < timezone.now():
#            logout_user(user)

#@app.task
#def require_ids():
#    for user in User.objects.all().exclude(id=settings.MODERATOR_USER_ID):
#        user.profile.id_front_scanned = False
#        user.profile.id_back_scanned = False
#        user.profile.save()

@app.task
def clear_tokens():
    from django.contrib.auth.models import User
    for user in User.objects.all():
        user.profile.recovery_token = ''
        user.profile.save()

@app.task
def start_server():
    from shell.execute import run_command
    run_command('sudo systemctl start apache2')

@app.task
def system_broadcast_stream_message(user_id, message):
    from django.contrib.auth.models import User
    from stream.models import ChatMessage
    ChatMessage.objects.create(vendor=User.objects.get(id=int(user_id)), message=message, system=True)

celery_beat_schedules = {}

for user in User.objects.filter(birthcontrol_profile__send_pill_reminder=True) if me else []:
    import pytz
    pill_reminder_time = user.birthcontrol_profile.reminder_time.astimezone(pytz.timezone(settings.TIME_ZONE))
    pill_reminder_hours = int(pill_reminder_time.strftime('%-H'))
    prm = int(pill_reminder_time.strftime('%-M'))
    pill_reminder_minutes = ''
    for x in range(3):
        pill_reminder_minutes = pill_reminder_minutes + str((prm + 5 * (x + 1))%60) + ','
    pill_reminder_minutes = pill_reminder_minutes[:-1]
    celery_beat_schedules.update({
        'birth-control-take-pill-reminder-{}'.format(user.id): {
            'task': 'lotteh.celery.birth_control_reminder_text',
            'schedule': crontab(hour=pill_reminder_hours, minute=pill_reminder_minutes),
            'args': (user.id,)
        },
        'birth-control-sleep-reminder-{}'.format(user.id): {
            'task': 'lotteh.celery.sleep_reminder_text',
            'schedule': crontab(hour='0,22,23', minute='0'),
            'args': (user.id,)
        }
    })

# Comprehensive Celery Beat holiday schedule builder
# Usage:
#   from celerybeat_schedule import build_holiday_schedule
#   schedule = build_holiday_schedule(vendors, year=2026, time_hour=9, time_minute=0)
#
# vendors should be an iterable of objects/dicts that expose:
#   vendor.id (int/str) and vendor.profile.name (str)
# or you can pass simple dicts with keys 'id' and 'profile_name' (the helper will normalize).
#
# For movable holidays that require lunar/calendar conversion (Chinese New Year, Diwali, Eid),
# pass a `custom_dates` dict with keys matching the holiday slug and values as (month, day).
# Example:
#   custom_dates = {'chinese_new_year': (2, 10), 'diwali': (10, 24)}
#
# The returned dict is safe to assign to CELERY_BEAT_SCHEDULE or update it.

from datetime import date, timedelta
from calendar import monthrange
from celery.schedules import crontab
from typing import Iterable, Dict, Any, Tuple, Optional

def _normalize_vendors(vendors):
    """Yield normalized vendor dicts with 'id' and 'name'."""
    for v in vendors:
        yield {'id': v.id, 'name': v.profile.name}

# --- Date helper functions ---

def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the date of the nth weekday in a month. weekday: Monday=0 .. Sunday=6"""
    d = date(year, month, 1)
    first_weekday = d.weekday()
    # offset days to the first desired weekday
    offset = (weekday - first_weekday) % 7
    day = 1 + offset + (n - 1) * 7
    if day > monthrange(year, month)[1]:
        raise ValueError("No such weekday occurrence")
    return date(year, month, day)

def last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the date of the last weekday in a month."""
    last_day = monthrange(year, month)[1]
    d = date(year, month, last_day)
    offset = (d.weekday() - weekday) % 7
    return d - timedelta(days=offset)

def easter_date(year: int) -> date:
    """Compute Easter (Gregorian) for given year using Anonymous Gregorian algorithm."""
    # Source: Meeus/Jones/Butcher algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

# --- Holidays definitions ---
# Each entry: slug -> dict with
#   'name': human friendly name
#   'type': 'fixed' or 'nth_weekday' or 'last_weekday' or 'easter' or 'custom'
#   'spec': depending on type:
#       fixed: (month, day)
#       nth_weekday: (month, weekday(int Mon=0..Sun=6), n)
#       last_weekday: (month, weekday)
#       easter: none
#       custom: will be filled from custom_dates mapping

HOLIDAYS = {
    # US Federal and commonly observed
    'new_years_day':        {'name': "New Year's Day", 'type': 'fixed', 'spec': (1, 1)},
    'mlk_day':              {'name': "Martin Luther King Jr. Day", 'type': 'nth_weekday', 'spec': (1, 0, 3)}, # 3rd Mon Jan
    'valentines_day':       {'name': "Valentine's Day", 'type': 'fixed', 'spec': (2, 14)},
    'presidents_day':       {'name': "Presidents' Day", 'type': 'nth_weekday', 'spec': (2, 0, 3)}, # 3rd Mon Feb
    'international_womens_day': {'name': "International Women's Day", 'type': 'fixed', 'spec': (3, 8)},
    'st_patricks_day':      {'name': "St. Patrick's Day", 'type': 'fixed', 'spec': (3, 17)},
    'easter':               {'name': "Easter", 'type': 'easter'},
    'earth_day':            {'name': "Earth Day", 'type': 'fixed', 'spec': (4, 22)},
    'may_day':              {'name': "May Day / Labour Day (many countries)", 'type': 'fixed', 'spec': (5, 1)},
    'memorial_day':         {'name': "Memorial Day", 'type': 'last_weekday', 'spec': (5, 0)}, # last Monday May
    'juneteenth':           {'name': "Juneteenth", 'type': 'fixed', 'spec': (6, 19)},
    'independence_day':     {'name': "Independence Day (US)", 'type': 'fixed', 'spec': (7, 4)},
    'labour_day_us':        {'name': "Labor Day (US)", 'type': 'nth_weekday', 'spec': (9, 0, 1)}, # 1st Mon Sep
    'halloween':            {'name': "Halloween", 'type': 'fixed', 'spec': (10, 31)},
    'columbus_indigenous_day': {'name': "Columbus Day / Indigenous Peoples' Day", 'type': 'nth_weekday', 'spec': (10, 0, 2)}, # 2nd Mon Oct
    'veterans_day':         {'name': "Veterans Day", 'type': 'fixed', 'spec': (11, 11)},
    'thanksgiving':         {'name': "Thanksgiving (US)", 'type': 'nth_weekday', 'spec': (11, 3, 4)}, # 4th Thu Nov (weekday 3)
    'black_friday':         {'name': "Black Friday", 'type': 'relative', 'spec': ('thanksgiving', 1)},
    'christmas':            {'name': "Christmas Day", 'type': 'fixed', 'spec': (12, 25)},
    'boxing_day':           {'name': "Boxing Day", 'type': 'fixed', 'spec': (12, 26)},
    'new_years_eve':        {'name': "New Year's Eve", 'type': 'fixed', 'spec': (12, 31)},

    # Popular world holidays (fixed-date or simple)
    'international_womens_day': {'name': "International Women's Day", 'type': 'fixed', 'spec': (3, 8)},
    'cinco_de_mayo':        {'name': "Cinco de Mayo", 'type': 'fixed', 'spec': (5, 5)},
    'pride_month_start':    {'name': "Pride Month Begins", 'type': 'fixed', 'spec': (6, 1)},
    'bastille_day':         {'name': "Bastille Day (France)", 'type': 'fixed', 'spec': (7, 14)},
    'german_unity_day':     {'name': "German Unity Day", 'type': 'fixed', 'spec': (10, 3)},

    # Placeholders for complex/movable lunar-based holidays — user should provide custom_dates
    'chinese_new_year':     {'name': "Chinese New Year (provide custom date)", 'type': 'custom', 'spec': None},
    'diwali':               {'name': "Diwali (provide custom date)", 'type': 'custom', 'spec': None},
    'eid_al_fitr':          {'name': "Eid al-Fitr (provide custom date)", 'type': 'custom', 'spec': None},
    'hanukkah_start':       {'name': "Hanukkah (provide custom date)", 'type': 'custom', 'spec': None},
}

# --- Messages per holiday ---
DEFAULT_MESSAGES = {
    'new_years_day': "Happy New Year! Wishing you a joyous start to the year — send @{} your first cheer of the year!",
    'mlk_day': "Honoring Martin Luther King Jr. today. Spread love and kindness — send @{} a supportive message during the stream.",
    'valentines_day': "Happy Valentine's Day! Send @{} a valentine right here during my livestream.",
    'presidents_day': "Happy Presidents' Day! Show some love to @{} during today's livestream.",
    'international_womens_day': "Happy International Women's Day! Celebrate strength and kindness — send @{} a message.",
    'st_patricks_day': "Happy St. Patrick's Day! Feeling lucky? Send @{} some green cheer in the chat.",
    'easter': "Happy Easter! Wishing you a joyful day — hop into @{}'s stream and say hello!",
    'earth_day': "Happy Earth Day! Love the planet — send @{} an eco-friendly greeting in stream.",
    'may_day': "Happy May Day! Celebrate spring — send @{} some blooms in the chat.",
    'memorial_day': "This Memorial Day we remember and honor. Share a respectful message with @{} during the stream.",
    'juneteenth': "Happy Juneteenth! Celebrate freedom and community — send @{} a celebratory message.",
    'independence_day': "Happy 4th of July! Fireworks and fun — send @{} your BBQ and fireworks stories!",
    'labour_day_us': "Happy Labor Day! Rest and celebrate — send @{} your appreciation messages today.",
    'halloween': "Happy Halloween! Spooky vibes in chat — send @{} a trick or treat message!",
    'columbus_indigenous_day': "Marking Columbus Day / Indigenous Peoples' Day — reflect and celebrate culture — send @{} a thoughtful message.",
    'veterans_day': "Honoring Veterans today. Send @{} a respectful thank-you message in stream.",
    'thanksgiving': "Happy Thanksgiving! What are you thankful for? Tell @{} in the chat.",
    'black_friday': "Black Friday deals! Share your finds with @{} during the livestream.",
    'christmas': "Merry Christmas! Send @{} your holiday wishes and cheer during the stream.",
    'boxing_day': "Happy Boxing Day! Keep the holiday spirit going — send @{} seasonal greetings.",
    'new_years_eve': "Happy New Year's Eve! Count down with @{} and share your wishes.",
    'cinco_de_mayo': "Happy Cinco de Mayo! Celebrate with @{} and share party vibes in chat.",
    'pride_month_start': "Happy Pride Month! Celebrate love and inclusion — send @{} supportive messages.",
    'bastille_day': "Happy Bastille Day! Celebrate with @{} and enjoy the festivities.",
    'german_unity_day': "Happy German Unity Day! Share unity and joy with @{}.",
    # placeholders for custom ones will be generic:
    'chinese_new_year': "Happy Chinese New Year! Wishing prosperity — send @{} your best wishes.",
    'diwali': "Happy Diwali! Wish @{} light and happiness during the stream.",
    'eid_al_fitr': "Eid Mubarak! Celebrate with @{} and send warm greetings.",
    'hanukkah_start': "Happy Hanukkah! Share light and joy with @{}.",
}

def _compute_holiday_date(slug: str, year: int, custom_dates: Optional[Dict[str, Tuple[int, int]]] = None) -> Optional[date]:
    """Return a date for the given holiday slug and year or None if not computable."""
    info = HOLIDAYS.get(slug)
    if not info:
        return None
    htype = info['type']
    if htype == 'fixed':
        month, day = info['spec']
        return date(year, month, day)
    if htype == 'nth_weekday':
        month, weekday, n = info['spec']
        return nth_weekday(year, month, weekday, n)
    if htype == 'last_weekday':
        month, weekday = info['spec']
        return last_weekday(year, month, weekday)
    if htype == 'easter':
        return easter_date(year)
    if htype == 'custom':
        if custom_dates and slug in custom_dates:
            m, d = custom_dates[slug]
            return date(year, m, d)
        # not provided; skip
        return None
    if htype == 'relative':
        ref_slug, offset_days = info['spec']
        ref_date = _compute_holiday_date(ref_slug, year, custom_dates)
        if ref_date is None:
            return None
        return ref_date + timedelta(days=offset_days)
    return None

def build_holiday_schedule(vendors: Iterable[Any],
                           year: int,
                           time_hour: int = 9,
                           time_minute: int = 0,
                           timezone: Optional[str] = None,
                           custom_dates: Optional[Dict[str, Tuple[int, int]]] = None,
                           messages: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Build a Celery beat schedule dict for the specified vendors and year.
    - vendors: iterable of vendor objects/dicts. Must supply id and profile name.
    - year: the calendar year for which this schedule is generated.
    - time_hour/time_minute: local time for the scheduled messages (crontab fields).
    - timezone: optional timezone name; celery will use CELERY_TIMEZONE if set globally.
    - custom_dates: mapping for complex movable holidays, e.g. {'chinese_new_year': (2,10)}
    - messages: optional mapping to override DEFAULT_MESSAGES
    Returns a dict suitable for CELERY_BEAT_SCHEDULE.
    """
    messages = messages or {}
    merged_messages = DEFAULT_MESSAGES.copy()
    merged_messages.update(messages)

    schedule = {}
    vendors_norm = list(_normalize_vendors(vendors))

    for v in vendors_norm:
        vid = v['id']
        vname = v['name']
        for slug in HOLIDAYS.keys():
            hol_date = _compute_holiday_date(slug, year, custom_dates=custom_dates)
            if hol_date is None:
                # skip holidays we can't compute unless a custom date was provided
                continue

            # special-case Black Friday computed as the day after Thanksgiving
            if slug == 'black_friday':
                # Thanksgiving slug 'thanksgiving' exists
                tg = _compute_holiday_date('thanksgiving', year, custom_dates=custom_dates)
                if tg is None:
                    continue
                hol_date = tg + timedelta(days=1)

            # Build unique schedule name
            sched_name = 'scheduled-system-broadcast-message-{vendor}-{holiday}-{year}'.format(
                vendor=vid, holiday=slug, year=year
            )

            # Build message text, substituting vendor profile name where '{}' appears
            template = merged_messages.get(slug, "Happy {name}! Send @{profile} some love today.")
            try:
                # allow templates that expect a single replacement slot for vendor name
                message = template.format(vname, profile=vname) if '{}' in template else template.format(profile=vname, name=HOLIDAYS[slug]['name'])
            except Exception:
                # fallback: simple replacement for legacy templates using @{}
                message = template.replace('@{}', '@{}'.format(vname)).replace('{}', vname)
            # Ensure message still mentions @profile if original pattern used '@{}'
            if '@' not in message and '{}' in merged_messages.get(slug, ''):
                message = merged_messages.get(slug, '').replace('{}', vname)

            # Create crontab schedule for the exact month and day
            schedule[sched_name] = {
                'task': 'lotteh.celery.system_broadcast_stream_message',
                'schedule': crontab(month_of_year=hol_date.month, day_of_month=hol_date.day, hour=time_hour, minute=time_minute),
                'args': (vid, message)
            }
            # Optionally attach timezone key for clarity (Celery uses CELERY_TIMEZONE global config)
            if timezone:
                schedule[sched_name]['options'] = {'timezone': timezone}

    return schedule

try:
    for vendor in User.objects.filter(profile__vendor=True):
        from django.utils import timezone
        sched = build_holiday_schedule([vendor], year=timezone.now().year, time_hour=9, time_minute=0, timezone=settings.TIME_ZONE)
        celery_beat_schedules.update(sched)
        celery_beat_schedules.update({
            'scheduled-system-broadcast-message-{}'.format(vendor.id): {
                'task': 'lotteh.celery.system_broadcast_stream_message',
                'schedule': crontab(month_of_year=2, day_of_month=14, hour=9, minute=0),
                'args': (vendor.id, 'Happy Valentine\'s Day! Send @{} a valentine right here during my livestream.'.format(vendor.profile.name))
            },
        })
except:
    import traceback
    print(traceback.format_exc())


@app.task
def clear_recordings():
    from live.models import VideoRecording
    from django.utils import timezone
    import datetime as dt
    from django.conf import settings
    recordings = VideoRecording.objects.filter(camera__icontains='*', last_frame__lte=timezone.now() - dt.timedelta(hours=24*settings.RECORDING_EXPIRY_DAYS))
    for recording in recordings:
        recording.delete()

@app.task
def send_admin_text():
    pass
#    admin = User.objects.get(id=settings.ADMIN_ID)
#    send_user_text(admin, '{} is sending you a text to keep your phone active, {}'.format(settings.SITE_NAME, admin.profile.name))
#    call('+12062409036')

@app.task
def hourly_review():
    pass
#    review_server()

@app.task
def sweep_bitcoin_payments():
    pass
#    sweep_all_to_master()

@app.task
def authorize_faces():
    from face.models import Face
    from django.utils import timezone
    import datetime as dt
    faces = Face.objects.filter(timestamp__lte=timezone.now()-dt.timedelta(minutes=30), authorized=False)
    for face in faces:
        face.authorized = True
        face.save()

@app.task
def send_emails():
    from retargeting.email import send_retargeting_emails, send_retargeting_email
    send_retargeting_emails()

@app.task
def send_email():
    from retargeting.email import send_retargeting_emails, send_retargeting_email
    send_retargeting_email()

@app.task
def routine_filter():
    import os
    from feed.models import Post
    post = Post.objects.filter(published=False, moderated=False).exclude(image=None).last()
    if post:
        try:
            from feed.nude import is_nude_fast
            from feed.tests import minor_identity_verified
            if post.image and not os.path.exists(post.image.path) and post.image_bucket: post.download_photo()
            post = Post.objects.get(id=post.id)
            if post.image and os.path.exists(post.image.path) and is_nude_fast(post.image.path):
                post.public = False
                post.secure = True
                if settings.NUDITY_FILTER and not minor_identity_verified(post.author):
                    os.remove(post.image.path)
                    post.image = None
                elif settings.NUDITY_FILTER:
                    post.private = True
                    post.public = False
                post.save()
    #        from security.safety import is_safe_file, is_safe_image
    #        if (post.image and os.path.exists(post.image.path) and not is_safe_image(post.image.path)) or (post.file and os.path.exists(post.file.path) and not is_safe_file(post.file.path)):
    #            post.safe = False
    #            post.secure = False
    #            try:
    #                if post.image: os.remove(post.image.path)
    #            except: pass
    #            try:
    #                if post.file: os.remove(post.file.path)
    #            except: pass
    #            post.private = True
    #            post.save()
            else:
                post.published = True
                post.save()
        except:
            import traceback
            print(traceback.format_exc())
        post.moderated = True
        post.save()
    return

@app.task
def async_risk_detection(ip_id):
    from security.models import UserIpAddress
    from security.apis import check_ip_risk
    ip = UserIpAddress.objects.filter(id=ip_id).last()
    ip.risk_detected = check_ip_risk(ip)
    ip.save()

@app.task
def routine_bucket_posts():
    from feed.models import Post
    from enhance.image import bucket_post
    import os
    for post in Post.objects.filter(published=True, uploaded=False):
        if post.image and os.path.exists(post.image.path):
            bucket_post(post.id)
            return

@app.task
def update_surrogacy_plans():
    from payments.models import SurrogacyPlan
    from django.conf import settings
    import datetime
    from django.conf import timezone
    from dateutil.relativedelta import relativedelta
    for plan in SurrogacyPlan.objects.filter(unpaid__gt=0, timestamp__gte=timezone.now() - relativedelta(weeks=37), completed=False, signed=True).order_by('-timestamp'):
        from payments.invoice import generate_invoice
        price = (settings.SURROGACY_FEE - settings.SURROGACY_DOWN_PAYMENT)/36
        if price > 0:
            generate_invoice(plan.mother, plan.expected_parent, price, 'This invoice is for the remaining balance of your surrogacy plan with {}, which is ${}.'.format(plan.mother.profile.name, str(round(price, 2))))


@app.task
def reset_chat_camera_keys():
    from chat.models import Key
    from django.utils import timezone
    import datetime
    for key in Key.objects.filter(created_at__lte=timezone.now()-datetime.timedelta(days=28)):
        key.delete()

app.conf.beat_schedule = {
    'async-sessions': {
        'task': 'lotteh.celery.async_sessions',
        'schedule': crontab(hour='*', minute='0,15,30,45'),
    },
    'clear-tokens': {
        'task': 'lotteh.celery.clear_tokens',
        'schedule': crontab(hour=0, minute=0),
    },
    'routine-filter': {
        'task': 'lotteh.celery.routine_filter',
        'schedule': crontab(hour='*', minute='*'),
    },
    'clear-recordings': {
        'task': 'lotteh.celery.clear_recordings',
        'schedule': crontab(day_of_month='*', hour=15, minute=0),
    },
    'reset-chat-camera-keys': {
        'task': 'lotteh.celery.reset_chat_camera_keys',
        'schedule': crontab(day_of_month='*', hour=0, minute=0),
    },
    'send-routine-emails': {
        'task': 'lotteh.celery.send_scheduled_emails',
        'schedule': crontab(hour='*', minute='*'),
    },
    'send-routine-engagement-emails': {
        'task': 'lotteh.celery.send_emails',
        'schedule': crontab(day_of_week=5, hour=6, minute=0),
    },
    'send-routine-retargeting-email': {
        'task': 'lotteh.celery.send_email',
        'schedule': crontab(day_of_week=4, hour=6, minute=0),
    },
    'clear-shell-logins': {
        'task': 'lotteh.celery.clear_shell_logins',
        'schedule': crontab(hour='*', minute=0)
    },
    'authorize-old-faces': {
        'task': 'lotteh.celery.authorize_faces',
        'schedule': crontab(hour='*', minute='*/30')
    },
    'rekey-cameras': {
        'task': 'lotteh.celery.rekey_cameras',
        'schedule': crontab(hour='0', minute='0')
    },
}

app.conf.beat_schedule.update(celery_beat_schedules)

app.conf.timezone = 'America/Los_Angeles'
