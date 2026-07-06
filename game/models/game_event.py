from pydantic import BaseModel

from .player import Player
from .enums import ActionType, GameStage


class GameEvent(BaseModel):
    action_type: ActionType
    target: Player
    stage: GameStage
    day_number: int
    is_successful: bool = True

    def __str__(self) -> str:
        status = "SUCCESS" if self.is_successful else "FAILED"

        return (
            f"[{status}] "
            f"{self.action_type.value} "
            f"{self.target}"
        )