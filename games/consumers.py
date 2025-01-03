from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth.models import User
from games.models import Game
from asgiref.sync import sync_to_async
from django.utils import timezone
import datetime

@sync_to_async
def get_game(id, code):
    game = Game.objects.filter(post__id=id, code=code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last()
    if not game: game = Game.objects.filter(post__id=id, uid=code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last()
    return game

@sync_to_async
def set_game(id, code, turn):
    game = Game.objects.filter(post__id=id, code=code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last()
    if not game: game = Game.objects.filter(post__id=id, uid=code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last()
    game.turn = turn
    game.turns = game.turns + turn
    game.save()

@sync_to_async
def update_players(game_id, p):
    game = Game.objects.get(id=int(game_id))
    if game.players is None or game.players < 0: game.players = 0
    game.players = game.players + p
    game.save()

@sync_to_async
def update_scores(id, code, score1, score2, player):
    game = Game.objects.filter(post__id=id, code=code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last()
    if not game: game = Game.objects.filter(post__id=id, uid=code, time__gte=timezone.now() - datetime.timedelta(hours=48)).last()
    if player:
        if game.player1_score and game.player1_score != score1:
            game.player1_score = 0
            game.player2_score = 0
            game.scored = False
            game.save()
            return
        if game.player2_score and game.player2_score != score2:
            game.player1_score = 0
            game.player2_score = 0
            game.scored = False
            game.save()
            return
        game.player1_score = score1
        game.player2_score = score2
        game.scored = True
    elif not player:
        if game.player1_score and game.player1_score != score1:
            game.player1_score = 0
            game.player2_score = 0
            game.scored = False
            game.save()
            return
        if game.player2_score and game.player2_score != score2:
            game.player1_score = 0
            game.player2_score = 0
            game.scored = False
            game.save()
            return
        game.player1_score = score1
        game.player2_score = score2
        game.scored = True
    game.save()

@sync_to_async
def get_user(user_id):
    print(user_id)
    return User.objects.get(id=user_id)

game_sockets = {}

class GameConsumer(AsyncWebsocketConsumer):
    id = None
    code = None
    last_turn = 'x'
    async def connect(self):
        self.id = int(self.scope['url_route']['kwargs']['id'])
        self.code = self.scope['url_route']['kwargs']['code']
        game = await get_game(self.id, self.code)
        global game_sockets
        if not self.code in game_sockets: game_sockets[self.code] = self
        else: return
        if game.players is None or game.players < 2:
            await self.accept()
            await update_players(game.id, 1)
        else:
            return
        await self.send(text_data=game.turns)

    async def disconnect(self, close_code):
        global game_sockets
        if self.code in game_sockets and game_sockets[self.code] == self: del game_sockets[self.code]
        game = await get_game(self.id, self.code)
        await update_players(game.id, -1)
        pass

    async def receive(self, text_data):
        game = await get_game(self.id, self.code)
        if text_data == 'x':
            await self.send(text_data=game.turns)
            return
        if text_data == 'y':
            await self.send(text_data=game.turn)
            return
        if text_data.startswith('<SCORE>,'):
            data = text_data.split(',')
            if data[1] == 'Player 1':
                await update_scores(self.id, self.code, data[2], data[3], True)
            elif data[1] == 'Player 2':
                await update_scores(self.id, self.code, data[2], data[3], False)
            return
        global game_sockets
#        print(text_data)
#        print(game_sockets)
        if game.code == self.code and game.uid in game_sockets: await game_sockets[game.uid].send(text_data=text_data)
        if game.uid == self.code and game.code in game_sockets: await game_sockets[game.code].send(text_data=text_data)
        await set_game(self.id, self.code, text_data)
        pass
    pass
