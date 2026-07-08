from game.models import Action, ActionType, ChannelType, GameEvent, GameStage, Player, PlayerType, Role, Team
from game.ui.null_presenter import NullPresenter
from tests.conftest import ScriptHumanInput, add_player, add_vote, make_game


class RecordingPresenter(NullPresenter):
    def __init__(self):
        self.sheriff_checks: list[str] = []

    def show_sheriff_check(self, result_text: str) -> None:
        self.sheriff_checks.append(result_text)


def test_human_sheriff_sees_check_result_immediately_after_night_choice():
    game = make_game({Role.MAFIA: 1, Role.SHERIFF: 1, Role.CITIZEN: 2})
    sheriff = add_player(game, 1, Role.SHERIFF, player_type=PlayerType.HUMAN)
    mafia = add_player(game, 2, Role.MAFIA)
    add_player(game, 3, Role.CITIZEN)
    add_player(game, 4, Role.CITIZEN)
    game.stage = GameStage.NIGHT
    game.human_input = ScriptHumanInput(actions=["2"])
    presenter = RecordingPresenter()
    game.presenter = presenter

    game._process_night_channel(f"private_{sheriff.player_number}", [sheriff])

    assert presenter.sheriff_checks == [
        "Результат проверки: Игрок 2 — Мафия."
    ]
    assert any(
        message.recipient == sheriff
        and message.channel == ChannelType.PRIVATE
        and "Игрок 2 — Мафия" in message.text
        for message in game.messages
    )
    assert game.current_actions[0].target == mafia


def test_check_win_citizens_when_no_mafia_alive():
    game = make_game()
    add_player(game, 1, Role.MAFIA, is_alive=False)
    add_player(game, 2, Role.CITIZEN)
    add_player(game, 3, Role.SHERIFF)

    assert game.check_win_cons() == Team.CITIZENS


def test_check_win_mafia_when_equal_or_greater():
    game = make_game()
    add_player(game, 1, Role.MAFIA)
    add_player(game, 2, Role.CITIZEN)
    add_player(game, 3, Role.SHERIFF, is_alive=False)

    assert game.check_win_cons() == Team.MAFIA


def test_check_win_none_while_game_continues():
    game = make_game()
    add_player(game, 1, Role.MAFIA)
    add_player(game, 2, Role.CITIZEN)
    add_player(game, 3, Role.SHERIFF)

    assert game.check_win_cons() is None


def test_resolve_day_vote_abstain_wins_over_single_candidate():
    game = make_game()
    voter_1 = add_player(game, 1, Role.CITIZEN)
    voter_2 = add_player(game, 2, Role.CITIZEN)
    voter_3 = add_player(game, 3, Role.CITIZEN)
    suspect = add_player(game, 4, Role.MAFIA)

    add_vote(game, voter_1, None)
    add_vote(game, voter_2, None)
    add_vote(game, voter_3, suspect)

    game.resolve_day_vote()

    assert game.current_game_events == []


def test_resolve_day_vote_lynches_top_candidate():
    game = make_game()
    voter_1 = add_player(game, 1, Role.CITIZEN)
    voter_2 = add_player(game, 2, Role.CITIZEN)
    suspect = add_player(game, 3, Role.MAFIA)
    other = add_player(game, 4, Role.CITIZEN)

    add_vote(game, voter_1, suspect)
    add_vote(game, voter_2, suspect)
    add_vote(game, suspect, other)

    game.resolve_day_vote()

    assert len(game.current_game_events) == 1
    assert game.current_game_events[0].target == suspect


def test_resolve_day_vote_starts_runoff_on_tie(monkeypatch):
    game = make_game()
    voter_1 = add_player(game, 1, Role.CITIZEN)
    voter_2 = add_player(game, 2, Role.CITIZEN)
    suspect_1 = add_player(game, 3, Role.MAFIA)
    suspect_2 = add_player(game, 4, Role.CITIZEN)

    add_vote(game, voter_1, suspect_1)
    add_vote(game, voter_2, suspect_2)
    add_vote(game, suspect_1, suspect_2)
    add_vote(game, suspect_2, suspect_1)

    runoff_called: list[list[Player]] = []
    monkeypatch.setattr(
        game,
        "_run_runoff",
        lambda candidates: runoff_called.append(candidates),
    )

    game.resolve_day_vote()

    assert len(runoff_called) == 1
    assert {player.player_number for player in runoff_called[0]} == {3, 4}
    assert game.current_game_events == []


def test_resolve_runoff_actions_picks_single_winner():
    game = make_game()
    candidate_1 = add_player(game, 2, Role.MAFIA)
    candidate_2 = add_player(game, 3, Role.CITIZEN)
    voter_1 = add_player(game, 1, Role.CITIZEN)
    voter_2 = add_player(game, 4, Role.CITIZEN)

    actions = [
        Action(
            action_type=ActionType.VOTE,
            stage=GameStage.DAY,
            day_number=1,
            player=voter_1,
            target=candidate_1,
        ),
        Action(
            action_type=ActionType.VOTE,
            stage=GameStage.DAY,
            day_number=1,
            player=voter_2,
            target=candidate_1,
        ),
        Action(
            action_type=ActionType.VOTE,
            stage=GameStage.DAY,
            day_number=1,
            player=candidate_1,
            target=candidate_2,
        ),
        Action(
            action_type=ActionType.VOTE,
            stage=GameStage.DAY,
            day_number=1,
            player=candidate_2,
            target=candidate_1,
        ),
    ]

    winners = game._resolve_runoff_actions(actions)

    assert winners == [candidate_1]


def test_resolve_runoff_actions_lynches_both_on_tie():
    game = make_game()
    candidate_1 = add_player(game, 2, Role.MAFIA)
    candidate_2 = add_player(game, 3, Role.CITIZEN)
    voter_1 = add_player(game, 1, Role.CITIZEN)
    voter_2 = add_player(game, 4, Role.CITIZEN)

    actions = [
        Action(
            action_type=ActionType.VOTE,
            stage=GameStage.DAY,
            day_number=1,
            player=voter_1,
            target=candidate_1,
        ),
        Action(
            action_type=ActionType.VOTE,
            stage=GameStage.DAY,
            day_number=1,
            player=voter_2,
            target=candidate_2,
        ),
        Action(
            action_type=ActionType.VOTE,
            stage=GameStage.DAY,
            day_number=1,
            player=candidate_1,
            target=candidate_2,
        ),
        Action(
            action_type=ActionType.VOTE,
            stage=GameStage.DAY,
            day_number=1,
            player=candidate_2,
            target=candidate_1,
        ),
    ]

    winners = game._resolve_runoff_actions(actions)

    assert {player.player_number for player in winners} == {2, 3}


def test_resolve_night_actions_mafia_tie_kills_nobody():
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 2})
    game.stage = GameStage.NIGHT
    mafia_1 = add_player(game, 1, Role.MAFIA)
    mafia_2 = add_player(game, 2, Role.MAFIA)
    citizen_1 = add_player(game, 3, Role.CITIZEN)
    citizen_2 = add_player(game, 4, Role.CITIZEN)

    game.actions.extend(
        [
            Action(
                action_type=ActionType.KILL,
                stage=GameStage.NIGHT,
                day_number=1,
                player=mafia_1,
                target=citizen_1,
            ),
            Action(
                action_type=ActionType.KILL,
                stage=GameStage.NIGHT,
                day_number=1,
                player=mafia_2,
                target=citizen_2,
            ),
        ]
    )

    game.resolve_night_actions()

    assert game.current_game_events == []


def test_resolve_night_actions_doctor_heals_kill_target():
    game = make_game({Role.MAFIA: 1, Role.DOCTOR: 1, Role.CITIZEN: 2})
    game.stage = GameStage.NIGHT
    mafia = add_player(game, 1, Role.MAFIA)
    doctor = add_player(game, 2, Role.DOCTOR)
    victim = add_player(game, 3, Role.CITIZEN)
    add_player(game, 4, Role.CITIZEN)

    game.actions.extend(
        [
            Action(
                action_type=ActionType.KILL,
                stage=GameStage.NIGHT,
                day_number=1,
                player=mafia,
                target=victim,
            ),
            Action(
                action_type=ActionType.HEAL,
                stage=GameStage.NIGHT,
                day_number=1,
                player=doctor,
                target=victim,
            ),
        ]
    )

    game.resolve_night_actions()
    game.execute_game_events()

    assert victim.is_alive


def test_execute_game_events_records_morning_death_on_next_day():
    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 1})
    game.stage = GameStage.NIGHT
    victim = add_player(game, 2, Role.CITIZEN)
    game.game_events.append(
        GameEvent(
            action_type=ActionType.KILL,
            stage=GameStage.NIGHT,
            day_number=1,
            target=victim,
        )
    )

    game.execute_game_events()

    assert victim.is_alive is False
    morning_message = game.messages[-1]
    assert morning_message.stage == GameStage.DAY
    assert morning_message.day_number == 2


def test_collect_mafia_kill_votes_requires_unanimous_choice(monkeypatch):
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 2})
    game.stage = GameStage.NIGHT
    mafia_1 = add_player(game, 1, Role.MAFIA)
    mafia_2 = add_player(game, 2, Role.MAFIA)
    add_player(game, 3, Role.CITIZEN)
    add_player(game, 4, Role.CITIZEN)
    responses = iter(["3", "4"])

    def fake_ai_answer(**kwargs):
        from game.logging import AIResponse

        return AIResponse(content=next(responses))

    monkeypatch.setattr("game.core.get_ai_answer", fake_ai_answer)

    result = game._collect_mafia_kill_votes([mafia_1, mafia_2])

    assert result is None


def test_collect_mafia_kill_votes_accepts_unanimous_choice(monkeypatch):
    game = make_game({Role.MAFIA: 2, Role.CITIZEN: 2})
    game.stage = GameStage.NIGHT
    mafia_1 = add_player(game, 1, Role.MAFIA)
    mafia_2 = add_player(game, 2, Role.MAFIA)
    victim = add_player(game, 3, Role.CITIZEN)
    add_player(game, 4, Role.CITIZEN)
    from game.logging import AIResponse

    monkeypatch.setattr(
        "game.core.get_ai_answer",
        lambda **kwargs: AIResponse(content="3"),
    )

    result = game._collect_mafia_kill_votes([mafia_1, mafia_2])

    assert result is not None
    assert all(action.target == victim for action in result)


def test_distribute_roles_and_types_assigns_exactly_one_human(monkeypatch):
    from game.models import PlayerType

    monkeypatch.setattr("game.core.random.randint", lambda _a, _b: 1)
    monkeypatch.setattr("game.core.random.shuffle", lambda _items: None)

    game = make_game({Role.MAFIA: 1, Role.CITIZEN: 3})
    game.distribute_roles_and_types()

    humans = [player for player in game.players if player.player_type == PlayerType.HUMAN]
    assert len(humans) == 1
    assert humans[0].player_number == 1

    mafia_players = [player for player in game.players if player.role == Role.MAFIA]
    for mafia in mafia_players:
        expected = [
            other.player_number
            for other in mafia_players
            if other.player_number != mafia.player_number
        ]
        assert mafia.mafia_ally_numbers == expected
