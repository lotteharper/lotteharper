from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from barcode.tests import pediatric_document_scanned
from django.views.decorators.cache import patch_cache_control, cache_page
from django.views.decorators.vary import vary_on_cookie
from django.contrib.auth.decorators import login_required

@login_required
def my_links(request):
    from .models import SharedLink
    from .forms import LinksForm
    from django.contrib.auth.models import User
    from django.contrib import messages
    user = request.user
    if not user: user = User.objects.filter(profile__name__icontains=username).order_by('-profile__last_seen').first()
    if request.user.is_authenticated and request.user.profile.vendor and not request.GET.get('show', False):
        if request.method == 'POST':
            links = SharedLink.objects.filter(user=request.user).order_by('created')
            form = LinksForm(request.POST, links=links)
            if form.is_valid():
                from django.utils import timezone
                for counter in range(0, links.count() + 2):
                    link = form.cleaned_data.get('link{}'.format(counter))
                    desc = form.cleaned_data.get('description{}'.format(counter))
                    color = form.cleaned_data.get('color{}'.format(counter))
                    l = links[counter] if counter < links.count() else False
                    if not l:
                        l = SharedLink.objects.create(user=request.user)
                    if l.description != desc:
                        l.description = desc
                        l.updated = timezone.now()
                    if l.url != link:
                        l.url = link
                        l.updated = timezone.now()
                    if l.color != color:
                        l.color = color
                        l.updated = timezone.now()
                    if (l.url == '') or not (l.url):
                        l.delete()
                    else:
                        l.save()
                messages.success(request, 'Your links have been saved.')
            else:
                messages.warning(request, str(form.errors))
        links = SharedLink.objects.filter(user=request.user).order_by('created')
        response = render(request, 'links/links.html', {
            'title': 'Your links',
            'links': links,
            'form': LinksForm(links=links),
            'links_user': request.user,
            'user_mode': True,
        })
        return response
    messages.warning(request, 'You must be a vendor to see this page.')
    return redirect(reverse('/'))

@cache_page(60*60)
def links(request, username):
    from .models import SharedLink
    from django.contrib.auth.models import User
    from django.contrib import messages
    user = User.objects.filter(profile__name=username).order_by('-profile__last_seen').first()
    if not user: user = User.objects.filter(profile__name__icontains=username).order_by('-profile__last_seen').first()
    links = SharedLink.objects.filter(user=user).order_by('created')
    response = render(request, 'links/links.html', {
        'title': '@{}\'s links'.format(user.profile.name),
        'links': links,
        'links_user': user,
        'user_mode': False,
    })
#        patch_cache_control(response, public=True)
    return response
