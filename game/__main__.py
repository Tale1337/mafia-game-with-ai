from .core import Game
from .logging import FileGameLogger
from .models import Role
from .ui.console_presenter import ConsolePresenter


if __name__ == "__main__":
    game = Game(
        roles={
            Role.MAFIA: 2,
            Role.SHERIFF: 1,
            Role.DOCTOR: 1,
            Role.CITIZEN: 3,
        },
        presenter=ConsolePresenter(),
        logger=FileGameLogger(),
    )

    winner = game.run()
    if winner is not None:
        game.presenter.show_game_end(winner)
