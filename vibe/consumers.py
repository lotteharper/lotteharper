from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

vibes = {}

@sync_to_async
def get_vibrator(user):
    from vibe.models import Vibrator
    vibrator, created = Vibrator.objects.get_or_create(user=user)
    return vibrator

@sync_to_async
def set_vibrator(user, setting):
    from vibe.models import Vibrator
    vibrator, created = Vibrator.objects.get_or_create(user=user)
    global vibes
    if (user.username in vibes) and vibes[user.username][1] < timezone.now() - datetime.timedelta(seconds=1.0/4 - 0.08):
        vibes[user.username][0].send(text_data=setting)

@sync_to_async
def get_vibe_user(name):
    from django.contrib.auth.models import User
    return User.objects.get(profile__name=name)

@sync_to_async
def get_user(user_id):
    from django.contrib.auth.models import User
    return User.objects.get(id=user_id)


# Send the setting to the server from foreign user
class RemoteConsumer(AsyncWebsocketConsumer):
    vibe_user = None
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    # This function receive messages from WebSocket.
    async def receive(self, text_data):
        user = await get_user(self.scope['user'].id)
        await set_vibrator(user, text_data)
        pass
    pass

async def vibe_event(self):
    vibrator = await get_vibrator(self.vibe_user)
    await self.send(text_data=vibrator.setting)

async def vibe_thread(self):
    while self.connected:
        await vibe_event(self)
        import asyncio
        await asyncio.sleep(1.0/4)

# Send the setting from the foreign user
class RemoteReceiveConsumer(AsyncWebsocketConsumer):
    vibe_user = None
    connected = False
    async def connect(self):
        self.vibe_user = await get_vibe_user(self.scope['url_route']['kwargs']['username'])
        await self.accept()
        self.connected = True
        await vibe_thread(self)
        global vibes
        from django.utils import timezone
        vibes[self.vibe_user] = (self, timezone.now())

    async def disconnect(self, close_code):
        self.connected = False
        pass

    # This function receive messages from WebSocket.
    async def receive(self, text_data):
        pass
    pass
