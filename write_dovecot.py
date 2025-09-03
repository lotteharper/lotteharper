import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')

import django
django.setup()
from mail.views import write_dovecot_user
from django.contrib.auth.models import User
from django.conf import settings
user = User.objects.get(id=settings.MY_ID)
write_dovecot_user(user, user.profile.email_password)
