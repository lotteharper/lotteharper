import json, threading
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
import asyncio
from .tests import face_mrz_or_nfc_verified

remote_sessions = {}

@sync_to_async
def get_user(id):
    try:
        user = User.objects.get(id=int(id))
    except: return False
    if not (user.profile.admin or user.is_superuser): return False
    return True

@sync_to_async
def get_auth(user_id, session_key):
    user = User.objects.get(id=int(user_id)) if user_id else None
    from security.models import UserSession
    from django.utils import timezone
    for u in UserSession.objects.filter(user__id=user_id, session_key=session_key).order_by('-timestamp'):
        if u.expires > timezone.now() and (u.authorized and u.bypass) and not u.deauth:
            return True
    return False

import re, uuid
import os
import sys
import select
from live.models import VideoCamera
import datetime
from security.models import Session
from asgiref.sync import sync_to_async
from django.utils import timezone

sessions = {}
last_update = None

@sync_to_async
def update_sessions():
    global remote_sessions
    global sessions
    global remote
    global last_update
    if not last_update or last_update < timezone.now() - datetime.timedelta(seconds=settings.SESSION_UPDATE_SECONDS):
        for key, sess in remote_sessions.items():
            session_auth = get_auth(sess.scope['user'].id, sess.scope['session'].session_key)
            message = 'y' if session_auth else 'n'
            sessions[sess.skey] = message
        last_update = timezone.now()

@sync_to_async
def get_session(skey):
    global remote_sessions
    bself = remote_sessions[skey]
    session_auth = get_auth(bself.scope['user'].id, bself.scope['session'].session_key)
    message = 'y' if session_auth else 'n'
    return message
#    session = Session.objects.filter(injection_key=session_id, time__gte=timezone.now() - datetime.timedelta(minutes=60*24*7), index=settings.SESSION_INDEX).last()
#    return session

@sync_to_async
def clear_session(session_id):
    global sessions
    del sessions[session_id]

async def remote_thread(self):
    while self.connected:
        await update_sessions()
        global remote_sessions
        global sessions
        if self.skey in sessions and sessions[self.skey] != self.last_session:
            await self.send(text_data=sessions[self.skey])
            self.last_session = sessions[self.skey]
        await asyncio.sleep(10)


class ModalConsumer(AsyncWebsocketConsumer):
    session_id = None
    connected = False
    user_id = None
    path = None
    ip = None
    skey = None
    last_session = None
    session_key = None
    async def connect(self):
        self.user_id = self.scope['user'].id
        self.session_key = self.scope['session'].session_key
        self.ip = self.scope["client"][0]
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
#        self.path = query_params['path'][0]
        await self.accept()
        self.skey = str(uuid.uuid4())
        self.connected = True
        global remote_sessions
        remote_sessions[self.skey] = self
        await remote_thread(self)

    async def receive(self, text_data):
        self.ip = text_data
#        await set_ip(self)

    async def disconnect(self, close_code):
        self.connected = False
        pass
