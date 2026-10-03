import json
import math
import re
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import transaction
from django.utils import timezone

from .models import WorldBlockEdit, WorldContainer, WorldPlayer


ROOM_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,48}$")
COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")
EMPTY_INVENTORY = [None] * 27
MAX_WORLD_COORDINATE = 1_000_000

# Keep these item type names in sync with the game's JavaScript.
ITEM_TYPES = {
    "log", "planks", "sticks", "stone", "dirt", "leaves",
    "coal", "iron_ore", "gold_ore", "crystal_ore",
    "iron_ingot", "gold_ingot", "crystal",
    "wood_pickaxe", "stone_pickaxe", "iron_pickaxe",
    "gold_pickaxe", "crystal_pickaxe",
    "wood_axe", "stone_axe", "iron_axe", "gold_axe", "crystal_axe",
    "door", "fence", "chest", "furnace",
}

LEGACY_TYPES_BY_COLOR = {
    "#76502e": "log",
    "#b9824a": "planks",
    "#c99355": "sticks",
    "#777b82": "stone",
    "#826344": "dirt",
    "#32853b": "leaves",
    "#d9ad55": "wood_pickaxe",
    "#98a4b5": "stone_pickaxe",
    "#bf8d43": "wood_axe",
    "#687b91": "stone_axe",
    "#9a6836": "door",
    "#a97843": "fence",
}


def clean_position(value):
    if not isinstance(value, dict):
        return None

    position = {}
    for name in ("x", "y", "z", "yaw", "pitch"):
        number = value.get(name)
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            return None
        if not math.isfinite(number):
            return None
        position[name] = max(-1_000_000.0, min(1_000_000.0, float(number)))

    return position


def clean_item(value):
    if value is None or not isinstance(value, dict):
        return None

    item_type = value.get("type")
    color = value.get("color")
    count = value.get("count")

    if not isinstance(item_type, str) or item_type not in ITEM_TYPES:
        return None
    if not isinstance(color, str) or not COLOR_PATTERN.fullmatch(color):
        return None
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 64:
        return None

    return {"type": item_type, "color": color.lower(), "count": count}


def clean_inventory(value):
    if not isinstance(value, list) or len(value) != 27:
        return None

    result = []

    for slot in value:
        if slot is None:
            result.append(None)
            continue
        if not isinstance(slot, dict):
            return None

        item_type = slot.get("type")
        color = slot.get("color")

        # Support old saved inventory entries that did not include `type`.
        if item_type is None and isinstance(color, str):
            item_type = LEGACY_TYPES_BY_COLOR.get(color.lower())

        cleaned = clean_item({
            "type": item_type,
            "color": color,
            "count": slot.get("count"),
        })
        if cleaned is None:
            return None
        result.append(cleaned)

    return result


def clean_container_data(kind, value):
    if not isinstance(value, dict) or not isinstance(value.get("slots"), list):
        return None

    slots = value["slots"]

    if kind == WorldContainer.CHEST:
        if len(slots) != 27:
            return None
        cleaned_slots = []
        for slot in slots:
            if slot is None:
                cleaned_slots.append(None)
                continue
            cleaned = clean_item(slot)
            if cleaned is None:
                return None
            cleaned_slots.append(cleaned)
        return {"slots": cleaned_slots}

    if kind == WorldContainer.FURNACE:
        if len(slots) != 3:
            return None
        cleaned_slots = []
        for slot in slots:
            if slot is None:
                cleaned_slots.append(None)
                continue
            cleaned = clean_item(slot)
            if cleaned is None:
                return None
            cleaned_slots.append(cleaned)

        burn_remaining = value.get("burn_remaining", 0)
        cook_progress = value.get("cook_progress", 0)

        for number in (burn_remaining, cook_progress):
            if (
                isinstance(number, bool)
                or not isinstance(number, (int, float))
                or not math.isfinite(number)
            ):
                return None

        return {
            "slots": cleaned_slots,
            "burn_remaining": max(0.0, min(3600.0, float(burn_remaining))),
            "cook_progress": max(0.0, min(1.0, float(cook_progress))),
        }

    return None


class WorldConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        room = self.scope["url_route"]["kwargs"].get("room", "")

        if (
            not user
            or not user.is_authenticated
            or not ROOM_PATTERN.fullmatch(room)
        ):
            await self.close(code=4401)
            return

        self.user_id = user.pk
        self.room = room
        self.room_group = f"world_{room}"
        self.last_position = None
        self.last_position_saved_at = None

        state = await self.load_player_state()
        self.player_id = state["player_id"]
        self.last_position = state["position"]

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        await self.send_json({
            "type": "welcome",
            "player_id": self.player_id,
            "position": state["position"],
            "inventory": state["inventory"],
            "players": state["players"],
            "edits": await self.load_room_edits(),
            "containers": await self.load_room_containers(),
        })

        if state["position"] is not None:
            await self.channel_layer.group_send(
                self.room_group,
                {
                    "type": "room.message",
                    "message": {
                        "type": "player_state",
                        "player_id": self.player_id,
                        "position": state["position"],
                    },
                },
            )

    async def disconnect(self, close_code):
        if not hasattr(self, "room_group"):
            return

        if hasattr(self, "player_id"):
            await self.set_player_offline(self.last_position)
            await self.channel_layer.group_send(
                self.room_group,
                {
                    "type": "room.message",
                    "message": {
                        "type": "player_left",
                        "player_id": self.player_id,
                    },
                },
            )

        await self.channel_layer.group_discard(
            self.room_group,
            self.channel_name,
        )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            message = json.loads(text_data or "")
        except (json.JSONDecodeError, TypeError):
            return

        if not isinstance(message, dict):
            return

        message_type = message.get("type")
        if message_type == "position":
            await self.receive_position(message.get("position"))
        elif message_type == "inventory":
            await self.receive_inventory(message.get("inventory"))
        elif message_type == "world_edit":
            await self.receive_world_edit(message)
        elif message_type == "container_get":
            await self.receive_container_get(message)
        elif message_type == "container_update":
            await self.receive_container_update(message)

    async def receive_position(self, raw_position):
        position = clean_position(raw_position)
        if position is None:
            return

        self.last_position = position
        now = time.monotonic()

        if (
            self.last_position_saved_at is None
            or now - self.last_position_saved_at >= 1.0
        ):
            await self.save_position(position)
            self.last_position_saved_at = now

        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "room.message",
                "message": {
                    "type": "player_state",
                    "player_id": self.player_id,
                    "position": position,
                },
            },
        )

    async def receive_inventory(self, raw_inventory):
        inventory = clean_inventory(raw_inventory)
        if inventory is None:
            return

        await self.save_inventory(inventory)
        await self.send_json({"type": "inventory_saved"})

    async def receive_world_edit(self, message):
        coordinates = self.clean_coordinates(message)
        if coordinates is None:
            return

        color = message.get("color")
        if color is not None and (
            not isinstance(color, str)
            or not COLOR_PATTERN.fullmatch(color)
        ):
            return

        x, y, z = coordinates
        edit = {
            "x": x,
            "y": y,
            "z": z,
            "color": color.lower() if isinstance(color, str) else None,
        }

        await self.persist_world_edit(edit)
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "room.message",
                "message": {"type": "world_edit", "edit": edit},
            },
        )

    async def receive_container_get(self, message):
        coordinates = self.clean_coordinates(message)
        if coordinates is None:
            return

        x, y, z = coordinates
        container = await self.load_container(x, y, z)

        await self.send_json({
            "type": "container_state",
            "x": x,
            "y": y,
            "z": z,
            "container": container,
        })

    async def receive_container_update(self, message):
        coordinates = self.clean_coordinates(message)
        if coordinates is None:
            return

        kind = message.get("kind")
        if kind not in {WorldContainer.CHEST, WorldContainer.FURNACE}:
            return

        data = clean_container_data(kind, message.get("data"))
        if data is None:
            return

        x, y, z = coordinates
        container = {
            "x": x,
            "y": y,
            "z": z,
            "kind": kind,
            "data": data,
        }

        await self.save_container(x, y, z, kind, data)
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "room.message",
                "message": {
                    "type": "container_state",
                    "container": container,
                },
            },
        )

    @staticmethod
    def clean_coordinates(message):
        coordinates = []
        for name in ("x", "y", "z"):
            value = message.get(name)
            if isinstance(value, bool) or not isinstance(value, int):
                return None
            if abs(value) > MAX_WORLD_COORDINATE:
                return None
            coordinates.append(value)
        return tuple(coordinates)

    async def room_message(self, event):
        await self.send_json(event["message"])

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))

    @database_sync_to_async
    def load_player_state(self):
        with transaction.atomic():
            player, created = WorldPlayer.objects.get_or_create(
                user_id=self.user_id,
                room=self.room,
            )
            player.is_online = True
            player.save(update_fields=("is_online", "updated_at"))

            others = list(
                WorldPlayer.objects.filter(room=self.room, is_online=True)
                .exclude(pk=player.pk)
                .values("player_id", "position")
            )

            position = None if created else clean_position(player.position)
            inventory = clean_inventory(player.inventory)

            return {
                "player_id": str(player.player_id),
                "position": position,
                "inventory": inventory if inventory is not None else EMPTY_INVENTORY,
                "players": [
                    {"id": str(row["player_id"]), "position": row["position"]}
                    for row in others
                ],
            }

    @database_sync_to_async
    def save_position(self, position):
        WorldPlayer.objects.filter(
            user_id=self.user_id,
            room=self.room,
        ).update(position=position, updated_at=timezone.now())

    @database_sync_to_async
    def save_inventory(self, inventory):
        WorldPlayer.objects.filter(
            user_id=self.user_id,
            room=self.room,
        ).update(inventory=inventory, updated_at=timezone.now())

    @database_sync_to_async
    def set_player_offline(self, last_position):
        updates = {"is_online": False, "updated_at": timezone.now()}
        if last_position is not None:
            updates["position"] = last_position

        WorldPlayer.objects.filter(
            user_id=self.user_id,
            room=self.room,
        ).update(**updates)

    @database_sync_to_async
    def load_room_edits(self):
        rows = WorldBlockEdit.objects.filter(room=self.room).values(
            "x", "y", "z", "color", "is_removed"
        )
        return [
            {
                "x": row["x"],
                "y": row["y"],
                "z": row["z"],
                "color": None if row["is_removed"] else row["color"],
            }
            for row in rows
        ]

    @database_sync_to_async
    def persist_world_edit(self, edit):
        removed = edit["color"] is None
        WorldBlockEdit.objects.update_or_create(
            room=self.room,
            x=edit["x"],
            y=edit["y"],
            z=edit["z"],
            defaults={
                "color": None if removed else edit["color"],
                "is_removed": removed,
            },
        )

    @database_sync_to_async
    def load_room_containers(self):
        result = []
        for row in WorldContainer.objects.filter(room=self.room).iterator():
            data = clean_container_data(row.kind, row.data)
            if data is None:
                continue
            result.append({
                "x": row.x,
                "y": row.y,
                "z": row.z,
                "kind": row.kind,
                "data": data,
            })
        return result

    @database_sync_to_async
    def load_container(self, x, y, z):
        row = WorldContainer.objects.filter(
            room=self.room,
            x=x,
            y=y,
            z=z,
        ).first()
        if row is None:
            return None

        data = clean_container_data(row.kind, row.data)
        if data is None:
            return None

        return {
            "x": row.x,
            "y": row.y,
            "z": row.z,
            "kind": row.kind,
            "data": data,
        }

    @database_sync_to_async
    def save_container(self, x, y, z, kind, data):
        with transaction.atomic():
            WorldContainer.objects.update_or_create(
                room=self.room,
                x=x,
                y=y,
                z=z,
                defaults={
                    "kind": kind,
                    "data": data,
                    "updated_at": timezone.now(),
                },
            )
