import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from django.conf import settings
from voice.ai import get_ai_response
arguments_string = ' '.join(sys.argv[1:])
if len(arguments_string) > 0:
    print(get_ai_response(arguments_string))
else:
    print('No input supplied.')
