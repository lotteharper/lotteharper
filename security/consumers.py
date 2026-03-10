import json, threading
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
import asyncio
from .tests import face_mrz_or_nfc_verified

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

@sync_to_async
def reset_session(user_id):
    user = User.objects.get(id=int(user_id))
    if user:
        for scan in user.mrz_scans.filter(valid=True, timestamp__gte=timezone.now()-datetime.timedelta(minutes=settings.MRZ_SCAN_REQUIRED_MINUTES)):
            scan.valid = False
            scan.save()
        for scan in user.nfc_scans.filter(valid=True, timestamp__gte=timezone.now()-datetime.timedelta(minutes=settings.NFC_SCAN_REQUIRED_MINUTES)):
            scan.valid = False
            scan.save()

@sync_to_async
def logout_user(user_id, session_key):
    user = User.objects.get(id=int(user_id))
    [s.delete() for s in Session.objects.all() if s.get_decoded().get('_auth_user_id') == user.id and s.session_key == session_key]

async def security_event(self):
    session_auth = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
    message = 'y' if session_auth else 'n'
#    print(message)
    return message
#    await self.send(text_data=message)

async def security_thread(self):
    while self.connected:
        try:
            message = await security_event(self)
            await self.send(text_data=message)
            await asyncio.sleep(30)
        except:
            import traceback
#            print(traceback.format_exc())

@sync_to_async
def patch_session(user_id, skey):
    from security.build import update_session
    update_session(user_id, skey)

@sync_to_async
def build_session(user_id, skey):
    from security.build import async_build_session
    update_session(user_id, skey)

class ModalConsumer(AsyncWebsocketConsumer):
    user_id = None
    session_key = None
    connected = False
    async def connect(self):
        self.user_id = self.scope['user'].id
        self.session_key = self.scope['session'].session_key
        auth = await get_user(self.scope['user'].id)
        if not (auth): return
        await patch_session(self.scope['user'].id, self.session_key)
        await self.accept()
        self.connected = True
        await security_thread(self)

    async def disconnect(self, close_code):
        self.connected = False
        pass

    # This function receive messages from WebSocket.
    async def receive(self, text_data):
        if text_data == 'logout': await logout_user(self.user_id, self.session_key)
        else: await reset_session(self.user_id)
        pass

    pass
