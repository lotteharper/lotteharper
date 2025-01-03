from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from feed.models import Post

class Game(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='games')
    time = models.DateTimeField(default=timezone.now)
    player1 = models.ForeignKey(User, related_name='created_games', null=True, blank=True, on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='joined_games', null=True, blank=True, on_delete=models.CASCADE)
    player1_score = models.CharField(max_length=10, default=None, null=True, blank=True)
    player2_score = models.CharField(max_length=10, default=None, null=True, blank=True)
    uid = models.CharField(max_length=10, default='')
    code = models.CharField(max_length=10, default='')
    begun = models.BooleanField(default=False)
    scored = models.BooleanField(default=False)
    players = models.IntegerField(default=0, null=True)
    turn = models.TextField(default='')
    turns = models.TextField(default='')
