from game.models import ChannelType, Player, PlayerType, Role, Team
from game.ui.console_presenter import ConsolePresenter


def test_should_show_channel_message_for_mafia_chat():
    presenter = ConsolePresenter()
    human = Player(player_number=1, role=Role.MAFIA, player_type=PlayerType.HUMAN)

    assert presenter.should_show_channel_message(
        ChannelType.MAFIA_NIGHT,
        human,
        None,
    )


def test_should_hide_channel_message_for_citizen():
    presenter = ConsolePresenter()
    human = Player(player_number=1, role=Role.CITIZEN, player_type=PlayerType.HUMAN)

    assert not presenter.should_show_channel_message(
        ChannelType.MAFIA_NIGHT,
        human,
        None,
    )


def test_game_run_returns_winner(monkeypatch):
    class SilentPresenter(ConsolePresenter):
        def show_game_start(self, human):
            pass

        def show_day_start(self, day_number):
            pass

        def show_player_speech(self, player, text):
            pass

        def show_vote_start(self):
            pass

        def show_night_enter_prompt(self):
            pass

        def show_game_end(self, winner):
            pass

    from game.core import Game

    game = Game(
        roles={Role.MAFIA: 1, Role.CITIZEN: 3},
        presenter=SilentPresenter(),
    )
    calls = {"count": 0}

    def fake_change_stage():
        calls["count"] += 1
        if calls["count"] >= 1:
            game.is_active = False

    monkeypatch.setattr(game, "distribute_roles_and_types", lambda: None)
    monkeypatch.setattr(game, "process_day", lambda: None)
    monkeypatch.setattr(game, "change_stage", fake_change_stage)
    monkeypatch.setattr(game, "check_win_cons", lambda: Team.CITIZENS)

    winner = game.run()
    assert winner == Team.CITIZENS
