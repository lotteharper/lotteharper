print('Use caution when approving logins. Shell access can corrupt the system.')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

import datetime, pytz
from django.conf import settings
from django.utils import timezone
from shell.models import ShellLogin
s = ShellLogin.objects.filter(time__gte=timezone.now() - datetime.timedelta(minutes=5), validated=False).order_by('-time')
op = ''

count = 0

from feed.templatetags.app_filters import getflag

for login in s.order_by('-time'):
    op = op + '#{} At {} with code #{} from {} {} with ip {}'.format(len(s) - count, login.time.astimezone(pytz.timezone(settings.TIME_ZONE)), login.code, login.country, getflag(login.country), login.ip_address) + '\n'
    count+=1

print(op if op else 'No login found.')
