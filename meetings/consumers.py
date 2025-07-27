import json
from channels.generic.websocket import AsyncWebsocketConsumer

# In-memory room state (for demo purposes; use Redis or DB for production!)
ROOMS = {}  # {room_id: set([user_id, ...])}

class MeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.user_id = None
        await self.accept()

    async def disconnect(self, close_code):
        if self.meeting_id and self.user_id:
            ROOMS[self.meeting_id].discard(self.user_id)
            # Notify others
            await self.channel_layer.group_send(
                self.meeting_id,
                {
                    "type": "peer.leave",
                    "user_id": self.user_id,
                }
            )
            await self.channel_layer.group_discard(self.meeting_id, self.channel_name)

    async def receive(self, text_data):
        msg = json.loads(text_data)
        msg_type = msg.get('type')

        # On join
        if msg_type == 'join':
            self.user_id = msg['userId']
            # Add to room
            if self.meeting_id not in ROOMS:
                ROOMS[self.meeting_id] = set()
            ROOMS[self.meeting_id].add(self.user_id)
            await self.channel_layer.group_add(self.meeting_id, self.channel_name)

            # Send existing participants to new joiner (excluding self)
            others = list(ROOMS[self.meeting_id] - {self.user_id})
            await self.send(text_data=json.dumps({
                'type': 'participants',
                'participants': others,
            }))

            # Notify others a new peer joined
            await self.channel_layer.group_send(
                self.meeting_id,
                {
                    "type": "peer.join",
                    "user_id": self.user_id,
                }
            )

        # Relay signaling
        elif msg_type in ['offer', 'answer', 'ice-candidate']:
            # Relay only to the intended peer
            await self.channel_layer.group_send(
                self.meeting_id,
                {
                    "type": "peer.signal",
                    "message": msg,
                    "target": msg.get('to'),
                }
            )

        # Broadcast chat, media-state, screenshare-state to all
        elif msg_type in ['chat', 'media-state', 'screenshare-state']:
            await self.channel_layer.group_send(
                self.meeting_id,
                {
                    "type": "peer.broadcast",
                    "message": msg,
                }
            )

        # Participant requested leave
        elif msg_type == 'leave':
            if self.user_id:
                ROOMS[self.meeting_id].discard(self.user_id)
                await self.channel_layer.group_send(
                    self.meeting_id,
                    {
                        "type": "peer.leave",
                        "user_id": self.user_id,
                    }
                )
                await self.channel_layer.group_discard(self.meeting_id, self.channel_name)

    # --- Group event handlers ---
    async def peer_join(self, event):
        # Notify clients except the one who just joined
        if self.user_id != event["user_id"]:
            await self.send(text_data=json.dumps({
                "type": "join",
                "userId": event["user_id"],
            }))

    async def peer_leave(self, event):
        if self.user_id != event["user_id"]:
            await self.send(text_data=json.dumps({
                "type": "leave",
                "userId": event["user_id"],
            }))

    async def peer_signal(self, event):
        # Only relay if this is the intended recipient
        if self.user_id == event["target"]:
            await self.send(text_data=json.dumps(event["message"]))

    async def peer_broadcast(self, event):
        await self.send(text_data=json.dumps(event["message"]))
