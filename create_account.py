import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
u = User.objects.create_user(email=sys.argv[1], username=sys.argv[2], password=sys.argv[3])
print(u)
