from pydantic import BaseModel

from .player import Player
from .enums import ActionType, GameStage


class Action(BaseModel):
    action_type: ActionType
    player: Player
    target: Player
    stage: GameStage
    day_number: int

    def __str__(self) -> str:
        return (
            f"{self.player} -> "
            f"{self.action_type.value} -> "
            f"{self.target}"
        )
