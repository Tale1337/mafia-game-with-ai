from pathlib import Path

from ..models import Player, Team, GameStage, ActionType
from .tasks import TASKS
from .templates import USER_PROMPT


SYSTEM_PROMPTS_DIR = Path(__file__).parent / "system"


class PromptBuilder:
    @staticmethod
    def get_system_prompt(player: Player) -> str:
        path = SYSTEM_PROMPTS_DIR / f"{player.role.value}.txt"
        return path.read_text(encoding="utf-8")

    @staticmethod
    def get_user_prompt(game, player: Player, action_type: ActionType | None = None) -> str:
        return USER_PROMPT.format(
            day=game.day_number,
            stage=game.stage.value,
            alive_players=PromptBuilder._alive_players(game),
            history=PromptBuilder._history(game, player),
            private_information=PromptBuilder._private_information(game, player),
            task=PromptBuilder._task(action_type),
        )

    @staticmethod
    def _alive_players(game) -> str:
        return "\n".join(
            f"- Игрок {player.player_number}"
            for player in game.alive_player
        )

    @staticmethod
    def _history(game, player: Player) -> str:
        if player.role.team == Team.CITIZENS:
            messages = [
                message
                for message in game.messages
                if message.stage == GameStage.DAY
            ]
        else:
            messages = game.messages

        if not messages:
            return "История пока отсутствует."

        return "\n".join(
            f"[День {message.day_number}] Игрок {message.player.player_number}: {message.text}"
            for message in messages
        )

    @staticmethod
    def _private_information(game, player: Player) -> str:
        if player.role.team != Team.MAFIA:
            return ""

        mafia_members = [
            f"Игрок {other.player_number}"
            for other in game.alive_player
            if other.role.team == Team.MAFIA and other != player
        ]

        if mafia_members:
            return (
                "Твои союзники:\n"
                + "\n".join(f"- {member}" for member in mafia_members)
            )

        return "Ты единственный оставшийся мафиози."

    @staticmethod
    def _task(action_type: ActionType | None) -> str:
        return TASKS.get(action_type, TASKS[None])