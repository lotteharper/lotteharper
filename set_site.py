import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from django.conf import settings
from django.contrib.sites.models import Site
Site.objects.update_or_create(pk=1, defaults={'domain': settings.DOMAIN, 'name': settings.SITE_NAME})

