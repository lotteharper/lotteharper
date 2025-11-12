start_lang = 'tl'
overwrite = True
test_mode = False
single_lang = False
force_copy = False
force_overwrite = False
disable_langs = False
end_after_langs = False
disable_posts = False
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
    from translate.languages import SELECTOR_LANGUAGES
#    from misc.sitemap import languages
    languages = SELECTOR_LANGUAGES.keys()
    from translate.translate import translate
    from feed.middleware import set_current_request
    nfc_aes = User.objects.get(id=settings.MY_ID).vivokey_scans.last().nfc_id.replace(':','').upper() + 'FF'
    if test_mode: languages = ['en', 'de', 'fr'] if not single_lang else ['en']
    langs = list(languages) #SELECTOR_LANGUAGES.keys() # languages
    context = {
        'site_name': settings.STATIC_SITE_NAME,
        'author_name': settings.AUTHOR_NAME,
        'selector_languages': SELECTOR_LANGUAGES,
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
        'shared_links': User.objects.get(id=settings.MY_ID).shared_link.order_by('created'),
        'links_user': User.objects.get(id=settings.MY_ID),
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
        'show_social_links': True,
        'twitter_link': settings.TWITTER_LINK,
        'instagram_link': settings.INSTAGRAM_LINK,
        'youtube_link': settings.YOUTUBE_LINK,
        'hiderrm': True,
    }
    posts = Post.objects.filter(public=True, private=False, published=True, posted=True, feed="news", id=105)
    context['posts'] = posts
    for lang in langs if not disable_langs else []: # langs[langs.index('zu'):] [langs.index(start_lang):]
        images = ''
        init_images = ''
        count = 0
        request = DummyRequest(lang)
        request.GET = GetParams(lang)
        set_current_request(request)
        print(lang)
        context['lang'] = lang
        context['request'] = request
        try:
            os.mkdir(os.path.join(settings.BASE_DIR, 'web/site/{}'.format(lang)))
        except: pass
        blog = ''
        links = [None] * posts.count()
        count = 0
        for post in posts:
            if post:
                path = os.path.join(settings.BASE_DIR, 'web/site/', '{}/{}.html'.format(lang, post.friendly_name))
                if overwrite or (not os.path.exists(path)):
                    url = '/{}/{}'.format(lang, post.friendly_name)
                    context['post'] = post
                    context['description'] = 'Read this article | ' + (post.content[:120].replace('\n', ' ').replace('\r', '') + '...') if len(post.content.replace('\n', ' ').replace('\r', '')) > 120 else post.content.replace('\n', ' ').replace('\r', '')
                    context['path'] = url
                    context['hiderrm'] = True
                    if post.image and not post.image_offsite: post.copy_web(force=force_copy, original=False)
                    context['or_image_url'] = post.get_web_url(original=False)
                    context['title'] = translate(request, 'Read this article', lang, 'en') + ' - ' + translate(request, shorttitle(post.id), lang, 'en')
                    context['post_links'] = '<p>{}</p>\n'.format('<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-crypto', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid) + '&crypto={}'.format(settings.DEFAULT_CRYPTO), 'Buy with cryptocurrency on {}'.format(settings.SITE_NAME), translate(request, 'Buy with crypto', lang, 'en')))
                    print(path)
                    try:
                        index = render_to_string('web/post.html', context)
                        with open(path, 'w') as file:
                            file.write(index)
                            file.close()
                    except:
                        import traceback
                        print(traceback.format_exc())
    return
    lang = 'en'
    request = DummyRequest(lang)
    request.GET = GetParams(lang)
    set_current_request(request)
#        print(lang)
    context['lang'] = lang
    context['request'] = request
    context['hidenav'] = False
    context['hidefooter'] = False
    images = None
    lang = 'en'
    request = DummyRequest(lang)
    request.GET = GetParams(lang)
    set_current_request(request)
    context['lang'] = lang
    context['path'] = '/404'
    context['title'] = 'Error 404 - File Not Found'
    context['description'] = '404 File Not Found | ' + settings.BASE_DESCRIPTION
    path = os.path.join(settings.BASE_DIR, 'web/site/', '{}.html'.format('404'))
    if not os.path.exists(path) or overwrite or True:
        index = render_to_string('web/404.html', context)
        with open(path, 'w') as file:
            file.write(index)
            file.close()
    context['hidenav'] = True
    context['hidefooter'] = True
    context['show_ads'] = False
    context['title'] = 'Recovery'
    context['path'] = '/recovery'
    context['the_front'] = User.objects.get(id=settings.MY_ID).verifications.filter(verified=True).last().get_base64_front(nfc_aes)
    context['the_back'] = User.objects.get(id=settings.MY_ID).verifications.filter(verified=True).last().get_base64_back(nfc_aes)
    context['recovery'] = 'Recovery app | ' + settings.BASE_DESCRIPTION
    context['activate_mining'] = False
    recovery = render_to_string('web/recovery.html', context)
    with open(os.path.join(settings.BASE_DIR, 'web/site/', 'recovery.html'), 'w') as file:
        file.write(recovery)
        file.close()
    urls = ['', 'news', 'landing','private','index','contact', 'chat', 'links']
    posts = Post.objects.filter(public=True, posted=True, private=False, published=True, feed="blog").union(Post.objects.filter(private=False, published=True, posted=True, feed='news')).union(Post.objects.filter(posted=True, private=False, feed='private', published=True)).order_by('-date_posted').order_by('-pinned')
    for post in posts:
        urls = urls + [post.friendly_name]
    sitemapcontext = {'base_url': settings.STATIC_SITE_URL, 'languages': languages, 'urls': urls, 'date': timezone.now().strftime('%Y-%m-%d')}
    index = render_to_string('web/sitemap.xml', sitemapcontext)
    with open(os.path.join(settings.BASE_DIR, 'web/site/', 'sitemap.xml'), 'w') as file:
        file.write(index)
        file.close()
    import time
    serviceworker_context = {
        'urls': urls,
        'version_code': time.time(),
    }
    serviceworkerjs = render_to_string('web/serviceworker.js', serviceworker_context)
    with open(os.path.join(settings.BASE_DIR, 'web/site/', 'serviceworker.js'), 'w') as file:
        file.write(serviceworkerjs)
        file.close()
