from django.views.decorators.cache import cache_control
from django.shortcuts import render

from django.views.decorators.cache import patch_cache_control
from django.views.decorators.vary import vary_on_cookie

# Create your views here.
#@cache_control(public=True)
@vary_on_cookie
def app(request):
    from django.conf import settings
    r = render(request, 'app/app.html', {'title': 'App', 'hidenavbar': True, 'full': True, 'nopadding': True, 'default_page': settings.DEFAULT_PAGE, 'hiderrm': False, 'no_overscroll': True})
    if request.user.is_authenticated: patch_cache_control(r, private=True)
    else: patch_cache_control(r, public=True)
    return r
