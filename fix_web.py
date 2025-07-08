import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from translate.languages import SELECTOR_LANGUAGES
for lang in list(SELECTOR_LANGUAGES):
    cmd = "sed -i 's/ca-pub-6209985848112194/ca-pub-8062317950995248/' /home/team/lotteh/web/site/{}/*".format(lang)
    print(cmd)
    os.system(cmd)
