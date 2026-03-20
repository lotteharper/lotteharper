from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
import asyncio
import uuid
sessions = {}
remote_sessions = {}
import datetime
from django.utils import timezone

@sync_to_async
def get_user(id):
    from django.contrib.auth.models import User
    try:
        user = User.objects.filter(id=int(id)).first()
        if user is None: return False
    except: return False
    return True

last_updated = None

async def update_event(self):
    global sessions
    global remote_sessions
    global last_updated
    if (not last_updated) or last_updated < timezone.now() - datetime.timedelta(seconds=15):
        for key, sess in sessions.items():
            auth = await get_user(sess.scope['user'].id)
            remote_sessions[sess.pkey] = auth
        last_updated = timezone.now()

async def user_thread(self):
    while self.connected:
        await update_event(self)
        global remote_sessions
        if self.pkey in remote_sessions and remote_sessions[self.pkey]: await self.send(text_data='y')
        await asyncio.sleep(20)


class AuthConsumer(AsyncWebsocketConsumer):
    connected = False
    pkey = None
    async def connect(self):
        await self.accept()
        self.connected = True
        global sessions
        sessions[self.pkey] = self
        await user_thread(self)
        self.pkey = str(uuid.uuid4())
        pass

    async def disconnect(self, close_code):
        self.connected = False
        global sessions
        del sessions[self.pkey]
        global remote_sessions
        del remote_sessions[self.pkey]
        pass

    # This function receive messages from WebSocket.
    async def receive(self, text_data):
        pass

    pass
