from face.tests import is_superuser_or_vendor
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import identity_verified

def getbody(message):
    body = None
    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
               for subpart in part.walk():
                    if subpart.get_content_type() == 'text/html':
                        body = subpart.get_payload(decode=True)
            elif part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
    elif message.get_content_type() == 'text/plain':
        body = message.get_payload(decode=True)
    elif message.get_content_type() == 'text/html':
        body = message.get_payload(decode=True)
    return body

def gettextbody(message):
    body = None
    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
               for subpart in part.walk():
                    if subpart.get_content_type() == 'text/plain':
                        body = subpart.get_payload(decode=True)
            elif part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
    elif message.get_content_type() == 'text/plain':
        body = message.get_payload(decode=True)
    elif message.get_content_type() == 'text/html':
        body = message.get_payload(decode=True)
    return body

def get_subject(message):
    from email.header import decode_header
    header = message["subject"]
    if not header:
        return ''
    header, encoding = decode_header(header)[0]
    if encoding is not None:
        try:
            header = header.decode(encoding)
        except:
            header = header.decode('latin-1')
    return header

@login_required
@user_passes_test(is_superuser_or_vendor)
def inbox(request):
    import datetime, os, re, mailbox, pytz
    from django.shortcuts import render, redirect
    from django.urls import reverse
    from django.utils import timezone
    from django.contrib import messages
    from django.conf import settings
    from django.core.paginator import Paginator
    from dateutil.parser import parse
    from django.contrib.auth.models import User
    from mail.models import LastUpdatedMail
    from django.utils.html import strip_tags
    import os
    page = 1
    if(request.GET.get('page', '') != ''):
        page = int(request.GET.get('page', ''))
    a = list(mailbox.mbox('/var/mail/{}'.format(request.user.profile.bash)))
    a.reverse()
    p = Paginator(a, settings.EMAIL_PER_PAGE)
    mails = []
    current = (page-1) * settings.EMAIL_PER_PAGE
    for msg in p.page(page):
        content = gettextbody(msg)
        sender = msg['from']
        excerpt = strip_tags(content.decode("utf-8"))[:400] if content else ''
        mails = mails + [{'id': current, 'sender': sender, 'subject': get_subject(msg), 'excerpt': excerpt, 'time': parse(msg['date']).astimezone(pytz.timezone(settings.TIME_ZONE))}]
        current = current + 1
    return render(request, 'mail/inbox.html', {
        'title': 'Inbox',
        'mails': mails,
        'count': p.count,
        'page_obj': p.get_page(page),
        'current_page': page
    })

@login_required
@user_passes_test(is_superuser_or_vendor)
def message(request, id):
#    from shell.execute import run_command
#    run_command('/bin/sudo chown {}:users {}'.format(settings.BASH_USER, config_dir))
    from django.shortcuts import render
    import datetime, os, re, mailbox, pytz
    from django.utils import timezone
    from dateutil.parser import parse
    from django.conf import settings
    a = list(mailbox.mbox('/var/mail/{}'.format(request.user.profile.bash)))
    a.reverse()
    i = a[int(id)]
    return render(request, 'mail/message.html', {'title': 'Message {}'.format(id), 'subject': get_subject(i), 'content': getbody(i).decode("utf-8"), 'from': i['from'], 'to': i['to'], 'time': parse(i['date']).astimezone(pytz.timezone(settings.TIME_ZONE))})

def notify_user(user, from_email, subject, body):
    from django.conf import settings
    payload = {"head": 'New Mail ({}) - {}'.format(from_email, subject), "body": body[:200] + '' if len(body) <= 200 else '...', "url": settings.BASE_URL + '/mail/message/0/', 'icon': '{}{}'.format(settings.BASE_URL, settings.ICON_URL)}
    from webpush import send_user_notification
    send_user_notification(user=user, payload=payload, ttl=1000)

def update_notify():
    from django.contrib.auth.models import User
    users = User.objects.filter(profile__email_verified=True, is_active=True).exclude(profile__bash='').order_by('-profile__last_seen')
    for user in users:
        update_user(user)

def update_user(user):
    import datetime, os, re, mailbox, pytz
    from .models import LastUpdatedMail
    from django.utils import timezone
    a = list(mailbox.mbox('/var/mail/{}'.format(user.profile.bash)))
    a.reverse()
    updated, created = LastUpdatedMail.objects.get_or_create(user=user)
    if not created and len(a) > updated.count:
        msg = a[0]
        try:
            notify_user(user, msg['from'], get_subject(msg), strip_tags(getbody(msg).decode("utf-8")))
        except: pass
        updated.count = len(a)
        updated.updated = timezone.now()
        updated.save()
    elif created:
        updated.count = len(a)
        updated.updated = timezone.now()
        updated.save()

def get_dovecot(user, password):
    from shell.execute import run_command
    import os, re
    from django.contrib.auth.models import User
    from django.conf import settings
    dove = ''
#    write_user(user)
    hash = os.popen('sudo doveadm pw -s SHA512-CRYPT -p {} -u {}'.format(password, user.profile.bash)).read()
    dove = dove + user.profile.bash + ':' + '{}\n'.format(hash)
    return dove


def write_dovecot_user(user, password):
    import os
    from django.conf import settings
    from shell.execute import run_command
    bash = user.profile.bash
    config_dir = str(os.path.join(settings.BASE_DIR, 'config/etc_dovecot_users'))
    run_command('sudo adduser --disabled-password --gecos "" {}'.format(bash))
    run_command('sudo chown {}:users {}'.format(settings.BASH_USER, config_dir))
#    try:
#        user_line = int(os.popen('grep -n "{}:" {}'.format(user.profile.bash, config_dir)).read().split(':')[0])
#    except:
#        user_line = 0
    config = os.popen('cat {}'.format(config_dir)).read()
    user_line = 1 if '{}:'.format(user.profile.bash) in config else 0
#    print(user_line)
    op = '\n'
    if user_line < 1:
        op = op + get_dovecot(user, password)
    for line in config.split('\n'):
        if line.startswith(user.profile.bash):
            op = op + get_dovecot(user, password)
        else: op = op + ((line + '\n') if line != '' else '')
    with open(os.path.join(settings.BASE_DIR, 'config/etc_dovecot_users'), 'w') as file:
        file.write(op)
        file.close()
    run_command('sudo cp {} /etc/dovecot/users'.format(config_dir))
    run_command('sudo chown root:root /etc/dovecot/users')
