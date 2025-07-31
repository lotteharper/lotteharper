import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope["url_route"]["kwargs"]["meeting_id"]
        self.room_group_name = f"meeting_{self.meeting_id}"
        self.user_id = self.channel_name  # Unique per connection

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Announce new peer
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "peer.joined",
                "peer_id": self.user_id,
            }
        )

    async def disconnect(self, close_code):
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
                "data": payload
            })

    async def peer_joined(self, event):
        # Notify all peers except the one who just joined
        if event["peer_id"] != self.user_id:
            await self.send(text_data=json.dumps({
                "type": "peer-joined",
                "peer_id": event["peer_id"],
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
            "data": event["data"]
        }))
