import pytest

from game.allies import (
    assign_mafia_allies,
    get_mafia_allies,
    get_sheriff_confirmed_peaceful,
    get_valid_action_targets,
)
from game.models import ActionType, ChannelType, GameStage, Message, Role
from tests.conftest import add_player, make_game


def test_assign_mafia_allies_sets_numbers_at_start():
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 2})
    mafia_1 = add_player(game, 1, Role.MAFIA)
    mafia_2 = add_player(game, 2, Role.MAFIA)
    add_player(game, 3, Role.CITIZEN)

    assign_mafia_allies(game.players)

    assert mafia_1.mafia_ally_numbers == [2]
    assert mafia_2.mafia_ally_numbers == [1]


def test_get_mafia_allies_lists_alive_allies_from_stored_numbers():
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 2})
    mafia_1 = add_player(game, 1, Role.MAFIA)
    mafia_2 = add_player(game, 2, Role.MAFIA)
    add_player(game, 3, Role.CITIZEN)
    assign_mafia_allies(game.players)

    allies = get_mafia_allies(game, mafia_1)
    assert allies == [mafia_2]


def test_get_sheriff_confirmed_peaceful_reads_private_messages():
    game = make_game({Role.MAFIA: 1, Role.SHERIFF: 1, Role.CITIZEN: 2})
    sheriff = add_player(game, 1, Role.SHERIFF)
    peaceful = add_player(game, 2, Role.CITIZEN)
    game.messages.append(
        Message(
            channel=ChannelType.PRIVATE,
            text=f"Результат проверки: Игрок {peaceful.player_number} — Мирный житель.",
            player=None,
            recipient=sheriff,
            stage=GameStage.NIGHT,
            day_number=1,
        )
    )

    assert get_sheriff_confirmed_peaceful(game, sheriff) == [peaceful]


def test_get_valid_action_targets_excludes_self_for_vote():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 3})
    voter = add_player(game, 1, Role.CITIZEN)
    other = add_player(game, 2, Role.CITIZEN)
    add_player(game, 3, Role.MAFIA)

    targets = get_valid_action_targets(game, voter, ActionType.VOTE)

    assert voter not in targets
    assert other in targets


def test_get_valid_action_targets_excludes_self_in_runoff_vote():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 3})
    candidate_1 = add_player(game, 1, Role.CITIZEN)
    candidate_2 = add_player(game, 2, Role.MAFIA)

    targets = get_valid_action_targets(
        game,
        candidate_1,
        ActionType.VOTE,
        allowed_targets=[candidate_1, candidate_2],
    )

    assert targets == [candidate_2]


def test_get_valid_action_targets_excludes_sheriff_self_for_role_check():
    game = make_game({Role.MAFIA: 1, Role.SHERIFF: 1, Role.CITIZEN: 2})
    sheriff = add_player(game, 1, Role.SHERIFF)
    mafia = add_player(game, 2, Role.MAFIA)
    citizen = add_player(game, 3, Role.CITIZEN)

    targets = get_valid_action_targets(game, sheriff, ActionType.ROLE_CHECK)

    assert targets == [mafia, citizen]
    assert sheriff not in targets


def test_get_valid_action_targets_excludes_mafia_allies_for_kill():
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 2})
    mafia_1 = add_player(game, 1, Role.MAFIA)
    mafia_2 = add_player(game, 2, Role.MAFIA)
    citizen_1 = add_player(game, 3, Role.CITIZEN)
    citizen_2 = add_player(game, 4, Role.CITIZEN)
    assign_mafia_allies(game.players)

    targets = get_valid_action_targets(game, mafia_1, ActionType.KILL)

    assert targets == [citizen_1, citizen_2]
    assert mafia_1 not in targets
    assert mafia_2 not in targets
