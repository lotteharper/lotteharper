import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from .models import Message
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from users.models import Profile
import datetime
from django.core.paginator import Paginator

chats = {}
remote_chats = {}

def get_chat(user_id, recipient_id, lang='en'):
    user = User.objects.get(id=int(user_id))
    recipient = User.objects.get(id=int(recipient_id))
    page = 1
    msgs = None
    new = False
    if recipient == user:
        msgs = Message.objects.filter(recipient=recipient).order_by('-sent_at')
    else:
        msgs = Message.objects.filter(sender=recipient).union(Message.objects.filter(sender=user)).order_by('-sent_at')
    p = Paginator(msgs, 10)
    for m in p.get_page(page):
        if (m.sender == user and m.senderseen == False) or m.seen == False:
            new = True
    if new:
        page = 1
        p = Paginator(msgs, 10)
        for message in p.page(page):
            message.lang = lang
            if message.recipient == user:
                message.seen = True
                message.save()
            if message.sender == user:
                message.senderseen = True
                message.save()
        context = {
            'messages': p.page(page),
            'count': p.count,
            'page_obj': p.get_page(page),
        }
        text = render_to_string('chat/messages_raw.html', context)
        return text
    return False

@sync_to_async
def get_chat_user(name):
    return User.objects.get(profile__name=name)

@sync_to_async
def get_user(user_id):
    return User.objects.get(id=user_id)

from django.utils import timezone

last_update = None

import datetime

@sync_to_async
def chat_event(self):
    global last_update
    global chats
    if not last_update or last_update < timezone.now() - datetime.timedelta(seconds=15):
        for uid, chat in chats.items():
            c = get_chat(chat.scope['user'].id, chat.chat_user.id)
            chat.send(text_data=c)
        last_update = timezone.now()

async def chat_thread(self):
    import asyncio
    while self.connected:
        try:
            await chat_event(self)
        except: pass
        await asyncio.sleep(15)

import uuid

# Send the setting to the server from foreign user
class ChatConsumer(AsyncWebsocketConsumer):
    chat_user = None
    connected = False
    uid = None
    async def connect(self):
        self.chat_user = await get_chat_user(self.scope['url_route']['kwargs']['username'])
        await self.accept()
        self.connected = True
        user = await get_user(self.scope['user'].id)
        await chat_thread(self)
        self.uid = str(uuid.uuid4())
        global chats
        chats[self.uid] = self

    async def disconnect(self, close_code):
        self.connected = False
        pass

    # This function receive messages from WebSocket.
    async def receive(self, text_data):
        pass
    pass
