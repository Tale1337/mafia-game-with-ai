from pydantic import BaseModel

from .player import Player
from .enums import GameStage


class Message(BaseModel):
    text: str
    player: Player
    stage: GameStage
    day_number: int

    def __str__(self) -> str:
        return f"[{self.stage} {self.day_number}] Игрок {self.player.player_number}: {self.text}"