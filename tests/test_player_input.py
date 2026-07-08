import pytest

from game.models import ActionType, PlayerType, Role
from tests.conftest import ScriptHumanInput, add_player, make_game


def test_get_player_action_parses_number_from_text():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 1})
    mafia = add_player(game, 1, Role.MAFIA, player_type=PlayerType.HUMAN)
    victim = add_player(game, 2, Role.CITIZEN)
    game.human_input = ScriptHumanInput(actions=["Игрок 2"])

    action = game.get_player_action(ActionType.KILL, mafia)

    assert action.target == victim


def test_get_player_action_rejects_mafia_killing_ally():
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 1})
    mafia = add_player(game, 1, Role.MAFIA, player_type=PlayerType.HUMAN)
    add_player(game, 2, Role.MAFIA)
    victim = add_player(game, 3, Role.CITIZEN)
    game.human_input = ScriptHumanInput(actions=["2", "3"])

    action = game.get_player_action(ActionType.KILL, mafia)

    assert action.target == victim


def test_get_player_action_rejects_self_vote():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 1})
    voter = add_player(game, 1, Role.CITIZEN, player_type=PlayerType.HUMAN)
    other = add_player(game, 2, Role.MAFIA)
    game.human_input = ScriptHumanInput(actions=["1", "2"])

    action = game.get_player_action(ActionType.VOTE, voter)

    assert action.target == other


def test_get_player_action_rejects_non_candidate_in_runoff():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 3})
    voter = add_player(game, 1, Role.CITIZEN, player_type=PlayerType.HUMAN)
    candidate = add_player(game, 2, Role.MAFIA)
    outsider = add_player(game, 3, Role.CITIZEN)
    game.human_input = ScriptHumanInput(actions=["3", "2"])

    action = game.get_player_action(
        ActionType.VOTE,
        voter,
        task_key="runoff_vote",
        allowed_targets=[candidate],
        allow_abstain=False,
    )

    assert action.target == candidate


def test_get_player_action_raises_after_max_attempts():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 1})
    mafia = add_player(game, 1, Role.MAFIA, player_type=PlayerType.HUMAN)
    add_player(game, 2, Role.CITIZEN)
    game.human_input = ScriptHumanInput(actions=["abc"] * 5)

    with pytest.raises(RuntimeError):
        game.get_player_action(ActionType.KILL, mafia)
