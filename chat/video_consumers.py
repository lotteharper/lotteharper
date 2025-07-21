import json, uuid, asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

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

class VideoConsumer(AsyncWebsocketConsumer):
    uid = None
    connected = False
    key = None
    connected_with = None
    async def connect(self):
        self.uid = str(uuid.uuid4())
        self.room_group_name = 'test_room'
#        self.key = self.scope['url_route']['kwargs']['key']
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
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
            case 'login':
                if message['name']:
                    await add_connected_user(self, message['name'], message['key'])
            case 'start_call':
                self.connected_with = message['otherPerson']
                receiver = await find_user_by_name(message['otherPerson'])
                if receiver and sender: receiver['socket'].connected_with = sender['name']
                await forward_message(sender, message)
            case 'end_call':
                await forward_message(sender, message)
                u = await find_user_by_name(message['otherPerson'])
                if u: u['socket'].connected_with = None
                self.connected_with = None
                print('end call ' + text_data)
            case 'webrtc_ice_candidate':
                await forward_message(sender, message)
            case 'webrtc_offer':
                await forward_message(sender, message)
            case 'webrtc_answer':
                await forward_message(sender, message)
            case 'members':
                await send_updates(self)
            case 'update':
                if message['name']:
                    await update_connected_user(self, message['name'])
            case 'age':
                await update_age(self, sender, message)
                await send_updates(self)
