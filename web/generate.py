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
    posts = Post.objects.filter(public=True, posted=True, private=False, published=True, feed="blog").union(Post.objects.filter(public=True, private=False, published=True, pinned=True, posted=True, feed='news')).order_by('-date_posted').order_by('-pinned')
    context['posts'] = posts
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
        context['path'] = '/{}/{}'.format(lang, '')
        context['title'] = translate(request, 'My Photos', lang, 'en')
        index = render_to_string('web/index.html', context)
        with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/index.html'.format(lang)), 'w') as file:
            file.write(index)
        context['path'] = '/{}/{}'.format(lang, 'news')
        context['title'] = translate(request, 'News', lang, 'en')
        news = render_to_string('web/news.html', context)
        with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/news.html'.format(lang)), 'w') as file:
            file.write(news)
        context['path'] = '/{}/{}'.format(lang, 'contact')
        context['title'] = translate(request, 'Contact', lang, 'en')
        contact = render_to_string('web/contact.html', context)
        with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/contact.html'.format(lang)), 'w') as file:
            file.write(contact)
        context['path'] = '/{}/{}'.format(lang, 'landing')
        context['title'] = translate(request, 'Landing', lang, 'en')
        landing = render_to_string('web/landing.html', context)
        with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/landing.html'.format(lang)), 'w') as file:
            file.write(landing)
        import urllib.parse
        from security.crypto import encrypt_cbc
        images = ''
        count = 0
        for post in Post.objects.filter(uploaded=True, private=True, posted=True, published=True, feed="private").exclude(image_bucket=None).exclude(image=None).order_by('-date_posted')[:settings.PAID_POSTS * 2]:
            if post.image:
                if post.image: post.copy_web(force=force_copy, original=True, altcode=nfc_aes)
                img_url = post.get_web_url(original=True) # post.get_image_url() if post.image_offsite else
#                if not img_url: img_url = post.image_bucket.url if post.image_bucket else post.author.profile.get_image_url
                count = count + 1
                images = images + '<div id="div{}">{}'.format(count, translate(request, post.content, lang, 'en')) + ('<img class="loadenc" width="100%" height="auto" src="{}" id="img{}" alt="{}"/>'.format(img_url, count, shorttitle(post.id)) if post.image else '')
                images = images + '<p>{} | {}</p></div><hr>\n'.format('<a href="{}/feed/post/{}" title="{}">{}</a>'.format(settings.BASE_URL, post.friendly_name, translate(request, 'View post', lang, 'en') + ' - {} by {}'.format(translate(request, translate(request, 'Buy on', lang, 'en'), lang, 'en'), post.author.profile.name), translate(request, 'View', lang, 'en')), '<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-crypto', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid) + '&crypto={}'.format(settings.DEFAULT_CRYPTO), 'Buy with cryptocurrency on {}'.format(settings.SITE_NAME), translate(request, 'Buy with cryptocurrency', lang, 'en')))
        context['images'] = urllib.parse.quote(encrypt_cbc(images, settings.PRV_AES_KEY))
        context['nfc_images'] = urllib.parse.quote(encrypt_cbc(images, nfc_aes))
        context['path'] = '/{}/{}'.format(lang, 'private')
        context['hiderrm'] = True
        context['title'] = translate(request, 'Private', lang, 'en')
        private = render_to_string('web/private.html', context)
        if (not os.path.exists(os.path.join(settings.BASE_DIR, 'web/site/', '{}/private.html'.format(lang)))) or overwrite: # or force_overwrite:
            with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/private.html'.format(lang)), 'w') as file:
                file.write(private)
        context['footer'] = False # ...None).exclude(image_offsite=None)
        for post in [] if disable_posts else Post.objects.filter(public=True, posted=True, published=True, feed="blog").union(Post.objects.filter(uploaded=True, public=True, posted=True, published=True, feed="private").exclude(image_bucket=None)).union(Post.objects.filter(public=True, private=False, published=True, pinned=True, posted=True, feed='news')).order_by('-date_posted'):
            if post:
                url = '/{}/{}'.format(lang, post.friendly_name)
                context['post'] = post
                context['path'] = url
                context['or_image_url'] = post.get_web_url(original=False)
                if post.feed == 'news': context['hiderrm'] = True
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
        for post in [] if disable_posts else Post.objects.filter(private=True, posted=True, published=True, feed="private").union(Post.objects.filter(uploaded=True, private=True, posted=True, published=True, feed="private").exclude(image_bucket=None)).order_by('-date_posted')[:settings.PAID_POSTS * 2]:
            if post:
                path = os.path.join(settings.BASE_DIR, 'web/site/', '{}/{}.html'.format(lang, post.friendly_name))
                if overwrite or (not os.path.exists(path)):
                    url = '/{}/{}'.format(lang, post.friendly_name)
                    context['post'] = post
                    context['path'] = url
                    context['hiderrm'] = True
                    if post.image and not post.image_offsite: post.copy_web(force=force_copy, original=False)
                    context['or_image_url'] = post.get_web_url(original=False)
                    context['title'] = translate(request, 'Private Photo', lang, 'en') + ' - ' + translate(request, shorttitle(post.id), lang, 'en')
                    context['post_links'] = '<p>{}</p>\n'.format('<a href="{}" title="{}">{}</a>'.format(settings.BASE_URL + reverse('payments:buy-photo-crypto', kwargs={'username': post.author.profile.name}) + '?id={}'.format(post.uuid) + '&crypto={}'.format(settings.DEFAULT_CRYPTO), 'Buy with cryptocurrency on {}'.format(settings.SITE_NAME), translate(request, 'Buy with crypto', lang, 'en')))
                    try:
                        index = render_to_string('web/post.html', context)
                        with open(path, 'w') as file:
                            file.write(index)
                    except:
                        import traceback
                        print(traceback.format_exc())
        context['hiderrm'] = True
        context['title'] = 'Video Chat'
        context['path'] = '/{}/{}'.format(lang, 'chat')
        page = render_to_string('web/chat.html', context)
        with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/chat.html'.format(lang)), 'w') as file:
            file.write(page)
        context['title'] = 'Our Online Experience'
        context['hidenav'] = True
        context['hidefooter'] = True
        context['path'] = '/{}/{}'.format(lang, 'ad')
        ad = render_to_string('web/ad.html', context)
        with open(os.path.join(settings.BASE_DIR, 'web/site/', '{}/ad.html'.format(lang)), 'w') as file:
            file.write(ad)
        images = None
        context['path'] = '/{}/404'.format(lang)
        context['title'] = translate(request, 'Error 404 - File Not Found', lang, 'en')
        context['hidenav'] = False
        context['hidefooter'] = False
        path = os.path.join(settings.BASE_DIR, 'web/site/', '{}/{}.html'.format(lang, '404'))
        if test_mode or not os.path.exists(path) or overwrite:
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
