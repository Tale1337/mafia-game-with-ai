import enum
from pydantic import BaseModel

class Team(enum.StrEnum):
    MAFIA = "mafia"
    CITIZENS = "citizens"
    NEUTRAL = "neutral"

class Role(enum.StrEnum):
    MAFIA = "mafia"
    CITIZEN = "citizen"

    @property
    def team(self) -> Team:
        mapping = {
            Role.MAFIA: Team.MAFIA,
            Role.CITIZEN: Team.CITIZENS,
        }
        return mapping[self]


class PlayerType(enum.StrEnum):
    AI = "ai"
    HUMAN = "human"

class Player(BaseModel):
    role: Role
    player_type: PlayerType
    player_number: int
    is_alive: bool = True

class GameStage(enum.StrEnum):
    DAY = "day"
    NIGHT = "night"

