import json, threading
from channels.generic.websocket import AsyncWebsocketConsumer
import re
import os
import sys
import select
from django.conf import settings
from django.contrib.auth.models import User
from live.models import VideoCamera
import asyncio, threading, datetime
from security.models import Session
from asgiref.sync import sync_to_async
from django.utils import timezone

sessions = {}
last_update = None

@sync_to_async
def update_sessions():
    global sessions
    global last_update
    if (not last_update) or last_update < timezone.now() - datetime.timedelta(seconds=settings.SESSION_UPDATE_SECONDS):
        sess = Session.objects.filter(time__gte=timezone.now() - datetime.timedelta(minutes=60*24*7)).exclude(injection_key__in=sessions).exclude(injection='')
        for s in sess:
            if not s.injection_key in sessions.keys():
                sessions[s.injection_key] = s.injection
        last_update = timezone.now()

@sync_to_async
def session_is_injection(session_id):
    global sessions
    if session_id in sessions.keys(): return True
    return False

@sync_to_async
def get_session(session_id):
    global sessions
    if session_id in sessions.keys(): return sessions[session_id]
    return False

@sync_to_async
def clear_session(session_id):
    session = Session.objects.filter(injection_key=session_id).last()
    session.injected = True
    session.past_injections = session.past_injections + session.injection + '\n'
    session.injection = ''
    session.save()
    global sessions
    del sessions[session_id]

@sync_to_async
def generate_session(self):
    from security.models import Session
    from django.utils import timezone
    import uuid
    from django.contrib.auth.models import User
    user = User.objects.filter(id=self.user_id).first()
    s, created = Session.objects.get_or_create(user=user if user else None, ip_address=self.ip[:39] if self.ip else None, path=self.path, method='GET', time=timezone.now(), index=0, injection_key=str(uuid.uuid4()))
    return s.injection_key

@sync_to_async
def set_id(self):
    s = Session.objects.filter(injection_key=self.session_id).first()
    if s:
        s.ip_address = self.ip
        s.save()

@sync_to_async
def init_session(ip, path, session_key, user_id):
    from django.contrib.auth.models import User
    session = Session.objects.filter(ip_address=ip, session_key=session_key, path=path, user=User.objects.get(id=user_id) if user_id else None, time__gte=timezone.now() - datetime.timedelta(minutes=60*24*7)).order_by('-time').first()
    if not session: return False
#    if not session:
#        session = Session.objects.create(ip_address=ip, session_key=session_key, path=path, user=User.objects.get(id=user_id) if user_id else None, time__gte=timezone.now() - datetime.timedelta(minutes=60*24*7)).order_by('-time').first()
    return session.injection_key

async def remote_thread(self):
    key = None
    while not key:
        key = await init_session(self.ip, self.path, self.session_key, self.user_id)
        await asyncio.sleep(10)
#    print('{} {} {} {}'.format(self.ip, self.path, self.session_key, self.user_id))
    self.session_id = key
    while self.connected:
        await update_sessions()
        session = await get_session(self.session_id)
        if session:
            await self.send(text_data=session)
            await clear_session(self.session_id)
        await asyncio.sleep(10)


class RemoteConsumer(AsyncWebsocketConsumer):
    session_id = None
    connected = False
    user_id = None
    path = None
    ip = None
    session_key = None
    async def connect(self):
        self.user_id = self.scope['user'].id
        self.session_key = self.scope['session'].session_key
        self.ip = self.scope["client"][0]
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        self.path = query_params['path'][0]
        await self.accept()
        self.connected = True

    async def receive(self, text_data):
        self.ip = text_data
        await remote_thread(self)

    async def disconnect(self, close_code):
        self.connected = False
        pass

