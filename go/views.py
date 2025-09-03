from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import pediatric_identity_verified
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import patch_cache_control
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import cache_page

@cache_page(60*60*24)
@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def go(request):
    from django.shortcuts import render
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.contrib.auth.models import User
    from feed.models import Post
    from django.conf import settings
    from barcode.models import DocumentScan
    id = DocumentScan.objects.filter(user=request.user, side=True).last().document_isolated.url if DocumentScan.objects.filter(user=request.user, side=True).last() and DocumentScan.objects.filter(user=request.user, side=True).last().document_isolated else ''
    smp = Post.objects.filter(id=settings.STATUS_SAMPLE).first()
    post = Post.objects.filter(id=settings.SPLASH).first()
    ad_post = None
    status_messages = None #smp.content.split('\n') if smp else []
    r = render(request, 'go/go.html', {'title': 'Go', 'splash_id': post.id if post else 1, 'smp_id': smp.id if smp else None, 'digital_id': id, 'ad_post': ad_post.id if ad_post else None})
    patch_cache_control(r, private=True)
    return r
