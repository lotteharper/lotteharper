import json, uuid, asyncio
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

connected_users = []

async def forward_message(sender, message):
    receiver = await find_user_by_name(message['otherPerson'])
    if not receiver or not sender: return
    message['otherPerson'] = sender['name']
    await receiver['socket'].send(text_data=json.dumps(message))

async def find_user_by_socket(socket):
    global connected_users
    for user in connected_users:
        if user['socket'].uid == socket.uid: return user
    return None

def find_user_by_socket_sync(socket):
    global connected_users
    for user in connected_users:
        if user['socket'].uid == socket.uid: return user
    return None

def update_username_socket(socket, name):
    global connected_users
    for user in connected_users:
        if user['socket'].uid == socket.uid: user['name'] = name
    return None

async def find_user_by_name(name):
    global connected_users
    for user in connected_users:
        if user['name'] == name: return user
    return None

def find_user_by_name_sync(name):
    global connected_users
    for user in connected_users:
        if user['name'] == name: return user
    return None

@sync_to_async
def update_connected_user(socket, name):
    global connected_users
    from chat.models import Key
    keys = Key.objects.filter(name=name)
    key = keys.last()
    print(keys)
    if key and key.check_password(socket.key) and key.permitted:
        if name and not find_user_by_name_sync(name):
            update_username_socket(socket, name)
            print(connected_users)
            return True
    keys = Key.objects.filter(name=name)
    if (key) and key.name and key.name != name and not find_user_by_name_sync(name) and keys.count > 1:
        k = Keys.last()
        k.name = name
        k.save()
        update_username_socket(socket, name)
        print(connected_users)
        return True
    return False


@sync_to_async
def add_connected_user(socket, name, passcode):
    global connected_users
    from chat.models import Key
    from django.utils import timezone
    import datetime
    keys = Key.objects.filter(name=name, keyed_at__gte=timezone.now()-datetime.timedelta(hours=24*28))
    key = keys.last()
    print(keys)
    from security.crypto import encrypt, decrypt
    socket.key = passcode
    try:
        socket.key = decrypt(passcode)
    except: pass # self.send(text_data=json.dumps({'channel': 'key', 'key': encrypt(self.key)})
    if key and key.check_password(socket.key) and key.permitted:
        if name and not find_user_by_name_sync(name):
            if key.age and key.sex:
                connected_users = connected_users + [{'socket': socket, 'name': name, 'sex': key.sex, 'age': key.age}]
            else:
                connected_users = connected_users + [{'socket': socket, 'name': name}]
            print(connected_users)
            ip = socket.scope["client"][0]
            from security.models import UserIpAddress
            ips = UserIpAddress.objects.filter(ip_address=ip)
            for i in ips:
                if i.risk_detected: return False
            return True
            from django.utils import timezone
            import datetime
            if key.keyed_at < timezone.now() - datetime.timedelta(hours=24*7):
                from django.utils.crypto import get_random_string
                key.keyed_at = timezone.now()
                thekey = get_random_string(32)
                key.set_password(thekey)
                key.save()
                from security.crypto import encrypt
                socket.send(text_data=json.dumps({'channel': 'key', 'key': encrypt(thekey)}))
            else: self.send(text_data=json.dumps({'channel': 'key', 'key': encrypt(socket.key)}))

    elif key and not key.permitted: return False
    keys = Key.objects.filter(name=name)
    if (not key) and name and not find_user_by_name_sync(name) and keys.count() == 0:
        Key.objects.create(name=name)
        key.set_password(socket.key)
        connected_users = connected_users + [{'socket': socket, 'name': name}]
        print(connected_users)
        return True
    return False

async def remove_connected_user(socket):
    global connected_users
    count = 0
    for user in connected_users:
        if user['socket'].uid == socket.uid: del connected_users[count]
        count = count + 1

def remove_connected_user_sync(socket):
    global connected_users
    count = 0
    for user in connected_users:
        if user['socket'].uid == socket.uid: del connected_users[count]
        count = count + 1

@sync_to_async
def get_user_text():
    text = ''
    global connected_users
    print(connected_users)
    for user in connected_users:
        text = text + ('{} ({}'.format(user['name'], (str(user['age']) + 'yo') if 'age' in user else '?') + '{}), '.format((str(user['sex']) + '') if 'sex' in user else '') if not user['socket'].connected_with else '')
    return text

async def send_updates(self):
    print("Connected is " + str(self.connected))
#    while self.connected:
    u = await get_user_text()
    to_send = json.dumps({'channel': 'members', 'members': u})
    print(u)
    try:
        await self.send(text_data=to_send)
        print(to_send)
        print('Sent')
    except: pass
#        await asyncio.sleep(15)

@sync_to_async
def update_users(self):
    while self.connected:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_updates(self))
        loop.close()
        asyncio.sleep(15)

def ban_user(self, name):
    remove_connected_user_sync(self)
    from chat.models import Key
    self.close()
    keys = Key.objects.filter(name=name, key=self.key)
    for key in keys:
        key.permitted = False
        key.save()

@sync_to_async
def update_age(self, user, message):
    global connected_users
    for us in connected_users:
        if user and us['name'] and us['name'] == user['name']:
            from django.utils import timezone
            from datetime import timedelta
            from chat.models import Key
            keys = Key.objects.filter(name=us['name'])
            key = keys.last()
            if key.updated < timezone.now() - timedelta(minutes=5) or not (key.age and key.sex):
                from chat.age import get_age
                print('Running AI tests')
                age = None
                try:
                    age = get_age(message['data'])
                    key.age = int(age)
                    if age != '?': us['age'] = age
                except: pass
                try:
                    from chat.age import get_sex
                    sex = get_sex(message['data'])
                    if sex != '?': us['sex'] = 'F' if sex > 2 else 'M'
                    key.sex = us['sex']
                except: pass
                key.updated = timezone.now()
                key.save()
                try:
                    from chat.age import is_nude
                    nude = None
                    nude = is_nude(message['data'])
                    other_person = find_user_by_name_sync(self.connected_with)
                    if 'age' in other_person and other_person['age'] < 18:
                        ban = True
                    if ban or (nude and (age and age != '?' and int(age) < 18)) or (age and age != '?' and int(age) < 13):
                        ban_user(self, us['name'])
                        from security.models import UserIpAddress
                        ip = self.scope["client"][0]
                        ips = UserIpAddress.objects.filter(ip_address=ip)
                        for i in ips:
                            i.risk_detected = True
                            i.save()
                        self.disconnect()
                except: pass
                try:
#                    from chat.age import is_violent
                    violent = False #is_violent(message['data'])
                    if violent:
                        ban_user(self, us['name'])
                        from security.models import UserIpAddress
                        ip = self.scope["client"][0]
                        ips = UserIpAddress.objects.filter(ip_address=ip)
                        for i in ips:
                            i.risk_detected = True
                            i.save()
                        self.disconnect()
                except: pass

class StreamConsumer(AsyncWebsocketConsumer):
    uid = None
    connected = False
    key = None
    connected_with = None
    user = None
    streamer = None
    username = None
    async def connect(self):
        self.uid = str(uuid.uuid4())
        try:
            self.username = await get_user_name(self.scope['user'].id)
        except: self.username = None
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'u' in query_params and query_params['u']: self.streamer = query_params['u'][0]
        self.room_group_name = self.streamer if self.streamer else self.username
#        self.key = self.scope['url_route']['kwargs']['key']
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_named
        )

#        print(f"room_group_name : {self.room_group_name} and channel_name : {self.channel_name}")

        await self.accept()
        self.connected = True
        await send_updates(self)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await remove_connected_user(self)
        self.connected = False

    async def receive(self, text_data):
        global connected_users
        sender = await find_user_by_socket(self)
        message = json.loads(text_data)
        match message['channel']:
#            case 'login':
#                if message['name']:
#                    await add_connected_user(self, message['name'], message['key'])
            case 'start_call':
                receiver = await find_user_by_name(message['otherPerson'])
                await forward_message(sender, message)
            case 'end_call':
                await forward_message(sender, message)
            case 'webrtc_ice_candidate':
                await forward_message(sender, message)
            case 'webrtc_offer':
                await forward_message(sender, message)
            case 'webrtc_answer':
                await forward_message(sender, message)
#            case 'members':
#                await send_updates(self)
#            case 'update':
#                if message['name']:
#                    await update_connected_user(self, message['name'])
#            case 'age':
#                await update_age(self, sender, message)
#                await send_updates(self)

@sync_to_async
def create_stream_message(user_id, vendor_name, message):
    from django.contrib.auth.models import User
    user = User.objects.filter(id=int(user_id)).first() if user_id else None
    vendor = User.objects.get(profile__name=vendor_name) if vendor_name else None
    from stream.models import ChatMessage
    ChatMessage.objects.create(user=user, vendor=vendor, message=message)

import json
from channels.generic.websocket import AsyncWebsocketConsumer

@sync_to_async
def censor_profanity(text):
    from better_profanity import profanity
    return profanity.censor(text)

@sync_to_async
def translate_message(self, message):
    from translate.translate import translate_html
    return translate_html(None, message, target=self.lang)


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
                'username': data.get('username', 'Guest')
            }
        )
        await create_stream_message(self.scope["user"].id if self.scope['user'] else None, self.room_name, data['message'])

    async def chat_message(self, event):
        mess = await translate_message(self, event['message'])
        await self.send(text_data=json.dumps({
            'message': mess,
            'username': event['username']
        }))

import json
from channels.generic.websocket import AsyncWebsocketConsumer

open_channels = []

class WebRTCSignalingConsumer(AsyncWebsocketConsumer):
    broadcast = None
    async def connect(self):
        # Get channel name from URL
        self.channel_name_param = self.scope['url_route']['kwargs']['channel_name']
        self.room_group_name = f"webrtc_{self.channel_name_param}"

        # Determine if this connection is the broadcaster (logged in as <channel_name>)
        user = self.scope["user"]
        username = await get_user_name(self.scope['user'].id)
        auth = await get_auth(self.scope['user'].id, self.scope['session'].session_key)
        global open_channels
        channel_open = self.channel_name_param not in open_channels
        from urllib.parse import parse_qs
        query_params = parse_qs(self.scope["query_string"].decode())
        if 'broadcast' in query_params and query_params['broadcast']: self.broadcast = query_params['broadcast'][0]
        self.is_broadcaster = user.is_authenticated and user.username == self.channel_name_param and username == self.channel_name_param and auth and self.broadcast and channel_open

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
        elif self.is_broadcaster:
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "broadcaster_online"}
            )
            open_channels += [self.channel_name_param]

    async def disconnect(self, close_code):
#        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if self.is_broadcaster:
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "broadcaster_offline"}
            )
            global open_channels
            open_channels.remove(self.channel_name_param)

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
