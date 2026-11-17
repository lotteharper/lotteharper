import asyncio
import hashlib
import json
import logging
from contextlib import suppress
from datetime import timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import transaction
from django.utils import timezone

from .models import Camera
from security.models import UserSession

logger = logging.getLogger(__name__)


def camera_group(username, name):
    # Hash arbitrary names into a valid, bounded channel-layer group name.
    key = json.dumps([username, name], ensure_ascii=True).encode("utf-8")
    return "camera." + hashlib.sha256(key).hexdigest()


@database_sync_to_async
def is_authorized(user_id, session_key):
    if not user_id or not session_key:
        return False

    return UserSession.objects.filter(
        user_id=user_id,
        session_key=session_key,
        expires__gt=timezone.now(),
        authorized=True,
        bypass=True,
        deauth=False,
    ).exists()


@database_sync_to_async
def take_camera_data(username, name):
    with transaction.atomic():
        camera = (
            Camera.objects.select_for_update()
            .filter(user__profile__name=username, name=name)
            .order_by("-connected")
            .first()
        )
        if camera is None or not camera.data:
            return None

        data = camera.data
        camera.data = ""
        camera.save(update_fields=["data"])
        return data


class PhotoboothConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = None
        self.poll_task = None

        user = self.scope["user"]
        session_key = self.scope["session"].session_key
        if not user.is_authenticated or not await is_authorized(user.id, session_key):
            await self.close()
            return

        self.camera_user = self.scope["url_route"]["kwargs"]["username"]
        self.camera_name = self.scope["url_route"]["kwargs"]["name"]
        self.group_name = camera_group(self.camera_user, self.camera_name)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.poll_task = asyncio.create_task(self.poll_camera())

    async def poll_camera(self):
        try:
            while True:
                data = await take_camera_data(self.camera_user, self.camera_name)
                if data:
                    await self.send(text_data=data)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Camera polling failed")
            await self.close(code=1011)

    async def camera_message(self, event):
        await self.send(text_data=event["text"])

    async def disconnect(self, close_code):
        if self.poll_task is not None:
            self.poll_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.poll_task

        if self.group_name is not None:
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        pass


class PhotoboothRemoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        username = self.scope["url_route"]["kwargs"]["username"]
        name = self.scope["url_route"]["kwargs"]["name"]
        self.group_name = camera_group(username, name)
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            await self.close(code=1003)
            return

        await self.channel_layer.group_send(
            self.group_name,
            {"type": "camera.message", "text": text_data},
        )
