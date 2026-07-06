from pydantic import BaseModel

from .enums import PlayerType, Role


class Player(BaseModel):
    player_number: int
    role: Role
    player_type: PlayerType
    is_alive: bool = True

    @property
    def is_ai(self) -> bool:
        return self.player_type == PlayerType.AI

    @property
    def is_human(self) -> bool:
        return self.player_type == PlayerType.HUMAN

    def __str__(self) -> str:
        return f"Игрок {self.player_number}"