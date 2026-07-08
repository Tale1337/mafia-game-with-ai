import pytest

from game.models import ActionType, ChannelType, Message, Player, PlayerType, Role, Team
from game.models import GameStage
from game.validation import validate_action_target, validate_roles_config
from tests.conftest import add_player, make_game


def test_validate_roles_config_requires_minimum_players():
    with pytest.raises(ValueError, match="минимум 4"):
        validate_roles_config({Role.MAFIA: 1, Role.CITIZEN: 1})


def test_validate_roles_config_requires_mafia():
    with pytest.raises(ValueError, match="хотя бы одна мафия"):
        validate_roles_config({Role.CITIZEN: 4, Role.SHERIFF: 1})


def test_validate_roles_config_requires_more_citizens_than_mafia():
    with pytest.raises(ValueError, match="больше"):
        validate_roles_config({Role.MAFIA: 2, Role.CITIZEN: 2})


def test_validate_roles_config_accepts_valid_setup():
    validate_roles_config(
        {
            Role.MAFIA: 2,
            Role.SHERIFF: 1,
            Role.DOCTOR: 1,
            Role.CITIZEN: 3,
        }
    )


def test_validate_action_target_allows_vote_abstain():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 3})
    actor = Player(player_number=1, role=Role.CITIZEN, player_type=PlayerType.AI)
    assert validate_action_target(game, actor, None, ActionType.VOTE) is None


def test_validate_action_target_rejects_dead_target():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 3})
    actor = Player(player_number=1, role=Role.MAFIA, player_type=PlayerType.AI)
    target = Player(
        player_number=2,
        role=Role.CITIZEN,
        player_type=PlayerType.AI,
        is_alive=False,
    )
    assert validate_action_target(game, actor, target, ActionType.KILL) == "игрок уже мёртв"


def test_validate_action_target_allows_mafia_voting_ally():
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 2})
    actor = add_player(game, 1, Role.MAFIA)
    target = add_player(game, 2, Role.MAFIA)
    assert validate_action_target(game, actor, target, ActionType.VOTE) is None


def test_validate_action_target_rejects_mafia_killing_ally():
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 2})
    actor = add_player(game, 1, Role.MAFIA)
    target = add_player(game, 2, Role.MAFIA)
    assert (
        validate_action_target(game, actor, target, ActionType.KILL)
        == "мафия может убивать только мирных жителей"
    )


def test_validate_action_target_rejects_mafia_killing_self():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 3})
    actor = add_player(game, 1, Role.MAFIA)
    assert (
        validate_action_target(game, actor, actor, ActionType.KILL)
        == "мафия может убивать только мирных жителей"
    )


def test_validate_action_target_allows_runoff_candidate_only():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 3})
    voter = add_player(game, 1, Role.CITIZEN)
    candidate = add_player(game, 2, Role.MAFIA)
    outsider = add_player(game, 3, Role.CITIZEN)

    assert (
        validate_action_target(
            game,
            voter,
            outsider,
            ActionType.VOTE,
            allowed_targets=[candidate],
        )
        == "можно голосовать только за кандидатов: 2"
    )
    assert (
        validate_action_target(
            game,
            voter,
            candidate,
            ActionType.VOTE,
            allowed_targets=[candidate],
        )
        is None
    )


def test_validate_action_target_rejects_self_vote():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 3})
    voter = add_player(game, 1, Role.CITIZEN)

    assert (
        validate_action_target(game, voter, voter, ActionType.VOTE)
        == "нельзя голосовать за себя"
    )


def test_validate_action_target_rejects_sheriff_checking_self():
    game = make_game({Role.MAFIA: 1, Role.SHERIFF: 1, Role.CITIZEN: 2})
    sheriff = add_player(game, 1, Role.SHERIFF)

    assert (
        validate_action_target(game, sheriff, sheriff, ActionType.ROLE_CHECK)
        == "шериф не может проверять себя"
    )


def test_validate_action_target_allows_sheriff_voting_confirmed_peaceful():
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
    assert validate_action_target(game, sheriff, peaceful, ActionType.VOTE) is None
