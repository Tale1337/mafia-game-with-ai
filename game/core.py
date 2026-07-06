import random
from pydantic import BaseModel, Field
from .models import GameStage, Role, Player, PlayerType, Team


class Game (BaseModel):
    stage: GameStage = GameStage.NIGHT
    day_number: int = 0
    roles: dict[Role, int]
    mafia_chat: list[str] = Field(default_factory=list)
    day_chat: list[str] = Field(default_factory=list)
    players: list[Player] = Field(default_factory=list)
    is_active: bool = True

    def distribute_roles_and_types(self) -> None:
        if self.players or not self.roles:
            return
        roles_list = []
        for role, count in self.roles.items():
            for _ in range(count):
                roles_list.append(role)

        human_player_number = random.randint(1, len(roles_list))
        random.shuffle(roles_list)
        for i, role in enumerate(roles_list):
            player_type = PlayerType.HUMAN if i+1==human_player_number else PlayerType.AI
            player = Player(player_number=i+1, role=role, player_type=player_type)
            self.players.append(player)

    def change_stage(self) -> None:
        if self.check_win_cons():
            self.is_active = False
            return

        if self.stage == GameStage.NIGHT:
            self.stage = GameStage.DAY
            self.day_number += 1
        else:
            self.stage = GameStage.NIGHT

    def check_win_cons(self):
        teams = {team: 0 for team in Team}
        alive_players = [player for player in self.players if player.is_alive]
        for player in alive_players:
            teams[player.role.team] += 1

        if not teams[Team.MAFIA] and not teams[Team.NEUTRAL]:
            return Team.CITIZENS
        elif teams[Team.MAFIA] >= teams[Team.CITIZENS] and not teams[Team.NEUTRAL]:
            return Team.MAFIA
        elif teams[Team.NEUTRAL] >= teams[Team.CITIZENS] and not teams[Team.MAFIA]:
            return Team.NEUTRAL
        else:
            return None

    def process_day(self):
        # for p in self.players:
        pass

    def process_night(self):
        pass