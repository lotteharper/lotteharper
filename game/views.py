from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def game(request):
    return render(request, 'game/game.html', {'title': 'Little Blockworks', 'preload': 5000, 'load_timeout': 5000})
