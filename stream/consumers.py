import json, uuid, asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

@sync_to_async
def get_auth(user_id, session_key):
    from django.contrib.auth.models import User
    user = User.objects.get(id=int(user_id)) if user_id else None
    from security.models import UserSession
    from django.utils import timezone
    for u in UserSession.objects.filter(user__id=user_id, session_key=session_key).order_by('-timestamp'):
        if u.expires > timezone.now() and (u.authorized and u.bypass) and not u.deauth:
            return True
    return False

@sync_to_async
def get_user_name(id):
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(id=int(id))
    except: return False
#    if not (user.profile.vendor or user.is_superuser): return False
    return user.profile.name

@sync_to_async
def create_stream_message(user_id, vendor_name, message, lang):
    from django.contrib.auth.models import User
    user = User.objects.filter(id=int(user_id)).first() if user_id else None
    vendor = User.objects.get(profile__name=vendor_name) if vendor_name else None
    from stream.models import ChatMessage
    ChatMessage.objects.create(user=user, vendor=vendor, message=message, lang=lang)

import json
from channels.generic.websocket import AsyncWebsocketConsumer

@sync_to_async
def censor_profanity(text):
    from better_profanity import profanity
    return profanity.censor(text)

@sync_to_async
def translate_message(self, message, lang):
    from translate.translate import translate_html
    return translate_html(None, message, target=self.lang, src=lang)


class ChatConsumer(AsyncWebsocketConsumer):
    lang = 'en'
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'lang' in query_params and query_params['lang']: self.lang = query_params['lang'][0]
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        from feed.templatetags.app_filters import embedlinks
        data['message'] = await censor_profanity(embedlinks(data['message']))
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data['message'],
                'username': data.get('username', 'Guest'),
                'lang': self.lang,
            }
        )
        await create_stream_message(self.scope["user"].id if self.scope['user'] else None, self.room_name, data['message'], self.lang)

    async def chat_message(self, event):
        mess = await translate_message(self, event['message'], event['lang'])
        await self.send(text_data=json.dumps({
            'message': mess,
            'username': event['username']
        }))

import json
from channels.generic.websocket import AsyncWebsocketConsumer

open_channels = {}
channel_rotation = {}

class WebRTCSignalingConsumer(AsyncWebsocketConsumer):
    broadcast = None
    async def connect(self):
        # Get channel name from URL
        self.channel_name_param = self.scope['url_route']['kwargs']['channel_name']
        self.camera_name_param = self.scope['url_route']['kwargs']['camera_name']
        self.verbose_name = f"{self.channel_name_param}_{self.camera_name_param}"
        self.room_group_name = f"webrtc_{self.verbose_name}"
        # Determine if this connection is the broadcaster (logged in as <channel_name>)
        user = self.scope["user"]
        username = await get_user_name(self.scope['user'].id)
        auth = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
        global open_channels
        channel_open = self.verbose_name in open_channels.keys()
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'broadcast' in query_params and query_params['broadcast']: self.broadcast = query_params['broadcast'][0]
        self.is_broadcaster = user.is_authenticated and user.username == self.channel_name_param and username == self.channel_name_param and auth and self.broadcast and not channel_open

        # Add to group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # If viewer, notify broadcaster of new connection
        if not self.is_broadcaster:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "new_viewer",
                    "viewer_channel": self.channel_name,
                }
            )
            global channel_rotation
            rot = channel_rotation[self.room_group_name] if self.room_group_name in channel_rotation else 0
            await self.send(text_data=json.dumps({"type": "rotation", "data": rot,}))
        elif self.is_broadcaster:
            open_channels[self.verbose_name] = self
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "broadcaster_online"}
            )

    async def disconnect(self, close_code):
        if self.is_broadcaster:
            global open_channels
            del open_channels[self.verbose_name]
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "broadcaster_offline"}
            )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Broadcaster sends offer
        if self.is_broadcaster and data.get("type") == "offer":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_offer",
                    "offer": data["offer"],
                    "broadcaster": self.channel_name,
                    "to": data.get("to"),  # viewer's channel_name
                }
            )
        # Viewer sends answer to broadcaster
        elif not self.is_broadcaster and data.get("type") == "answer":
            await self.channel_layer.send(
                data["to"],  # broadcaster's channel_name
                {
                    "type": "broadcast_answer",
                    "answer": data["answer"],
                    "from": self.channel_name,
                }
            )
        # ICE candidate relay
        elif data.get("type") == "candidate":
            await self.channel_layer.send(
                data["to"],
                {
                    "type": "broadcast_candidate",
                    "candidate": data["candidate"],
                    "from": self.channel_name,
                }
            )
        elif data.get("type") == "rotation" and self.is_broadcaster:
            global channel_rotation
            channel_rotation[self.room_group_name] = data["data"]
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "rotation",
                    "data": data["data"],
                }
            )

    # Notify broadcaster of a new viewer
    async def new_viewer(self, event):
        if self.is_broadcaster:
            await self.send(text_data=json.dumps({
                "type": "new_viewer",
                "id": event["viewer_channel"]
            }))

    # Send offer from broadcaster to a viewer
    async def broadcast_offer(self, event):
        # Only send to the intended viewer
        if not self.is_broadcaster and self.channel_name == event.get("to"):
            await self.send(text_data=json.dumps({
                "type": "offer",
                "offer": event["offer"],
                "from": event["broadcaster"]
            }))

    # Send answer from viewer to broadcaster
    async def broadcast_answer(self, event):
        if self.is_broadcaster:
            await self.send(text_data=json.dumps({
                "type": "answer",
                "answer": event["answer"],
                "from": event["from"]
            }))

    async def broadcaster_online(self, event):
        if not self.is_broadcaster:
            await self.send(text_data=json.dumps({
                "type": "broadcaster_online"
            }))

    async def broadcaster_offline(self, event):
        if not self.is_broadcaster:
            await self.send(text_data=json.dumps({
                "type": "broadcaster_offline"
            }))

    # Relay ICE candidates
    async def broadcast_candidate(self, event):
        await self.send(text_data=json.dumps({
            "type": "candidate",
            "candidate": event["candidate"],
            "from": event["from"]
        }))
