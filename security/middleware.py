from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
import re, datetime
from security.apis import get_client_ip, check_ip_risk
from django.conf import settings
from django.contrib import messages

RISK_LEVEL = 1
FRAUD_MOD = settings.PAGE_LOADS_PER_API_CALL

def get_uuid():
    import uuid
    filename = "%s" % (uuid.uuid4())
    return filename

def get_qs(get_data):
    get_length = 0
    qs = '?'
    if get_data:
        for key, value in get_data.items():
            qs = qs + '{}={}&'.format(key, value)
            get_length = get_length + 1
    try:
        if qs[-1] == '&':
            qs = qs[:-1]
        if qs[-1] == '?':
            qs = qs[:-1]
        if qs[-1] == '&':
            qs = qs[:-1]
    except: pass
    return qs

redirect_paths = ['accounts/logout', 'accounts/auth', 'face', 'admin', 'kick', 'appeal', 'auth', 'recovery', 'feed/secure', 'feed/grid/api', 'feed/profile', 'shell/edit', 'serviceworker.js', 'melanin', 'terms', 'feed/secure', 'hypnosis', 'pay/idscan', 'pay/webdev', 'sitemap.xml', 'news.xml', 'webauth', 'remote/generate', 'pay', 'security/vivokey', 'security/mrz', 'security/nfc', 'security/otp', 'security/biometric', 'security/pin', 'security/shake']

def redirect_path(path):
#    if path == '/': return False
    for p in redirect_paths:
       pa = '/{}'.format(p)
       if path.startswith(pa):
           return False
    return True

def redirect_request(request):
    if request.method == 'POST':
        return False
    return True

def uuid_valid(id):
    UUID_PATTERN = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', re.IGNORECASE)
    if UUID_PATTERN.match(id):
        return True
    return False

def unique_list(l):
    ulist = []
    [ulist.append(x) for x in l if x not in ulist]
    return ulist

from lotteh.celery import async_process_user_request
from security.models import UserIpAddress
from security.models import UserSession
# /feed/grid/Daisy/?handtrack=tlang
from django.shortcuts import redirect


OVERCLICK_HTML_NOTE = '<!DOCTYPE html><html><head></head><body><h3>You have clicked or tapped too many times and sent too many post requests</h3><p>Please <a href="/" title="Return home">click here to return</a> to the homepage.</p></body></html>'

# birthing middleware
def security_middleware(get_response):
    def middleware(request):
        response = None
        if any(x in request.path for x in ["favicon.ico", "jsi18n", "static", "serviceworker.js", "ads.txt", "robots.txt", "security/modal"]):
            return self.get_response(request)
        try:
            if request.get_full_path().startswith('/feed/profile/Daisy/?feed=privatelang') or request.get_full_path().startswith('/feed/grid/Daisy/?handtrack=tlang') or request.get_full_path().startswith('/feed/profile/Daisy/?feed=privateembed=tlang') or request.get_full_path().startswith('/collections/shop-accessories/products/cotton-tote-bag/'):
                return redirect(settings.REDIRECT_URL)
            print(request.get_full_path())
            ip = get_client_ip(request)
            qs = get_qs(request.GET)
            sessions = None
            if request.method == 'POST':
                from .models import SessionDedup
                sd = SessionDedup.objects.create(user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None, ip_address=ip[:39] if ip else None, path=request.path, querystring=qs, method=request.method)
                sd.async_delete()
                sessions = SessionDedup.objects.filter(user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None, ip_address=ip[:39] if ip else None, path=request.path, querystring=qs, method=request.method, time__gte=timezone.now() - datetime.timedelta(seconds=2))
                if sessions.count() < settings.SESSION_INDEX and request.method == 'POST': return redirect(request.path + qs) #return HttpResponse(OVERCLICK_HTML_NOTE)
                if sessions.count() > settings.SESSION_INDEX and request.method == 'POST': return redirect(request.path + qs) # return HttpResponse(OVERCLICK_HTML_NOTE)
#                print('{} - {} - {}'.format(ip, request.method, request.path + ((qs) if qs else '') + '*' + str(sessions.count())))
            if not (request.user.is_authenticated and (request.user.is_superuser or request.user.profile.vendor)):
                ip_obj = UserIpAddress.objects.filter(ip_address=ip, user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None).first()
                if ip_obj and ip_obj.risk_detected and not request.path == '/kick/reasess/':
                    from django.http import HttpResponseRedirect
                    if ip_obj.page_loads > 12:
                        return HttpResponseRedirect(settings.ALT_REDIRECT_URL)
                    return HttpResponseRedirect(settings.REDIRECT_URL)
#            request.GET._mutable = True
            if request.user.is_authenticated and (request.user.is_superuser or request.user.profile.vendor):
                sess = UserSession.objects.filter(user=request.user, session_key=request.session.session_key).order_by('-timestamp').first()
                if not sess:
                    sess, created = UserSession.objects.get_or_create(user=request.user, session_key=request.session.session_key, user_agent=request.META["HTTP_USER_AGENT"], authorized=False, bypass=False)
                if sess.timestamp < timezone.now() - datetime.timedelta(minutes=settings.LOGIN_VALID_MINUTES):
                    from security.build import delete_old_sessions
                    delete_old_sessions(minutes=settings.LOGIN_VALID_MINUTES, user=request.user, session_key=sess.session_key)
                if (not sess.expiry_warning) and sess.timestamp < timezone.now() - datetime.timedelta(minutes=settings.LOGIN_VALID_MINUTES-settings.LOGIN_EXPIRY_WARNING_MINUTES):
                    difference_seconds = (settings.LOGIN_VALID_MINUTES*60) - (timezone.now() - sess.timestamp).total_seconds()
                    difference_minutes = round(difference_seconds/60, 2)
#                    difference_relational_second = difference_seconds%60
                    messages.warning(request, 'Your session is expiring in {} minutes. Please complete authentication again soon to proceed.'.format(difference_minutes))
                    sess.expiry_warning = True
                    sess.save()
                request.security_modal = redirect_path(request.path)
                if request.security_modal or (not sess.authorized) or (not sess.bypass): # and request.security_modal:
                    from security.build import get_next_redirect
                    red = get_next_redirect(request)
                    if red: return red
            async_process_user_request.delay(ip, request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None, request.session.session_key, True if hasattr(request, 'user') and request.user.is_authenticated else False, request.path, request.META.get('CONTENT_LENGTH'), request.META.get('HTTP_REFERER'), qs, request.method, sessions.count() if sessions else -1)
        except:
            import traceback
            from stacktrace.models import Error
            try:
                Error.objects.create(user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None, stack_trace=traceback.format_exc(), notes='Logged by security middleware.')
            except: pass
            from feed.middleware import set_current_exception
            set_current_exception(traceback.format_exc())
            print(traceback.format_exc())
        response = get_response(request)
        return response
    return middleware
