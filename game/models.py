import uuid

from django.conf import settings
from django.db import models


class WorldBlockEdit(models.Model):
    """Persistent override for a generated or player-placed world block."""

    room = models.CharField(max_length=48)
    x = models.IntegerField()
    y = models.IntegerField()
    z = models.IntegerField()
    color = models.CharField(max_length=7, null=True, blank=True)
    is_removed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("room", "x", "y", "z"),
                name="unique_world_block_edit_per_room_coordinate",
            ),
        ]
        indexes = [
            models.Index(fields=("room",)),
        ]

    def __str__(self):
        return f"{self.room}: ({self.x}, {self.y}, {self.z})"


def default_position():
    return {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "yaw": 0.0,
        "pitch": 0.0,
    }


def default_inventory():
    return [None for _ in range(27)]


class WorldPlayer(models.Model):
    """A player's persistent state within a world room."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="world_player_states",
    )
    room = models.CharField(max_length=48)
    player_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    position = models.JSONField(default=default_position)
    inventory = models.JSONField(default=default_inventory)
    is_online = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "room"),
                name="unique_world_player_per_user_room",
            ),
        ]
        indexes = [
            models.Index(fields=("room", "is_online")),
        ]

    def __str__(self):
        return f"{self.user_id} in {self.room}"


def default_chest_data():
    return {"slots": [None for _ in range(27)]}


def default_furnace_data():
    return {
        "slots": [None, None, None],
        "burn_remaining": 0.0,
        "cook_progress": 0.0,
    }


class WorldContainer(models.Model):
    """Persistent chest or furnace state at a room coordinate."""

    CHEST = "chest"
    FURNACE = "furnace"
    KIND_CHOICES = [
        (CHEST, "Chest"),
        (FURNACE, "Furnace"),
    ]

    room = models.CharField(max_length=48)
    x = models.IntegerField()
    y = models.IntegerField()
    z = models.IntegerField()
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("room", "x", "y", "z"),
                name="unique_world_container_per_room_coordinate",
            ),
        ]
        indexes = [
            models.Index(fields=("room",)),
        ]

    def __str__(self):
        return f"{self.kind} in {self.room}: ({self.x}, {self.y}, {self.z})"
