import re

from .models import ActionType, ChannelType, Player, Role, Team

_PEACEFUL_CHECK_RE = re.compile(
    r"Игрок (\d+) — Мирный житель",
)


def assign_mafia_allies(players: list[Player]) -> None:
    mafia_players = [player for player in players if player.role == Role.MAFIA]
    for player in mafia_players:
        player.mafia_ally_numbers = [
            other.player_number
            for other in mafia_players
            if other.player_number != player.player_number
        ]


def get_mafia_allies(game, player: Player) -> list[Player]:
    if not player.mafia_ally_numbers:
        return []
    ally_numbers = set(player.mafia_ally_numbers)
    return [
        other
        for other in game.alive_players
        if other.player_number in ally_numbers
    ]


def is_mafia_ally(actor: Player, target: Player) -> bool:
    return target.player_number in actor.mafia_ally_numbers


def get_sheriff_confirmed_peaceful(game, sheriff: Player) -> list[Player]:
    if sheriff.role != Role.SHERIFF:
        return []

    confirmed_numbers: set[int] = set()
    for message in game.messages:
        if message.channel != ChannelType.PRIVATE or message.recipient != sheriff:
            continue
        match = _PEACEFUL_CHECK_RE.search(message.text)
        if match:
            confirmed_numbers.add(int(match.group(1)))

    players = []
    for player in game.players:
        if player.player_number in confirmed_numbers and player.is_alive:
            players.append(player)
    return players


def get_valid_action_targets(
    game,
    actor: Player,
    action_type,
    *,
    allowed_targets: list[Player] | None = None,
) -> list[Player]:
    if allowed_targets is not None:
        targets = list(allowed_targets)
    else:
        targets = list(game.alive_players)

    if action_type == ActionType.VOTE:
        targets = [
            player
            for player in targets
            if player.player_number != actor.player_number
        ]
    elif actor.role.team == Team.MAFIA and action_type == ActionType.KILL:
        targets = [
            player
            for player in targets
            if player.player_number != actor.player_number
            and not is_mafia_ally(actor, player)
        ]
    elif actor.role == Role.SHERIFF and action_type == ActionType.ROLE_CHECK:
        targets = [
            player
            for player in targets
            if player.player_number != actor.player_number
        ]
    return targets
