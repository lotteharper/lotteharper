from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page, never_cache

def get_num_length(num, length):
    n = ''
    for x in range(length):
        n = n + str(num)
    return int(n)

@cache_page(60*5)
def leaderboard(request):
    from django.conf import settings
    from .models import Game
    from django.shortcuts import render
    board = ''
    games = Game.objects.filter(scored=True).exclude(player1=None).exclude(player2=None).order_by('-time')
    from django.core.paginator import Paginator
    from django.contrib import messages
    page = 1
    if(request.GET.get('page', '') != ''):
        page = int(request.GET.get('page', ''))
    p = Paginator(games, 50)
    if page > p.num_pages or page < 1:
        messages.warning(request, "The page you requested, " + str(page) + ", does not exist. You have been redirected to the first page.")
        page = 1
    return render(request, 'games/leaderboard.html', {
        'title': 'Game Leaderboard',
        'games': p.page(page),
        'count': p.count,
        'page_obj': p.get_page(page),
        'current_page': page,
        'description': 'See the leading players on {}'.format(settings.SITE_NAME)
    })

def invite(request, id):
    from django.urls import reverse
    from feed.models import Post
    from games.models import Game
    from django.utils import timezone
    import datetime
    import random
    from django.conf import settings
    from django.shortcuts import render, get_object_or_404, redirect
    post = Post.objects.filter(friendly_name__icontains=id).order_by('-date_posted').first()
    if not post: post = Post.objects.filter(friendly_name__icontains=id[:32]).order_by('-date_posted').first()
    if not post: post = Post.objects.filter(friendly_name__icontains=id[:24]).order_by('-date_posted').first()
    if not post: post = Post.objects.filter(friendly_name__icontains=id[:15]).order_by('-date_posted').first()
    code = str(random.randint(get_num_length(1, settings.GAME_CODE_LENGTH), get_num_length(9, settings.GAME_CODE_LENGTH)))
    user_code = str(random.randint(get_num_length(1, settings.GAME_CODE_LENGTH), get_num_length(9, settings.GAME_CODE_LENGTH)))
    while (Game.objects.filter(uid=user_code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last() or Game.objects.filter(uid=user_code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last()):
        code = str(random.randint(get_num_length(1, settings.GAME_CODE_LENGTH), get_num_length(9, settings.GAME_CODE_LENGTH)))
        user_code = str(random.randint(get_num_length(1, settings.GAME_CODE_LENGTH), get_num_length(9, settings.GAME_CODE_LENGTH)))
    game = Game.objects.create(post=post, uid=user_code, code=code)
    return render(request, 'games/invite.html', {'game': game, 'code': code, 'user_code': user_code, 'post': post, 'title': 'Invite Player', 'small': True})

@csrf_exempt
@never_cache
#@cache_page(60*60*24*30)
def join(request):
    from .forms import JoinForm
    from django.urls import reverse
    from games.models import Game
    from django.utils import timezone
    import datetime
#    from django.conf import settings
    from django.shortcuts import redirect
    if request.method == 'POST':
        form = JoinForm(request.POST)
        if form.is_valid():
            game = Game.objects.filter(code=form.cleaned_data.get('code', None), time__gte=timezone.now() - datetime.timedelta(hours=48)).last()
            if not game:
                from django.contrib import messages
                messages.warning(request, 'This code was not recognized. Please try again.')
                return redirect(request.path)
            game.started = True
            game.save()
            return redirect(reverse('games:play', kwargs={'id': game.post.id, 'code': game.code}))
    from django.shortcuts import render
    return render(request, 'games/join.html', {'title': 'Join Game', 'form': JoinForm(), 'small': True})

def play(request, id, code):
    from .forms import JoinForm
    from django.urls import reverse
    from games.models import Game
    from django.utils import timezone
    import datetime
    from feed.models import Post
#    from django.conf import settings
    from django.shortcuts import render, get_object_or_404, redirect
    post = get_object_or_404(Post, id=id)
    game = Game.objects.filter(post=post, code=code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last()
    player = False
    if not game:
        game = Game.objects.filter(post=post, uid=code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last()
        player = True
    if request.user.is_authenticated and player:
        game.player1 = request.user
        game.save()
    elif request.user.is_authenticated and not player:
        game.player2 = request.user
        game.save()
    return render(request, 'games/game.html', {'hidenavbar': True, 'title': 'Play Game', 'post': post, 'game': game, 'player': player, 'full': True, 'game_code': code, 'show_ads': False})
