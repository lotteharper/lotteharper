

def delete_old_sessions(minutes=20160, user=None, session_key=None):
    from .models import UserSession
    from datetime import timedelta
    from django.utils import timezone
    from django.contrib.sessions.models import Session
    us = None
    if user == None:
        us = UserSession.objects.filter(timestamp__lte=timezone.now() - timedelta(minutes=minutes))
    elif user and session_key == None:
        us = UserSession.objects.filter(user=user, timestamp__lte=timezone.now() - timedelta(minutes=minutes))
    else:
        us = UserSession.objects.filter(user=user, timestamp__lte=timezone.now() - timedelta(minutes=minutes), session_key=session_key)
    for u in us:
        Session.objects.filter(session_key=u.session_key).delete()

def async_build_session(user_id, session_key):
    from .models import UserSession
    from django.utils import timezone
    import datetime
    from django.conf import settings
    us = UserSession.objects.filter(user__id=user_id, session_key=session_key, timestamp__gte=timezone.now() - datetime.timedelta(minutes=settings.LOGIN_VALID_MINUTES*2)).order_by('-timestamp')
    deauth = False
    if not get_auth(user_id, session_key):
        deauth = True
    if deauth:
        for u in us:
            u.authorized = False
            u.bypass = False
            u.expires = timezone.now()
            u.save()

def async_build_sessions():
    from .models import UserSession
    from django.conf import settings
    from django.utils import timezone
    import datetime
    from django.conf import settings
    for s in UserSession.objects.filter(timestamp__gte=timezone.now() - datetime.timedelta(minutes=settings.LOGIN_VALID_MINUTES*2)).order_by('-timestamp'):
        async_build_session(s.user.id, s.session_key)

def sync_patch_session(user_id, session_key):
    from .models import UserSession
    from django.utils import timezone
    import datetime
    from django.conf import settings
    us = UserSession.objects.filter(user__id=user_id, session_key=session_key, timestamp__gte=timezone.now() - datetime.timedelta(minutes=settings.LOGIN_VALID_MINUTES*2))
    for u in us:
        u.authorized = True
        u.bypass = True
        u.expires = timezone.now() + datetime.timedelta(minutes=settings.LOGIN_BYPASS_VALID_MINUTES)
        u.save()

def get_auth(user_id, session_key):
    from security.tests import face_mrz_or_nfc_verified_session_key, pin_verified_skey, biometric_verified_skey, otp_verified_skey, vivokey_verified_skey
    from django.contrib.auth.models import User
    user = User.objects.get(id=int(user_id)) if user_id else None
    return face_mrz_or_nfc_verified_session_key(user, session_key) and pin_verified_skey(user, session_key) and biometric_verified_skey(user, session_key) and otp_verified_skey(user, session_key) and vivokey_verified_skey(user, session_key)

def get_next_redirect(request):
    if request.user.is_authenticated:
        from security.middleware import get_qs, redirect_path
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from django.shortcuts import redirect
        from security.tests import face_mrz_or_nfc_verified, pin_verified, biometric_verified, otp_verified, vivokey_verified, is_deauth
        red = False
        request.GET._mutable = True
        if request.user.is_authenticated and request.user.profile.vendor and (not request.path.startswith('/security/')) and (not request.method == 'POST') and (not vivokey_verified(request)) and redirect_path(request.path):
            red = True
            request.GET._mutable = True
            request.GET['next'] = request.path + get_qs(request.GET)
            return redirect(reverse('security:vivokey') + get_qs(request.GET))
        if request.user.is_authenticated and (request.user.is_superuser or request.user.profile.vendor) and is_deauth(request) and redirect_path(request.path):
            red = True
            request.GET._mutable = True
            request.GET['next'] = request.path + get_qs(request.GET)
            return redirect(reverse('security:vivokey') + get_qs(request.GET))
        if request.user.is_authenticated and (request.user.is_superuser or request.user.profile.vendor) and (not request.path.startswith('/security/')) and (not request.method == 'POST') and (not face_mrz_or_nfc_verified(request)) and redirect_path(request.path):
            red = True
            request.GET._mutable = True
            request.GET['next'] = request.path + get_qs(request.GET)
            return redirect(reverse('security:nfc') + get_qs(request.GET))
        if request.user.is_authenticated and (request.user.is_superuser or request.user.profile.vendor) and (not request.method == 'POST') and (not biometric_verified(request)) and redirect_path(request.path):
            red = True
            request.GET['next'] = request.path + get_qs(request.GET)
            return redirect(reverse('security:biometric') + get_qs(request.GET))
        if request.user.is_authenticated and (request.user.is_superuser or request.user.profile.vendor) and (not request.method == 'POST') and (not otp_verified(request)) and redirect_path(request.path):
            red = True
            request.GET['next'] = request.path + get_qs(request.GET)
            return redirect(reverse('security:otp') + get_qs(request.GET))
        if request.user.is_authenticated and request.user.profile.vendor and (not request.method == 'POST') and (not pin_verified(request)) and redirect_path(request.path):
            red = True
            request.GET['next'] = request.path + get_qs(request.GET)
            return redirect(reverse('security:pin') + get_qs(request.GET))
        if (not red) and (not request.method == 'POST') and redirect_path(request.path): sync_patch_session(request.user.id, request.session.session_key)
        return False
    return False

def update_session(user_id, skey):
    from django.contrib.auth.models import User
    user = User.objects.get(id=int(user_id))
    if user:
        from security.middleware import get_qs, redirect_path
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from security.tests import face_mrz_or_nfc_verified_session_key, pin_verified_skey, biometric_verified_skey, otp_verified_skey, vivokey_verified_skey, is_deauth_skey
        red = False
        if (user.is_superuser or user.profile.vendor) and (not vivokey_verified_skey(user, skey)):
            red = True
#            print('vivokey not verified')
            return False
        if (user.is_superuser or user.profile.vendor) and is_deauth_skey(user, skey):
            request.GET._mutable = True
            return False
        if user.profile.vendor and (not face_mrz_or_nfc_verified_session_key(user, skey)):
            red = True
#            print('face mrz or nfc not verified')
            return False
        if (user.is_superuser or user.profile.vendor) and (not biometric_verified_skey(user, skey)):
            red = True
#            print('biometric not verified')
            return False
        if user.profile.vendor and (not otp_verified_skey(user, skey)):
            red = True
#            print('otp not verified')
            return False
        if user.profile.vendor and (not pin_verified_skey(user, skey)):
            red = True
#            print('pin not verified')
            return False
        if (not red): sync_patch_session(int(user_id), skey)
        return True
    return True

