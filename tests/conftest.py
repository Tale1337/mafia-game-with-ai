from game.core import Game
from game.models import Action, ActionType, GameStage, Player, PlayerType, Role, Team
from game.ui.null_presenter import NullPresenter


DEFAULT_ROLES = {
    Role.MAFIA: 2,
    Role.SHERIFF: 1,
    Role.DOCTOR: 1,
    Role.CITIZEN: 3,
}


class ScriptHumanInput:
    def __init__(
        self,
        speeches: list[str] | None = None,
        actions: list[str] | None = None,
    ):
        self.speeches = list(speeches or [])
        self.actions = list(actions or [])

    def get_speech(
        self,
        player: Player,
        day_number: int,
        stage: GameStage,
        *,
        speech_context: str | None = None,
    ) -> str:
        return self.speeches.pop(0)

    def get_action(
        self,
        game,
        player: Player,
        action_type: ActionType,
        day_number: int,
        stage: GameStage,
        *,
        task_key: str | None = None,
        allowed_targets: list[Player] | None = None,
        allow_abstain: bool = True,
    ) -> str:
        return self.actions.pop(0)


def make_game(roles: dict[Role, int] | None = None) -> Game:
    return Game(roles=roles or DEFAULT_ROLES, presenter=NullPresenter())


def add_player(
    game: Game,
    player_number: int,
    role: Role,
    *,
    player_type: PlayerType = PlayerType.AI,
    is_alive: bool = True,
) -> Player:
    player = Player(
        player_number=player_number,
        role=role,
        player_type=player_type,
        is_alive=is_alive,
    )
    game.players.append(player)
    return player


def add_vote(
    game: Game,
    voter: Player,
    target: Player | None,
    *,
    day_number: int | None = None,
    stage: GameStage = GameStage.DAY,
) -> Action:
    action = Action(
        action_type=ActionType.VOTE,
        stage=stage,
        day_number=day_number if day_number is not None else game.day_number,
        player=voter,
        target=target,
    )
    game.actions.append(action)
    return action
