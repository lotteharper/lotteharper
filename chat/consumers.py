from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string

from .models import Message

User = get_user_model()


def chat_group(user_id, recipient_id):
    first, second = sorted((int(user_id), int(recipient_id)))
    return f"chat.{first}.{second}"


@database_sync_to_async
def get_chat_user_id(name):
    return User.objects.filter(profile__name=name).values_list("id", flat=True).first()


@database_sync_to_async
def render_chat(user_id, recipient_id, lang="en"):
    messages = Message.objects.filter(
        Q(sender_id=user_id, recipient_id=recipient_id)
        | Q(sender_id=recipient_id, recipient_id=user_id)
    ).order_by("-sent_at", "-pk")

    paginator = Paginator(messages, 10)
    page = paginator.get_page(1)

    for message in page:
        message.lang = lang
        changed = []

        if message.recipient_id == user_id and not message.seen:
            message.seen = True
            changed.append("seen")
        if message.sender_id == user_id and not message.senderseen:
            message.senderseen = True
            changed.append("senderseen")
        if changed:
            message.save(update_fields=changed)

    return render_to_string(
        "chat/messages_raw.html",
        {"messages": page, "count": paginator.count, "page_obj": page},
    )


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=4401)
            return

        self.user_id = user.id
        self.chat_user_id = await get_chat_user_id(
            self.scope["url_route"]["kwargs"]["username"]
        )
        if self.chat_user_id is None:
            await self.close(code=4404)
            return

        self.group_name = chat_group(self.user_id, self.chat_user_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_chat()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def chat_refresh(self, event):
        await self.send_chat()

    async def send_chat(self):
        html = await render_chat(self.user_id, self.chat_user_id)
        await self.send(text_data=html)


def notify_chat_changed(message):
    """Call after saving a message, inside the same transaction."""
    group = chat_group(message.sender_id, message.recipient_id)

    def notify():
        channel_layer = get_channel_layer()
        if channel_layer is None:
            raise RuntimeError("A channel layer must be configured")
        async_to_sync(channel_layer.group_send)(
            group, {"type": "chat.refresh"}
        )

    transaction.on_commit(notify)
