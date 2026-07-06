import enum


class Team(enum.StrEnum):
    MAFIA = "mafia"
    CITIZENS = "citizens"
    NEUTRAL = "neutral"


class PlayerType(enum.StrEnum):
    AI = "ai"
    HUMAN = "human"


class GameStage(enum.StrEnum):
    DAY = "day"
    NIGHT = "night"


class ActionType(enum.StrEnum):
    VOTE = "vote"
    KILL = "kill"
    SAVE = "save"
    ROLE_CHECK = "role_check"


class Role(enum.StrEnum):
    MAFIA = "mafia"
    CITIZEN = "citizen"
    DOCTOR = "doctor"
    SHERIFF = "sheriff"

    @property
    def team(self) -> Team:
        return {
            Role.MAFIA: Team.MAFIA,
            Role.CITIZEN: Team.CITIZENS,
            # Role.DOCTOR: Team.CITIZENS,
            # Role.SHERIFF: Team.CITIZENS,
        }[self]

    @property
    def action(self) -> ActionType | None:
        return {
            Role.MAFIA: ActionType.KILL,
            Role.CITIZEN: None,
            # Role.DOCTOR: ActionType.SAVE,
            # Role.SHERIFF: ActionType.ROLE_CHECK,
        }[self]