import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from django.conf import settings
os.system('DJANGO_SUPERUSER_PASSWORD={} {}/manage.py createsuperuser --no-input --username={} --email={}'.format(sys.argv[3], str(settings.BASE_DIR), sys.argv[1], sys.argv[2]))
