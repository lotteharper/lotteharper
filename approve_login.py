print('Use caution when approving logins. Shell access can corrupt the system.')
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

import datetime
from django.utils import timezone
from shell.models import ShellLogin
s = ShellLogin.objects.filter(time__gte=timezone.now() - datetime.timedelta(minutes=5), validated=False).order_by('time')
if len(sys.argv) > 1:
    login = int(sys.argv[1])-1
    if s.count() > 0 and s.count() > login and login >= 0:
        s = s[login]
        s.validated = True
        s.approved = True
        s.save()
        print('Login approved')
    else:
        print('No login found')
else:
    print('No login found.')
