import enum
from pydantic import BaseModel

class Team(enum.StrEnum):
    MAFIA = "mafia"
    CITIZENS = "citizens"
    NEUTRAL = "neutral"


class PlayerType(enum.StrEnum):
    AI = "ai"
    HUMAN = "human"


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

    @property
    def action(self) -> ActionType:
        pass


class Player(BaseModel):
    role: Role
    player_type: PlayerType
    player_number: int
    is_alive: bool = True


class GameStage(enum.StrEnum):
    DAY = "day"
    NIGHT = "night"


# class ChannelType(enum.StrEnum):
#     DAY = "day"
#     MAFIA_NIGHT = "mafia_night"
#     NEUTRAL_NIGHT = "neutral_night"
#
#     def channel(self) -> Team:
#         mapping = {
#             ChannelType.DAY: Team.CITIZENS,
#             ChannelType.MAFIA_NIGHT: Team.MAFIA,
#             Role.CITIZEN: Team.CITIZENS,
#         }
#         return mapping[self]


class Message(BaseModel):
    # channel: ChannelType
    text: str
    player: Player
    stage: GameStage
    day_number: int


class ActionType(enum.StrEnum):
    VOTE = "vote"
    KILL = "kill"
    ROLE_CHECK = "role_check"


class Action(BaseModel):
    action_type: ActionType
    stage: GameStage
    day_number: int
    player: Player
    target: Player


class GameEvent(BaseModel):
    is_successful: bool = True
    action_type: ActionType
    stage: GameStage
    day_number: int
    target: Player