overwrite = True
test_mode = False
single_lang = False
force_copy = False
force_overwrite = False
disable_langs = False
end_after_langs = False
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
        'show_social_links': True,
        'twitter_link': settings.TWITTER_LINK,
        'instagram_link': settings.INSTAGRAM_LINK,
        'youtube_link': settings.YOUTUBE_LINK,
        'hiderrm': True,
    }
    for lang in langs if not disable_langs else []:
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
        for post in Post.objects.filter(uploaded=True, public=True, private=False, posted=True, published=True, feed="private").exclude(image_bucket=None).order_by('-date_posted'):
            if post.image and post.image:
                if post.image and not post.image_offsite: post.copy_web(force=force_copy)
                img_url = post.get_image_url() if post.image_offsite else post.get_web_url()
                if not img_url: img_url = post.image_bucket.url if post.image_bucket else post.author.profile.get_image_url
                count = count + 1
                if count < 11:
                    init_images = init_images + '<div id="div{}">{}'.format(count, translate(request, post.content, lang, 'en')) + ('<img width="100%" height="auto" src="{}" id="img{}" alt="{}"/>'.format(img_url, count, translate(request, shorttitle(post.id), lang, 'en')) if post.image else '')
                    init_images = init_images + '<p>{} | {} | {}</p></div><hr>\n'.format('<a href="/{}'.format(lang) + '/{}" title="{}">{}</a>'.format(post.friendly_name, translate(request, 'View Post', lang, 'en') + ' - {} by {}'.format(translate(request, shorttitle(post.id), lang, 'en'), post.author.profile.name), translate(request, 'View', lang, 'en')), '<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-card', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid),  translate(request, 'Buy on', lang, 'en') + ' {}'.format(settings.SITE_NAME), translate(request, 'Buy', lang, 'en')), '<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-crypto', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid) + '&crypto={}'.format(settings.DEFAULT_CRYPTO), translate(request, translate(request, 'Buy with cryptocurrency on', lang, 'en'), lang, 'en') + ' {}'.format(settings.SITE_NAME), translate(request, 'Buy with cryptocurrency', lang, 'en')))
                    if count % 5 == 0:
                        init_images = init_images + render_to_string('banner_ad.html', {'show_ads': True}) + '<hr>'
                else:
                    images = images + '<div id="div{}">{}'.format(count, translate(request, post.content, lang, 'en')) + ('<img width="100%" height="auto" src="{}" id="img{}" alt="{}"/>'.format(img_url, count, shorttitle(post.id)) if post.image else '')
                    images = images + '<p>{} | {} | {}</p></div><hr>\n'.format('<a href="/{}'.format(lang) + '/{}" title="{}">{}</a>'.format(post.friendly_name, 'View Post - {} by {}'.format(shorttitle(post.id), post.author.profile.name), translate(request, 'View', lang, 'en')), '<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-card', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid), translate(request, 'Buy on', lang, 'en') + ' {}'.format(settings.SITE_NAME), translate(request, 'Buy', lang, 'en')), '<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-crypto', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid) + '&crypto={}'.format(settings.DEFAULT_CRYPTO), 'Buy with cryptocurrency on {}'.format(settings.SITE_NAME), translate(request, 'Buy with cryptocurrency', lang, 'en')))
        context['images'] = images
        context['init_images'] = init_images
        blog = ''
        count = 0
        context['path'] = '/{}/{}'.format(lang, '')
        context['title'] = translate(request, 'My Photos', lang, 'en')
        index = render_to_string('web/index.html', context)
        with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/index.html'.format(lang)), 'w') as file:
            file.write(index)
