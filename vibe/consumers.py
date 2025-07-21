from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

vibes = {}

@sync_to_async
def get_vibrator(user):
    from vibe.models import Vibrator
    vibrator, created = Vibrator.objects.get_or_create(user__id=user)
    return vibrator

@sync_to_async
def set_vibrator(user, setting):
    import asyncio
    from vibe.models import Vibrator
    vibrator, created = Vibrator.objects.get_or_create(user__id=user)
    global vibes
    from django.utils import timezone
    import datetime
    if (user in vibes):
        for u in vibes[user]:
            if u[1] < timezone.now() - datetime.timedelta(seconds=1.0/4 - 0.08):
                asyncio.run(u[0].send(text_data=setting))
                u[1] = timezone.now()
#                print(setting)
#    vibrator.setting = setting
#    vibrator.save()

@sync_to_async
def get_vibe_user(name):
    from django.contrib.auth.models import User
    return User.objects.get(id=name)

@sync_to_async
def get_user(user_id):
    from django.contrib.auth.models import User
    return User.objects.get(id=user_id)

remotes = {}

# Send the setting to the server from foreign user
class RemoteConsumer(AsyncWebsocketConsumer):
    vibe_user = None
    async def connect(self):
        global remotes
        user = await get_user(self.scope['user'].id)
        if not user in remotes:
            remotes[user] = self
        else: return
        await self.accept()

    async def disconnect(self, close_code):
        global remotes
        user = await get_user(self.scope['user'].id)
        if user in remotes and remotes[user] == self: del remotes[user]
        pass

    # This function receive messages from WebSocket.
    async def receive(self, text_data):
        user = await get_user(self.scope['user'].id)
        await set_vibrator(user.id, text_data)
        pass
    pass

async def vibe_event(self):
    vibrator = await get_vibrator(self.vibe_user)
#    await self.send(text_data=vibrator.setting)

async def vibe_thread(self):
    while self.connected:
        await vibe_event(self)
        import asyncio
        await asyncio.sleep(1.0/4)

@sync_to_async
def is_vendor(user):
    return user.profile.vendor

# Send the setting from the foreign user
class RemoteReceiveConsumer(AsyncWebsocketConsumer):
    vibe_user = None
    connected = False
    async def connect(self):
        self.vibe_user = await get_vibe_user(int(self.scope['url_route']['kwargs']['username']))
        vendor = await is_vendor(self.vibe_user)
        if not vendor: return
        self.vibe_user = self.vibe_user.id
        global vibes
        from django.utils import timezone
        self.connected = True
        if not self.vibe_user in vibes:
            vibes[self.vibe_user] = [[self, timezone.now()],]
        else: vibes[self.vibe_user] += [[self, timezone.now()],]
        await self.accept()

    async def disconnect(self, close_code):
        self.connected = False
        global vibes
        pass

    async def receive(self, text_data):
        pass
    pass
