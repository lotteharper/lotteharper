from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from verify.tests import pediatric_identity_verified
from vendors.tests import is_vendor
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.vary import vary_on_cookie

@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def stream(request):
    from django.contrib.auth.models import User
    from django.conf import settings
    context = {
        'title': 'Watch stream',
        'description': 'Stream on Lotte Harper. ' + settings.BASE_DESCRIPTION,
    }
    return render(request, 'stream/stream.html', context)

@cache_page(60*15)
@vary_on_cookie
def watch(request, username):
    from django.http import Http404
    from django.contrib.auth.models import User
    user = User.objects.filter(profile__name=username, profile__vendor=True).order_by('-profile__last_seen').first()
    if not user:
        from django.contrib import messages
        messages.warning(request, 'This streamer is not available, friend. Please try another page.')
        raise Http404
    from django.conf import settings
    context = {
        'title': 'Watch stream',
        'description': 'Watch {}\'s stream on Lotte Harper. ' + settings.BASE_DESCRIPTION,
        'vendor': user,
    }
    response = render(request, 'stream/watch.html', context)
    from django.views.decorators.cache import patch_cache_control
    if request.user.is_authenticated:
        patch_cache_control(response, private=True)
    else:
        patch_cache_control(response, public=True)
    return response
