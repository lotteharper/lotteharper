import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

target = sys.argv[len(sys.argv)-1]
src = sys.argv[2] if len(sys.argv) == 4 else 'en'
print(f"Translating from {src} to {target}")

from translate.translate import translate_html
print(translate_html(None, sys.argv[1], src=src, target=target))
