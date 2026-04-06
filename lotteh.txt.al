nforce any right or provision of these Terms of Use shall not operate as a waiver of such right or provision. These Terms of Use operate to the fullest extent permissible by law. We may assign any or all of our rights and obligations to others at any time. We shall not be responsible or liable for any loss, damage, delay, or failure to act caused by any cause beyond our reasonable control. If any provision or part of a provision of these Terms of Use is determined to be unlawful, void, or unenforceable, that provision or part of the provision is deemed severable from these Terms of Use and does not affect the validity and enforceability of any remaining provisions. There is no joint venture, partnership, employment or agency relationship created between you and us as a result of these Terms of Use or use of the Site. You agree that these Terms of Use will not be construed against us by virtue of having drafted them. You hereby waive any and all defenses you may have based on the electronic form of these Terms of Use and the lack of signing by the parties hereto to execute these Terms of Use.

25. RETURN AND REFUND POLICY

Products, services, goods, and other purchases made on this site may not be returned. No refunds may be issued for subscriptions or purchases with us on {{ the_site_name }}. {{ the_site_name }} reserves the right to refuse any refund of payment made with us on this website or otherwise.

26. CONTACT US

In order to resolve a complaint regarding the Site or to receive further information regarding use of the Site, please contact us at:
</div>
{% endblocktrans %}

<div style="white-space: pre-wrap;">
{{ site_name }}
ATTN: {{ agent_name }}
{{ address }}
Phone: {{ phone_number }} {% blocktrans en %}(press option 6 for information, or use the menu to call me){% endblocktrans %}
{{ email_address }}
</div>
{% endblock %}
```


--- File: lotteharper-main/misc/tests.py ---
```python
```


--- File: lotteharper-main/misc/urls.py ---
```python
from django.urls import path

from . import views

app_name='misc'

urlpatterns = [
    path('search/', views.search, name='search'),
    path('terms/', views.terms, name='terms'),
    path('auth/', views.authenticated, name='auth'),
    path('logo/', views.logo, name='logo'),
    path('time/', views.time, name='time'),
    path('ad/', views.ad, name='ad'),
    path('ads.txt', views.adstxt, name='adstxt'),
    path('robots.txt', views.robotstxt, name='robotstxt'),
    path('idscan/', views.idscan, name='idscan'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
    path('news.xml', views.news, name='news'),
    path('map/', views.map, name='map'),
    path('opendkimkey/', views.opendkimkey, name='opendkimkey'),
    path('publickeys/', views.publickeys, name='publickeys'),
    path('upload/', views.upload_video_api, name='upload'),
    path('site.webmanifest', views.webmanifest, name='webmanifest'),
    path('serviceworker.js', views.service_worker, name='serviceworker'),
]
```


--- File: lotteharper-main/misc/views.py ---
```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache, cache_page
from users.tests import is_superuser_or_vendor

@never_cache
def logo(request):
    from django.shortcuts import render
    return render(request, 'misc/logo.html')

@login_required
@user_passes_test(is_superuser_or_vendor)
def publickeys(request):
    from django.http import HttpResponse
    import subprocess
    return HttpResponse(subprocess.check_output("catkeys", shell=True))

@cache_page(60*60*24*28)
def opendkimkey(request):
    from django.http import HttpResponse
    import subprocess
    return HttpResponse(subprocess.check_output("opendkimkey", shell=True))

@cache_page(60*60*24*30)
def webmanifest(request):
    from django.shortcuts import render
    return render(request, 'misc/site.webmanifest', {})

@cache_page(60*60*24*28)
def map(request):
    from django.shortcuts import render
    from security.models import UserIpAddress, Session
    latlngs = []
    from django.conf import settings
    for ip in UserIpAddress.objects.all():
        if ip.latitude and ip.longitude: latlngs = latlngs + [(ip.latitude, ip.longitude)]
    import numpy as np
    from sklearn.cluster import DBSCAN
    coords = np.array(latlngs)
    # Haversine metric requires radians:
    kms_per_radian = 6371.0088
    epsilon = 50 / kms_per_radian # 50km radius
    db = DBSCAN(eps=epsilon, min_samples=2, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
    labels = db.labels_
    groups = {}
    for label, point in zip(labels, latlngs):
        groups.setdefault(label, []).append(point)
    pts = []
    for x in range(len(groups)-1):
        pts = pts + [groups[x][0]]
#    print(pts)
    return render(request, 'misc/map.html', {'title': 'Visitor Map', 'latlngs': pts, 'maps_api_key': settings.GOOGLE_API_KEY})

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
        from django.template.loader import render_to_string
        from datetime import datetime
        context = {'timestamp': str(datetime.now().timestamp()).split('.')[0]}
        sw_js = render_to_string('serviceworker.js', context)
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
    from translate.languages import SELECTOR_LANGUAGES
    author = User.objects.get(id=settings.MY_ID)
    return render(request, 'misc/sitemap.xml', {'posts': Post.objects.filter(public=True, private=False, published=True).exclude(content=''), 'vendors': User.objects.filter(profile__vendor=True, is_active=True), 'surrogates': User.objects.filter(profile__vendor=True, is_active=True, vendor_profile__activate_surrogacy=True), 'vendor_urls': vendor_urls, 'urls': urls, 'surrogate_urls': surrogate_urls, 'vendor_feeds': vendor_feeds, 'languages': SELECTOR_LANGUAGES.keys(), 'base_url': settings.BASE_URL, 'date': author.profile.date_joined}, content_type='application/xml')

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

@csrf_exempt
def upload_video_api(request):
    return False
    from django.http import HttpResponse
    from .forms import UploadForm
    from django.conf import settings
    if not request.GET.get('k', None) == settings.UPLOAD_KEY: return HttpResponse(400)
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            from django.contrib.auth.models import User
            user = User.objects.get(id=settings.MY_ID)
            form.instance.user = user
            recording = form.save()
            from live.models import VideoRecording, VideoCamera
            from live.models import get_file_path
            import pytz, os, traceback
            from django.conf import settings
            from recordings.youtube import upload_youtube
            from better_profanity import profanity
            count = 0
            if recording:
                cameras = VideoCamera.objects.filter(name='private*', user=user).order_by('-last_frame')
                print(recording.camera)
                print(cameras)
                camera = cameras.first()
                from live.duration import get_duration
                if camera.upload and get_duration(recording.file.path) > settings.LIVE_INTERVAL/1000 * 1.5:
                    try:
                        if not (recording.file and os.path.exists(recording.file.path)):
                            print('Getting file from bucket for upload')
                            full_path = os.path.join(settings.BASE_DIR, 'media/', get_file_path(None, 'rec.mp4'))
                            with recording.file_processed.storage.open(str(recording.file_processed.name), mode='rb') as bucket_file:
                                with open(full_path, "wb") as video_file:
                                    video_file.write(bucket_file.read())
                                video_file.close()
                            bucket_file.close()
                            recording.file = full_path
                            recording.save()
                    except:
                        return HttpResponse(traceback.format_exc())
                    try:
                        upload_youtube(user, recording.file.path, profanity.censor(camera.title[:67-len(recording.last_frame.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%A %B %d, %Y %H:%M:%S'))]) + ' - ' + recording.last_frame.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime('%A %B %d, %Y %H:%M:%S'), profanity.censor(camera.description) + ' - ' + profanity.censor(recording.transcript[:4000 - 3]), [tag for tag in camera.tags.split(',')], category='22', privacy_status='public', age_restricted=not recording.public)
                        recording.uploaded = True
                        recording.save()
                        os.remove(recording.file.path)
                        return HttpResponse(status_code=200)
                    except:
                        recording.uploaded = False
                        print(traceback.format_exc())
                    recording.save()
                    return HttpResponse(status_code=500)
    return HttpResponse(status_code=500)
```


--- File: lotteharper-main/net.ipv4.ip_local_port_range = 1024 999999 ---
```



```


--- File: lotteharper-main/notes/mail.txt ---
```
echo "sample test message" | mail -s "sample test mail subject" jasper.camber.holton@gmail.com
```


--- File: lotteharper-main/notes/notes.txt ---
```
grep -nH "text" */file.txt
```


--- File: lotteharper-main/notes/registry.txt ---
```
/home/team/lotteh/venv/lib/python3.10/site-packages/django/apps/registry.py
```


--- File: lotteharper-main/notes/tricks.txt ---
```
chmod -R go+rX
redis-cli KEYS "celery*" | xargs redis-cli DEL
/home/team/clemn/venv/lib/python3.10/site-packages/django/apps/registry.py


In Django, the loaddata command loads data from a fixture into the database. By default, it doesn't overwrite existing data. However, you can achieve the effect of overwriting by:
1. Truncating the tables:
Before loading:
Use the manage.py sqlflush command or manually truncate the relevant tables in your database. This will delete all existing data in those tables.
Then load:
Run manage.py loaddata <fixturename> to load your fixture data into the now-empty tables.

manage.py loaddata <app_name>

Git fix: reset last commit (as many times as needed)
git reset HEAD~
sudo git reset HEAD~

pkill -9 -f path/to/my_script.py

# Root's crontab
MAILTO=someone@example.com
0 0 * * * /usr/bin/somescript

# Reset webpush
from webpush.models import SubscriptionInfo
SubscriptionInfo.objects.all().delete()
```


--- File: lotteharper-main/notifications/admin.py ---
```python
from django.contrib import admin

# Register your models here.
```


--- File: lotteharper-main/notifications/apps.py ---
```python
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
```


--- File: lotteharper-main/notifications/forms.py ---
```python
from django import forms

class NotificationForm(forms.Form):
    head = forms.CharField(required=False, max_length=63)
    body = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 5}))
    url = forms.CharField(required=False, max_length=120)
    def __init__(self, *args, **kwargs):
        super(NotificationForm, self).__init__(*args, **kwargs)```


--- File: lotteharper-main/notifications/__init__.py ---
```python
```


--- File: lotteharper-main/notifications/migrations/__init__.py ---
```python
```


--- File: lotteharper-main/notifications/models.py ---
```python
from django.db import models

# Create your models here.
```


--- File: lotteharper-main/notifications/push.py ---
```python
def routine_push():
    from webpush import send_group_notification
    from feed.models import Post
    from django.conf import settings
    posts = Post.objects.filter(author__id=settings.MY_ID, enhanced=True, private=False, public=True, published=True, recipient=None).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
    post = Post.objects.filter(id__in=posts).order_by('?').first()
    payload = {
        'head': 'See more on {}'.format(settings.SITE_NAME),
        'body': 'Visit {} today and see more posts like this one. I\'d love to see you there!'.format(settings.SITE_NAME),
        'icon': post.get_face_blur_thumb_url(),
        'url': settings.BASE_URL,
    }
    send_group_notification(group_name='guests', payload=payload)
```


--- File: lotteharper-main/notifications/serviceworker.js ---
```
// Base Service Worker implementation.  To use your own Service Worker, set the PWA_SERVICE_WORKER_PATH variable in settings.py

var staticCacheName = "django-pwa-v" + new Date().getTime();
var filesToCache = [
    '/offline',
    '/static/css/django-pwa-app.css',
    '/static/images/icons/icon-72x72.png',
    '/static/images/icons/icon-96x96.png',
    '/static/images/icons/icon-128x128.png',
    '/static/images/icons/icon-144x144.png',
    '/static/images/icons/icon-152x152.png',
    '/static/images/icons/icon-192x192.png',
    '/static/images/icons/icon-384x384.png',
    '/static/images/icons/icon-512x512.png',
    '/static/images/icons/splash-640x1136.png',
    '/static/images/icons/splash-750x1334.png',
    '/static/images/icons/splash-1242x2208.png',
    '/static/images/icons/splash-1125x2436.png',
    '/static/images/icons/splash-828x1792.png',
    '/static/images/icons/splash-1242x2688.png',
    '/static/images/icons/splash-1536x2048.png',
    '/static/images/icons/splash-1668x2224.png',
    '/static/images/icons/splash-1668x2388.png',
    '/static/images/icons/splash-2048x2732.png'
];

// Cache on install
self.addEventListener("install", event => {
    this.skipWaiting();
    event.waitUntil(
        caches.open(staticCacheName)
            .then(cache => {
                return cache.addAll(filesToCache).catch(_=>console.error("can't load file to cache"));
            })
    )
});

// Clear cache on activate
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(cacheName => (cacheName.startsWith("django-pwa-")))
                    .filter(cacheName => (cacheName !== staticCacheName))
                    .map(cacheName => caches.delete(cacheName))
            );
        })
    );
});

// Serve from Cache
self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                return response || fetch(event.request);
            })
            .catch(() => {
                return caches.match('offline');
            })
    )
});

// Register event listener for the 'push' event.
self.addEventListener('push', function(event) {
  // Retrieve the textual payload from event.data (a PushMessageData object).
  // Other formats are supported (ArrayBuffer, Blob, JSON), check out the documentation
  // on https://developer.mozilla.org/en-US/docs/Web/API/PushMessageData.
  let payload = event.data ? event.data.text() : {"head": "No Content", "body": "No Content", "icon": ""},
    data = JSON.parse(payload),
    head = data.head,
    body = data.body,
    icon = data.icon;
    // If no url was received, it opens the home page of the website that sent the notification
    // Whitout this, it would open undefined or the service worker file.
    url = data.url ? data.url: self.location.origin;

  // Keep the service worker alive until the notification is created.
  event.waitUntil(
    // Show a notification with title 'ServiceWorker Cookbook' and use the payload
    // as the body.
    self.registration.showNotification(head, {
      body: body,
      icon: icon,
      data: {url: url}
    })
  );
});

self.addEventListener('notificationclick', function (event) {
  event.waitUntil(
    event.preventDefault(),
    event.notification.close(),
    self.clients.openWindow(event.notification.data.url)
  );
})
```


--- File: lotteharper-main/notifications/templates/notifications/send.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block content %}
<legend>Send Push Message</legend>
<form method="POST" enctype="multipart/form-data">
            {% csrf_token %}
            <fieldset class="form-group">
                {{ form|crispy }}
            </fieldset>
            <div class="form-group float-right" style="position: relative; bottom: 20px;">
                <button class="btn btn-outline-info bg-white text-right" type="submit">Send</button>
            </div>
        </form>
{% endblock %}```


--- File: lotteharper-main/notifications/tests.py ---
```python
```


--- File: lotteharper-main/notifications/urls.py ---
```python
from django.urls import path
from . import views

app_name='notifications'

urlpatterns = [
    path('', views.send_guest_notification, name='send'),
]```


--- File: lotteharper-main/notifications/views.py ---
```python
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import pediatric_identity_verified
from django.contrib.auth.decorators import login_required

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def send_guest_notification(request):
    from django.shortcuts import render
    from .forms import NotificationForm
    from django.conf import settings
    from django.contrib import messages
    import traceback
    from feed.models import Post
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data.get('url', None)
            posts = Post.objects.filter(author__id=settings.MY_ID, enhanced=True, private=False, public=True, published=True, recipient=None).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:settings.FREE_POSTS]
            post = Post.objects.filter(id__in=posts).order_by('?').first()
            payload = {"head": form.cleaned_data.get('head', 'Visit {}'.format(settings.SITE_NAME)), "body": form.cleaned_data.get('body', 'Enjoy your time with {}'.format(settings.SITE_NAME)), 'icon': post.get_face_blur_thumb_url(), 'url': settings.BASE_URL if not url else url}
            messages.success(request, 'Successful push notification - {}'.format(form.cleaned_data.get('head')))
            from webpush import send_group_notification
            import traceback
            try:
                send_group_notification(group_name="guests", payload=payload, ttl=1000)
            except: print(traceback.format_exc())
    return render(request, 'notifications/send.html', {'title': 'Send Notification', 'form': NotificationForm()})
```


--- File: lotteharper-main/pam_code.sh ---
```bash
echo "Please enter the following code to access the software"
exit -1
#/home/team/lotteh/venv/bin/python pam_code.py

```


--- File: lotteharper-main/pam.py ---
```python
import re, traceback, requests, json, regex, sys, glob, time, threading, datetime, asyncio
with open('/etc/apis.json') as config_file:
    keys = json.load(config_file)
from subprocess import Popen, STDOUT, PIPE

output = ''

def run_command(command):
    cmd = command.split(' ')
    proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, cwd=str("/"))
    time.sleep(0.1)
    proc.kill()
    return proc.stdout.read().decode("unicode_escape")

def unique(thelist):
    u = []
    for i in thelist:
        if i not in u: u.append(i)
    return u

def check_blacklist(ip):
    try:
        with open('blacklist.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.replace('\n', '') == ip: return True
        return False
    except: pass
    return False

def blacklist(ip):
    with open('blacklist.txt', 'a') as file:
        file.write('{}\n'.format(ip))
        file.close()

logpath = glob.glob('/var/log/auth.log')[-1]

def load_path1():
    global output
#    print(output)

def load_path2():
    global output
    try:
        if glob.glob('/var/log/auth.log.*')[-1]:
            run_command('sudo rm {}*'.format(logpath))
    except:
        run_command('sudo rm {}*'.format(logpath))
    sys.exit(1)
    logpath = glob.glob('/var/log/auth.log.*')[-1]
    output = run_command('tail -n 5000 {}'.format(logpath))

thread_started = False

from lotteh import settings

ipv4_pattern = r"\bAccepted publickey for {} from ".format(settings.BASH_USER) + r"(?:\d{1,3}\.){3}\d{1,3}\b"
ipv6_pattern = r"\bAccepted publickey for {} from ".format(settings.BASH_USER) + r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"

output = run_command('sudo tail -n 500 {}'.format(logpath))
time.sleep(1)
op = output.split('\n')
op.reverse()
output = '\n'.join(op)
ips = unique(re.findall(ipv6_pattern + '|' + ipv4_pattern, output))

print(output)
thread_started = False
while False and not output:
    print('awaiting output')
    time.sleep(3)
    if output:
        op = output.split('\n')
        op.reverse()
        output = '\n'.join(op)
        ips = unique(re.findall(ipv6_pattern + '|' + ipv4_pattern, output))
#        if len(ips) == 0 and thread_started: sys.exit(2)
    if not thread_started and not output:
        thread_started = True
        load_path2()
        break

#print(output)

print(ips)
if len(ips) == 0:
    sys.exit(2)
#    logpath = glob.glob('/var/log/auth.log.*')[-1]
#    if logpath: output2 = run_command('sudo tail -n 5000 {}'.format(logpath))
#    op = output2.split('\n')
#    op.reverse()
#    output = '\n'.join(op)
#    ips = unique(re.findall(IPV4ADDR + '|' + IPV6ADDR, output))
#if len(ips) == 0:
#    import sys
#    sys.exit(0)
ip = ips[0][len("Accepted publickey for {} from ".format(settings.BASH_USER)):]

if ip != '127.0.0.1':
    print('Foreign IP')
    import os
    from requests.auth import HTTPBasicAuth
    FRAUDGUARD_USER = keys['FRAUDGUARD_USER']
    FRAUDGUARD_SECRET = keys['FRAUDGUARD_SECRET']
    ANTIDEO_KEY = keys['ANTIDEO_KEY']
    RISK_LEVEL = 1
    def check_raw_ip_risk(ip_addr, soft=False, guard=True):
        if not guard:
            try:
                ip=requests.get('https://api.antideo.com/ip/health/' + ip_addr + '&apiKey={}'.format(ANTIDEO_KEY))
                j = None
                try:
                    j = ip.json()
                except: pass
                if j and j['health']['toxic'] or j['health']['spam']:
                    return True
                else:
                    return not soft
            except:
                print(traceback.format_exc())
                return not soft
        try:
            ip=requests.get('https://api.fraudguard.io/v2/ip/' + ip_addr, verify=True, auth=HTTPBasicAuth(FRAUDGUARD_USER, FRAUDGUARD_SECRET))
            for resp in ip.history: print(resp.status_code)
            print(ip)
            j = ip.json()
            if int(j['risk_level']) > RISK_LEVEL:
                return True
            else:
                return False
        except:
            print(traceback.format_exc())
            return not soft
        return False
    blacklisted = check_blacklist(ip)
    if not ip == '127.0.0.1' and (blacklisted or check_raw_ip_risk(ip, soft=True)):
        run_command('doveadm kick team {}'.format(output))
        if not blacklisted:
            blacklist(ip)
        sys.exit(1)
    print(blacklisted)
    sys.exit(0)
```


--- File: lotteharper-main/pam.sh ---
```bash
#!/bin/bash
return_code=0
/home/team/lotteh/venv/bin/python /home/team/lotteh/pam.py
return_code=$(($return_code + $?))
echo $return_code
if [ $return_code == 0 ]; then
    echo "Your login has succeeded. Please continue." >> /dev/stdout
    exit 0
else
    echo "Your login has been denied due to lack of authentication. Key-based auth was successful but no secondary authentication was provided. No further information is available about this error." >> /dev/stderr
    exit 103
fi
```


--- File: lotteharper-main/patch_captions.py ---
```python
import os, sys, re
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from feed.models import Post

def patch_uncaptioned_posts():
    for post in Post.objects.filter(private=True, content__icontains='sorry, but i can\'t'):
        post.download_photo()
        from feed.caption_old import caption_image as caption_old
        post = Post.objects.get(id=post.id)
        post.content = caption_old(post.image.path)
        post.save()

def augment_text(post, caption_text):
    pronouns = post.author.vendor_profile.pronouns
    caption_text = caption_text.lower()
    replace = {
        'person': 'woman' if pronouns == 'Her' else 'man' if pronouns == 'Him' else 'person',
        'person\'s': 'woman\'s' if pronouns == 'Her' else 'man\'s' if pronouns == 'Him' else 'person\'s',
        'they have': 'she has' if pronouns == 'Her' else 'he has' if pronouns == 'Him' else 'they have',
        'they are': 'she is' if pronouns == 'Her' else 'he is' if pronouns == 'Him' else 'they are',
        'man': 'woman' if pronouns == 'Her' else 'man' if pronouns == 'Him' else 'person',
        'boy': 'woman' if pronouns == 'Her' else 'man' if pronouns == 'Him' else 'person',
        'his': 'hers' if pronouns == 'Her' else 'his' if pronouns == 'Him' else 'person\'s',
        'man\'s': 'woman\'s' if pronouns == 'Her' else 'man\'s' if pronouns == 'Him' else 'person\'s',
        'men': 'women' if pronouns == 'Her' else 'women\'s' if pronouns == 'Him' else 'people',
        'him': 'her' if pronouns == 'Her' else 'him' if pronouns == 'Him' else 'them',
        'them': 'her' if pronouns == 'Her' else 'him' if pronouns == 'Him' else 'them',
        'their': 'her' if pronouns == 'Her' else 'her' if pronouns == 'Him' else 'their',
        'they\'re': 'she is' if pronouns == 'Her' else 'he is' if pronouns == 'Him' else 'they\'re',
        'beard': 'piercing',
        'knife': 'pose',
        'mustache': 'makeup',
        'a makeup': 'makeup',
        'with makeup': 'wearing makeup',
        'dog': 'phone'
    }
    for key, value in replace.items():
        caption_text = re.sub('\s' + key + '\s', ' ' + value + ' ', caption_text)
        caption_text = re.sub('\s' + key + '\s', ' ' + value + ' ', caption_text)
        caption_text = re.sub('\s' + key + '\.', ' ' + value + '.', caption_text)
        caption_text = re.sub('\s' + key + '\,', ' ' + value + ',', caption_text)
    if post.author.vendor_profile.pronouns != 'They':
        replace = {
            'and are': 'and is',
            'and have': 'and has',
            'also have': 'also has',
        }
    else:
        replace = {}
    for key, value in replace.items():
        caption_text = re.sub('\s' + key + '\s', ' ' + value + ' ', caption_text)
        caption_text = re.sub('\s' + key + '\s', ' ' + value + ' ', caption_text)
        caption_text = re.sub('\s' + key + '\.', ' ' + value + '.', caption_text)
        caption_text = re.sub('\s' + key + '\,', ' ' + value + ',', caption_text)
    caption_text_split = caption_text.split('.')
    op = ''
    for t in caption_text_split[:-1]:
        op = op + ' {}.'.format(t.strip().capitalize())
    return op.strip()

for post in Post.objects.filter(content__length__lte=1000):
    print(post.content)
    post.content = post.content.replace('. .', '.') #augment_text(post, post.content)
    post.save()
```


--- File: lotteharper-main/patch_database.py ---
```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()

from users.patch import patch_users
patch_users('lotteh2024')
```


--- File: lotteharper-main/patch_posts.py ---
```python
ID = 2
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotteh.settings')
import django
django.setup()
from feed.models import Post
from voice.models import AudioInteractive

#for post in Post.objects.all():
#    if post.image_thumbnail:
#        post.image_thumbnail = str(post.image_thumbnail.path).replace('uglek', 'lotteh')
#        post.save()

for post in AudioInteractive.objects.all():
    if post.content:
        post.content = str(post.content.path).replace('uglek', 'lotteh')
        post.save()
```


--- File: lotteharper-main/payments/admin.py ---
```python
from django.contrib import admin

from .models import VendorPaymentsProfile
# Register your models here.
admin.site.register(VendorPaymentsProfile)
```


--- File: lotteharper-main/payments/agreements.py ---
```python
def generate_surrogacy_agreement(name, text, agreeing_users):
    import uuid, os
    from django.conf import settings
    folder = 'surrogacy'
    HEIGHT = 11
    WIDTH = 8.5
    output_name = name + '-' + str(uuid.uuid4())
    base_dir = os.path.join(settings.BASE_DIR, 'media/{}/'.format(folder))
    code_lines = 45
    code_per_line = 90

    font_size = 13

    from PIL import Image
    from docx import Document
    from docx.oxml import parse_xml, OxmlElement
    from docx.oxml.ns import nsdecls, qn
    from docx.shared import Inches, Cm, Pt
    from pygments import highlight
    from pygments.lexers import PythonLexer, HtmlLexer, BashLexer, JavascriptLexer
    from pygments.formatters import ImageFormatter
    import re

    document = Document()

    text = ''

    title = text.split('\n')[0]

    document.add_heading(title, 0)

    text = text.replace('‘','\'').replace('’','\'')
    text_split = text.split('***')

    def create_element(name):
        return OxmlElement(name)

    def create_attribute(element, name, value):
        element.set(qn(name), value)

    def add_page_number(run):
        fldChar1 = create_element('w:fldChar')
        create_attribute(fldChar1, 'w:fldCharType', 'begin')

        instrText = create_element('w:instrText')
        create_attribute(instrText, 'xml:space', 'preserve')
        instrText.text = "PAGE"

        fldChar2 = create_element('w:fldChar')
        create_attribute(fldChar2, 'w:fldCharType', 'end')

        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)

    add_page_number(document.sections[0].footer.paragraphs[0].add_run())

    sections = document.sections
    for section in sections:
        section.page_height = Inches(HEIGHT)
        section.page_width = Inches(WIDTH)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)

    paragraph_format = document.styles['Normal'].paragraph_format
    paragraph_format.space_before = Cm(0.01)
    paragraph_format.space_after = Cm(0.01)

    style = document.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(font_size)
    signature_rep = "__________________________________"
    roles = ['Intended Parent', 'Intended Parent', 'Surrogate Mother', 'Surrogate Mother\'s Partner']
    signature_count = 0
    def add_paragraph(line):
        if signature_rep in line and agreeing_users[signature_count]:
            p = document.add_paragraph()
            run = p.add_run()
            run.add_text('X ')
            from jsignature.utils import draw_signature
            image_path = base_dir + 'signature-{}'.format(uuid.uuid4())
            file = draw_signature(agreeing_users[signature_count].verifications.last().signature)
            file.save(image_path)
            width = Image.open(image_path).size[0] / 90
                        if width > WIDTH - 1: width = WIDTH - 1
                        run.add_picture(image_path, width=Inches(width))
            signature_count = signature_count + 1
            run.add_text(', {} - Dated: {}'.format(roles[signature_count], timezone.now().strftime('%B, %d, %Y')))
        else:
            paragraph = document.add_paragraph(line)
            paragraph.style = document.styles['Normal']

    image_count = 0

    for t in text_split:
        split = re.split('\*[\w\.]+\*', t)
        language = '\n'
        try:
            language = t[len(split[0]):len(t)-len(split[1])][1:-1].lower()
        except: pass
        for line in split[0].split('\n'):
            paragraph = add_paragraph(line)
        code = split[1] if len(split) > 1 else False
        if code:
            run = True
            while run:
                s = code.split('\n')[:code_lines]
                lines_formatted = []
                for code_line in s:
                    for x in range(0, int(len(code_line)/code_per_line)):
                        lines_formatted = lines_formatted + [('(continued line) ' if x > 0 else '') + code_line[x*code_per_line:(x+1)*code_per_line]]
                c = '\n'.join(lines_formatted)
                remaining_code = '\n'.join(code.split('\n')[code_lines:])
                image_path = base_dir + 'image{}.png'.format(image_count)
                with open(image_path, "wb") as f:
                    add = True
                    print(language)
                    if language == 'python':
                        f.write(highlight(c, PythonLexer(), ImageFormatter()))
                    elif language == 'javascript':
                        f.write(highlight(c, JavascriptLexer(), ImageFormatter()))
                    elif language == 'html':
                        f.write(highlight(c, HtmlLexer(), ImageFormatter()))
                    elif language == 'bash':
                        f.write(highlight(c, BashLexer(), ImageFormatter()))
                    elif language.startswith('screenshot'):
                        image_path = base_dir + language
                    else:
                        add = False
                        for line in c.split('\n'):
                            paragraph = document.add_paragraph(line)
                            paragraph.style = document.styles['Normal']
                    f.close()
                    if add:
                        width = Image.open(image_path).size[0] / 90
                        if width > WIDTH - 1: width = WIDTH - 1
                        document.add_picture(image_path, width=Inches(width))
                    image_count = image_count + 1
                    if len(remaining_code) == 0: run = False
    savename = base_dir + '{}.docx'.format(output_name)
    document.save(savename)
    from spire.doc import *
    from spire.doc.common import *
    document = Document()
    document.LoadFromFile(savename)
    document.SaveToFile(savename + '.pdf', FileFormat.PDF)
    document.Close()
    return savename
```


--- File: lotteharper-main/payments/apis.py ---
```python
import requests, json

prices = {}

def get_trumpcoin_price_ccxt(exchange_id, symbol):
  import ccxt
  """Fetches real-time price data using the CCXT library."""
  exchange = getattr(ccxt, exchange_id)()  # Instantiate the exchange class
  try:
      ticker = exchange.fetch_ticker(symbol)
      return ticker['last'] # Or ticker['bid'], ticker['ask'], etc. based on your needs
  except ccxt.ExchangeError as e:
      return f"Error fetching price from {exchange_id}: {e}"
  except AttributeError as e:
      return f"Invalid exchange: {e}"

def get_trump_price():
  """Fetches the current price of $TRUMP from the CoinGecko API."""

  url = "https://api.coingecko.com/api/v3/simple/price?ids=official-trump&vs_currencies=usd"
  try:
    response = requests.get(url)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    data = response.json()
    trump_price = data['official-trump']['usd']
    return trump_price
  except requests.exceptions.RequestException as e:
      print(f"Error fetching data: {e}")
      return None

if __name__ == "__main__":
  price = get_trump_price()
  if price:
      print(f"The current price of $TRUMP is: ${price}")

def get_crypto_price(crypto):
    if crypto == 'USDC': return 1.0
    if crypto == 'ALPH': crypto = 'ETH'
    global prices
    from django.utils import timezone
    if crypto in prices:
        import datetime
        price, time = prices[crypto]
        if time > timezone.now() - datetime.timedelta(minutes=10):
            return price
    if crypto == 'TRUMP':
        return get_trump_price()
    currencies = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binance Coin",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "XRP": "Ripple",
        "LTC": "litecoin",
        "BCH": "bitcoin-cash",
        "LINK": "Chainlink",
        "XLM": "stellar",
        "USDT": "tether",
        "USDC": "USD Coin",
        "XMR": "Monero",
        "EOS": "EOS",
        "TRX": "TRON",
        "ADA": "Cardano",
        "SOL": "Solana",
        "ATOM": "Cosmos",
        "NEO": "NEO",
        "XEM": "NEM",
        "MIOTA": "IOTA",
        "XTZ": "Tezos",
        "VET": "VeChain",
        "POL": "polygon-ecosystem-token",
        "ETC": "Ethereum Classic",
        "ICP": "Internet Computer",
        "DCR": "Decred",
        "TRUMP": "SOL/TRUMP",
        "AVAX": "avalanche",
    }
    from realtime_crypto import RealTimeCrypto
    tracker = RealTimeCrypto()
    try:
        currency = tracker.get_coin(currencies[crypto].lower())
        price = currency.get_price()
        prices[crypto] = (price, timezone.now())
        return price
    except: raise Exception('This currency is not supported at this time.')

def get_crypto_price_nowpayments(crypto):
    if crypto == 'ALPH': crypto = 'ETH'
    global prices
    from django.utils import timezone
    if crypto in prices:
        import datetime
        price, time = prices[crypto]
        if time > timezone.now() - datetime.timedelta(minutes=10):
            return price
    from django.conf import settings
    url = "https://api.nowpayments.io/v1/estimate?amount=1.0&currency_from={}&currency_to=usd".format(crypto)
    data = requests.get(url, headers={'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'})
    data = data.json()
    import json
    print(json.dumps(data))
    try:
        price =  float(data['estimated_amount'])
        prices[crypto] = (price, timezone.now())
        return price
    except: raise Exception('This currency is not supported at this time.')

from web3 import Web3

def is_valid_erc20_address(address):
    """
    Checks if the given string is a valid ERC20 address.

    Args:
        address (str): The address string to validate.

    Returns:
        bool: True if the address is valid, False otherwise.
    """
    if not isinstance(address, str):
        return False
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    try:
         return Web3.is_address(address)
    except ValueError:
        return False

def validate_address(currency, address):
    from django.conf import settings
    if currency.lower() == 'trump': currency = 'sol'
    if currency.lower() == 'usdt': return is_valid_erc20_address(address)
    data = {'address': address, 'network': currency.lower()}
    url = "https://api.checkcryptoaddress.com/wallet-checks"
    data = requests.post(url, data=json.dumps(data), headers={'X-Api-Key': settings.CCA_KEY, 'Content-Type': 'application/json'})
#    print(data)
#    print(data.text)
    r = data.json()
    return r['valid'] if 'valid' in r else False

def validate_address_nowpayments(address, currency):
    from django.conf import settings
    data = {'address': address, 'currency': currency}
    url = "https://api.nowpayments.io/v1/payout/validate-address?"
    data = requests.post(url, data=json.dumps(data), headers={'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'})
    return data.text == 'OK'
```


--- File: lotteharper-main/payments/apps.py ---
```python
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
```


--- File: lotteharper-main/payments/async.py ---
```python
from .models import IDScanSubscription
import stripe
from django.contrib.auth.models import User

def update_privledges():
    for user in User.objects.all():
        if not user.payment_links.objects.filter(valid=False): continue
        for payment_link in user.payment_links.objects.filter(valid=False):
            
```


--- File: lotteharper-main/payments/authorizenet.py ---
```python
from django.conf import settings
ANET_NAME = settings.ANET_NAME
ANET_KEY = settings.ANET_KEY

def pay_fee(model, amount, card, full_name=None, address=None, customer_type=None, name=None, description=None):
    import random
    import imp
    import os
    import sys
    from authorizenet import apicontractsv1
    from authorizenet.apicontrollers import createTransactionController
    # Create a merchantAuthenticationType object with authentication details
    # retrieved from the constants file
    merchantAuth = apicontractsv1.merchantAuthenticationType()
    merchantAuth.name = ANET_NAME
    merchantAuth.transactionKey = ANET_KEY
    # Create the payment data for a credit card
    creditCard = apicontractsv1.creditCardType()
    creditCard.cardNumber = str(card.number)
    creditCard.expirationDate = "{}-{}".format(card.expiry_year, card.expiry_month)
    creditCard.cardCode = str(card.cvv_code)
    # Add the payment data to a paymentType object
    payment = apicontractsv1.paymentType()
    payment.creditCard = creditCard
    # Create order information
    order = apicontractsv1.orderType()
    order.invoiceNumber = str(random.randint(10000,99999))
    order.description = "Adult webcam modeling" if not description else description
    info = card.user.verifications.filter(verified=True).last()
    address = card.address if not address else address
    # Set the customer's Bill To address
    customerAddress = apicontractsv1.customerAddressType()
    if full_name:
        customerAddress.firstName = full_name.split(' ')[0]
        customerAddress.lastName = (full_name.split(' ')[2] if len(full_name.split(' ')) > 2 else full_name.split(' ')[1])
    else:
        customerAddress.firstName = info.full_name.split(' ')[0]
        customerAddress.lastName = (info.full_name.split(' ')[2] if len(info.full_name.split(' ')) > 2 else info.full_name.split(' ')[1])
    customerAddress.company = ""
    customerAddress.address = address.raw.split(',')[0]
    customerAddress.city = address.locality.name
    customerAddress.state = address.locality.state.code
    customerAddress.zip = str(address.locality.postal_code)
    customerAddress.country = address.locality.state.country.code
    # Set the customer's identifying information
    customerData = apicontractsv1.customerDataType()
    customerData.type = "individual" if not customer_type else customer_type
    customerData.id = str(card.user.id)
    customerData.email = card.user.email if not customer_email else customer_email
    # Add values for transaction settings
    duplicateWindowSetting = apicontractsv1.settingType()
    duplicateWindowSetting.settingName = "duplicateWindow"
    duplicateWindowSetting.settingValue = "600"
    settings = apicontractsv1.ArrayOfSetting()
    settings.setting.append(duplicateWindowSetting)
    # setup individual line items
    line_item_1 = apicontractsv1.lineItemType()
    line_item_1.itemId = str(model.id)
    line_item_1.name = model.profile.name if not name else name
    line_item_1.description = (model.profile.bio[:20] + '...') if not description else description
    line_item_1.quantity = "1"
    line_item_1.unitPrice = str(amount)
    # build the array of line items
    line_items = apicontractsv1.ArrayOfLineItem()
    line_items.lineItem.append(line_item_1)
    # Create a transactionRequestType object and add the previous objects to it.
    transactionrequest = apicontractsv1.transactionRequestType()
    transactionrequest.transactionType = "authCaptureTransaction"
    transactionrequest.amount = amount
    transactionrequest.payment = payment
    transactionrequest.order = order
    transactionrequest.billTo = customerAddress
    transactionrequest.customer = customerData
    transactionrequest.transactionSettings = settings
    transactionrequest.lineItems = line_items
    # Assemble the complete transaction request
    createtransactionrequest = apicontractsv1.createTransactionRequest()
    createtransactionrequest.merchantAuthentication = merchantAuth
    createtransactionrequest.refId = "MerchantID-0001"
    createtransactionrequest.transactionRequest = transactionrequest
    # Create the controller
    createtransactioncontroller = createTransactionController(
        createtransactionrequest)
    createtransactioncontroller.execute()
    response = createtransactioncontroller.getresponse()
    if response is not None:
        # Check to see if the API request was successfully received and acted upon
        if response.messages.resultCode == "Ok":
            # Since the API request was successful, look for a transaction response
            # and parse it to display the results of authorizing the card
            if hasattr(response.transactionResponse, 'messages') is True:
                print(
                    'Successfully created transaction with Transaction ID: %s'
                    % response.transactionResponse.transId)
                print('Transaction Response Code: %s' %
                      response.transactionResponse.responseCode)
                print('Message Code: %s' %
                      response.transactionResponse.messages.message[0].code)
                print('Description: %s' % response.transactionResponse.
                      messages.message[0].description)
                return True
            else:
                print('Failed Transaction.')
                if hasattr(response.transactionResponse, 'errors') is True:
                    print('Error Code:  %s' % str(response.transactionResponse.
                                                  errors.error[0].errorCode))
                    print(
                        'Error message: %s' %
                        response.transactionResponse.errors.error[0].errorText)
                return False
        # Or, print errors if the API request wasn't successful
        else:
            print('Failed Transaction.')
            if hasattr(response, 'transactionResponse') is True and hasattr(
                    response.transactionResponse, 'errors') is True:
                print('Error Code: %s' % str(
                    response.transactionResponse.errors.error[0].errorCode))
                print('Error message: %s' %
                      response.transactionResponse.errors.error[0].errorText)
            else:
                print('Error Code: %s' %
                      response.messages.message[0]['code'].text)
                print('Error message: %s' %
                      response.messages.message[0]['text'].text)
            return False
    else:
        print('Null Response.')
        return False
    return False
```


--- File: lotteharper-main/payments/bitcoin.py ---
```python
from bitcoinlib.wallets import Wallet, wallet_create_or_open
import sys
from django.utils.crypto import get_random_string

args = sys.argv
arg = args[1]

name = get_random_string(length=16)

if arg == 'create':
    w = Wallet.create(name=name)
    key1 = w.get_key()
    print(key1.address + ',' + key1.wif)
elif arg == 'balance':
    w = Wallet.create(name=name, keys=args[2])
    w.scan()
    print(w.balance())
elif arg == 'info':
    w = wallet_create_or_open(name=name, keys=args[2])
    w.scan()
    print(w.info())
elif arg == 'send':
    keys = args[2].split(',')
    w = wallet_create_or_open(name=name, keys=keys)
    w.scan()
    w.utxos_update()
    t = w.send_to(args[3], args[4] + ' BTC', offline=False)
    print(t.info())
```


--- File: lotteharper-main/payments/bitcoin.sh ---
```bash
#!/bin/bash
venv/bin/python /home/team/clemn/payments/bitcoin.py $*
```


--- File: lotteharper-main/payments/cart.py ---
```python
def process_cart_purchase(user, cart, private=False):
    from django.utils import timezone
    from feed.models import Post
    posts = []
    cart = cart.replace('\\', ',').replace('+', ',').replace('"', '')
    for item in cart.replace('+', ',').split(','):
        s = item.split('=')
        if len(s) < 2: continue
        uid = s[0]
        quant = s[1]
        post = Post.objects.filter(uuid=uid, date_auction__lte=timezone.now()).first()
        if post and not post.private:
            if not post.paid_file:
                post.recipient = user
                post.save()
            else:
                post.paid_users.add(user)
                post.save()
            posts = posts + [post]
        elif post and post.private and minor_document_scanned(user) and private:
            if not post.paid_file:
                post.recipient = user
                post.save()
            else:
                post.paid_users.add(user)
                post.save()
            posts = posts + [post]
    from feed.email import send_photos_email
    send_photos_email(user, posts)

def get_cart_cost(cookies, private=False):
    from django.utils import timezone
    from feed.models import Post
    items = ''
    cookies['cart'] = cookies['cart'].replace('\\', ',').replace('+', ',').replace('"', '')
    try: items = cookies['cart'].replace('+', ',').split(',') if 'cart' in cookies else cookies.split(',')
    except: items = cookies.split(',') if cookies else []
    if not items: items = cookies.split(',')
    price = 0
    if len(items) < 1: return 0
    from django.conf import settings
    for item in items[:-1]:
        s = item.split('=')
        uid = s[0]
        quant = 1
        try:
            quant = s[1]
        except: quant = 1
        post = Post.objects.filter(uuid=uid, date_auction__lte=timezone.now()).first()
        p = post
        if p:
            if (not p.private) or (p.private and private):
                price = price + ((float(p.price) * (quant if settings.ALLOW_MULTIPLE_SALES else 1)) if ((p and (not p.private)) or (p.private and private)) else 0)
    return price

def get_cart(cookies, private=False):
    from django.utils import timezone
    from feed.models import Post
    items = ''
    if not 'cart' in cookies: return ''
    cookies['cart'] = cookies['cart'].replace('\\', ',').replace('+', ',').replace('"', '')
    try: items = cookies['cart'].replace('+', ',').split(',') if 'cart' in cookies else []
    except: items = cookies.split(',') if cookies else []
    if len(items) < 1: return None
    contents = ''
    from translate.translate import translate
    from feed.middleware import get_current_request
    request = get_current_request()
    for item in items[:-1]:
        s = item.split('=')
        uid = s[0]
        add = '<button onclick="addToCart(\'{}\');" class="btn btn-outline-success" title="{}">{}</button>'.format(uid, translate(request, 'Add another'),translate(request, 'Add another'))
        remove = '<button onclick="removeFromCart(\'{}\');" class="btn btn-outline-danger" title="{}">{}</button>'.format(uid, translate(request, 'Remove'), translate(request, 'Remove'))
        quant = 1
        try:
            quant = s[1]
        except: quant = 1
        post = Post.objects.filter(uuid=uid, date_auction__lte=timezone.now()).first()
        if post:
            image = post.get_image_thumb_url() if not post.private else post.get_blur_thumb_url()
            print(uid)
            print(post)
            if (not post.private) or post.private and private:
                contents = contents + ('<div id="{}"><p>{}: <i id="total{}">{}</i> <img align="left" style="float: left; align: left;" height="100px" width="100px" class="m-2" src="{}">\n{} (<a href="{}" title="{}">{}</a>) - ${} ea {}</p><div style="height: 100px;"></div></div>'.format(post.uuid, translate(request, 'Count'), post.uuid, quant, image, translate(request, 'One photo, video, audio, and/or download'), post.get_absolute_url() if post else '', translate(request, 'See this item'), translate(request, 'See this item'), post.price if post else 0, add + ' ' + remove))
    return contents
```


--- File: lotteharper-main/payments/charge-credit-card.py ---
```python
"""
Charge a credit card
"""

import imp
import os
import sys

from authorizenet import apicontractsv1
from authorizenet.apicontrollers import createTransactionController

CONSTANTS = imp.load_source('modulename', 'constants.py')


def charge_credit_card(amount):
    """
    Charge a credit card
    """

    # Create a merchantAuthenticationType object with authentication details
    # retrieved from the constants file
    merchantAuth = apicontractsv1.merchantAuthenticationType()
    merchantAuth.name = CONSTANTS.apiLoginId
    merchantAuth.transactionKey = CONSTANTS.transactionKey

    # Create the payment data for a credit card
    creditCard = apicontractsv1.creditCardType()
    creditCard.cardNumber = "4111111111111111"
    creditCard.expirationDate = "2035-12"
    creditCard.cardCode = "123"

    # Add the payment data to a paymentType object
    payment = apicontractsv1.paymentType()
    payment.creditCard = creditCard

    # Create order information
    order = apicontractsv1.orderType()
    order.invoiceNumber = "10101"
    order.description = "Golf Shirts"

    # Set the customer's Bill To address
    customerAddress = apicontractsv1.customerAddressType()
    customerAddress.firstName = "Ellen"
    customerAddress.lastName = "Johnson"
    customerAddress.company = "Souveniropolis"
    customerAddress.address = "14 Main Street"
    customerAddress.city = "Pecan Springs"
    customerAddress.state = "TX"
    customerAddress.zip = "44628"
    customerAddress.country = "USA"

    # Set the customer's identifying information
    customerData = apicontractsv1.customerDataType()
    customerData.type = "individual"
    customerData.id = "99999456654"
    customerData.email = "EllenJohnson@example.com"

    # Add values for transaction settings
    duplicateWindowSetting = apicontractsv1.settingType()
    duplicateWindowSetting.settingName = "duplicateWindow"
    duplicateWindowSetting.settingValue = "600"
    settings = apicontractsv1.ArrayOfSetting()
    settings.setting.append(duplicateWindowSetting)

    # setup individual line items
    line_item_1 = apicontractsv1.lineItemType()
    line_item_1.itemId = "12345"
    line_item_1.name = "first"
    line_item_1.description = "Here's the first line item"
    line_item_1.quantity = "2"
    line_item_1.unitPrice = "12.95"
    line_item_2 = apicontractsv1.lineItemType()
    line_item_2.itemId = "67890"
    line_item_2.name = "second"
    line_item_2.description = "Here's the second line item"
    line_item_2.quantity = "3"
    line_item_2.unitPrice = "7.95"

    # build the array of line items
    line_items = apicontractsv1.ArrayOfLineItem()
    line_items.lineItem.append(line_item_1)
    line_items.lineItem.append(line_item_2)

    # Create a transactionRequestType object and add the previous objects to it.
    transactionrequest = apicontractsv1.transactionRequestType()
    transactionrequest.transactionType = "authCaptureTransaction"
    transactionrequest.amount = amount
    transactionrequest.payment = payment
    transactionrequest.order = order
    transactionrequest.billTo = customerAddress
    transactionrequest.customer = customerData
    transactionrequest.transactionSettings = settings
    transactionrequest.lineItems = line_items

    # Assemble the complete transaction request
    createtransactionrequest = apicontractsv1.createTransactionRequest()
    createtransactionrequest.merchantAuthentication = merchantAuth
    createtransactionrequest.refId = "MerchantID-0001"
    createtransactionrequest.transactionRequest = transactionrequest
    # Create the controller
    createtransactioncontroller = createTransactionController(
        createtransactionrequest)
    createtransactioncontroller.execute()

    response = createtransactioncontroller.getresponse()

    if response is not None:
        # Check to see if the API request was successfully received and acted upon
        if response.messages.resultCode == "Ok":
            # Since the API request was successful, look for a transaction response
            # and parse it to display the results of authorizing the card
            if hasattr(response.transactionResponse, 'messages') is True:
                print(
                    'Successfully created transaction with Transaction ID: %s'
                    % response.transactionResponse.transId)
                print('Transaction Response Code: %s' %
                      response.transactionResponse.responseCode)
                print('Message Code: %s' %
                      response.transactionResponse.messages.message[0].code)
                print('Description: %s' % response.transactionResponse.
                      messages.message[0].description)
            else:
                print('Failed Transaction.')
                if hasattr(response.transactionResponse, 'errors') is True:
                    print('Error Code:  %s' % str(response.transactionResponse.
                                                  errors.error[0].errorCode))
                    print(
                        'Error message: %s' %
                        response.transactionResponse.errors.error[0].errorText)
        # Or, print errors if the API request wasn't successful
        else:
            print('Failed Transaction.')
            if hasattr(response, 'transactionResponse') is True and hasattr(
                    response.transactionResponse, 'errors') is True:
                print('Error Code: %s' % str(
                    response.transactionResponse.errors.error[0].errorCode))
                print('Error message: %s' %
                      response.transactionResponse.errors.error[0].errorText)
            else:
                print('Error Code: %s' %
                      response.messages.message[0]['code'].text)
                print('Error message: %s' %
                      response.messages.message[0]['text'].text)
    else:
        print('Null Response.')

    return response


if (os.path.basename(__file__) == os.path.basename(sys.argv[0])):
    charge_credit_card(CONSTANTS.amount)
```


--- File: lotteharper-main/payments/crypto.py ---
```python
import requests
import json
import uuid
from django.conf import settings
from django.contrib.auth.models import User
from feed.middleware import get_current_request
from django.contrib import messages

def get_bearer_token():
    data = {
        "email": settings.NOWPAYMENTS_EMAIL,
        "password": settings.NOWPAYMENTS_PASSWORD,
    }
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/auth', headers=headers, data=json.dumps(data))
    data = output.json()
    return data['token']

def generate_sub_partner(id):
    data = {
        "name": str(id) + '-BD',
    }
    headers = {"Authorization": "Bearer {}".format(get_bearer_token()), 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/sub-partner/balance', data=json.dumps(data), headers=headers)
    data = output.json()
    return data['result']['id']


addresses = {}

def get_lightning_address(model, currency, amount, ln=True, tip=False):
    global addresses
    from django.utils import timezone
    request = get_current_request()
    currency += 'ln' if ln else ''
    if request:
        session_key = request.session.session_key
        if tip and (currency in addresses and (session_key in addresses[currency]) and (amount in addresses[currency][session_key])):
            import datetime
            try:
                address, payment_id, time = addresses[currency][session_key][amount]
                if time > timezone.now() - datetime.timedelta(minutes=10):
                    return address, payment_id
            except: pass
    data = {'currency': 'BTC', 'amount': str(round(float(amount) * 100000000))}
    headers = {"Authorization": "{}".format(settings.OPENNODE_KEY), 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.opennode.com/v1/charges', data=json.dumps(data), headers=headers)
    data = output.json()
    print(output)
    print(output.text)
    if tip:
        if not currency in addresses:
            addresses[currency] = {}
        if not session_key in addresses[currency]:
            addresses[currency][session_key] = {}
        addresses[currency][session_key][amount] = (data['data']['lightning_invoice']['payreq'], data['data']['id'], timezone.now()) if ln else (data['data']['address'], data['data']['order_id'], timezone.now())
    return (data['data']['lightning_invoice']['payreq'], data['data']['id']) if ln else (data['data']['address'], data['data']['order_id'])

def get_payment_address(model, currency, amount, tip=False):
    if currency == 'BTC': return get_lightning_address(model, currency, amount, ln=False, tip=tip)
    if currency == 'ALPH': currency = 'ETH'
    global addresses
    from django.utils import timezone
    request = get_current_request()
    if request:
        session_key = request.session.session_key
        if tip and (currency in addresses and (session_key in addresses[currency])):
            import datetime
            address, payment_id, time = addresses[currency][session_key]
            if time > timezone.now() - datetime.timedelta(minutes=30):
                return address, payment_id
    from cryptapi import CryptAPIHelper
    import random
    from django.urls import reverse
    from django.conf import settings
    order_id = random.randrange(11111111, 99999999)
    payable_addresses = {
        'BTC': model.vendor_profile.bitcoin_address,
        'ETH': model.vendor_profile.ethereum_address,
        'USDC': model.vendor_profile.usdcoin_address,
        'SOL': model.vendor_profile.solana_address,
        'POL': model.vendor_profile.polygon_address,
        'XLM': model.vendor_profile.stellarlumens_address,
        'TRUMP': model.vendor_profile.trump_address,
        'BCH': model.vendor_profile.bitcoin_cash_address,
        'LTC': model.vendor_profile.litecoin_address,
        'USDT': model.vendor_profile.usdtether_address,
        'DOGE': model.vendor_profile.dogecoin_address,
        'AVAX': model.vendor_profile.avalanche_address,
    }
    tickers = {
        'BTC': 'btc',
        'ETH': 'eth',
        'POL': 'polygon/pol',
        'AVAX': 'avax-c/avax',
        'SOL': 'sol/sol',
        'USDC': 'base/usdc',
        'USDT': 'erc20/usdt',
        'LTC': 'ltc',
        'DOGE': 'doge',
        'TRUMP': 'sol/trump',
        'BCH': 'bch',
#        'USDP': 'erc20/usdp'
    }
    try:
        ca = CryptAPIHelper(tickers[currency], payable_addresses[currency], settings.BASE_URL + reverse('payments:authorize'), {'orderid': order_id}, {'post': 1})
        pay_address = ca.get_address()['address_in']
        if tip:
            if not currency in addresses:
                addresses[currency] = {}
            addresses[currency][session_key] = pay_address, order_id, timezone.now()
        return pay_address, order_id
    except:
        from .exceptions import PaymentLessThanMinimalException
        raise PaymentLessThanMinimalException('This crypto payment received an error or was less than minimal and cannot be completed. Try using another payment method, or another product.')

def get_payment_address_nowpayments(model, currency, amount, tip=False):
    if currency == 'BTC': return get_lightning_address(model, currency, amount, ln=False, tip=tip)
    if currency == 'ALPH': currency = 'ETH'
    global addresses
    from django.utils import timezone
    request = get_current_request()
    session_key = request.session.session_key
    if tip and (currency in addresses and (session_key in addresses[currency])):
        import datetime
        address, payment_id, time = addresses[currency][session_key]
        if time > timezone.now() - datetime.timedelta(minutes=30):
            return address, payment_id
#    id = str(model.vendor_payments_profile.first().get_sub_partner_id())
    data = {
        "price_amount": str(amount),
        "price_currency": currency.lower(),
        "pay_currency": currency.lower(),
        "payout_address": model.vendor_profile.payout_address,
        "payout_currency": model.vendor_profile.payout_currency
#        "sub_partner_id": id,
#        "fixed_rate": False
    }
    headers = {'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/payment', data=json.dumps(data), headers=headers)
    data = output.json()
    print(data)
    try:
        if tip:
            if not currency in addresses:
                addresses[currency] = {}
            addresses[currency][session_key] = data['pay_address'], data['payment_id'], timezone.now()
        return data['pay_address'], data['payment_id']
    except:
        from .exceptions import PaymentLessThanMinimalException
        raise PaymentLessThanMinimalException('This crypto payment is less than minimal and cannot be completed. Try using another payment method, or another product.')

def get_payment_address_sub_partner(model, currency, amount):
    id = str(model.vendor_payments_profile.first().get_sub_partner_id())
    data = {
        "currency": currency.lower(),
        "amount": str(amount),
        "sub_partner_id": id,
        "fixed_rate": False
    }
    headers = {"Authorization": "Bearer {}".format(get_bearer_token()), 'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/sub-partner/payment', data=json.dumps(data), headers=headers)
    data = output.json()
#    print(data)
    return data['result']['pay_address'], data['result']['payment_id']

def get_lightning_status(payment_id):
    headers = {"Authorization": "{}".format(settings.OPENNODE_KEY), 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.get('https://api.opennode.com/v2/charge/{}'.format(payment_id), headers=headers)
    data = output.json()
#    print(output.text)
    return float(data['data']['fee'])/1000000.0 if data['data']['status'] == 'paid' else 0

def get_payment_status(payment_id, crypto, address):
    from cryptapi import CryptAPIHelper
    from django.conf import settings
    from django.urls import reverse
    url = settings.BASE_URL + reverse('payments:authorize') + '?orderid={}&orderid={}'.format(payment_id, payment_id)
    ca = CryptAPIHelper(crypto.lower(), address, url, {'orderid': payment_id}, {'post': 1})
    data = ca.get_logs()
    print(data)
    paid = 0
    if 'callbacks' in data and len(data['callbacks']) > 0 and 'value_coin' in data['callbacks'][0]:
        for callback in data['callbacks']: paid = paid + callback['value_coin']
    return paid

def get_payment_status_nowpayments(payment_id):
    headers = {'x-api-key': settings.NOWPAYMENTS_KEY}
    output = requests.get('https://api.nowpayments.io/v1/payment/{}'.format(payment_id), headers=headers)
    data = output.json()
    return float(data['actually_paid'])

def get_sub_partner_balance(id):
    id = str(id)
    headers = {'x-api-key': settings.NOWPAYMENTS_KEY}
    output = requests.get('https://api.nowpayments.io/v1/sub-partner/balance/{}'.format(id), headers=headers)
    print(output)
    data = output.json()
    return data['result']['balances']

def sweep_all_to_master():
    for user in User.objects.filter(profile__vendor=True):
        id = str(user.vendor_payments_profile.first().get_sub_partner_id())
        for coin, balance in get_sub_partner_balance(id):
            sweep_to_master(user, coin, balance['amount'])

def sweep_to_master(user, currency, amount):
    id = str(user.vendor_payments_profile.first().get_sub_partner_id())
    data = {
        "currency": currency,
        "amount": amount,
        "sub_partner_id": id
    }
    headers = {"Authorization": "Bearer {}".format(get_bearer_token()), 'x-api-key': settings.NOWPAYMENTS_KEY, 'Content-Type': 'application/json; charset=utf-8'}
    output = requests.post('https://api.nowpayments.io/v1/sub-partner/write-off', data=json.dumps(data), headers=headers)
    data = output.json()
    return data
```


--- File: lotteharper-main/payments/email.py ---
```python
def send_tip_email(user, model, tip, crypto, network):
    from users.email import send_html_email
    from django.contrib.auth.models import User
    from django.utils import timezone
    from datetime import timedelta
    from django.conf import settings
    from django.template.loader import render_to_string
    from webpush import send_group_notification
    from users.tfa import send_user_text
    from feed.models import Post
    posts = Post.objects.filter(author__id=settings.MY_ID, enhanced=True, private=False, public=True, published=True, recipient=None).exclude(image=None).order_by('-date_posted').values_list('id', flat=True)[:500]
    post = Post.objects.filter(id__in=posts).exclude(image_offsite=None).order_by('?').first()
    photo_url = post.image_offsite
    days = 3
    from payments.apis import get_crypto_price
    tip = format(get_crypto_price(crypto) * float(tip), '.2f')
    for user in [user]:
        html_message = render_to_string('payments/tip_email.html', {
            'site_name': settings.SITE_NAME,
            'user': user,
            'model': model,
            'tip': tip,
            'crypto': crypto,
            'network': network,
            'domain': settings.DOMAIN,
            'protocol': 'https',
            'photo': photo_url,
        })
        send_html_email(user, 'Thank you for your tip on {}, {}'.format(settings.SITE_NAME, user.username), html_message)
```


--- File: lotteharper-main/payments/exceptions.py ---
```python
class PaymentLessThanMinimalException(Exception):
    pass
```


--- File: lotteharper-main/payments/forms.py ---
```python
from django import forms
from .models import CustomerPaymentsProfile
from .models import PaymentCard
from address.forms import AddressField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

class CardNumberForm(forms.ModelForm):
    agreed = forms.BooleanField(required=True)
    def __init__(self, user, *args, **kwargs):
        super(CardNumberForm, self).__init__(*args, **kwargs)
        self.instance.user = user
        self.instance.save()
        self.fields['agreed'].label = 'By checking this box, you agree to the <a href="/terms/" title="Read the terms of service and privacy policy">Terms of Service and Privacy Policy</a>, as well as agree to and and acknowledge the sale as outlined.'
        self.fields['address'].required = True
        self.fields['number'].widget.attrs.update({'autocomplete': 'cc-number'})
    class Meta:
        model = PaymentCard
        fields = ('agreed', 'address', 'number',)

expiry_months = ['MM']
for x in range(12):
    val = str(x + 1)
    expiry_months = expiry_months + [[val,val]]

expiry_years = ['YY']
for x in range(10):
    val = str(timezone.now().year + x)[2:]
    expiry_years = expiry_years + [[val,val]]

class CardInfoForm(forms.ModelForm):
    expiry_month = forms.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)]) #forms.CharField(widget=forms.Select(choices=expiry_months),max_length=2)
    expiry_year = forms.IntegerField(validators=[MinValueValidator(timezone.now().year - 2000), MaxValueValidator(timezone.now().year + 10)]) #forms.CharField(widget=forms.Select(choices=expiry_years),max_length=4)
    def __init__(self, user, *args, **kwargs):
        super(CardInfoForm, self).__init__(*args, **kwargs)
        self.instance.user = user
        self.instance.save()
        self.fields['expiry_month'].widget.attrs.update({'autocomplete': 'cc-exp-month'})
        self.fields['expiry_year'].widget.attrs.update({'autocomplete': 'cc-exp-year'})
        self.fields['cvv_code'].widget.attrs.update({'autocomplete': 'cc-csc'})
    class Meta:
        model = PaymentCard
        fields = ('expiry_month','expiry_year','cvv_code',)


CHOICES = [['individual','Individual'], ['business', 'Business']]

class InvoiceForm(forms.Form):
    client_email = forms.EmailField()
    cost = forms.FloatField(required=True)
    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.fields['cost'].initial = 100.0
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['client_email'].label = translate(r, 'The client\'s email for the invoice', src='en')
        self.fields['cost'].label = translate(r, 'The cost of the invoice in USD', src='en')
        self.fields['description'].label = translate(r, 'A description of the product/serivce', src='en')
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 7}))


class PaymentForm(forms.Form):
    total = forms.FloatField(required=True, max_value=1000000000000, min_value=0.99, widget=forms.NumberInput(attrs={'step': "0.01"}))
    item_name = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    full_name = forms.CharField(max_length=100)
    customer_type = forms.CharField(widget=forms.Select(choices=CHOICES))

class BitcoinPaymentForm(forms.Form):
    transaction_id = forms.CharField(max_length=100)
    amount = forms.CharField(max_length=100)
    invoice = forms.CharField(max_length=100, required=False)
    email = forms.EmailField()
    def __init__(self, *args, **kwargs):
        super(BitcoinPaymentForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['email'].label = translate(r, 'Your email for the invoice', src='en')
        self.fields['transaction_id'].widget = forms.HiddenInput()
        self.fields['amount'].widget = forms.HiddenInput()
        self.fields['invoice'].widget = forms.HiddenInput()

class BitcoinPaymentFormUser(forms.Form):
    transaction_id = forms.CharField(max_length=100)
    amount = forms.CharField(max_length=100)
    invoice = forms.CharField(required=False, max_length=100)
    def __init__(self, *args, **kwargs):
        super(BitcoinPaymentFormUser, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['transaction_id'].widget = forms.HiddenInput()
        self.fields['amount'].widget = forms.HiddenInput()
        self.fields['invoice'].widget = forms.HiddenInput()

class CardPaymentForm(forms.Form):
    email = forms.EmailField(required=True)
    product = forms.HiddenInput()
    pid = forms.HiddenInput()
    def __init__(self, *args, **kwargs):
        super(CardPaymentForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['email'].label = translate(r, 'Your email for the invoice', src='en')
        from django.conf import settings
        if r.user.is_authenticated or settings.PAYMENT_PROCESSOR == 'stripe':
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['email'].required = False

class TipCryptoForm(forms.Form):
    tip = forms.FloatField(required=True)
    def __init__(self, *args, **kwargs):
        super(TipCryptoForm, self).__init__(*args, **kwargs)
        from feed.middleware import get_current_request
        r = get_current_request()
        from translate.translate import translate
        self.fields['tip'].label = translate(r, 'Your tip in USD', src='en')
        self.fields['tip'].initial = 0.0
```


--- File: lotteharper-main/payments/__init__.py ---
```python
```


--- File: lotteharper-main/payments/invoice.py ---
```python
def generate_invoice(vendor, user, price, description):
    import random
    from payments.models import Invoice
    from users.email import send_html_email
    from django.template.loader import render_to_string
    from django.conf import settings
    from django.urls import reverse
    invoice = Invoice.objects.create(vendor=vendor, user=user, price=price, product="invoice", cart=description, pid=random.randrange(111111,999999))
    html_email = render_to_string('payments/invoice.html', {
        'pay_url': settings.BASE_URL + reverse('payments:pay-invoice') + '?pid={}'.format(invoice.pid),
        'user': user,
        'vendor': vendor,
        'invoice': invoice,
        'description': description,
        'site_name': settings.SITE_NAME
    })
    send_html_email(user, 'Your invoice from {}'.format(settings.SITE_NAME), html_email)

def process_invoice(invoice):
    import random
    from payments.models import Invoice
    from users.email import send_html_email
    from django.template.loader import render_to_string
    from django.conf import settings
    from django.urls import reverse
    user = invoice.user
    vendor = invoice.vendor
    description = invoice.description
    html_email = render_to_string('payments/invoice_paid.html', {
        'user': user,
        'vendor': vendor,
        'invoice': invoice,
        'description': description,
        'site_name': settings.SITE_NAME
    })
    send_html_email(user, 'Invoice for {} (@{}) has been paid'.format(user.email, user.username), html_email)
```


--- File: lotteharper-main/payments/middleware.py ---
```python
import traceback

def payments_middleware(get_response):
    # One-time configuration and initialization.
    def middleware(request):
        response = None
        try:
            response = get_response(request)
        except:
            print(traceback.format_exc())
        return response
    return middleware
```


--- File: lotteharper-main/payments/migrations/0001_initial.py ---
```python
# Generated by Django 4.2.5 on 2023-10-04 16:02

import address.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('address', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorPaymentsProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sub_partner_id', models.TextField(blank=True, default=None, null=True)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendor_payments_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('expire_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('fee', models.IntegerField(default=0)),
                ('active', models.BooleanField(default=True)),
                ('stripe_subscription_id', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_subscribers', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PurchasedProduct',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('description', models.CharField(blank=True, max_length=1000, null=True)),
                ('price', models.IntegerField(default=0)),
                ('paid', models.BooleanField(default=False)),
                ('pay_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchased_products', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentLink',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('stripe_id', models.CharField(blank=True, max_length=100, null=True)),
                ('url', models.CharField(blank=True, max_length=300, null=True)),
                ('paid', models.BooleanField(default=False)),
                ('pay_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_links', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentCard',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('number', models.IntegerField(null=True)),
                ('expiry_month', models.CharField(max_length=2, null=True)),
                ('expiry_year', models.CharField(max_length=4, null=True)),
                ('cvv_code', models.IntegerField(null=True)),
                ('zip_code', models.IntegerField(null=True)),
                ('primary', models.BooleanField(default=True)),
                ('address', address.models.AddressField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='address.address')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_cards', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='IDScanSubscription',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('active', models.BooleanField(default=False)),
                ('subscribe_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='idware_privledge', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CustomerPaymentsProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bitcoin_address', models.CharField(blank=True, default='', max_length=34, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_payments_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CardPayment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('amount', models.FloatField()),
                ('index', models.IntegerField(default=0)),
                ('transaction_id', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='card_payments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BitcoinPayment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('amount', models.FloatField()),
                ('index', models.IntegerField(default=0)),
                ('transaction_id', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bitcoin_payments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0002_surrogacyplan.py ---
```python
# Generated by Django 5.0.7 on 2024-07-22 22:13

import django.db.models.deletion
import payments.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SurrogacyPlan',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('agreement', models.FileField(blank=True, max_length=500, null=True, upload_to=payments.models.get_file_path)),
                ('signed', models.BooleanField(default=False)),
                ('sent', models.BooleanField(default=False)),
                ('expected_parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='parents_plans', to=settings.AUTH_USER_MODEL)),
                ('expected_parents_partner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='parents_partners_plans', to=settings.AUTH_USER_MODEL)),
                ('mother', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='surrogacy_plans', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0003_invoice.py ---
```python
# Generated by Django 5.0.7 on 2024-08-14 03:19

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_surrogacyplan'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('price', models.IntegerField(default=0)),
                ('number', models.IntegerField(default=0)),
                ('pid', models.IntegerField(default=0)),
                ('product', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoice', to=settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendor_invoice', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0004_alter_invoice_user_alter_invoice_vendor.py ---
```python
# Generated by Django 5.0.7 on 2024-08-14 03:41

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_invoice'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invoice', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='vendor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vendor_invoice', to=settings.AUTH_USER_MODEL),
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0005_alter_invoice_number.py ---
```python
# Generated by Django 5.0.7 on 2024-08-14 03:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_alter_invoice_user_alter_invoice_vendor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='number',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0006_invoice_token.py ---
```python
# Generated by Django 5.0.7 on 2024-08-16 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_alter_invoice_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='token',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0007_invoice_processor.py ---
```python
# Generated by Django 5.0.7 on 2024-08-20 23:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0006_invoice_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='processor',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0008_validatedtransaction.py ---
```python
# Generated by Django 5.0.7 on 2024-08-25 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0007_invoice_processor'),
    ]

    operations = [
        migrations.CreateModel(
            name='ValidatedTransaction',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('uid', models.CharField(blank=True, default='', max_length=100, null=True)),
            ],
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0009_invoice_cart.py ---
```python
# Generated by Django 5.1.1 on 2024-09-23 04:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0008_validatedtransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='cart',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0010_validatedtransaction_user.py ---
```python
# Generated by Django 5.1.2 on 2024-11-05 05:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0009_invoice_cart'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='validatedtransaction',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='validated_transactions', to=settings.AUTH_USER_MODEL),
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0011_alter_vendorpaymentsprofile_vendor.py ---
```python
# Generated by Django 5.1.2 on 2024-11-06 06:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0010_validatedtransaction_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendorpaymentsprofile',
            name='vendor',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='vendor_payments_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0012_invoice_completed.py ---
```python
# Generated by Django 5.1.4 on 2025-01-25 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0011_alter_vendorpaymentsprofile_vendor'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='completed',
            field=models.BooleanField(default=False),
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/0013_surrogacyplan_completed_surrogacyplan_timestamp_and_more.py ---
```python
# Generated by Django 5.2 on 2025-04-27 23:23

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0012_invoice_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='surrogacyplan',
            name='completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='surrogacyplan',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='surrogacyplan',
            name='unpaid',
            field=models.FloatField(default=0.0),
        ),
    ]
```


--- File: lotteharper-main/payments/migrations/__init__.py ---
```python
```


--- File: lotteharper-main/payments/models.py ---
```python
from simple_history.models import HistoricalRecords
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from address.models import AddressField

class Invoice(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoice', null=True)
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_invoice', null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    price = models.IntegerField(default=0)
    pid = models.IntegerField(default=0)
    product = models.CharField(max_length=100, default='', null=True, blank=True)
    processor = models.CharField(max_length=100, default='', null=True, blank=True)
    number = models.CharField(max_length=100, default='', null=True, blank=True)
    token = models.CharField(max_length=100, default='', null=True, blank=True)
    cart = models.TextField(default='', null=True, blank=True)
    completed = models.BooleanField(default=False)

class IDScanSubscription(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='idware_privledge')
    active = models.BooleanField(default=False)
    subscribe_date = models.DateTimeField(default=timezone.now)

class PaymentLink(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_links')
    stripe_id = models.CharField(max_length=100, null=True, blank=True)
    url = models.CharField(null=True, blank=True, max_length=300)
    paid = models.BooleanField(default=False)
    pay_date = models.DateTimeField(default=timezone.now)

class PurchasedProduct(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchased_products')
    description = models.CharField(max_length=1000, null=True, blank=True)
    price = models.IntegerField(default=0)
    paid = models.BooleanField(default=False)
    pay_date = models.DateTimeField(default=timezone.now)

class PaymentCard(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_cards')
    number = models.IntegerField(null=True)
    expiry_month = models.CharField(null=True, max_length=2)
    expiry_year = models.CharField(null=True, max_length=4)
    cvv_code = models.IntegerField(null=True)
    address = AddressField(null=True, blank=True)
    zip_code = models.IntegerField(null=True)
    primary = models.BooleanField(default=True)

class Subscription(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_subscriptions')
    model = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_subscribers')
    expire_date = models.DateTimeField(default=timezone.now)
    fee = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=100,default='', null=True, blank=True)

class CardPayment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='card_payments')
    amount = models.FloatField()
    index = models.IntegerField(default=0)
    transaction_id = models.CharField(max_length=100, default='', null=True, blank=True)


class BitcoinPayment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bitcoin_payments')
    amount = models.FloatField()
    index = models.IntegerField(default=0)
    transaction_id = models.CharField(max_length=100, default='', null=True, blank=True)

class ValidatedTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.CharField(max_length=100, default='', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='validated_transactions', null=True, blank=True)

# Create your models here.
class VendorPaymentsProfile(models.Model):
    vendor = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_payments_profile')
    sub_partner_id = models.TextField(default=None, null=True, blank=True)

    def __str__(self):
        return 'user {} name "{}" {}'.format(self.vendor.profile.name, self.vendor.verifications.first().full_name, self.bitcoin_address.split(',')[0])

    def get_sub_partner_id(self):
        return None
        if self.sub_partner_id:
            return self.sub_partner_id
        else:
            try:
                self.sub_partner_id = generate_sub_partner(self.vendor.id)
            except Exception as e:
                print(e.stderr)
            self.save()
            return self.sub_partner_id

    def validate_crypto_transaction(self, user, min_balance, id, crypto, network, tip=False):
        from payments.crypto import get_payment_status, get_lightning_status
        from django.conf import settings
        if crypto == 'BTC' and network == 'lightning':
            recv = get_lightning_status(id)
            if recv > ((float(min_balance) * (settings.MIN_CRYPTO_PERCENTAGE/100.0)) if not tip else 0):
                if ValidatedTransaction.objects.filter(uid=id).count() > 0: return False
                ValidatedTransaction.objects.create(uid=id, user=user)
                return recv
        else:
            payable_addresses = {
                'BTC': model.vendor_profile.bitcoin_address,
                'ETH': model.vendor_profile.ethereum_address,
                'USDC': model.vendor_profile.usdcoin_address,
                'SOL': model.vendor_profile.solana_address,
                'POL': model.vendor_profile.polygon_address,
                'XLM': model.vendor_profile.stellarlumens_address,
            }
            recv = get_payment_status(id, crypto, payable_addresses[crypto])
            if recv > ((float(min_balance) * (settings.MIN_CRYPTO_PERCENTAGE/100.0)) if not tip else 0):
                if ValidatedTransaction.objects.filter(uid=id).count() > 0: return False
                ValidatedTransaction.objects.create(uid=id, user=user)
                return recv
        return False

    def get_crypto_balances(self):
        if not self.sub_partner_id:
            self.sub_partner_id = generate_sub_partner(self.vendor.id)
            self.save()
        from payments.crypto import get_payment_status, get_lightning_status, get_sub_partner_balance, generate_sub_partner
        return get_sub_partner_balance(self.sub_partner_id)

    def save(self, *args, **kwargs):
        super(VendorPaymentsProfile, self).save(*args, **kwargs)

class CustomerPaymentsProfile(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_payments_profile')
    bitcoin_address = models.CharField(default='', null=True, blank=True, max_length=34)

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (str(uuid.uuid4()), ext)
    return os.path.join('surrogacy/', filename)

class SurrogacyPlan(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(default=timezone.now)
    mother = models.ForeignKey(User, related_name='surrogacy_plans', null=True, blank=True, on_delete=models.DO_NOTHING)
    expected_parent = models.ForeignKey(User, related_name='parents_plans', null=True, blank=True, on_delete=models.DO_NOTHING)
    expected_parents_partner = models.ForeignKey(User, related_name='parents_partners_plans', null=True, blank=True, on_delete=models.DO_NOTHING)
    agreement = models.FileField(null=True, blank=True, upload_to=get_file_path, max_length=500)
    signed = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    unpaid = models.FloatField(default=0.0)
```


--- File: lotteharper-main/payments/paypal.py ---
```python
def get_paypal_token():
    import requests
    from django.conf import settings
    data = {
        'grant_type': 'client_credentials',
    }
    import json
    response = requests.post('https://api-m.paypal.com/v1/oauth2/token', data=data, auth=(settings.PAYPAL_ID, settings.PAYPAL_SECRET)).json()
    print(json.dumps(response))
    return response['access_token']

def get_paypal_link(invoice, price, token):
    import requests
    import uuid
    from django.conf import settings
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(get_paypal_token()),
        'PayPal-Request-Id': str(uuid.uuid4()),
    }
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": invoice,
                "amount": {
                    "currency_code": "USD",
                    "value": "{}.00".format(price)
                }
            }
        ],
         "payment_source": {
              "paypal": {
                   "experience_context": {
                       "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                       "brand_name": settings.SITE_NAME,
                       "locale": "en-US",
                        "landing_page": "LOGIN",
                        "shipping_preference": "SET_PROVIDED_ADDRESS",
                            "user_action": "PAY_NOW",
                            "return_url": "{}{}".format(settings.BASE_URL, '/payments/paypal/?token={}'.format(token)),
                            "cancel_url": "{}{}".format(settings.BASE_URL, '/payments/cancel/')
                        }
                    }
                }
            }
    import json
    response = requests.post('https://api-m.paypal.com/v2/checkout/orders', headers=headers, data=json.dumps(payload)).json()
    print(json.dumps(response))
    return response['id'], response['links'][1]['href']

def get_order_status(id):
    import requests, jsosn
    headers = {
        'Authorization': 'Bearer access_token{}'.format(get_paypal_token()),
    }
    response = requests.get('https://api-m.paypal.com/v2/checkout/orders/{}'.format(id), headers=headers).json()
    print(json.dumps(response))
    return response['status'] == 'APPROVED'
```


--- File: lotteharper-main/payments/square.py ---
```python
def get_payment_link(price, product, description, email, token, subscription=False):
    from django.conf import settings
    import uuid, urllib, requests, json

    headers = {
        'Square-Version': '2024-07-17',
        'Authorization': 'Bearer {}'.format(settings.SQUARE_ACCESS_TOKEN),
        'Content-Type': 'application/json',
    }
    sub = None
    if subscription:
        pay = {
            'object_ids': [
                'A3FWKJF3OQ2Z2CLKOBPFY2WR',
            ],
        }
        res = requests.post('https://connect.squareup.com/v2/catalog/batch-retrieve', data=json.dumps(pay), headers=headers).json()
        print(json.dumps(res))
        SQUARE_CATEGORY = "EFKKLKRWLTZPNZXPX5XBLROX"
        SQUARE_SUB_ITEM = res['objects'][0]['item_data']['variations'][0]['id']
        payload_sub = {
            "idempotency_key": str(uuid.uuid4()),
            "object": {
                "type": "SUBSCRIPTION_PLAN",
                "id": "#1",
                "subscription_plan_data": {
                    "name": "Member Subscription",
                    "all_items": False,
                    "eligible_category_ids": [
                        "{}".format(SQUARE_CATEGORY),
                    ]
                }
            }
        }
        import requests, json
        print(email)
        j = requests.post('https://connect.squareup.com/v2/catalog/object/', data=json.dumps(payload_sub), headers=headers).json()
        print(json.dumps(j))
        p = j['catalog_object']
        sub = p['id']
        print(sub)
    payload = {
        "idempotency_key": str(uuid.uuid4()),
        "quick_pay": {
          "name": description,
          "price_money": {
            "amount": int(float(price) * 100),
            "currency": "USD"
          },
          "location_id": settings.SQUARE_LOCATION
        },
        "redirect_url": settings.BASE_URL + '/payments/square/?token={}'.format(token),
        "pre_populated_data": {
            "buyer_email": str(urllib.parse.unquote(email)),
        },
        "checkout_options":{'allow_tipping': True} if not subscription else {'subscription_plan_variation_id': sub},
    }
    print(email)
    j = requests.post('https://connect.squareup.com/v2/online-checkout/payment-links', data=json.dumps(payload), headers=headers).json()
    print(json.dumps(j))
    p = j['payment_link']
    return p['order_id'], p['url']

def get_payment(id):
    import requests, json
    from django.conf import settings
    headers = {
        'Authorization': 'Bearer {}'.format(settings.SQUARE_ACCESS_TOKEN),
        'Content-Type': 'application/json',
    }
    res = False
    j = requests.get('https://connect.squareup.com/v2/online-checkout/payment-links/{}'.format(id), headers=headers).json()
    print(json.dumps(j))
    if j['order']['state'] == 'COMPLETED':
        res = True
    return res

def verify_payment(id):
    import requests, json
    from django.conf import settings
    headers = {
        'Authorization': 'Bearer {}'.format(settings.SQUARE_ACCESS_TOKEN),
        'Content-Type': 'application/json',
    }
    res = False
    j = requests.get('https://connect.squareup.com/v2/orders/{}'.format(id), headers=headers).json()
    print(json.dumps(j))
    if 'order' in j.keys() and j['order']['state'] == 'OPEN':
        res = True
    return res
```


--- File: lotteharper-main/payments/stripe.py ---
```python
PRICE_IDS = ["price_1NqSBIDNUMHo0j8JyMJoFcJl", "price_1NqSBIDNUMHo0j8JbtvVS5pT", "price_1NqSBIDNUMHo0j8JPR4iYPmY", "price_1NqSBIDNUMHo0j8JgOigQC2I", "price_1NqSBIDNUMHo0j8JrlwK12jz", "price_1NqSBIDNUMHo0j8JZWSZpU3A", "price_1NqSBIDNUMHo0j8JJNChQvJM", "price_1NqSBIDNUMHo0j8Joimlo0kE", "price_1NqSBIDNUMHo0j8JvYF7XvRG", "price_1NqSBIDNUMHo0j8J5WV0aUX3"]
WEBDEV_PRICE_IDS = ["price_1NqS9SDNUMHo0j8JM4dCImE0", "price_1NqS9SDNUMHo0j8JW1Muzlf4", "price_1NqS9SDNUMHo0j8J2gHVo7yd", "price_1NqS9SDNUMHo0j8JJwHNpStV", "price_1NqS9TDNUMHo0j8JKMzqGIBv", "price_1NqS9TDNUMHo0j8Jy3RA8fw5"]
WEBDEV_MONTHLY_PRICE_IDS = ["price_1ObFDTDNUMHo0j8JKmX3FKsW", "price_1ObFDcDNUMHo0j8J1ft3uhf8", "price_1ObFDlDNUMHo0j8JAK5B0GgL", "price_1ObFDsDNUMHo0j8JqS5IeNxK", "price_1ObFDzDNUMHo0j8JqHKhtuNM", "price_1ObFEBDNUMHo0j8JZbhoKEst"]
#"price_1Koi4MDNUMHo0j8JUjVdK5ZA", "price_1KoVXmDNUMHo0j8JMyudvUja", "price_1Nqp3VDNUMHo0j8JY6soNnfk", "price_1Koi4VDNUMHo0j8JsLO8HabI", "price_1NqgdRDNUMHo0j8JAmUB03Kv", "price_1Koi4MDNUMHo0j8JUjVdK5ZA", "price_1KoVXmDNUMHo0j8JMyudvUja",
PROFILE_MEMBERSHIP_PRICE_IDS = ["price_1Koi4MDNUMHo0j8JUjVdK5ZA", "price_1KoVXmDNUMHo0j8JMyudvUja", "price_1Nqp3VDNUMHo0j8JY6soNnfk", "price_1Koi4VDNUMHo0j8JsLO8HabI", "price_1NqgdRDNUMHo0j8JAmUB03Kv", "price_1Koi4bDNUMHo0j8JauWHhYQA", "price_1NqgdgDNUMHo0j8JdknpoCgx", "price_1Koi4iDNUMHo0j8Js6rMAm3K", "price_1NqgfHDNUMHo0j8JyRky2t3w", "price_1NqgfMDNUMHo0j8JpWmXfSOh", "price_1NqgfTDNUMHo0j8Jc1UsGaHo", "price_1NqgfaDNUMHo0j8JMllYt5sL"]
PROFILE_MEMBERSHIP = "prod_RFyWOX5WwZ7Asq"
PHOTO_PRICE = "prod_RFyUZ2TFWuHb5E"
PHOTO_PRICE_IDS = ["price_1NqS6fDNUMHo0j8JSsibkHw7", "price_1NqS6fDNUMHo0j8JRl4UFBZv", "price_1NqS6fDNUMHo0j8JC15M3yPW", "price_1NqS6fDNUMHo0j8JJdkeCaUB", "price_1NqS6fDNUMHo0j8Jm9ocRrHv", "price_1NqS6fDNUMHo0j8Jocts6Mkh"]
WEBDEV_DESCRIPTIONS = ["Simple, static website. Ideal for businesses that don't need interactivity, just a business page with contacts, information, and photos.",
    "Basic website with simple interactivity, modals, and user logins. Ideal for small businesses that don't need complex interactivity or marketing.",
    "Complex website with email marketing. Ideal for small to mid sized businesses, campaigns, and websites that need basic marketing features and many pages.",
    "Complex website with email, SMS, webpush, Google News, and social marketing features. Good for mid-size businesses with marketing needs.",
    "Advanced website with security options, scalable design, image and video uploads, comprehensive compliance features, bluetooth capability, 3D rendering, negotiable options. Ideal for scientific and industrial needs in large scale businesses.",
    "Advanced website with facial recognition, biometric security, advanced login, custom authentication, barcode scanning, machine learning and more. Preceding features included. Ideal for large projects and governments. Multiple options available.",
]
SURROGACY_PRICE_ID = "price_1OBuzfDNUMHo0j8JEKdChyTl"
CART_ID = "prod_RFyYRWQb3e6uvm"

import stripe
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User

def create_connected_account(user_id):
    stripe.api_key = settings.STRIPE_API_KEY
    user = User.objects.get(id=user_id)
    if not user.profile.stripe_id:
        account = stripe.Account.create(
            type='custom',
            country='US',
            email=user.email,
            capabilities={
                "transfers": {"requested": True},
                "card_payments": {"requested": True},
            },
        )
        user.profile.stripe_id = account.id
        user.profile.save()
    return stripe.AccountLink.create(
        account=user.profile.stripe_id,
        refresh_url=settings.BASE_URL + reverse('payments:create-link'),
        return_url=settings.BASE_URL + reverse('users:profile'),
        type="account_onboarding",
    )['url']
```


--- File: lotteharper-main/payments/surrogacy.py ---
```python
def save_and_send_agreement(mother, parent):
    from payments.agreements import generate_surrogacy_agreement
    text = render_agreement(mother.verifications.last().full_name, parent, mother)
    path = generate_surrogacy_agreement(parent.verifications.last().full_name.replace(' ', '_') + '-x-' + mother.verifications.last().full_name.replace(' ', '_'), text, [parent, None, mother, None])
    from .models import SurrogacyAgreement
    from django.conf import settings
    a = SurrogacyAgreement.objects.create(intended_parent=parent, mother=mother, agreement=path, signed=True, unpaid=settings.SURROGACY_FEE)
    from users.email import send_html_email_template
    send_html_email_template(parent, 'Expected Parent, Here is Your Surrogacy Agreement from {}'.format(settings.SITE_NAME), 'Dear {}\n'.format(parent.verifications.last().full_name) + 'Attached is your copy of the surrogacy agreement you signed with {}. This agreement will be carried out within one year.\n'.format(mother.verifications.last().full_name) + 'Thank you for your loyalty and we look forward to working with you. We will be in touch soon to organize details for medical procedures.\nSincerely, {}'.format(settings.SITE_NAME), attachments=[path])
    send_html_email_template(mother, 'Expected Mother, Here is Your Surrogacy Agreement from {}'.format(settings.SITE_NAME), 'Dear {}\n'.format(mother.verifications.last().full_name) + 'Attached is your copy of the surrogacy agreement you signed with {}. This agreement will be carried out within one year.\n'.format(parent.verifications.last().full_name) + 'Thank you for your loyalty and we look forward to working with you. We will be in touch soon to organize details for medical procedures.\nSincerely, {}'.format(settings.SITE_NAME), attachments=[path])
    a.sent = True
    a.save()
```


--- File: lotteharper-main/payments/templates/payments/buy_photo_card.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block head %}
{% if payment_processor == 'helcim' %}
<script type="text/javascript" src="https://secure.helcim.app/helcim-pay/services/start.js"></script>
{% elif payment_processor == 'stripe' %}
<script src="https://js.stripe.com/v3/"></script>
{% endif %}
<!--<script src="https://js.stripe.com/v3/"></script>-->
{% endblock %}
{% block styles %}
#card-info-parent * {
  margin-left: 3px;
  margin-right: 3px;
}
{% endblock %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
<h1><i class="bi bi-credit-card-fill"></i> {{ 'Buy this'|etrans }} {% if not post.file %}{{ 'photo'|etrans }}{% else %}{{ 'product'|etrans }}{% endif %} {{ 'of'|etrans }} @{{ username }} {{ 'with Card'|etrans }}</h1>
{% if post.image and post.public and not post.private %}<img class="mr-2 img-fluid rounded" style="float: left; width: 50%; max-width: 400px; margin-right: 13px;" src="{{ post.get_blur_thumb_url }}" alt="{{ 'Buy this photo for'|etrans }} ${{ fee|sub_fee }} USD"></img>
{% elif post.image and post.private or not post.public %}<img class="mr-2 img-fluid rounded" style="float: left; filter: blur(8px); width: 50%; max-width: 400px; margin-right: 13px;" src="{{ post.get_blur_thumb_url }}" alt="{{ 'Buy this photo for'|etrans }} ${{ fee|sub_fee }} USD"></img>{% endif %}
<div style="display: inline-block;">
    <a href="{{ request.path }}{% if request.GET.coupon %}?coupon={{ request.GET.coupon }}{% endif %}" title="{{ 'See another photo'|etrans }}" class="btn btn-outline-dark pink-borders">{{ 'See Another Photo'|etrans }}</a>
</div>
<div style="text-align: center;">
	<img alt="Accepting Visa and Mastercard" style="height: auto; width: 80%; max-width: 90px;" height="auto" src="/media/static/visa-mastercard.png"></img>
</div>
<p><button class="btn btn-outline-info" title="{{ 'Add this to your cart'|etrans }}" onclick="addToCart('{{ post.uuid }}');">{{ 'Add to Cart'|etrans }} <i><b id="total{{ post.uuid }}"></b></i></button></p>
<b>{{ 'Items:'|etrans }}</b>
<ul>
<li>{{ 'One private'|etrans }} {% if not post.file %}{{ 'photo'|etrans }}{% else %}{{ 'download, video or audio'|etrans }}{% endif %} {{ 'featuring'|etrans }} {{ username }} (${{ fee|sub_fee }})</li>
<li>{{ 'Billed once only.'|etrans }}</li>
</ul>
<p><i>{{ 'Want to pay with cryptocurrency instead?'|etrans }}</i> <a href="{% url 'payments:buy-photo-crypto' post.author.profile.name %}?id={{ post.uuid }}&crypto={{ default_crypto }}" class="btn btn-outline-info" title="{{ 'Pay with crypto'|etrans }}">{{ 'Pay with Cryptocurrency'|etrans }}</a></p>
<b>{{ 'Info:'|etrans }}</b>
<p>{{ 'The transaction will display on your bank statement as'|etrans }} "{{ statement_descriptor }} AUDIOVISUAL".</p>
<p>{{ 'For questions or concerns, please contact'|etrans }} {{ the_site_name }} {{ 'at'|etrans }} {{ agent_phone }} {{ 'or mail to'|etrans }} {{ agent_name }} {{ agent_address }}.</p>
<p>{{ 'You will pay'|etrans }} ${{ fee|sub_fee }} USD. {{ 'Please enter your credit or debit card information.'|etrans }}</p>
{% if request.GET.coupon %}
<p><legend>{{ 'You have received a coupon!'|etrans }}</legend> - {{ 'Use coupon code'|etrans }} <b id="coupon-code">{{ request.GET.coupon }}</b> <button class="btn btn-primary btn-sm" onclick="copyToClipboard('coupon-code');">{{ 'Copy'|etrans }}</button> {{ 'at checkout to get a discount on your purchase.'|etrans }}</p>
{% endif %}
<hr style="background-color: blue;">
<form id="pay-form" onsubmit="event.preventDefault(); payFee();">
{{ form|crispy }}
<button type="submit" class="btn btn-lg btn-outline-success" title="{{ 'Submit'|etrans }}">{{ 'Submit'|etrans }}</button>
</form>
</div>
<hr>
{% include 'social.html' %}
{% endblock %}
{% block javascript %}
var product = 'post';
var pid = {{ post.id }};
var price = {{ post.price }};
var vendor = {{ post.author.id }};
var payForm = document.getElementById('pay-form');
var checkoutToken;
{% if payment_processor == 'paypal' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:paypal-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'square' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:square-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'helcim' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:invoice' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            var j = JSON.parse(data);
            checkoutToken = j.checkoutToken;
            $(document.getElementById("clemn-navbar")).autoHidingNavbar().hide();
            appendHelcimPayIframe(j.checkoutToken);
        },
    });
}
window.addEventListener('message', (event) => {

  const helcimPayJsIdentifierKey = 'helcim-pay-js-' + checkoutToken;

  if(event.data.eventName === helcimPayJsIdentifierKey){

    if(event.data.eventStatus === 'ABORTED'){
      console.error('Transaction failed!', event.data.eventMessage);
    }

    if(event.data.eventStatus === 'SUCCESS'){
      validateResponse(event.data.eventMessage)
        .then(response => console.log(response))
        .catch(err => console.error(err));
    }
  }
});
function validateResponse(eventMessage) {
  const payload = {
    'rawDataResponse': eventMessage.data,
  };
  return fetch('{{ base_url }}/payments/helcim/', {body: payload, method: "POST"});
}
{% elif payment_processor == 'stripe' %}
var stripe = Stripe('{{ stripe_pubkey }}');
function payFee(){
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
        fetch("/payments/audiovisual/checkout/?photo={{ post.id }}&email=" + email)
          .then((result) => {
            return result.json();
          })
          .then((data) => {
            return stripe.redirectToCheckout({ sessionId: data.sessionId });
          });
}
{% endif %}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/buy_photo_card.html.save ---
```
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block head %}
{% if payment_processor == 'helcim' %}
<script type="text/javascript" src="https://secure.helcim.app/helcim-pay/services/start.js"></script>
{% elif payment_processor == 'stripe' %}
<script src="https://js.stripe.com/v3/"></script>
{% endif %}
{% endblock %}
{% block styles %}
#card-info-parent * {
  margin-left: 3px;
  margin-right: 3px;
}
{% endblock %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
<h1><i class="bi bi-credit-card-fill"></i> {{ 'Buy this'|etrans }} {% if not post.file %}{{ 'photo'|etrans }}{% else %}{{ 'product'|etrans }}{% endif %} {{ 'of'|etrans }} @{{ username }} {{ 'with Card'|etrans }}</h1>
{% if post.image and post.public and not post.private %}<img class="mr-2 img-fluid rounded" style="float: left; width: 50%; max-width: 400px; margin-right: 13px;" src="{{ post.get_blur_thumb_url }}" alt="{{ 'Buy this photo for'|etrans }} ${{ fee|sub_fee }} USD"></img>
{% elif post.image and post.private or not post.public %}<img class="mr-2 img-fluid rounded" style="float: left; filter: blur(8px); width: 50%; max-width: 400px; margin-right: 13px;" src="{{ post.get_blur_thumb_url }}" alt="{{ 'Buy this photo for'|etrans }} ${{ fee|sub_fee }} USD"></img>{% endif %}
<div style="display: inline-block;">
    <a href="{{ request.path }}{% if request.GET.coupon %}?coupon={{ request.GET.coupon }}{% endif %}" title="{{ 'See another photo'|etrans }}" class="btn btn-outline-dark pink-borders">{{ 'See Another Photo'|etrans }}</a>
</div>
<div style="text-align: center;">
	<img alt="Accepting Visa and Mastercard" style="height: auto; width: 80%; max-width: 90px;" height="auto" src="/media/static/visa-mastercard.png"></img>
</div>
<p><button class="btn btn-outline-info" title="{{ 'Add this to your cart'|etrans }}" onclick="addToCart('{{ post.uuid }}');">{{ 'Add to Cart'|etrans }} <i><b id="total{{ post.uuid }}"></b></i></button></p>
<b>Items:</b>
<ul>
<li>{{ 'One private'|etrans }} {% if not post.file %}{{ 'photo'|etrans }}{% else %}{{ 'download, video or audio'|etrans }}{% endif %} {{ 'featuring'|etrans }} {{ username }} (${{ fee|sub_fee }})</li>
<li>{{ 'Billed once only.'|etrans }}</li>
</ul>
<p><i>{{ 'Want to pay with cryptocurrency instead?'|etrans }}</i> <a href="{% url 'payments:buy-photo-crypto' post.author.profile.name %}?id={{ post.id }}&crypto={{ default_crypto }}" class="btn btn-outline-info" title="{{ 'Pay with crypto'|etrans }}">{{ 'Pay with Cryptocurrency'|etrans }}</a></p>
<b>{{ 'Info:'|etrans }}</b>
<p>{{ 'The transaction will display on your bank statement as'|etrans }} "{{ statement_descriptor }} AUDIOVISUAL".</p>
<p>{{ 'For questions or concerns, please contact'|etrans }} {{ the_site_name }} {{ 'at'|etrans }} {{ agent_phone }} {{ 'or mail to'|etrans }} {{ agent_name }} {{ agent_address }}.</p>
<p>{{ 'You will pay'|etrans }} ${{ fee|sub_fee }} USD. {{ 'Please enter your credit or debit card information.'|etrans }}</p>
{% if request.GET.coupon %}
<p><legend>{{ 'You have received a coupon!'|etrans }}</legend> - {{ 'Use coupon code'|etrans }} <b id="coupon-code">{{ request.GET.coupon }}</b> <button class="btn btn-primary btn-sm" onclick="copyToClipboard('coupon-code');">{{ 'Copy'|etrans }}</button> {{ 'at checkout to get a discount on your purchase.'|etrans }}</p>
{% endif %}
<hr style="background-color: blue;">
<form id="pay-form" onsubmit="event.preventDefault(); payFee();">
{{ form|crispy }}
button type="submit" class="btn btn-lg btn-outline-success" title="{{ 'Submit'|etrans }}">{{ 'Submit'|etrans }}</button>
</form>
</div>
<hr>
{% include 'social.html' %}
{% endblock %}
{% block javascript %}
var product = 'post';
var pid = {{ post.id }};
var price = {{ post.price }};
var vendor = {{ post.author.id }};
var payForm = document.getElementById('pay-form');
var checkoutToken;
{% if payment_processor == 'paypal' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:paypal-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'square' %}
pid = '{{ post.uuid }}';
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:square-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'helcim' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:invoice' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            var j = JSON.parse(data);
            checkoutToken = j.checkoutToken;
            $(document.getElementById("clemn-navbar")).autoHidingNavbar().hide();
            appendHelcimPayIframe(j.checkoutToken);
        },
    });
}
window.addEventListener('message', (event) => {

  const helcimPayJsIdentifierKey = 'helcim-pay-js-' + checkoutToken;

  if(event.data.eventName === helcimPayJsIdentifierKey){

    if(event.data.eventStatus === 'ABORTED'){
      console.error('Transaction failed!', event.data.eventMessage);
    }

    if(event.data.eventStatus === 'SUCCESS'){
      validateResponse(event.data.eventMessage)
        .then(response => console.log(response))
        .catch(err => console.error(err));
    }
  }
});
function validateResponse(eventMessage) {
  const payload = {
    'rawDataResponse': eventMessage.data,
  };
  return fetch('{{ base_url }}/payments/helcim/', {body: payload, method: "POST"});
}
{% elif payment_processor == 'stripe' %}
var stripe = Stripe('{{ stripe_pubkey }}');
function payFee(){
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
        fetch("/payments/audiovisual/checkout/?photo={{ post.id }}&email=" + email)
          .then((result) => {
            return result.json();
          })
          .then((data) => {
            return stripe.redirectToCheckout({ sessionId: data.sessionId });
          });
}
{% endif %}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/buy_photo_crypto.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %} 
{% block head %}
<script src="https://js.stripe.com/v3/"></script>
<script src="https://crypto-js.stripe.com/crypto-onramp-outer.js"></script>
{% endblock %}
{% block content %} 
<div class="container rounded shadow col-md-6 mx-auto">
<h1><i class="bi bi-credit-card-fill"></i> {{ 'Buy this'|etrans }} {% if not post.file %}{{ 'photo of'|etrans }}{% else %}{{ 'product from'|etrans }}{% endif %} @{{ username }} {{ 'with Crypto'|etrans }}</h1>
<div class="container">
<div class="row">
<div class="col-md-6">
{% if post.image and post.public and not post.private %}<img class="mr-2 img-fluid rounded" style="float: left; width: 100%; max-width: 400px; margin-right: 13px;" src="{{ post.get_blur_thumb_url }}" alt="{{ 'Buy this photo for'|etrans }} ${{ fee|sub_fee }} USD"></img>{% elif post.image and post.private or not post.public %}<img class="mr-2 img-fluid rounded" style="float: left; filter: blur(8px); width: 100%; max-width: 400px; margin-right: 13px;" src="{{ post.get_blur_thumb_url }}" alt="{{ 'Buy this photo for'|etrans }} ${{ fee|sub_fee }} USD"></img>{% endif %}
</div>
<div class="col-md-6">
<div style="display: inline-block;">
<a href="{{ request.path }}?crypto={{ request.GET.crypto }}{% if request.GET.lightning %}&lightning=t{% endif %}" title="{{ 'See another photo'|etrans }}" class="btn btn-outline-dark pink-borders">{{ 'See Another Photo'|etrans }}</a>
{% if not request.COOKIES.age_verified %}<a href="{% url 'verify:age' %}?next={{ request.path }}?crypto={{ request.GET.crypto }}{% if request.GET.lightning %}&lightning=t{% endif %}" title="{{ 'See private photos'|etrans }}" class="btn btn-outline-dark pink-borders">{{ 'See Private Photos'|etrans }}</a>{% endif %}
<hr>
<p>{{ 'This purchase is subject to'|etrans }} <a href="{% url 'misc:terms' %}" title="{{ 'View the terms and coniditons'|etrans }}">{{ 'the terms and conditions and privacy policy'|etrans }}</a> {{ 'of'|etrans }} {{ the_site_name }}.</p>
<div class="dropdown" style="display: inline-block;">
    <a class="btn btn-outline-dark pink-borders dropdown-toggle" role="button" id="dropdownMenuLink" data-bs-toggle="dropdown" aria-expanded="false">
    	<i class="bi bi-currency-bitcoin"></i> {{ 'Change Currency'|etrans }}
    </a>
  <ul class="dropdown-menu" aria-labelledby="dropdownMenuLink">
    <div style="max-height: 50vh; overflow: scroll;">
        <li><a class="dropdown-item" href="{{ request.path }}?lightning=t&crypto=BTC&id={{ post.uuid }}">BTC (Lightning Network)</a></li>
	{% for currency in currencies %}
		<li><a class="dropdown-item" href="{{ request.path }}?crypto={{ currency }}&id={{ post.uuid }}">{{ currency }}{% if forloop.counter < 6 %} - {{ 'Fiat options'|etrans }}{% endif %}</a></li>
	{% endfor %}
    </div>
  </ul>
</div>
<button class="btn btn-outline-primary" title="{{ 'Add this to your cart'|etrans }}" onclick="addToCart('{{ post.uuid }}');">{{ 'Add to Cart'|etrans }} <i><b id="total{{ post.uuid }}"></b></i></button>
</div>
</div>
</div>
</div>
<b>{{ 'Items:'|etrans }}</b>
<ul>
<li>{{ 'One private'|etrans }} {% if not post.file %}{{ 'photo'|etrans }}{% else %}{{ 'download, video or audio'|etrans }}{% endif %} {{ 'featuring'|etrans }} {{ username }} (${{ usd_fee|sub_fee }})</li>
<li>{{ 'Billed once only.'|etrans }}</li>
</ul>
<p>{{ 'Want to pay for this Crypto purchase with card?'|etrans }} <button onclick="payWithCard();" class="btn btn-outline-primary" title="{{ 'Pay for your cryptocurrency purchase with card, bank, or other payment method'|etrans }}">{{ 'Pay with Card in Crypto'|etrans }}</button></p>
<div id="onramp-element" style="max-width: 500px" class="mx-auto"><!--{% if request.GET.crypto == 'ALPH' %}<p>{{ 'To pay with your'|etrans }} Alephium (ALPH) {{ 'please'|etrans }} <a href="https://bridge.alephium.org/" title="{{ 'Use the'|etrans }} Alephium Bridge {{ 'to send'|etrans }} Alephium (ALPH)" target="_blank">{{ 'use the'|etrans }} Alephium Bridge {{ 'to send cryptocurrency to the wallet in the invoice using'|etrans }} ETH {{ 'and'|etrans }} Alephium (ALPH)</a></p>{% endif %}-->
<form method="POST" enctype="multipart/form-data">
{% csrf_token %}
<fieldset class="form-group">
<legend class="border-bottom mb-4">{{ 'Step 1: Send Crypto'|etrans }}</legend>
{% load app_filters %} 
<p>{{ 'Send'|etrans }} {{ crypto_fee|cryptoformat }} {{ request.GET.crypto|fixalph }} <button class="btn btn-sm btn-info" type="button" onclick="copyAmount();"><i class="bi bi-clipboard-check-fill"></i> {{ 'Copy'|etrans }}</button> (${{ usd_fee|sub_fee }}) {{ 'to the following wallet address:'|etrans }}</p>
<b><i>{{ crypto_address }}</i></b>
<button class="btn btn-sm btn-info" type="button" onclick="copyAddress();"><i class="bi bi-clipboard-check-fill"></i> {{ 'Copy'|etrans }}</button>
<hr style="background-color: green;">
<p>{% if not request.user.is_authenticated %}{{ 'Enter your email and press'|etrans }}{% else %}{{ 'Press'|etrans }}{% endif %} {{ 'the "Send" button to confirm your payment once you have initiated the transfer.'|etrans }}</p>
{{ form|crispy }}
<button type="submit" class="btn btn-outline-success">{{ 'Send'|etrans }}</button>
</form>
</div>
<div style="display: flex; justify-content: space-around;"><div id="paymentqrcode" style="border-style: solid; border-width: 15px; border-radius: 5px; border-color: #EEEEEE;"></div></div>
<div style="text-align: center;"><small>{{ 'Scan this QR code to pay with your Crypto wallet or bank'|etrans }}</small></div>
<hr>
{% if not request.GET.crypto == 'ALPH' %}<p>{{ 'To pay with'|etrans }} Alephium (ALPH) {{ 'please select'|etrans }} ETH (Ethereum) {{ 'as your currency and'|etrans }} <a href="https://bridge.alephium.org/" target="_blank" title="{{ 'Use the'|etrans }} Alephium Bridge {{ 'to send'|etrans }} Alephium (ALPH)">{{ 'use the'|etrans }} Alephium Bridge {{ 'to send cryptocurrency to the wallet in the invoice using'|etrans }} ETH {{ 'and'|etrans }} Alephium (ALPH)</a></p>{% endif %}
<p>{{ 'Buy crypto to send here:'|etrans }} <a href="{{ crypto_provider }}" title="{{ 'Buy crypto to send'|etrans }}">{{ crypto_provider }}</a>, {{ 'or with your crypto bank.'|etrans }}</p>
{% include 'social.html' %}
{% endblock %}
{% block javascript %}
/*var im = document.getElementById("post-image");
im.style.height = im.offsetWidth;
$(document).ready(function() {
    im.style.height = im.offsetWidth;
});*/
function copyAddress() {
	navigator.clipboard.writeText("{{ crypto_address }}");
}
function copyAmount() {
	navigator.clipboard.writeText("{{ crypto_fee }}");
}
var pqrdiv = document.getElementById("paymentqrcode");
$(pqrdiv).kjua({text: "{{ crypto_address }}", render: 'svg'});
var pimage = pqrdiv.querySelector('svg');
pimage.style.width = "100%";
pimage.style.height = "auto";
pimage.style.maxWidth = "250px";
pimage.alt = "{{ 'Scan this code to pay with a crypto wallet or bank'|etrans }}";
function payWithCard() {
    var paymentCrypto = "{{ request.GET.crypto }}";
    const onramp = window.StripeOnramp('{{ stripe_key }}');
    $.ajax({
        url: '{% url 'payments:crypto-onramp' username crypto_address usd_fee %}?crypto=' + paymentCrypto,
        method: 'POST',
        error: function() {
            window.location.href = '{{ request.path }}?id={{ post.uuid }}&crypto=ETH';
        },
        success: function(clientSecret) {
            try {
            onrampSession = onramp.createSession({clientSecret});
            onrampSession.mount("#onramp-element");
            } catch {
                window.location.href = '{{ request.path }}?id={{ post.uuid }}&crypto=ETH';
            }
        }
    });
}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/cancel.html ---
```html
{% extends 'base.html' %}
{% block content %}
{% load feed_filters %}
{% load app_filters %}
        <form method="POST">
            {% csrf_token %}
            <fieldset class="form-group">
                <legend class="border-bottom mb-4">{{ 'Cancel subscription'|etrans }}</legend>
                <h2>{{ 'Are you sure you want to unsubscribe from'|etrans }} {{ model.profile.name }}?</h2>
            </fieldset>
            <div class="form-group">
                <button class="btn btn-outline-danger" type="submit" title="{{ 'Unsubscribe from'|etrans }} {{ model.profile.name }}">{{ 'Yes, Unsubscribe'|etrans }}</button>
                <a class="btn btn-outline-secondary" href="{% url 'feed:profile' model.profile.name %}" title="{{ 'Go back'|etrans }}">{{ 'Go back'|etrans }}</a>
            </div>
        </form>
{% endblock content %}
```


--- File: lotteharper-main/payments/templates/payments/cancel_payment.html ---
```html
{% extends 'base.html' %}
{% block content %}
{% load app_filters %}
<h1>{{ 'Payment Cancelled'|etrans }}</h1>
<p>{{ 'Your payment was cancelled successfully. We are sad to see you go! Please consider us again in the future. Is there anything in particular you need or any questions you would like to ask? Use the form below to contact me.'|etrans }}</p>
{% include 'contact/form.html' %}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/card_card.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block head %}
{% if payment_processor == 'helcim' %}
<script type="text/javascript" src="https://secure.helcim.app/helcim-pay/services/start.js"></script>
{% elif payment_processor == 'stripe' %}
<script src="https://js.stripe.com/v3/"></script>
{% endif %}
<!--<script src="https://js.stripe.com/v3/"></script>-->
{% endblock %}
{% block styles %}
#card-info-parent * {
  margin-left: 3px;
  margin-right: 3px;
}
{% endblock %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
<h1><i class="bi bi-credit-card-fill"></i> Buy this {% if not post.file %}photo{% else %}product{% endif %} of @{{ username }} with Card</h1>
{% if post.image %}<img class="mr-2 img-fluid rounded" style="float: left; filter: blur(8px); width: 50%; max-width: 400px; margin-right: 13px;" src="{{ post.get_blur_thumb_url }}" alt="Buy this photo for ${{ fee|sub_fee }} USD"></img>{% endif %}
<div style="display: inline-block;">
<a href="{{ request.path }}{% if request.GET.coupon %}?coupon={{ request.GET.coupon }}{% endif %}" title="See another photo" class="btn btn-outline-dark pink-borders">See Another Photo</a>
</div>
<div style="text-align: center;">
	<img alt="Accepting Visa and Mastercard" style="height: auto; width: 80%; max-width: 90px;" height="auto" src="/media/static/visa-mastercard.png"></img>
</div>
<b>Items:</b>
<ul>
<li>One private {% if not post.file %}photo{% else %}download, video or audio{% endif %} featuring {{ username }} (${{ fee|sub_fee }})</li>
<li>Billed once only.</li>
</ul>
<b>Info:</b>
<p>The transaction will display on your bank statement as "{{ statement_descriptor }} AUDIOVISUAL".</p>
<p>For questions or concerns, please contact {{ the_site_name }} at {{ agent_phone }} or mail to {{ agent_name }} {{ agent_address }}.</p>
<p>You will pay ${{ fee|sub_fee }} USD. Please enter your credit or debit card information.</p>
{% if request.GET.coupon %}
<p><legend>You have received a coupon!</legend> - Use coupon code <b id="coupon-code">{{ request.GET.coupon }}</b> <button class="btn btn-primary btn-sm" onclick="copyToClipboard('coupon-code');">Copy</button> at checkout to get a discount on your purchase.</p>
{% endif %}
<hr style="background-color: blue;">
<form id="pay-form" onsubmit="event.preventDefault(); payFee();">
{{ form|crispy }}
<button type="submit" class="btn btn-lg btn-outline-success" title="Submit">Submit</button>
</form>
</div>
<hr>
{% include 'social.html' %}
{% endblock %}
{% block javascript %}
var product = 'post';
var pid = {{ post.id }};
var price = {{ post.price }};
var vendor = {{ post.author.id }};
var payForm = document.getElementById('pay-form');
var checkoutToken;
{% if payment_processor == 'paypal' %}
function payFee() {
    var email = document.getElementById('id_email').value;
    $.ajax({
        url: '{{ base_url }}{% url 'payments:paypal-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'square' %}
function payFee() {
    var email = document.getElementById('id_email').value;
    $.ajax({
        url: '{{ base_url }}{% url 'payments:square-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'helcim' %}
function payFee() {
    var email = document.getElementById('id_email').value;
    $.ajax({
        url: '{{ base_url }}{% url 'payments:invoice' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            var j = JSON.parse(data);
            checkoutToken = j.checkoutToken;
            $(document.getElementById("clemn-navbar")).autoHidingNavbar().hide();
            appendHelcimPayIframe(j.checkoutToken);
        },
    });
}
window.addEventListener('message', (event) => {

  const helcimPayJsIdentifierKey = 'helcim-pay-js-' + checkoutToken;

  if(event.data.eventName === helcimPayJsIdentifierKey){

    if(event.data.eventStatus === 'ABORTED'){
      console.error('Transaction failed!', event.data.eventMessage);
    }

    if(event.data.eventStatus === 'SUCCESS'){
      validateResponse(event.data.eventMessage)
        .then(response => console.log(response))
        .catch(err => console.error(err));
    }
  }
});
function validateResponse(eventMessage) {
  const payload = {
    'rawDataResponse': eventMessage.data,
  };
  return fetch('{{ base_url }}/payments/helcim/', {body: payload, method: "POST"});
}
{% elif payment_processor == 'stripe' %}
var stripe = Stripe('{{ stripe_pubkey }}');
function payFee(){
        fetch("/payments/audiovisual/checkout/?photo={{ post.id }}")
          .then((result) => {
            return result.json();
          })
          .then((data) => {
            return stripe.redirectToCheckout({ sessionId: data.sessionId });
          });
}
{% endif %}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/cart_card.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block head %}
{% if payment_processor == 'helcim' %}
<script type="text/javascript" src="https://secure.helcim.app/helcim-pay/services/start.js"></script>
{% elif payment_processor == 'stripe' %}
<script src="https://js.stripe.com/v3/"></script>
{% endif %}
<!--<script src="https://js.stripe.com/v3/"></script>-->
{% endblock %}
{% block styles %}
#card-info-parent * {
  margin-left: 3px;
  margin-right: 3px;
}
{% endblock %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
<h1><i class="bi bi-credit-card-fill"></i> {{ 'Checkout'|etrans }}</h1>
<p style="text-align: right;"><button class="btn btn-sm btn-outline-danger" title="{{ 'Clear cart'|etrans }}" onclick="setCookie('cart', '', 30); window.location.reload();">{{ 'Clear'|etrans }}</button></p>
<p>{{ 'Want to pay in crypto?'|etrans }} <a href="{% url 'payments:cart-crypto' %}?crypto={{ default_crypto }}" title="{{ 'Shopping Cart'|etrans }}" class="btn btn-lg btn-outline-primary"><i class="bi bi-bitcoin"></i> {{ 'Pay in Crypto'|etrans }}</a></p>
<div style="text-align: center;">
	<img alt="Accepting Visa and Mastercard" style="height: auto; width: 80%; max-width: 90px;" height="auto" src="/media/static/visa-mastercard.png"></img>
</div>
<p class="hide" id="copy-cart">{{ base_url }}/payments/cart/?cart={{ cart }}</p>
<p style="text-align: center;"><button class="btn btn-lg btn-outline-primary" title="Refresh cart" onclick="window.location.reload();">{{ 'Update Cart'|etrans }}</button> - <button class="btn btn-sm btn-outline-primary" title="{{ 'Copy cart'|etrans }}" onclick="copyToClipboard('copy-cart');">{{ 'Copy Cart'|etrans }}</button></p>
<b>{{ 'Items'|etrans }}:</b>
{% autoescape off %}
{% if cart_contents %}
<p style="white-space: pre-wrap;">{{ cart_contents }}</p>
{% else %}
<p>{{ 'Your cart is currently empty.'|etrans }}</p>
{% endif %}
{% endautoescape %}
<ul>
<li>{{ 'Total:'|etrans }} (${{ fee|sub_fee }})</li>
<li>{{ 'Billed once only.'|etrans }}</li>
</ul>
<b>{{ 'Info:'|etrans }}</b>
<p>{{ 'The transaction will display on your bank statement as'|etrans }} "{{ statement_descriptor }} SHOP".</p>
<p>{{ 'For questions or concerns, please contact'|etrans }} {{ the_site_name }} {{ 'at'|etrans }} {{ agent_phone }} {{ 'or mail to'|etrans }} {{ agent_name }} {{ agent_address }}.</p>
<p>{{ 'You will pay'|etrans }} ${{ fee|sub_fee }} USD. {{ 'Please enter your credit or debit card information.'|etrans }}</p>
{% if request.GET.coupon %}
<p><legend>{{ 'You have received a coupon!'|etrans }}</legend> - {{ 'Use coupon code'|etrans }} <b id="coupon-code">{{ request.GET.coupon }}</b> <button class="btn btn-primary btn-sm" onclick="copyToClipboard('coupon-code');">{{ 'Copy'|etrans }}</button> {{ 'at checkout to get a discount on your purchase.'|etrans }}</p>
{% endif %}
<hr style="background-color: blue;">
<form id="pay-form" onsubmit="event.preventDefault(); payFee();">
{{ form|crispy }}
<button type="submit" class="btn btn-lg btn-outline-success" title="Submit">{{ 'Submit'|etrans }}</button>
</form>
</div>
<hr>
{% include 'social.html' %}
{% endblock %}
{% block javascript %}
var product = 'cart';
var pid = '0';
var price = {{ fee }};
var vendor = {{ vendor.id }};
var payForm = document.getElementById('pay-form');
var checkoutToken;
{% if payment_processor == 'paypal' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:paypal-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'square' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    var email = document.getElementById('id_email').value;
    $.ajax({
        url: '{{ base_url }}{% url 'payments:square-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'helcim' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:invoice' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            var j = JSON.parse(data);
            checkoutToken = j.checkoutToken;
            $(document.getElementById("clemn-navbar")).autoHidingNavbar().hide();
            appendHelcimPayIframe(j.checkoutToken);
        },
    });
}
window.addEventListener('message', (event) => {

  const helcimPayJsIdentifierKey = 'helcim-pay-js-' + checkoutToken;

  if(event.data.eventName === helcimPayJsIdentifierKey){

    if(event.data.eventStatus === 'ABORTED'){
      console.error('Transaction failed!', event.data.eventMessage);
    }

    if(event.data.eventStatus === 'SUCCESS'){
      validateResponse(event.data.eventMessage)
        .then(response => console.log(response))
        .catch(err => console.error(err));
    }
  }
});
function validateResponse(eventMessage) {
  const payload = {
    'rawDataResponse': eventMessage.data,
  };
  return fetch('{{ base_url }}/payments/helcim/', {body: payload, method: "POST"});
}
{% elif payment_processor == 'stripe' %}
var stripe = Stripe('{{ stripe_pubkey }}');
function payFee(){
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
        fetch("/payments/cart/checkout/?email=" + email, {
          method: "GET",
          headers: { "cart": "{{ cart_cookie }}" },
        })
          .then((result) => {
            return result.json();
          })
          .then((data) => {
            return stripe.redirectToCheckout({ sessionId: data.sessionId });
          });
}
{% endif %}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/cart_crypto.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %} 
{% block head %}
<script src="https://js.stripe.com/v3/"></script>
<script src="https://crypto-js.stripe.com/crypto-onramp-outer.js"></script>
{% endblock %}
{% block content %} 
<div class="container rounded shadow col-md-6 mx-auto">
<h1><i class="bi bi-credit-card-fill"></i> {{ 'Checkout with Crypto'|etrans }}</h1>
<div style="display: flex; justify-content: space-around;">
{% if post.image %}<img class="mr-2 rounded" style="float: left; filter: blur(8px); width: 40vw; height: 40vw; max-height: 400px; max-width: 400px; margin-right: 13px;" src="{{ post.get_blur_thumb_url }}" alt="Buy this photo for ${{ fee|sub_fee }} USD" id="post-image">{% endif %}
<div style="display: inline-block;">
<hr>
<p>{{ 'This purchase is subject to'|etrans }} <a href="{% url 'misc:terms' %}" title="{{ 'View the terms and coniditons'|etrans }}">{{ 'the terms and conditions and privacy policy'|etrans }}</a> {{ 'of'|etrans }} {{ the_site_name }}.</p>
<div class="dropdown" style="display: inline-block;">
    <a class="btn btn-outline-dark pink-borders dropdown-toggle" role="button" id="dropdownMenuLink" data-bs-toggle="dropdown" aria-expanded="false">
    	<i class="bi bi-currency-bitcoin"></i> {{ 'Change Currency'|etrans }}
    </a>
  <ul class="dropdown-menu" aria-labelledby="dropdownMenuLink">
    <div style="max-height: 50vh; overflow: scroll;">
		<li><a class="dropdown-item" href="{{ request.path }}?crypto=BTC&lightning=t">BTC (Lightning Network)</a></li>
	{% for currency in currencies %}
		<li><a class="dropdown-item" href="{{ request.path }}?crypto={{ currency }}">{{ currency }}{% if forloop.counter < 6 %} {{ 'Fiat options'|etrans }}{% endif %}</a></li>
	{% endfor %}
    </div>
  </ul>
</div>
</div>
<p style="text-align: center;"><button class="btn btn-sm btn-outline-danger" title="{{ 'Clear cart'|etrans }}" onclick="setCookie('cart', '', 30); window.location.reload();">{{ 'Clear'|etrans }}</button></p>
</div>
<p class="hide" id="copy-cart">{{ base_url }}/payments/cart/crypto/?cart={{ cart }}</p>
<p style="text-align: center;"><button class="btn btn-lg btn-outline-primary" title="{{ 'Refresh cart'|etrans }}" onclick="window.location.reload();">{{ 'Update Cart'|etrans }}</button> - <button class="btn btn-sm btn-outline-primary" title="{{ 'Copy cart'|etrans }}" onclick="copyToClipboard('copy-cart');">{{ 'Copy Cart'|etrans }}</button></p>
<b>{{ 'Items:'|etrans }}</b>
<ul>
{% autoescape off %}
{% if cart_contents %}
<p style="white-space: pre-wrap;">{{ cart_contents }}</p>
{% else %}
<p>{{ 'Your cart is currently empty.'|etrans }}</p>
{% endif %}
{% endautoescape %}
<li>{{ 'All items total'|etrans }} (${{ usd_fee|sub_fee }})</li>
<li>{{ 'Billed once only.'|etrans }}</li>
</ul>
{% if crypto_address %}
<p>{{ 'Want to pay for this Crypto purchase with card?'|etrans }} <button onclick="payWithCard();" class="btn btn-outline-primary" title="{{ 'Pay for your cryptocurrency purchase with card, bank, or other payment method'|etrans }}">{{ 'Pay with Card in Crypto'|etrans }}</button></p>
<div id="onramp-element" style="max-width: 500px" class="mx-auto">
<!--<p>{{ 'Send'|etrans }} {{ crypto_fee|cryptoformat }} {{ request.GET.crypto|fixalph }} <button class="btn btn-sm btn-info" type="button" onclick="copyAmount();"><i class="bi bi-clipboard-check-fill"></i> {{ 'Copy'|etrans }}</button> (${{ usd_fee|sub_fee }}) {{ 'to the following wallet address:'|etrans }}</p>-->
<form method="POST" enctype="multipart/form-data">
{% csrf_token %}
<fieldset class="form-group">
<legend class="border-bottom mb-4">{{ 'Step 1: Send Crypto'|etrans }}</legend>
<b><i>{{ crypto_address }}</i></b>
<button class="btn btn-sm btn-info" type="button" onclick="copyAddress();"><i class="bi bi-clipboard-check-fill"></i> {{ 'Copy'|etrans }}</button>
<hr style="background-color: green;">
<p>{% if not request.user.is_authenticated %}{{ 'Enter your email and press'|etrans }}{% else %}{{ 'Press'|etrans }}{% endif %} {{ 'the "Send" button to confirm your payment once you have initiated the transfer.'|etrans }}</p>
{{ form|crispy }}
<button type="submit" class="btn btn-outline-success">{{ 'Send'|etrans }}</button>
</form>
</div>
<div style="display: flex; justify-content: space-around;"><div id="paymentqrcode" style="border-style: solid; border-width: 15px; border-radius: 5px; border-color: #EEEEEE;"></div></div>
<div style="text-align: center;"><small>{{ 'Scan this QR code to pay with your Crypto wallet or bank'|etrans }}</small></div>
<hr>
{% if not request.GET.crypto == 'ALPH' %}<p>{{ 'To pay with'|etrans }} Alephium (ALPH) {{ 'please select'|etrans }} ETH (Ethereum) {{ 'as your currency and'|etrans }} <a href="https://bridge.alephium.org/" target="_blank" title="{{ 'Use the'|etrans }} Alephium Bridge {{ 'to send'|etrans }} Alephium (ALPH)">{{ 'use the'|etrans }} Alephium Bridge {{ 'to send cryptocurrency to the wallet in the invoice using'|etrans }} ETH {{ 'and'|etrans }} Alephium (ALPH)</a></p>{% endif %}
<p>{{ 'Buy crypto to send here:'|etrans }} <a href="{{ crypto_provider }}" title="{{ 'Buy crypto to send'|etrans }}">{{ crypto_provider }}</a>, {{ 'or with your crypto bank.'|etrans }}</p>
{% else %}
<p><i>{{ 'This crypto payment cannot be completed because the transaction is less than minimal for the currency selected. Please add more items or select a new currency.'|etrans }}</i></p>
{% endif %}
{% include 'social.html' %}
{% endblock %}
{% block javascript %}
/*var im = document.getElementById("post-image");
im.style.height = im.offsetWidth;
$(document).ready(function() {
    im.style.height = im.offsetWidth;
});*/
{% if crypto_address %}
function copyAddress() {
	navigator.clipboard.writeText("{{ crypto_address }}");
}
function copyAmount() {
	navigator.clipboard.writeText("{{ crypto_fee }}");
}
var pqrdiv = document.getElementById("paymentqrcode");
$(pqrdiv).kjua({text: "{{ crypto_address }}", render: 'svg'});
var pimage = pqrdiv.querySelector('svg');
pimage.style.width = "100%";
pimage.style.height = "auto";
pimage.style.maxWidth = "250px";
pimage.alt = "{{ 'Scan this code to pay with a crypto wallet or bank'|etrans }}";
{% endif %}
function payWithCard() {
    var paymentCrypto = "{{ request.GET.crypto }}";
    const onramp = window.StripeOnramp('{{ stripe_key }}');
    $.ajax({
        url: '{% url 'payments:crypto-onramp' username crypto_address usd_fee %}?crypto=' + paymentCrypto,
        method: 'POST',
        error: function() {
            window.location.href = '{{ request.path }}?crypto=ETH';
        },
        success: function(clientSecret) {
            try {
            onrampSession = onramp.createSession({clientSecret});
            onrampSession.mount("#onramp-element");
            } catch {
                window.location.href = '{{ request.path }}?crypto=ETH';
            }
        }
    });
}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/charge_card.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block styles %}
#card-info-parent * {
  margin-left: 3px;
  margin-right: 3px;
}
{% endblock %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
<legend><i class="bi bi-credit-card-fill"></i> Virtual Terminal</legend>
<a href="{% url 'payments:tip-crypto-simple' username %}" title="Get a crypto address to send money to" class="btn btn-outline-success">Crypto</a>
<div>
<b>Info:</b>
<p>The transaction will display on your bank statement as "MAMASHEEN".</p>
<p>For questions or concerns, please contact {{ the_site_name }} at {{ agent_phone }} or mail to {{ agent_name }} {{ agent_address }}.</p>
</div>
<form id="payment-form" method="POST" enctype="multipart/form-data">
{% csrf_token %}
<p>Please enter the customer, product, and credit or debit card information.</p>
{{ payment_form|crispy }}
{{ card_number_form|crispy }}
<div id="card-info-parent" style="display: flex; justify-content: space-around;">
{{ card_info_form|crispy }}
</div>
<hr style="background-color: blue;">
<button id="submit-button" type="submit" class="btn btn-outline-success">Charge</button>
</form>
</div>
{% endblock %}
{% block javascript %}
$('#payment-form').on('submit', function(){
	document.getElementById('submit-button').disabled = true;
});
{% endblock %}
{% block javascripts %}
{% autoescape off %}
{{ card_number_form.media|removejsig }}
{% endautoescape %}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/delete_card.html ---
```html
<form style="display: inline-block;" action="{% url 'payments:delete' card.id %}" method="POST" id="publishForm">
{% csrf_token %}
<button class="btn btn-outline-danger" type="submit"><i class="bi bi-x-circle-fill"></i></button>
</form>
```


--- File: lotteharper-main/payments/templates/payments/idscan.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block head %}
{% if payment_processor == 'helcim' %}
<script type="text/javascript" src="https://secure.helcim.app/helcim-pay/services/start.js"></script>
{% elif payment_processor == 'stripe' %}
<script src="https://js.stripe.com/v3/"></script>
{% endif %}
<script type="text/javascript" src="/static/js/prism.js"></script>
<link rel="stylesheet" href="/static/css/prism.css">
{% endblock %}
{% block content %}
{% load app_filters %}
{% include 'users/register_modal.html' %}
<h1>{{ 'Buy an ID Scanner Plan'|etrans }}</h1>
<p>{{ 'Scan IDs with your phone using compliant, easy to use software.'|etrans }}</p>
<legend>{{ 'Only'|etrans }} $0.50/{{ 'Scan'|etrans }} - <a class="btn btn-lg btn-outline-primary" title="{{ 'Free ID scanner for demonstration'|etrans }}" href="{% url 'misc:idscan' %}">{{ 'Free Demo'|etrans }}</a></legend>
<p style="text-align: center;">
<i class="bi bi-person-vcard" style="font-size: 120px;"></i>
</p>
<p>{{ 'This ID scanner is also available as an API, see the following example to scan an ID with Python, or parse already scanned ID information from an image.'|etrans }}</p>
<pre><code class="language-python"># {{ 'Parse the data on an ID with Python'|etrans }}
import requests, json
payload = {
    'key': '... {{ 'api key delivered with purchase'|etrans }} ...',
    'side': True, # True {{ 'for the front side of the ID, false for the back'|etrans }}
    'data': 'WA Washington Driver License 1234...' # {{ 'The text on the front of the ID according to OCR, or parsed barcode on the back'|etrans }}
}
result = json.loads(requests.get('{{ base_url }}{% url 'verify:api' %}', data=payload))
print(json.dumps(result))
# {{ 'example output:'|etrans }} "{'result': True, 'birthdate': '1980-12-19', 'age': 43, 'data': '{'classified': True}'}"
</code></pre>
<p>{{ 'Generate an authenticity result from an image of the back of an ID (the barcode).'|etrans }}</p>
<pre><code class="language-python"># {{ 'Extract the data from the ID'|etrans }}
from docbarcodes.extract import process_document # {{ 'See'|etrans }} https://pypi.org/project/docbarcodes/
# {{ 'Simple barcode reading'|etrans }}
barcodes_raw, barcodes_combined = process_document('document_back.png')
data = barcodes_raw['BarcodesRaw'][0]['raw']

# {{ 'Parse the data on an ID with Python'|etrans }}
import requests, json
payload = {
    'key': '... {{ 'api key delivered with purchase'|etrans }} ...',
    'side': False
    'data': data
}
result = json.loads(requests.get('{{ base_url }}{% url 'verify:api' %}', data=payload))
print(json.dumps(result))
# {{ 'example output:'|etrans }} "{'result': True, 'birthdate': '1980-12-19', 'age': 43, 'data': '{'classified': True}'}"
</code></pre>
<p>{{ 'Generate an authenticity result from an image of the front of an ID (the text).'|etrans }}</p>
<pre><code class="language-python"># {{ 'Extract the data from the ID'|etrans }}
from PIL import Image
import pytesseract # {{ 'See'|etrans }} https://pypi.org/project/pytesseract/
# Simple image to string
data = pytesseract.image_to_string(Image.open('document_front.png'))

# {{ 'Parse the data on an ID with Python'|etrans }}
import requests, json
payload = {
    'key': '... api key delivered with purchase ...',
    'side': True
    'data': data
}
result = json.loads(requests.get('{{ base_url }}{% url 'verify:api' %}', data=payload))
print(json.dumps(result))
# {{ 'example output:'|etrans }} "{'result': True, 'birthdate': '1980-12-19', 'age': 43, 'data': '{'classified': True}'}"
</code></pre>
<p>{{ 'Verify a user\'s identity with hosted pages and API enforcement.'|etrans }}</p>
<pre><code class="language-python"># {{ 'Step 1'|etrans }}: {{ 'Generate a URL to redirect the user to in order to complete identity verification'|etrans }}
import requests, json
payload = {
    'key': '... {{ 'api key delivered with purchase'|etrans }} ...',
    'next': 'https://thegreatestapp.com/customer/auth/' # {{ 'The next parameter to redirect a customer to'|etrans }}
}
result = json.loads(requests.get('{{ base_url }}{% url 'verify:flow-api' %}', data=payload))
print(json.dumps(result))
# {{ 'example output:'|etrans }} "{'adminurl': '{{ base_url }}/verify/...', 'userurl': '{{ base_url }}/face/...'}" {{ 'Parse the data on an ID with Python'|etrans }}
# Step 2: {{ 'Check the results of the user\'s identity verification with the URL delivered from the last result, after passing the user facing URL to the user.'|etrans }}
import requests
result = requests.get('{{ base_url }}/verify/...')
print(json.dumps(result))
# {{ 'example output:'|etrans }} "{'success': True }"
</code></pre>
<p>{{ 'Please select a plan below to begin using the API. Your account will be created at checkout.'|etrans }}</p>
<p><small>{{ 'Please note that an ID scanning plan is not requried for authentication with the app, only the API.'|etrans }}</small></p>
<hr>
<div class="container">
<div class="row" style="display: inline-block; text-align: center;">
{% for plan in plans %}
<div class="col-5 m-2 p-2 rounded" style="display: inline-block; background-color: #{% if darkmode %}555555{% else %}DDDDDD{% endif %};">
<p>{{ 'Tier'|etrans }} {{ forloop.counter|nts|capitalize }}</p>
<hr>
<legend>{{ plan|idscanprice|sub_fee }} {{ 'Scans/Month'|etrans }}</legend>
<button onclick="monthlyPlan({{plan}});" id="monthlyplan{{ plan }}" class="monthlyplan btn btn-lg btn-outline-success" title="{{ 'Subscribe to this plan'|etrans }}"><p>${{ plan|sub_fee }} {{ 'billed monthly'|etrans }}</p></button>
</div>
{% endfor %}
</div>
</div>
<hr>
<b>{{ 'Items:'|etrans }}</b>
<ul>
<li>{{ 'Subscription to ID document scanning services provided by'|etrans }} {{ the_site_name }}</li>
<li>{{ 'Billed monthly, until cancellation.'|etrans }}{% if not free_trial == 0 %} {{ 'The first'|etrans }} {{ free_trial }} {{ 'days will be free, with an opportunity to cancel your subscription before a payment is made should you choose to.'|etrans }}{% endif %}</li>
</ul>
<p>{{ 'ID Scanning (ID document scanner) plan services are provided with proprietary software within the limitations outlined in the plan. The ID Scanner is compatible with most smartphones, including Google, Samsung, iPhone, Android, iOS, and many computers with webcams. The ID scanning and reporting is provided with IDWare software, an industry standard for ID scanning compliance, powered by Zebra Technologies.'|etrans }} {{ the_site_name }} {{ 'is an official Zebra Technologies partner. Monthly reports are provided through email. Custom options are available on request.'|etrans }}</p>
<p>{{ 'By checking out, you agree to the'|etrans }} <a href="/terms/" title="{{ 'Read the terms of service and privacy policy'|etrans }}">{{ 'Terms of Service and Privacy Policy'|etrans }}</a>, {{ 'as well as agree to and and acknowledge the sale as outlined and selected, as well as the plan described.'|etrans }}</p>
<p>{{ 'The transaction will display on your bank statement as'|etrans }} "{{ statement_descriptor }} IDSCAN".</p>
<p>{{ 'You will be redirected to a checkout page to buy the product. Please enter your credit or debit card information, you will be billed monthly until you cancel through the website, or by email, cancellation service, or any other form of cancellation request.'|etrans }}</p>
<div class="container container-table m-4 col-md-8 mx-auto">
<div class="container container-table m-4 col-md-8 mx-auto">
<form id="pay-form" onsubmit="event.preventDefault(); payFee();">
{{ form|crispy }}
<button type="submit" class="btn btn-lg btn-outline-success" title="{{ 'Submit'|etrans }}">{{ 'Submit'|etrans }}</button>
</form>
</div>
</div>
{% include 'social.html' %}
{% endblock %}
{% block javascript %}
var price = 500;
function monthlyPlan(fee) {
    price = fee;
    var button = document.getElementById('monthlyplan' + new String(fee));
    for(var el of document.getElementsByClassName('monthlyplan')) {
        el.classList.remove('btn-success');
        el.classList.add('btn-outline-success');
    }
    $(button).toggleClass('btn-success');
}
var product = 'idscan';
var pid = {{ vendor.id }};
var vendor = {{ vendor.id }};
var payForm = document.getElementById('pay-form');
{% if payment_processor == 'paypal' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:square-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid + '&sub=t',
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'square' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:square-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid + '&sub=t',
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'helcim' %}
var checkoutToken;
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:invoice' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            var j = JSON.parse(data);
            checkoutToken = j.checkoutToken;
            $(document.getElementById("clemn-navbar")).autoHidingNavbar().hide();
            appendHelcimPayIframe(j.checkoutToken);
        },
    });
}
window.addEventListener('message', (event) => {

  const helcimPayJsIdentifierKey = 'helcim-pay-js-' + checkoutToken;

  if(event.data.eventName === helcimPayJsIdentifierKey){

    if(event.data.eventStatus === 'ABORTED'){
      console.error('Transaction failed!', event.data.eventMessage);
    }

    if(event.data.eventStatus === 'SUCCESS'){
      validateResponse(event.data.eventMessage)
        .then(response => console.log(response))
        .catch(err => console.error(err));
    }
  }
});
function validateResponse(eventMessage) {
  const payload = {
    'rawDataResponse': eventMessage.data,
  };
  return fetch('{{ base_url }}/payments/helcim/', {body: payload, method: "POST"});
}
{% elif payment_processor == 'stripe' %}
var stripe = Stripe('{{ stripe_pubkey }}');
function payFee(){
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
        fetch("/payments/idscan/monthly/?plan=" + price + "&email=" + email)
          .then((result) => {
            return result.json();
          })
          .then((data) => {
            return stripe.redirectToCheckout({ sessionId: data.sessionId });
          });
}
{% endif %}
{% include 'users/register_modal.js' %}
Prism.highlightAll();
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/invoice.html ---
```html
{% load app_filters %}Dear {{ user.username }},

This email is in regards to an invoice from {{ site_name }} for services as follows.

The below products and/or services are offered for ${{ invoice.price|sub_fee }}:

{{ invoice.cart }}

Please use this link to pay the invoice in full: <a href="{{ pay_url }}" title="Pay the invoice">{{ pay_url }}</a>

Alternatively, you can paste the following link into your address bar:

{{ pay_url }}

Thank you for using {{ site_name }} for your purchase. {{ vendor.name }} looks forward to working with you and awaits payment of the above invoice.

Sincerely,

{{ site_name }}
```


--- File: lotteharper-main/payments/templates/payments/invoice_paid.html ---
```html
Dear {{ vendor.profile.name }},

This email is in regards to an invoice from {{ site_name }}.

The total paid was ${{ invoice.price|sub_fee }}

For the following items:

{{ invoice.cart }}

This invoice has been paid in full. Please arrange services accordingly for the client.

The client's contact info is as follows:
Name: {{ user.profile.name }}
Phone number: {{ user.profile.phone_number }}
Email: {{ user.email }}
Username: {{ user.username }}

Sincerely,

{{ site_name }}
```


--- File: lotteharper-main/payments/templates/payments/pay_invoice_crypto.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block head %}
<script src="https://js.stripe.com/v3/"></script>
<script src="https://crypto-js.stripe.com/crypto-onramp-outer.js"></script>
{% endblock %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
<h1><i class="bi bi-currency-bitcoin"></i> {{ the_site_name }} - {{ 'Pay invoice from'|etrans }} @{{ username }} {{ 'with'|etrans }} {{ request.GET.crypto }}</h1>
<div style="display: inline-block;">
<img align="left" src="{{ model.get_face_blur_url }}" style="width:33%; margin-right: 10px;" class="rounded"></img>
<!-- <img class="mr-2 img-fluid rounded" src="{{ post.get_blur_thumb_url }}" style="float: left; width: 40%; max-width: 400px;" alt="{{ 'See photos like these'|etrans }}"></img>-->
</div>
<p>{{ 'This purchase is subject to the agreement on the referring page of your purchase and'|etrans }} <a href="{% url 'misc:terms' %}" title="{{ 'View the terms and coniditons'|etrans }}">{{ 'the terms and conditions and privacy policy'|etrans }}</a> {{ 'of'|etrans }} {{ the_site_name }}.</p>
<div style="display: flex; justify-content: space-around;">
<div class="dropdown" style="display: inline-block;">
  <a class="btn btn-outline-dark pink-borders dropdown-toggle" role="button" id="dropdownMenuLink" data-bs-toggle="dropdown" aria-expanded="false">
    <i class="bi bi-currency-bitcoin"></i> {{ 'Change Currency'|etrans }}
  </a>
  <ul class="dropdown-menu" aria-labelledby="dropdownMenuLink">
	<div style="max-height: 50vh; overflow: scroll;">
        <li><a class="dropdown-item" href="{{ request.path }}?lightning=t&crypto=BTC">BTC (Lightning Network)</a></li>
    {% for currency in currencies %}
        <li><a class="dropdown-item" href="{{ request.path }}?crypto={{ currency }}">{{ currency }}{% if forloop.counter < 6 %} - {{ 'Fiat options'|etrans }}{% endif %}</a></li>
    {% endfor %}
	</div>
  </ul>
</div>
</div>
<p>This invoice is for the below products/services.</p>
<p>{{ invoice.cart }}</p>
<b>Items:</b>
<ul>
<li>{{ 'To be paid for products/services as arranged above.'|trans }}</li>
<li>{{ 'Billed once only.'|etrans }}</li>
</ul>
<b>{{ 'Info:'|etrans }}</b>
<p>{{ 'The transaction will display on your bank statement as'|etrans }} "{{ statement_descriptor }} INVOICE".</p>
<p>{{ 'For questions or concerns, please contact'|etrans }} {{ the_site_name }} {{ 'at'|etrans }} {{ agent_phone }} {{ 'or mail to'|etrans }} {{ agent_name }} {{ agent_address }}.</p>
<p>{{ 'You will pay'|etrans }} ${{ usd_fee|sub_fee }} USD.</p>
<p>{{ 'Want to pay for this Crypto purchase with card?'|etrans }} <button onclick="payWithCard();" class="btn btn-outline-primary" title="{{ 'Pay for your cryptocurrency purchase with card, bank, or other payment method'|etrans }}">{{ 'Pay with Card in Crypto'|etrans }}</button></p>
<div id="onramp-element" style="max-width: 500px" class="mx-auto">
<!--{% if request.GET.crypto == 'ALPH' %}<p>{{ 'To pay with your'|etrans }} Alephium (ALPH) {{ 'please'|etrans }} <a href="https://bridge.alephium.org/" title="{{ 'Use the'|etrans }} Alephium Bridge {{ 'to send'|etrans }} Alephium (ALPH)" target="_blank">{{ 'use the'|etrans }} Alephium Bridge {{ 'to send cryptocurrency to the wallet in the invoice using'|etrans }} ETH {{ 'and'|etrans }} Alephium (ALPH)</a></p>{% endif %}-->
<form id="payment-form" method="POST" enctype="multipart/form-data">
{% csrf_token %}
<legend class="border-bottom mb-4">{{ 'Step 1: Send'|etrans }} {{ request.GET.crypto }}</legend>
<fieldset class="form-group">
<p>{{ 'Send'|etrans }} {{ crypto_fee|cryptoformat }} {{ request.GET.crypto|fixalph }} <button class="btn btn-sm btn-info" type="button" onclick="copyAmount();"><i class="bi bi-clipboard-check-fill"></i> {{ 'Copy'|etrans }}</button> (${{ usd_fee|sub_fee }}) {{ 'to the following wallet address:'|etrans }}</p>
<b><i style="overflow-wrap: break-word;">{{ crypto_address }}</i></b>
<button class="btn btn-sm btn-info" type="button" onclick="copyAddress();"><i class="bi bi-clipboard-check-fill"></i> {{ 'Copy'|etrans }}</button>
<hr style="background-color: green;">
<div style="display: flex; justify-content: space-around;"><div id="paymentqrcode" style="border-style: solid; border-width: 15px; border-radius: 5px; border-color: #EEEEEE;"></div></div>
<div style="text-align: center;"><small>{{ 'Scan this QR code to pay with your Crypto wallet or bank'|etrans }}</small></div>
<p>{% if not request.user.is_authenticated %}{{ 'Enter your email and press'|etrans }}{% else %}{{ 'Press'|etrans }}{% endif %} {{ 'the "Send" button to confirm your payment once you have initiated the transfer.'|etrans }}</p>
{{ form|crispy }}
</fieldset>
<button id="submit-button" type="submit" class="btn btn-outline-success">{{ 'Verify'|etrans }}</button>
</form>
<hr>
{% if not request.GET.crypto == 'ALPH' %}<p>{{ 'To pay with'|etrans }} Alephium (ALPH) {{ 'please select'|etrans }} ETH (Ethereum) {{ 'as your currency and'|etrans }} <a href="https://bridge.alephium.org/" title="{{ 'Use the'|etrans }} Alephium Bridge {{ 'to send'|etrans }} Alephium (ALPH)" target="_blank">{{ 'use the'|etrans }} Alephium Bridge {{ 'to send cryptocurrency to the wallet in the invoice using'|etrans }} ETH {{ 'and'|etrans }} Alephium (ALPH)</a></p>{% endif %}
<p>{{ 'Buy crypto to send here:'|etrans }} <a href="{{ crypto_provider }}" title="{{ 'Buy crypto to send'|etrans }}">{{ crypto_provider }}</a>, {{ 'or with your crypto bank.'|etrans }}</p>
</div>
<p>{{ 'Want to pay for this invoice with card? Select the option above to use the onramp or'|etrans }} <a href="{% url 'payments:pay-invoice' %}{% if request.GET %}?{% for key, val in request.GET.items %}{{ key }}={{ val }}&{% endfor %}{% endif %}" class="btn btn-outline-secondary" title="{{ 'Pay with Card'|etrans }}">{{ 'Pay with Card'|etrans }}</a></p>
{% endblock %}
{% block javascript %}
function copyAddress() {
	navigator.clipboard.writeText("{{ crypto_address }}");
}
function copyAmount() {
	navigator.clipboard.writeText("{{ crypto_fee }}");
}
$('#payment-form').on('submit', function(){
        document.getElementById('submit-button').disabled = true;
});
var pqrdiv = document.getElementById("paymentqrcode");
$(pqrdiv).kjua({text: "{{ crypto_address }}", render: 'svg'});
var pimage = pqrdiv.querySelector('svg');
pimage.style.width = "100%";
pimage.style.height = "auto";
pimage.style.maxWidth = "250px";
pimage.alt = "{{ 'Scan this code to pay with a crypto wallet or bank'|etrans }}";
function payWithCard() {
    var paymentCrypto = "{{ request.GET.crypto }}";
    const onramp = window.StripeOnramp('{{ stripe_key }}');
    $.ajax({
        url: '{% url 'payments:crypto-onramp' username crypto_address usd_fee %}?crypto=' + paymentCrypto,
        method: 'POST',
        error: function() {
            window.location.href = '{{ request.path }}?crypto=ETH';
        },
        success: function(clientSecret) {
            try {
            onrampSession = onramp.createSession({clientSecret});
            onrampSession.mount("#onramp-element");
            } catch {
                window.location.href = '{{ request.path }}?crypto=ETH';
            }
        }
    });
}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/pay_invoice.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block head %}
{% if payment_processor == 'helcim' %}
<script type="text/javascript" src="https://secure.helcim.app/helcim-pay/services/start.js"></script>
{% elif payment_processor == 'stripe' %}
<script src="https://js.stripe.com/v3/"></script>
{% endif %}
<!--<script src="https://js.stripe.com/v3/"></script>-->
{% endblock %}
{% block styles %}
#card-info-parent * {
  margin-left: 3px;
  margin-right: 3px;
}
{% endblock %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
<h1><i class="bi bi-credit-card-fill"></i> {{ 'Pay this invoice with card'|trans }}</h1>
<div style="text-align: center;">
	<img alt="{{ 'Accepting Visa and Mastercard'|etrans }}" style="height: auto; width: 80%; max-width: 90px;" height="auto" src="/media/static/visa-mastercard.png"></img>
</div>
<p>{{ 'This invoice is for the below products/services.'|etrans }}</p>
<p>{{ invoice.cart|trans }}</p>
<b>{{ 'Items:'|etrans }}</b>
<ul>
<li>{{ 'To be paid for products/services as arranged above.'|trans }}</li>
<li>{{ 'Billed once only.'|etrans }}</li>
</ul>
<p><i>{{ 'Want to pay with cryptocurrency instead?'|etrans }}</i> <a href="{% url 'payments:pay-invoice-crypto' %}{% if request.GET %}?{% for key, val in request.GET.items %}{{ key }}={{ val }}&{% endfor %}{% endif %}" class="btn btn-outline-info" title="{{ 'Pay with crypto'|etrans }}">{{ 'Pay with Cryptocurrency'|etrans }}</a></p>
<b>{{ 'Info:'|etrans }}</b>
<p>{{ 'The transaction will display on your bank statement as'|etrans }} "{{ statement_descriptor }} INVOICE".</p>
<p>{{ 'For questions or concerns, please contact'|etrans }} {{ the_site_name }} {{ 'at'|etrans }} {{ agent_phone }} {{ 'or mail to'|etrans }} {{ agent_name }} {{ agent_address }}.</p>
<p>{{ 'You will pay'|etrans }} ${{ fee|sub_fee }} USD. {{ 'Please enter your credit or debit card information.'|etrans }}</p>
{% if request.GET.coupon %}
<p><legend>{{ 'You have received a coupon!'|etrans }}</legend> - {{ 'Use coupon code'|etrans }} <b id="coupon-code">{{ request.GET.coupon }}</b> <button class="btn btn-primary btn-sm" onclick="copyToClipboard('coupon-code');">{{ 'Copy'|etrans }}</button> {{ 'at checkout to get a discount on your purchase.'|etrans }}</p>
{% endif %}
<hr style="background-color: blue;">
<form id="pay-form" onsubmit="event.preventDefault(); payFee();">
{{ form|crispy }}
<button type="submit" class="btn btn-lg btn-outline-success" title="{{ 'Submit'|etrans }}">{{ 'Submit'|etrans }}</button>
</form>
</div>
<hr>
<p>{{ 'Want to pay for this invoice with cryptocurrency?'|etrans }} <a href="{% url 'payments:pay-invoice-crypto' %}{% if request.GET %}?{% for key, val in request.GET.items %}{{ key }}={{ val }}&{% endfor %}{% endif %}" class="btn btn-outline-secondary" title="{{ 'Pay with Cryptocurrency'|etrans }}">{{ 'Pay with Crypto'|etrans }}</a></p>
{% endblock %}
{% block javascript %}
var product = 'invoice';
var pid = {{ invoice.pid }};
var price = {{ invoice.price }};
var vendor = {{ invoice.vendor.id }};
var payForm = document.getElementById('pay-form');
var checkoutToken;
{% if payment_processor == 'paypal' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:paypal-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'square' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:square-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'helcim' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:invoice' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid,
        method:'POST',
        success: function(data) {
            var j = JSON.parse(data);
            checkoutToken = j.checkoutToken;
            $(document.getElementById("clemn-navbar")).autoHidingNavbar().hide();
            appendHelcimPayIframe(j.checkoutToken);
        },
    });
}
window.addEventListener('message', (event) => {

  const helcimPayJsIdentifierKey = 'helcim-pay-js-' + checkoutToken;

  if(event.data.eventName === helcimPayJsIdentifierKey){

    if(event.data.eventStatus === 'ABORTED'){
      console.error('Transaction failed!', event.data.eventMessage);
    }

    if(event.data.eventStatus === 'SUCCESS'){
      validateResponse(event.data.eventMessage)
        .then(response => console.log(response))
        .catch(err => console.error(err));
    }
  }
});
function validateResponse(eventMessage) {
  const payload = {
    'rawDataResponse': eventMessage.data,
  };
  return fetch('{{ base_url }}/payments/helcim/', {body: payload, method: "POST"});
}
{% elif payment_processor == 'stripe' %}
var stripe = Stripe('{{ stripe_pubkey }}');
function payFee(){
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
        fetch("/payments/invoice/checkout/?pid={{ invoice.pid }}&email=" + email)
          .then((result) => {
            return result.json();
          })
          .then((data) => {
            return stripe.redirectToCheckout({ sessionId: data.sessionId });
          });
}
{% endif %}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/payment_cards.html ---
```html
{% extends 'base.html' %}
{% block content %}
{% load app_filters %}
<legend>Payment Cards</legend>
<hr>
{% if cards.count == 0 %}
<b>You do not have any payment cards with {{ the_site_name }}.</b>
{% endif %}
{% for card in cards %}
<p>{{ card.number|censorcard }} - Expires {{ card.expiry_month }}/{{ card.expiry_year }}</p>
<p>Make preferred? {% include 'payments/primary_card.html' %} or delete? {% include 'payments/delete_card.html' %}</p>
</hr>
{% endfor %}
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/primary_card.html ---
```html
<form style="display: inline-block;" action="{% url 'payments:card' card.id %}" method="POST" id="publishForm">
{% csrf_token %}
<button class="btn btn-outline-success" type="submit">{% if card.primary %}<i class="bi bi-pin-angle-fill"></i>{% else %}<i class="bi bi-pin-fill"></i>{% endif %}</button>
</form>
```


--- File: lotteharper-main/payments/templates/payments/send_invoice.html ---
```html
{% extends 'base.html' %}
{% block content %}
{% load app_filters %}
{% load crispy_forms_tags %}
<legend>{{ 'Send an invoice'|etrans }}</legend>
<form method="POST">
{% csrf_token %}
{{ form|crispy }}
<button type="submit" title="{{ 'Send this invoice'|etrans }}" class="btn btn-outline-success">{{ 'Send'|etrans }}</button>
</form>
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/subscribe_bitcoin.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
<h1><i class="bi bi-currency-bitcoin"></i> Subscribe to @{{ username }} with Crypto</h1>
<img align="left" src="{{ profile.get_face_blur_url }}" style="width:33%; margin-right: 10px;" class="rounded"></img>
<form id="payment-form" method="POST" enctype="multipart/form-data">
{% csrf_token %}
<fieldset class="form-group">
<legend class="border-bottom mb-4">Step 1: Send Bitcoin</legend>
<p>Send {{ bitcoin_fee }} BTC <button class="btn btn-sm btn-info" onclick="copyAmount();"><i class="bi bi-clipboard-check-fill"></i> Copy</button> (${{ usd_fee|sub_fee }}) to the following wallet address:</p>
<b><i style="overflow-wrap: break-word;">{{ vendor_profile.get_bitcoin_address }}</i></b>
<button class="btn btn-sm btn-info" onclick="copyAddress();"><i class="bi bi-clipboard-check-fill"></i> Copy</button>
<hr style="background-color: green;">
<legend class="border-bottom mb-4">Step 2: Enter Transaction ID</legend>
<p>Return here and enter your transaction ID. After a few minutes, reload this page.</p>
{{ form|crispy }}
</fieldset>
<hr style="background-color: blue;">
<button id="submit-button" type="submit" class="btn btn-outline-success">Verify</button>
</form>
</div>
{% endblock %}
{% block javascript %}
function copyAddress() {
	navigator.clipboard.writeText("{{ vendor_profile.get_bitcoin_address }}");
}
function copyAmount() {
	navigator.clipboard.writeText("{{ bitcoin_fee }}");
}
$('#payment-form').on('submit', function(){
        document.getElementById('submit-button').disabled = true;
});
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/subscribe_bitcoin_thankyou.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load feed_filters %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
{% blocktrans en %}
<h1>Thank you!</h1>
<p>Thank you for subscribing. Your subscription is being verified. Please wait 5 minutes and then refresh the page to continue, or return back to this page. Thank you for your patience while the transaction is being verified.</p>
{% endblocktrans %}
{% if not user.is_authenticated or not user|barcodescanned %}
{% blocktrans en %}
<p>If this is an age restricted purchase, and your account is new or you have not scanned your ID, you will need to follow the links in your email to activate your account and set your password as well as <a href="{% url 'barcode:scan' %}" title="Scan your ID before continuing">scan your ID before continuing</a> please.</p>
{% endblocktrans %}
{% endif %}
</div>
{% endblock %}
{% block javascript %}
setTimeout(function() {
	window.location.reload();
}, 1000 * 60 * 5); // 5 minutes
{% endblock %}
```


--- File: lotteharper-main/payments/templates/payments/subscribe_card.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% load app_filters %}
{% block head %}
{% if payment_processor == 'helcim' %}
<script type="text/javascript" src="https://secure.helcim.app/helcim-pay/services/start.js"></script>
{% elif payment_processor == 'stripe' %}
<script src="https://js.stripe.com/v3/"></script>
{% endif %}
{% endblock %}
{% block styles %}
#card-info-parent * {
  margin-left: 3px;
  margin-right: 3px;
}
{% endblock %}
{% block content %}
<div class="container rounded shadow col-md-6 mx-auto">
<legend><i class="bi bi-credit-card-fill"></i> {{ 'Subscribe to'|etrans }} @{{ username }} {{ 'with Card'|etrans }}</legend>
<div style="display: inline-block;">
<img align="left" src="{{ model.get_face_blur_url }}" style="width:33%; margin-right: 10px;" class="rounded"></img>
<img class="mr-2 img-fluid rounded" src="{{ post.get_blur_thumb_url }}" style="float: left; width: 40%; max-width: 400px;" alt="{{ 'See photos like these'|etrans }}"></img>
</div>
<div style="text-align: center;">
	<img alt="{{ 'Accepting Visa and Mastercard'|etrans }}" style="height: auto; width: 80%; max-width: 90px;" height="auto" src="/media/static/visa-mastercard.png"></img>
</div>
{% include 'payments/_subscription_perks.html' %}
<p> - {{ profile.name }}</p>
<b>{{ 'Items:'|etrans }}</b>
<ul>
<li>{{ 'Subscription to'|etrans }} {{ username }} {{ 'with'|etrans }} {{ the_site_name }} (${{ fee|sub_fee }})</li>
<li>{{ 'Billed monthly, until cancellation.'|etrans }}{% if not profile.user.vendor_profile.free_trial == '0' %} {{ 'The first'|etrans }} {{ profile.user.vendor_profile.free_trial }} {{ 'days will be free, with an opportunity to cancel your subscription before a payment is made should you choose to.'|etrans }}{% endif %}</li>
</ul>
<b>{{ 'Info:'|etrans }}</b>
<p>{{ 'The transaction will display on your bank statement as'|etrans }} "{{ statement_descriptor }} SUBS".</p>
<p>{{ 'For questions or concerns, please contact'|etrans }} {{ the_site_name }} {{ 'at'|etrans }} {{ agent_phone }} {{ 'or mail to'|etrans }} {{ agent_name }} {{ agent_address }}.</p>
<p>{{ 'You will be redirected to a checkout page to buy the product. Please enter your credit or debit card information, you will be billed monthly until you cancel through the website, or by email, cancellation service, or any other form of cancellation request.'|etrans }}</p>
<p>{{ 'You will pay'|etrans }} ${{ fee|sub_fee }} USD. {{ 'Please click the button below to continue.'|etrans }}</p>
{% if request.GET.coupon %}
<p><legend>{{ 'You have received a coupon!'|etrans }}</legend> - {{ 'Use coupon code'|etrans }} {{ request.GET.coupon }} {{ 'at checkout to get a discount on your purchase.'|etrans }}</p>
{% endif %}
<form id="pay-form" onsubmit="event.preventDefault(); payFee();">
{{ form|crispy }}
<button type="submit" class="btn btn-lg btn-outline-success" title="{{ 'Submit'|etrans }}">{{ 'Submit'|etrans }}</button>
</form>
</div>
<hr>
{% include 'social.html' %}
{% endblock %}
{% block javascript %}
var product = 'membership';
var pid = {{ profile.user.id }};
var price = {{ fee }};
var vendor = {{ profile.user.id }};
var payForm = document.getElementById('pay-form');
{% if payment_processor == 'paypal' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:paypal-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid + '&sub=t',
        method:'POST',
        success: function(data) {
            if(data.startsWith(window.location.protocol + '//')) {
                window.location.href = data;
            } else { console.log('Invalid response from server.'); }
        },
    });
}
{% elif payment_processor == 'square' %}
function payFee() {
    var email = {% if request.user.is_authenticated %}"{{ request.user.email }}"{% else %}document.getElementById('id_email').value{% endif %};
    $.ajax({
        url: '{{ base_url }}{% url 'payments:square-checkout' %}?vendor=' + vendor + '&email=' + email + '&price=' + price + '&product=' + product + '&pid=' + pid + '&sub=t',
        