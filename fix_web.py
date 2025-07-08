import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from translate.languages import SELECTOR_LANGUAGES
for lang in list(SELECTOR_LANGUAGES):
    cmd = "sed -i 's/class=\"nav-link\"\ href=\"{}\/links\"/class=\"nav-link\"\ href=\"\/{}\/links\"/g' /home/team/lotteh/web/site/{}/*".format(lang, lang, lang)
    print(cmd)
    os.system(cmd)
