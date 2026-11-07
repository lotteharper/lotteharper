import datetime
import json
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import transaction
from django.utils import timezone

from games.models import Game


GAME_MAX_AGE = datetime.timedelta(hours=48)

# Game.players stores occupied player slots as bits, not a socket count.
PLAYER_SLOTS = {"Player 1": 1, "Player 2": 2}
BOTH_PLAYERS = 3


def normalise_action(value):
    """
    Remove whitespace and trailing slash characters.

    Browser example:
        draw,deck,Player 1/

    Stored example:
        draw,deck,Player 1
    """
    return str(value or "").strip().strip("/").strip()


def split_history(turns):
    """
    Convert the slash-delimited Game.turns value into actions.

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
    Convert actions to the format stored in Game.turns.
    """
    if not actions:
        return ""

    return "/".join(actions) + "/"


def find_game(queryset, code):
    """
    Support both the current Game.code field and legacy Game.uid.
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
def claim_player_slot(game_id, player):
    with transaction.atomic():
        game = (
            Game.objects
            .select_for_update()
            .filter(id=game_id)
            .first()
        )

        if game is None:
            return False

        slots = game.players or 0
        slot = PLAYER_SLOTS[player]
        if slots & slot:
            return False
        game.players = slots | slot
        game.save(update_fields=["players"])

        return True


@database_sync_to_async
def release_player_slot(game_id, player):
    with transaction.atomic():
        game = (
            Game.objects
            .select_for_update()
            .filter(id=game_id)
            .first()
        )

        if game is None:
            return 0

        game.players = (game.players or 0) & ~PLAYER_SLOTS[player]
        game.save(update_fields=["players"])

        return game.players


@database_sync_to_async
def append_turn(game_id, action, player):
    """
    Append an action atomically and return the updated history.
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

        if (
            game is None
            or game.players != BOTH_PLAYERS
            or action.split(",")[-1] != player
        ):
            return None

        existing_actions = split_history(game.turns)

        action_parts = action.split(",")

        # Only the server may create an advance after both players are ready.
        if action_parts[0] == "round_advance":
            return None

        if action_parts[0] == "round_ready":
            completed_round = action_parts[1]
            ready_prefix = "round_ready," + completed_round + ","
            advance_prefix = "round_advance," + completed_round + ","
            previous_advance = next(
                (existing for existing in existing_actions
                 if existing.startswith(advance_prefix)),
                None,
            )

            if action in existing_actions:
                return {
                    "action": action,
                    "advance": previous_advance,
                    "history": existing_actions,
                    "duplicate": True,
                }

            if previous_advance or not any(
                existing.startswith("round_complete," + completed_round + ",")
                for existing in existing_actions
            ):
                return None

            existing_actions.append(action)
            ready_players = {
                existing.split(",")[2]
                for existing in existing_actions
                if existing.startswith(ready_prefix)
                and len(existing.split(",")) == 3
            }
            advance = None
            if {"Player 1", "Player 2"} <= ready_players:
                advance = "round_advance," + completed_round + "," + action_parts[2]
                existing_actions.append(advance)

            game.turn = advance or action
            game.turns = serialise_history(existing_actions)
            game.begun = True
            game.save(update_fields=["turn", "turns", "begun"])
            return {
                "action": action,
                "advance": advance,
                "history": existing_actions,
                "duplicate": False,
            }

        if existing_actions and existing_actions[-1] == action:
            return {
                "action": action,
                "history": existing_actions,
                "duplicate": True,
            }

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
            "history": existing_actions,
            "duplicate": False,
        }


@database_sync_to_async
def get_persisted_state(game_id):
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
        "players_connected": game.players == BOTH_PLAYERS,
    }


@database_sync_to_async
def save_scores(post_id, code, player1_score, player2_score):
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

        if game is None or game.players != BOTH_PLAYERS:
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
    Deliberately reset a brand-new game.

    Do not call this from connect().
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

    if action_type in {"round_complete", "round_ready", "round_advance"}:
        if len(parts) != 3:
            return False

        try:
            round_number = int(parts[1])
        except (TypeError, ValueError):
            return False

        return (
            3 <= round_number <= 13
            and (
                parts[2] in {"Player 1", "Player 2"}
                if action_type == "round_ready"
                else bool(parts[2])
            )
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

        query = parse_qs(
            self.scope.get("query_string", b"").decode("utf-8", errors="replace"),
            keep_blank_values=True,
        )
        players = query.get("player")
        if players is None:
            # Older clients identify the host by uid and the guest by code.
            players = [
                player for player, player_code in (
                    ("Player 1", game.uid),
                    ("Player 2", game.code),
                )
                if code == player_code
            ]
        if len(players) != 1 or players[0] not in PLAYER_SLOTS:
            await self.close(code=4000)
            return

        self.game_id = game.id
        self.post_id = post_id
        self.code = code
        self.group_name = f"game_{game.id}"
        self.player_counted = False
        self.player = players[0]

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        if not await claim_player_slot(self.game_id, self.player):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            self.group_name = None
            await self.close(code=4009)
            return
        self.player_counted = True

        state = await get_persisted_state(self.game_id)

        if state is None:
            await self.close(code=4004)
            return

        await self.send(
            text_data=json.dumps(state)
        )
        await self.broadcast_presence()

    async def disconnect(self, close_code):
        if (
            getattr(self, "player_counted", False)
            and getattr(self, "game_id", None) is not None
        ):
            await release_player_slot(self.game_id, self.player)
            self.player_counted = False
            await self.broadcast_presence()

        if getattr(self, "group_name", None):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

        self.player_counted = False

    async def receive(self, text_data):
        message = normalise_action(text_data)

        if not message:
            return

        if message == "x":
            state = await get_persisted_state(self.game_id)

            if state is None:
                await self.close(code=4004)
                return

            await self.send(
                text_data=json.dumps(state)
            )

            return

        if message == "y":
            game = await get_game_by_primary_key(self.game_id)

            latest_action = normalise_action(
                game.turn if game else ""
            )

            if latest_action:
                await self.send(
                    text_data=json.dumps({
                        "type": "game_action",
                        "action": latest_action,
                    })
                )

            return

        if message.startswith("<SCORE>,"):
            parts = message.split(",")

            if len(parts) == 4:
                if parts[1] == "Player 1" and self.player == "Player 1":
                    await save_scores(
                        self.post_id,
                        self.code,
                        parts[2],
                        parts[3],
                    )

                elif parts[1] == "Player 2" and self.player == "Player 2":
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
            self.player,
        )

        if result is None:
            state = await get_persisted_state(self.game_id)
            await self.send(text_data=json.dumps({
                "type": "game_action_error",
                "action": message,
                "state": state,
            }))
            return

        if result["duplicate"]:
            state = await get_persisted_state(self.game_id)
            await self.send(text_data=json.dumps(state))
            return

        actions = [result["action"]]
        if result.get("advance"):
            actions.append(result["advance"])

        for action in actions:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "game.action",
                    "action": action,
                    "sender": self.channel_name,
                },
            )
            await self.send(text_data=json.dumps({
                "type": "game_action",
                "action": action,
            }))

    async def broadcast_presence(self):
        await self.channel_layer.group_send(
            self.group_name, {"type": "game.presence"}
        )

    async def game_presence(self, event):
        state = await get_persisted_state(self.game_id)
        if state is not None:
            await self.send(text_data=json.dumps({
                "type": "game_presence",
                "players_connected": state["players_connected"],
            }))

    async def game_action(self, event):
        if event.get("sender") == self.channel_name:
            return

        action = normalise_action(
            event.get("action", "")
        )

        if not action:
            return

        await self.send(
            text_data=json.dumps({
                "type": "game_action",
                "action": action,
            })
        )
