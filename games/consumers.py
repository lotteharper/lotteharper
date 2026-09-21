import datetime
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import transaction
from django.utils import timezone

from games.models import Game


GAME_MAX_AGE = datetime.timedelta(hours=48)


def normalise_action(value):
    """
    Store actions without trailing slash characters.

    The browser may send:
        draw,deck,Player 1/

    The database stores:
        draw,deck,Player 1
    """
    return str(value or "").strip().strip("/").strip()


def split_history(turns):
    """
    Convert Game.turns into individual actions.

    Stored format:
        draw,deck,Player 1/discard,4.2,Player 1/
    """
    if not turns:
        return []

    return [
        action
        for action in (
            normalise_action(item)
            for item in str(turns).split("/")
        )
        if action
    ]


def serialise_history(actions):
    """
    Convert actions into the format used by the JavaScript client.
    """
    if not actions:
        return ""

    return "/".join(actions) + "/"


def find_game(queryset, code):
    """
    Support both Game.code and the legacy Game.uid.
    """
    game = queryset.filter(code=code).order_by("-id").first()

    if game is None:
        game = queryset.filter(uid=code).order_by("-id").first()

    return game


@database_sync_to_async
def get_game_for_connection(post_id, code):
    cutoff = timezone.now() - GAME_MAX_AGE

    games = Game.objects.filter(
        post__id=post_id,
        time__gte=cutoff,
    )

    return find_game(games, code)


@database_sync_to_async
def get_game_by_primary_key(game_id):
    return Game.objects.filter(id=game_id).first()


@database_sync_to_async
def increment_connected_players(game_id):
    with transaction.atomic():
        game = (
            Game.objects
            .select_for_update()
            .filter(id=game_id)
            .first()
        )

        if game is None:
            return 0

        game.players = max(0, game.players or 0) + 1
        game.save(update_fields=["players"])

        return game.players


@database_sync_to_async
def decrement_connected_players(game_id):
    with transaction.atomic():
        game = (
            Game.objects
            .select_for_update()
            .filter(id=game_id)
            .first()
        )

        if game is None:
            return 0

        game.players = max(0, (game.players or 0) - 1)
        game.save(update_fields=["players"])

        return game.players


@database_sync_to_async
def append_turn(game_id, action):
    """
    Append one gameplay action to Game.turns.

    This is the important persistence operation. The database row is
    locked so simultaneous requests cannot overwrite each other's history.
    """
    action = normalise_action(action)

    if not action:
        return None

    with transaction.atomic():
        game = (
            Game.objects
            .select_for_update()
            .filter(id=game_id)
            .first()
        )

        if game is None:
            return None

        existing_actions = split_history(game.turns)
        existing_actions.append(action)

        game.turn = action
        game.turns = serialise_history(existing_actions)
        game.begun = True

        game.save(
            update_fields=[
                "turn",
                "turns",
                "begun",
            ]
        )

        return {
            "action": action,
            "history": game.turns,
        }


@database_sync_to_async
def get_persisted_state(game_id):
    """
    Return the complete state needed by a reloading browser.
    """
    game = Game.objects.filter(id=game_id).first()

    if game is None:
        return None

    return {
        "type": "game_state",
        "game_id": game.id,
        "history": split_history(game.turns),
        "player1_score": game.player1_score,
        "player2_score": game.player2_score,
        "scored": bool(game.scored),
        "begun": bool(game.begun),
    }


@database_sync_to_async
def save_scores(post_id, code, player1_score, player2_score):
    """
    Persist final score metadata.

    Scores are not appended to Game.turns because they are not gameplay
    actions. The JavaScript reconstructs round scores from round_complete
    actions.
    """
    try:
        score1 = str(int(player1_score))
        score2 = str(int(player2_score))
    except (TypeError, ValueError):
        return False

    cutoff = timezone.now() - GAME_MAX_AGE

    games = Game.objects.filter(
        post__id=post_id,
        time__gte=cutoff,
    )

    game = find_game(games, code)

    if game is None:
        return False

    with transaction.atomic():
        game = (
            Game.objects
            .select_for_update()
            .filter(id=game.id)
            .first()
        )

        if game is None:
            return False

        game.player1_score = score1
        game.player2_score = score2
        game.scored = True

        game.save(
            update_fields=[
                "player1_score",
                "player2_score",
                "scored",
            ]
        )

    return True


@database_sync_to_async
def reset_game_state(game_id):
    """
    Call this only when deliberately starting a brand-new game.

    Do not call it from connect(), because a page reload or the second
    player connecting would erase the existing game.
    """
    with transaction.atomic():
        game = (
            Game.objects
            .select_for_update()
            .filter(id=game_id)
            .first()
        )

        if game is None:
            return False

        game.turn = ""
        game.turns = ""
        game.player1_score = None
        game.player2_score = None
        game.scored = False
        game.begun = False
        game.players = 0

        game.save(
            update_fields=[
                "turn",
                "turns",
                "player1_score",
                "player2_score",
                "scored",
                "begun",
                "players",
            ]
        )

    return True


def is_valid_game_action(action):
    """
    Validate actions that are allowed in Game.turns.

    Accepted examples:

        draw,deck,Player 1
        draw,discard,Player 2
        discard,4.2,Player 1
        round_complete,3,Player 1
    """
    action = normalise_action(action)

    if not action:
        return False

    parts = action.split(",")
    action_type = parts[0]

    if action_type == "draw":
        return (
            len(parts) == 3
            and parts[1] in {"deck", "discard"}
            and bool(parts[2])
        )

    if action_type == "discard":
        if len(parts) != 3:
            return False

        card_parts = parts[1].split(".")

        if len(card_parts) != 2:
            return False

        try:
            value = int(card_parts[0])
            suit = int(card_parts[1])
        except (TypeError, ValueError):
            return False

        return (
            0 <= value < 13
            and 0 <= suit < 4
            and bool(parts[2])
        )

    if action_type == "round_complete":
        if len(parts) != 3:
            return False

        try:
            round_number = int(parts[1])
        except (TypeError, ValueError):
            return False

        return (
            3 <= round_number <= 13
            and bool(parts[2])
        )
    if action_type == "round_advance":
        if len(parts) != 3:
            return False

        try:
            round_number = int(parts[1])
        except (TypeError, ValueError):
            return False

        return (
            3 <= round_number <= 13
            and bool(parts[2])
        )


    return False


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            post_id = int(
                self.scope["url_route"]["kwargs"]["id"]
            )
            code = str(
                self.scope["url_route"]["kwargs"]["code"]
            )
        except (KeyError, TypeError, ValueError):
            await self.close(code=4000)
            return

        game = await get_game_for_connection(post_id, code)

        if game is None:
            await self.close(code=4004)
            return

        self.game_id = game.id
        self.post_id = post_id
        self.code = code
        self.group_name = f"game_{game.id}"
        self.player_counted = False

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        await increment_connected_players(self.game_id)
        self.player_counted = True

        state = await get_persisted_state(self.game_id)

        if state is None:
            state = {
                "type": "game_state",
                "game_id": self.game_id,
                "history": [],
                "player1_score": None,
                "player2_score": None,
                "scored": False,
                "begun": False,
            }

        await self.send(text_data=json.dumps(state))

    async def disconnect(self, close_code):
        if getattr(self, "group_name", None):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

        if (
            getattr(self, "player_counted", False)
            and getattr(self, "game_id", None) is not None
        ):
            await decrement_connected_players(self.game_id)

        self.player_counted = False

    async def receive(self, text_data):
        message = normalise_action(text_data)

        if not message:
            return

        if message == "x":
            state = await get_persisted_state(self.game_id)

            if state is None:
                state = {
                    "type": "game_state",
                    "game_id": self.game_id,
                    "history": [],
                    "player1_score": None,
                    "player2_score": None,
                    "scored": False,
                    "begun": False,
                }

            await self.send(text_data=json.dumps(state))
            return

        if message == "y":
            game = await get_game_by_primary_key(self.game_id)

            await self.send(
                text_data=json.dumps({
                    "type": "game_action",
                    "action": normalise_action(
                        game.turn if game else ""
                    ),
                })
            )
            return

        if message.startswith("<SCORE>,"):
            parts = message.split(",")

            if len(parts) == 4:
                if parts[1] == "Player 1":
                    await save_scores(
                        self.post_id,
                        self.code,
                        parts[2],
                        parts[3],
                    )
                elif parts[1] == "Player 2":
                    await save_scores(
                        self.post_id,
                        self.code,
                        parts[3],
                        parts[2],
                    )

            return

        if not is_valid_game_action(message):
            return

        result = await append_turn(
            self.game_id,
            message,
        )

        if result is None:
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "game.action",
                "action": result["action"],
            },
        )

    async def game_action(self, event):
        await self.send(
            text_data=json.dumps({
                "type": "game_action",
                "action": event.get("action", ""),
            })
        )
