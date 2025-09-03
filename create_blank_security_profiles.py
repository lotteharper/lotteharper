import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

import datetime
from django.utils import timezone
from django.contrib.auth.models import User

def create_blank():
    for instance in User.objects.all():
        if not hasattr(instance, 'profile'):
            from .models import Profile
            Profile.objects.create(user=instance)
        if not hasattr(instance, 'security_profile'):
            from security.models import SecurityProfile
            SecurityProfile.objects.create(user=instance)


create_blank()
