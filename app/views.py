from django.views.decorators.cache import cache_control, never_cache, cache_page
from django.shortcuts import render

from django.views.decorators.cache import patch_cache_control
from django.views.decorators.vary import vary_on_cookie

# Create your views here.
#@cache_control(public=True)
#@cache_page(60*60*24*7)
#@vary_on_cookie
@never_cache
def app(request):
    from django.conf import settings
#    r = render(request, 'app/app.html', {'title': 'App', 'hidenavbar': True, 'full': True, 'nopadding': True, 'default_page': settings.DEFAULT_PAGE, 'hiderrm': False, 'no_overscroll': True})
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    from django.shortcuts import redirect
    import datetime
    r = None
    if not request.user.is_authenticated and not request.COOKIES.get('guest_visit'):
        max_age = settings.PUSH_COOKIE_EXPIRATION_HOURS * 60 * 60
        expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
            "%a, %d-%b-%Y %H:%M:%S GMT",
        )
        response = redirect('landing:index')
        response.set_cookie('guest_visit', True, max_age=max_age, expires=expires)
        return response
    if request.user.is_authenticated and request.user.profile.vendor:
        r = redirect(reverse('go:go'))
    else:
        from django.contrib.auth.models import User
        from django.conf import settings
        r = redirect(reverse('feed:profile-grid', kwargs={'username': User.objects.get(id=settings.MY_ID).profile.name}))
    if request.user.is_authenticated and request.user.profile.vendor: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r

