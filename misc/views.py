from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from feed.tests import identity_verified
from vendors.tests import is_vendor
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache, cache_page

@cache_page(60*60*24*30)
def webmanifest(request):
    from django.shortcuts import render
    return render(request, 'misc/site.webmanifest', {})

def map(request):
    from django.shortcuts import render
    from security.models import UserIpAddress, Session
    latlngs = []
    from django.conf import settings
    for ip in UserIpAddress.objects.all():
        if ip.latitude and ip.longitude: latlngs = latlngs + [(ip.latitude, ip.longitude, ip.timestamp.strftime("%m/%d/%Y at %H:%M:%S"), ip.page_loads)];
    return render(request, 'misc/map.html', {'title': 'Visitor Map', 'latlngs': latlngs, 'maps_api_key': settings.GOOGLE_API_KEY})

@cache_page(60*60*24*30)
def adstxt(request):
    from django.shortcuts import render
    return render(request, 'ads.txt')

@cache_page(60*60*24*30)
def service_worker(request):
    from django.http import HttpResponse
    from django.conf import settings
    import os
    sw_path = os.path.join(settings.BASE_DIR, 'templates', 'serviceworker.js')
    try:
        with open(sw_path, 'r') as f:
            sw_js = f.read()
        return HttpResponse(sw_js, content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse("Service worker not found", status=404)

@cache_page(60*60*24*30)
def sitemap(request):
    from .sitemap import languages
    from .sitemap import urls
    from .sitemap import vendor_urls
    from .sitemap import surrogate_urls
    from .sitemap import vendor_feeds
    from django.shortcuts import render
    from feed.models import Post
    from django.contrib.auth.models import User
    from django.conf import settings
    from django.utils import timezone
    surrogate_urls = ['/surrogacy/', '/surrogacy/checkout/']
    return render(request, 'misc/sitemap.xml', {'posts': Post.objects.filter(public=True, private=False, published=True).exclude(content=''), 'vendors': User.objects.filter(profile__vendor=True, is_active=True), 'surrogates': User.objects.filter(profile__vendor=True, is_active=True, vendor_profile__activate_surrogacy=True), 'vendor_urls': vendor_urls, 'urls': urls, 'surrogate_urls': surrogate_urls, 'vendor_feeds': vendor_feeds, 'languages': languages, 'base_url': settings.BASE_URL, 'date': timezone.now().strftime('%Y-%m-%d')}, content_type='application/xml')

@cache_page(60*60*24)
def news(request):
    from .sitemap import languages
    languages = ['en']
    from django.contrib.auth.models import User
    from django.shortcuts import render
    return render(request, 'misc/news.xml', {'profiles': User.objects.filter(is_active=True, profile__vendor=True), 'surrogates': User.objects.filter(is_active=True, profile__vendor=True, vendor_profile__activate_surrogacy=True), 'posts': Post.objects.filter(public=True, private=False, published=True).exclude(content=''), 'languages': languages, 'base_url': settings.BASE_URL, 'date': timezone.now().strftime('%Y-%m-%d')}, content_type='application/xml')

@cache_page(60*60*24*30*3)
def idscan(request):
    from django.shortcuts import render
    return render(request, 'misc/idscan.html')

@cache_page(60*60*24*30*3)
def ad(request):
    from django.shortcuts import render
    return render(request, 'ad_frame.html', {'hidenavbar': True, 'load_timeout': 0})

@cache_page(60*60*24*30*3)
def verify(request):
    from django.http import HttpResponse
    return HttpResponse('f7fcf64bfb499980d251f6ffb6676460')

def current_time(now):
    from feed.templatetags.app_filters import nts, stime, ampm
    resp = '{} {}'.format(stime(now).capitalize(), ampm(now))
    return resp

def time(request):
    resp = current_time()
    from django.http import HttpResponse
    return HttpResponse(resp)

@csrf_exempt
def authenticated(request):
    from django.http import HttpResponse
    return HttpResponse('y' if request.user.is_authenticated else 'n')

@cache_page(60*60*24*30)
def terms(request):
    from django.shortcuts import render
    from django.conf import settings
    return render(request, 'misc/terms.html', {
        'title': 'Terms and Conditions',
        'city_state': settings.CITY_STATE,
        'address': settings.ADDRESS,
        'phone_number': settings.PHONE_NUMBER,
        'email_address': settings.EMAIL_ADDRESS,
        'agent_name': settings.AGENT_NAME,
    })

def privacy(request):
    from django.shortcuts import render
    return render(request, 'misc/privacy.html', {'title': 'Privacy'})

def get_posts_for_query(request, qs):
    import regex
    from django.utils import timezone
    from feed.models import Post
    from django.conf import settings
    now = timezone.now()
    try:
        now = datetime.datetime.fromtimestamp(int(request.GET.get('time')) / 1000)
    except: pass
    from autocorrect import Speller
    from translate.translate import translate
    from misc.regex import SEARCH_REGEX
    from misc.regex import ESCAPED_QUERIES
#    spell = Speller()
#    qs = spell(qs)
    qs = translate(request, qs, target=settings.DEFAULT_LANG)
    qsplit = qs.split(' ')
    posts = Post.objects.filter(content__icontains=qs.lower(), private=False, published=True, date_posted__lte=now)
    for q in qsplit:
        posts = posts.union(Post.objects.filter(content__icontains=q.lower(), private=False, published=True, date_posted__lte=now))
    posts = posts.order_by('-date_posted')
    pos = []
    for post in posts:
        count = 0
        matches = regex.findall(SEARCH_REGEX.format(qs.lower()), post.content.lower(), flags=regex.IGNORECASE)
        count = count + len(matches) * len(qsplit)
        for q in qsplit:
            matches = regex.findall(SEARCH_REGEX.format(q.lower()), post.content.lower(), flags=regex.IGNORECASE) # | regex.BESTMATCH)
            for match in matches:
                if not match in ESCAPED_QUERIES:
                    count = count + 1
        if count > 0:
            pos = pos + [(post.id, count)]
    pos = sorted(pos, key = lambda x: x[1], reverse=True)
    posts = []
    for post, count in pos:
        post = Post.objects.get(id=post)
        posts = posts + ([post] if (not post.private) or request.user.is_authenticated and post.author in request.user.profile.subscriptions.all() or request.user.is_authenticated and request.user.profile.vendor else [])
    return posts



def get_posts_for_multilingual_query(request, qs):
    from django.utils import timezone
    from feed.models import Post
    from django.conf import settings
    now = timezone.now()
    try:
        now = datetime.datetime.fromtimestamp(int(request.GET.get('time')) / 1000)
    except: pass
    from autocorrect import Speller
    from translate.translate import translate
    import regex
    from misc.regex import SEARCH_REGEX
    from misc.regex import ESCAPED_QUERIES
    from misc.sitemap import languages
    posts = []
    count = 0
    results = [None] * (len(languages) + 1)
    last_threads = []
    threads = [None] * (len(languages) + 1)
    thread_count = 0
    def get_posts_for_query_lang(qs, lang, results, res_count, src):
        pos = []
        from translate.translate import translate
        from feed.models import Post
        import regex
        from misc.regex import SEARCH_REGEX
        from misc.regex import ESCAPED_QUERIES
        from django.conf import settings
        if src != lang:
            qs = translate(None, qs, target=lang, src=settings.DEFAULT_LANG if not src else src)
        qsplit = qs.split(' ')
        from django.utils import timezone
        now = timezone.now()
        try:
            now = datetime.datetime.fromtimestamp(int(request.GET.get('time')) / 1000)
        except: pass
        psts = Post.objects.filter(content__icontains=qs.lower(), private=False, published=True, date_posted__lte=now)
        for q in qsplit:
            psts = psts.union(Post.objects.filter(content__icontains=q.lower(), private=False, published=True, date_posted__lte=now))
        psts = psts.order_by('-date_posted')
        for post in psts:
            count = 0
            matches = regex.findall(SEARCH_REGEX.format(qs.lower()), post.content.lower(), flags=regex.IGNORECASE | regex.BESTMATCH)
            count = count + len(matches) * len(qsplit)
            for q in qsplit:
                matches = regex.findall(SEARCH_REGEX.format(q.lower()), post.content.lower(), flags=regex.IGNORECASE | regex.BESTMATCH)
                for match in matches:
                    if not match in ESCAPED_QUERIES:
                        count = count + 1
            if count > 0:
                pos = pos + [(post.id, count)]
        results[res_count] = pos
    oqs = qs
    qs = translate(request, qs, target=settings.DEFAULT_LANG)
    print('QS is ' + qs)
    print('OQS is ' + oqs)
    import threading
    src = request.LANGUAGE_CODE if request and not request.GET.get('lang', None) else request.GET.get('lang', None) if request.GET.get('lang', None) else settings.DEFAULT_LANG
    threads[thread_count] = threading.Thread(target=get_posts_for_query_lang, args=(qs, settings.DEFAULT_LANG, results, thread_count, settings.DEFAULT_LANG))
    threads[thread_count].start()
    thread_count = thread_count + 1
    for lang in languages:
        threads[thread_count] = threading.Thread(target=get_posts_for_query_lang, args=(oqs, lang, results, thread_count, src))
        threads[thread_count].start()
        thread_count = thread_count + 1
    for i in range(len(threads)):
        if threads[i]: threads[i].join()
    for pos in results:
        if pos:
            pos = sorted(pos, key = lambda x: x[1], reverse=True)
            for post, count in pos:
                post = Post.objects.filter(id=post).first()
                ex = False
                for p in posts:
                    if p.id == post.id:
                        ex = True
                if (not ex) and (post and (not post.private) or request.user.is_authenticated and post.author in request.user.profile.subscriptions.all() or (request.user.is_authenticated and request.user.profile.vendor)):
                    posts = posts + [post]
    return posts

#@login_required
#@user_passes_test(identity_verified, login_url='/verify/', redirect_field_name='next')
@cache_page(60*60*24*30)
def search(request):
    from django.conf import settings
    from django.contrib import messages
    from django.core.paginator import Paginator
    page = 1
    if(request.GET.get('page', None) != None):
        page = int(request.GET.get('page'))
    qs = request.GET.get('q',None)
    if not qs:
        messages.warning(request, "Please enter a valid querystring to search {}".format(settings.SITE_NAME))
        qs = ''
    posts = get_posts_for_multilingual_query(request, qs) if settings.MULTILINGUAL_SEARCH else get_posts_for_query(request, qs)
    p = Paginator(posts, 10)
    if page > p.num_pages or page < 1:
        messages.warning(request, "The page you requested, " + str(page) + ", does not exist. You have been redirected to the first page.")
        page = 1
    template_name = 'misc/search.html'
    if request.GET.get('grid'):
        template_name = 'feed/profile_grid.html'
    from django.shortcuts import render
    return render(request, template_name, {
        'title': 'Search {}'.format(settings.SITE_NAME),
        'posts': p.page(page),
        'count': p.count,
        'page_obj': p.get_page(page),
        'query': request.GET.get('q', None),
        'full': request.GET.get('grid'),
    })

@cache_page(60*60*24*30*3)
def robotstxt(request):
    from django.shortcuts import render
    return render(request, 'robots.txt')
