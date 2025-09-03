overwrite = False
test_mode = False
single_lang = False
force_copy = False
force_overwrite = False
disable_langs = False
end_after_langs = True
PRIV_POSTS = 24
import os, pytz
from datetime import datetime
from feed.models import Post
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from contact.forms import ContactForm
from django.utils import timezone
from feed.templatetags.app_filters import shorttitle
from django.urls import reverse

class GetParams():
    lang = None
    def __init__(self, lang, *args, **kwargs):
        self.lang = lang

    def get(self, param, other=False):
        return self.lang

class DummyUser():
    is_authenticated = False

class DummyRequest():
    GET = None
    LANGUAGE_CODE = None
    user = None
    def __init__(self, lang, *args, **kwargs):
        self.GET = GetParams(lang)
        self.LANGUAGE_CODE = lang
        self.user = DummyUser()

def generate_site():
    global overwrite
    global priv_posts
    from feed.templatetags.app_filters import embedlinks, addhttpstodomains, highlightcode
    from misc.sitemap import languages
    from translate.translate import translate
    from feed.middleware import set_current_request
    nfc_aes = User.objects.get(id=settings.MY_ID).vivokey_scans.last().nfc_id.replace(':','').upper() + 'FF'
    if test_mode: languages = ['en', 'de', 'fr'] if not single_lang else ['en']
    langs = languages
    context = {
        'site_name': settings.STATIC_SITE_NAME,
        'the_site_name': settings.STATIC_SITE_NAME,
        'static_url': settings.STATIC_SITE_URL,
        'site_url': settings.BASE_URL,
        'description': settings.BASE_DESCRIPTION,
        'base_url': settings.STATIC_SITE_URL,
        'add_url': settings.ADD_URL,
        'author_name': settings.AUTHOR_NAME,
        'activate_mining': settings.ACTIVATE_MINING,
        'model_name': User.objects.get(id=settings.MY_ID).profile.name,
        'model': User.objects.get(id=settings.MY_ID),
        'my_profile': User.objects.get(id=settings.MY_ID).profile,
        'typical_response_time': settings.TYPICAL_RESPONSE_TIME_HOURS,
        'contact_form': ContactForm(),
        'github_url': settings.GITHUB_URL,
        'base_domain': settings.DOMAIN,
        'base_description': settings.BASE_DESCRIPTION,
        'clock_color': '#ffcccb',
        'year': timezone.now().strftime('%Y'),
        'show_ads': True,
        'path': '/',
        'request': {},
        'footer': True,
        'btc_wallet': settings.BITCOIN_WALLET,
        'polling_now': timezone.now() < datetime(2024, 11, 6).replace(tzinfo=pytz.timezone(settings.TIME_ZONE)),
        'default_vibration': settings.DEFAULT_VIBRATION,
        'rel_aes_key': settings.REL_AES_KEY,
        'monero_address': settings.MONERO_ADDRESS,
        'the_ad_text': settings.AD_TEXT,
        'languages': languages,
    }
    posts = Post.objects.filter(public=True, posted=True, private=False, published=True, feed="blog").union(Post.objects.filter(public=True, private=False, published=True, pinned=True, posted=True, feed='news')).order_by('-date_posted').order_by('-pinned')
    context['posts'] = posts
    for lang in langs if not disable_langs else []:
        images = ''
        init_images = ''
        count = 0
        request = DummyRequest(lang)
        request.GET = GetParams(lang)
        set_current_request(request)
#        print(lang)
        context['lang'] = lang
        context['request'] = request
        try:
            os.mkdir(os.path.join(settings.BASE_DIR, 'web/site/{}'.format(lang)))
        except: pass
        images = None
        context['path'] = '/{}/{}'.format(lang, 'landing')
        context['title'] = translate(request, 'Landing', lang, 'en')
        landing = render_to_string('web/landing.html', context)
        with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/landing.html'.format(lang)), 'w') as file:
            file.write(landing)
        if True: continue
        context['path'] = '/{}/404'.format(lang)
        context['title'] = translate(request, 'Error 404 - File Not Found', lang, 'en')
        context['hiderrm'] = True
        context['hidenav'] = False
        context['hidefooter'] = False
        path = os.path.join(settings.BASE_DIR, 'web/site/', '{}/{}.html'.format(lang, '404'))
        if test_mode or not os.path.exists(path) or overwrite or True:
            index = render_to_string('web/404.html', context)
            with open(path, 'w') as file:
                file.write(index)
    if end_after_langs: return
    lang = 'en'
    request = DummyRequest(lang)
    request.GET = GetParams(lang)
    set_current_request(request)
#        print(lang)
    context['lang'] = lang
    context['request'] = request
    context['hidenav'] = False
    context['hidefooter'] = False
    urls = ['', 'news', 'landing','private','index','contact']
    images = None
    lang = 'en'
    request = DummyRequest(lang)
    request.GET = GetParams(lang)
    set_current_request(request)
    context['lang'] = lang
    context['path'] = '/404'
    context['title'] = 'Error 404 - File Not Found'
    context['hiderrm'] = True
    path = os.path.join(settings.BASE_DIR, 'web/site/', '{}.html'.format('404'))
    if not os.path.exists(path) or overwrite or True:
        index = render_to_string('web/404.html', context)
        with open(path, 'w') as file:
            file.write(index)
    context['hidenav'] = True
    context['hidefooter'] = True
    context['show_ads'] = False
    context['title'] = 'Recovery'
    context['path'] = '/recovery'
    context['the_front'] = User.objects.get(id=settings.MY_ID).verifications.filter(verified=True).last().get_base64_front(nfc_aes)
    context['the_back'] = User.objects.get(id=settings.MY_ID).verifications.filter(verified=True).last().get_base64_back(nfc_aes)
    context['activate_mining'] = False
    recovery = render_to_string('web/recovery.html', context)
    with open(os.path.join(settings.BASE_DIR, 'web/site/', 'recovery.html'), 'w') as file:
        file.write(recovery)
    for post in context['posts']:
        urls = urls + [post.friendly_name]
    sitemapcontext = {'base_url': settings.STATIC_SITE_URL, 'languages': languages, 'urls': urls, 'date': timezone.now().strftime('%Y-%m-%d')}
    index = render_to_string('web/sitemap.xml', sitemapcontext)
    with open(os.path.join(settings.BASE_DIR, 'web/site/', 'sitemap.xml'), 'w') as file:
        file.write(index)
