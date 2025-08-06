import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

@sync_to_async
def get_auth(user_id, session_key):
    from security.models import UserSession
    sess = UserSession.objects.filter(user__id=user_id, session_key=session_key).order_by('-timestamp')
    for s in sess:
        if s.authorized: return True
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
def censor_profanity(text):
    from better_profanity import profanity
    return profanity.censor(text)

@sync_to_async
def translate_message(self, message):
    from translate.translate import translate_html
    return translate_html(None, message, target=self.lang)

@sync_to_async
def create_stream_message(user_id, meeting_id, message):
    from django.contrib.auth.models import User
    user = User.objects.filter(id=int(user_id)).first() if user_id else None
    from meetings.models import ChatMessage
    ChatMessage.objects.create(user=user, meeting_id=meeting_id, message=message)

class ChatConsumer(AsyncWebsocketConsumer):
    lang = 'en'
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.room_group_name = f'meeting_chat_{self.meeting_id}'
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
                'username': data.get('username', 'Guest')
            }
        )
        await create_stream_message(self.scope["user"].id if self.scope['user'] else None, self.meeting_id, data['message'])

    async def chat_message(self, event):
        mess = await translate_message(self, event['message'])
        await self.send(text_data=json.dumps({
            'message': mess,
            'username': event['username']
        }))


class MeetingConsumer(AsyncWebsocketConsumer):
    audio_volume = -1000
    connected = False
    username = 'Guest'
    async def connect(self):
        self.meeting_id = self.scope["url_route"]["kwargs"]["meeting_id"]
        self.room_group_name = f"meeting_{self.meeting_id}"
        self.user_id = self.channel_name  # Unique per connection

        # Announce new peer
        self.username = await get_user_name(self.scope['user'].id)
        if not self.username:
            import random
            self.username = "Guest {}".format(random.randrange(111,999))

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

#await self.channel_layer.group_send(
#    self.room_group_name,
#    {
#        "type": "signal_message",
#        "message": {
#            "type": "peer-joined",
#            "peer_id": peer_id,
#            "username": self.scope["user"].username if self.scope["user"].is_authenticated else "Guest",
#                "peer_name": self.name
#        },
#    }
#)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "peer.joined",
                "peer_id": self.user_id,
                "peer_name": self.username,
            }
        )
        self.connected = True

    async def disconnect(self, close_code):
        self.connected = False
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # Announce peer left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "peer.left",
                "peer_id": self.user_id,
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        target = data.get("target")
        payload = data.get("data", {})

        # Signal relay: send signal to a specific peer
        if action == "signal":
            await self.channel_layer.send(target, {
                "type": "signal.message",
                "from": self.user_id,
                "data": payload,
                "username": self.username,
            })
        if action == "volume":
            self.audio_volume = payload['volume'] if 'volume' in payload else -1000
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "volume_event",
                    "peer_id": self.user_id,
                    "volume": self.audio_volume
                }
            )
#            print(self.volume)

    async def peer_joined(self, event):
        # Notify all peers except the one who just joined
        if event["peer_id"] != self.user_id and 'peer_name' in event and event['peer_name']:
            await self.send(text_data=json.dumps({
                "type": "peer-joined",
                "peer_id": event["peer_id"],
                "peer_name": event["peer_name"],
    #event["peer_name"],
            }))

    async def peer_left(self, event):
        # Notify peers
        await self.send(text_data=json.dumps({
            "type": "peer-left",
            "peer_id": event["peer_id"],
        }))

    async def signal_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "signal",
            "from": event["from"],
            "data": event["data"],
            "username": event["username"],
        }))

    async def volume_event(self, event):
        # Notify peers
        await self.send(text_data=json.dumps({
            "type": "volume",
            "peer_id": event["peer_id"],
            "volume": event["volume"],
        }))

