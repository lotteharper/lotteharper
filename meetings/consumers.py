import json
from channels.generic.websocket import AsyncWebsocketConsumer

ROOMS = {}

class MeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = str(self.scope['url_route']['kwargs']['meeting_id'])
        self.user_id = None
        await self.accept()

    async def disconnect(self, _close_code):
        if self.meeting_id and self.user_id:
            ROOMS[self.meeting_id].discard(self.user_id)
            await self.channel_layer.group_discard(self.meeting_id, self.channel_name)
            # Notify others
            await self.channel_layer.group_send(
                self.meeting_id, {
                    "type": "peer_leave",
                    "user_id": self.user_id,
                }
            )

    async def receive(self, text_data):
        msg = json.loads(text_data)
        msg_type = msg.get('type')

        if msg_type == 'join':
            self.user_id = msg['userId']
            if self.meeting_id not in ROOMS:
                ROOMS[self.meeting_id] = set()
            ROOMS[self.meeting_id].add(self.user_id)
            await self.channel_layer.group_add(self.meeting_id, self.channel_name)

            others = list(ROOMS[self.meeting_id] - {self.user_id})
            await self.send(json.dumps({
                'type': 'participants',
                'participants': others,
            }))
            # Notify others
            await self.channel_layer.group_send(
                self.meeting_id, {
                    "type": "peer_join",
                    "user_id": self.user_id,
                }
            )

        elif msg_type in ['offer', 'answer', 'ice-candidate']:
            # Relay only to the intended peer
            await self.channel_layer.group_send(
                self.meeting_id,
                {
                    "type": "peer_signal",
                    "target": msg.get('to'),
                    "message": msg,
                }
            )
        elif msg_type == 'chat':
            await self.channel_layer.group_send(
                self.meeting_id, {
                    "type": "peer_broadcast",
                    "message": msg
                }
            )
        elif msg_type == 'leave':
            if self.user_id:
                ROOMS[self.meeting_id].discard(self.user_id)
                await self.channel_layer.group_discard(self.meeting_id, self.channel_name)
                await self.channel_layer.group_send(
                    self.meeting_id, {
                        "type": "peer_leave",
                        "user_id": self.user_id,
                    }
                )

    async def peer_join(self, event):
        if self.user_id != event["user_id"]:
            await self.send(json.dumps({
                "type": "join",
                "userId": event["user_id"],
            }))

    async def peer_leave(self, event):
        if self.user_id != event["user_id"]:
            await self.send(json.dumps({
                "type": "leave",
                "userId": event["user_id"],
            }))

    async def peer_signal(self, event):
        if self.user_id == event["target"]:
            await self.send(json.dumps(event["message"]))

    async def peer_broadcast(self, event):
        await self.send(json.dumps(event["message"]))
