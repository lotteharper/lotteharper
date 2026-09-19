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


@sync_to_async
def increment_watchcount(slug):
    from django.core.cache import cache

    # cache.add() only succeeds when the key does not already exist.
    # This initializes the counter to zero before incrementing it.
    cache.add(slug, 0, timeout=600)

    try:
        return cache.incr(slug)
    except ValueError:
        # Handles a backend where the key disappeared between add/incr.
        cache.set(slug, 1, timeout=600)
        return 1


@sync_to_async
def decrement_watchcount(slug):
    from django.core.cache import cache

    try:
        count = cache.decr(slug)
    except ValueError:
        count = 0

    if count <= 0:
        cache.delete(slug)
        return 0

    # Refresh the expiration time after each update.
    cache.touch(slug, timeout=600)
    return count


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


@sync_to_async
def get_watchcount(slug):
    from django.core.cache import cache

    return cache.get(slug, 0) or 0


class WebRTCSignalingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_name_param = self.scope["url_route"]["kwargs"]["channel_name"]
        self.camera_name_param = self.scope["url_route"]["kwargs"]["camera_name"]

        self.verbose_name = (
            f"{self.channel_name_param}_{self.camera_name_param}"
        )
        self.room_group_name = f"webrtc_{self.verbose_name}"

        self.is_broadcaster = False
        self.counted_as_viewer = False

        user = self.scope["user"]

        # Keep your existing authentication logic here.
        username = await get_user_name(user.id) if user.is_authenticated else False
        auth = (
            await get_auth(
                user.id,
                self.scope["session"].session_key,
            )
            if user.is_authenticated
            else False
        )
        from urllib.parse import parse_qs
        query_params = parse_qs(
            self.scope["query_string"].decode()
        )

        broadcast = query_params.get("broadcast", [None])[0]

        channel_open = self.verbose_name in open_channels

        self.is_broadcaster = bool(
            user.is_authenticated
            and user.username == self.channel_name_param
            and username == self.channel_name_param
            and auth
            and broadcast
            and not channel_open
        )

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

        # Count viewers, but do not count the broadcaster.
        self.watchcount_slug = f"watchcount:{self.channel_name_param}"

        if not self.is_broadcaster:
            self.counted_as_viewer = True
            await increment_watchcount(self.watchcount_slug)

        # Always send the current count to every connection, including
        # the broadcaster.
        await self.send_watch_count()
        await self.broadcast_watch_count()

        if not self.is_broadcaster:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "new_viewer",
                    "viewer_channel": self.channel_name,
                },
            )

            rotation = channel_rotation.get(self.room_group_name, 0)

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "rotation",
                        "data": rotation,
                    }
                )
            )
        else:
            open_channels[self.verbose_name] = self

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcaster_online",
                },
            )

            # Make sure existing viewers also receive the count when the
            # broadcaster connects.

    async def disconnect(self, close_code):
        if getattr(self, "counted_as_viewer", False):
            await decrement_watchcount(self.watchcount_slug)
            self.counted_as_viewer = False

            await self.broadcast_watch_count()

        if getattr(self, "is_broadcaster", False):
            open_channels.pop(self.verbose_name, None)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcaster_offline",
                },
            )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def send_watch_count(self):
        count = await get_watchcount(self.watchcount_slug)

        await self.send(
            text_data=json.dumps(
                {
                    "type": "watchcount",
                    "count": count,
                }
            )
        )

    async def broadcast_watch_count(self):
        count = await get_watchcount(self.watchcount_slug)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "watchcount",
                "count": count,
            },
        )

    async def watchcount(self, event):
        # Do not exclude the broadcaster. The broadcaster also has a
        # #watchcount element in the template.
        await self.send(
            text_data=json.dumps(
                {
                    "type": "watchcount",
                    "count": event["count"],
                }
            )
        )
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
