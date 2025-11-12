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
        blog = ''
        links = [None] * posts.count()
        count = 0
        for post in posts:
            text = ''
            title = translate(request, translate(request, 'Buy on', lang, 'en'), lang, 'en')
    #            print(post.content)
    #        for obj in highlightcode(post.content):
    #            text = embedlinks(addhttpstodomains(obj['text'])) + ('<pre class="language-{}"><code>{}</code></pre>'.format(obj['lang'], obj['code']) if ('code' in obj) and ('lang' in obj) else '')
    #            blog = blog + text
            if not post.content_compiled:
                from feed.compile import compile
                compile(post)
                post = Post.objects.get(id=post.id)
            if post.image and not post.image_offsite: post.copy_web(force=force_copy)
            img_url = post.get_image_url() if post.image_offsite else post.get_web_url()
            if not img_url: img_url = post.image_bucket.url if post.image_bucket else post.author.profile.get_image_url()
            blog = ''
            blog = blog + '<img width="100%" height="auto" src="{}" id="img{}" alt="{}"/>'.format(img_url, count, title) if post.image else ''
            blog = blog + '<p>{} / {} | {} | {}</p><hr>\n'.format(translate(request, 'by', lang, 'en') + ' {}'.format(post.author.profile.name), '<a href="/{}'.format(lang) + '/{}" title="{}">{}</a>'.format(post.friendly_name, translate(request, 'View post', lang, 'en'), translate(request, 'View', lang, 'en')), '<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-card', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid), translate(request, 'Buy on', lang, 'en') + ' {}'.format(settings.SITE_NAME), translate(request, 'Buy', lang, 'en')), '<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-crypto', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid) + '&crypto={}'.format(settings.DEFAULT_CRYPTO), translate(request, 'Buy with cryptocurrency on', lang, 'en') + ' {}'.format(settings.SITE_NAME), translate(request, 'Buy with cryptocurrency', lang, 'en')))
            if count%8 == 0:
                blog = blog + render_to_string('banner_ad.html', {'show_ads': True})
                blog = blog + '<hr>'
            links[count] = blog
            count = count + 1
        context['blog'] = blog
        context['links'] = links
        context['path'] = '/{}/{}'.format(lang, 'news')
        context['title'] = translate(request, 'News', lang, 'en')
        news = render_to_string('web/news.html', context)
        with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/news.html'.format(lang)), 'w') as file:
            file.write(news)
        #.union(Post.objects.filter(public=True, private=False, published=True, pinned=True, posted=True, feed='news'))
        for post in [] if False else Post.objects.filter(friendly_name__icontains='three-thirteen'): #Post.objects.filter(public=True, posted=True, published=True, feed="blog").order_by('-date_posted'):
            if post:
                url = '/{}/{}'.format(lang, post.friendly_name)
                context['post'] = post
                context['path'] = url
                context['title'] = translate(request, shorttitle(post.id), lang, 'en')
                context['post_links'] = '<p>{} | {}</p>\n'.format('<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-card', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid), 'Buy on {}'.format(settings.SITE_NAME), translate(request, 'Buy', lang, 'en')), '<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-crypto', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid) + '&crypto={}'.format(settings.DEFAULT_CRYPTO), 'Buy with cryptocurrency on {}'.format(settings.SITE_NAME), translate(request, 'Buy with crypto', lang, 'en')))
                path = os.path.join(settings.BASE_DIR, 'web/site/', '{}/{}.html'.format(lang, post.friendly_name))
                if (not os.path.exists(path)) or overwrite:
                    try:
                        index = render_to_string('web/post.html', context)
                        with open(path, 'w') as file:
                            file.write(index)
                    except:
                        import traceback
                        print(traceback.format_exc())
