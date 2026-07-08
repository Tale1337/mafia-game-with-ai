from pathlib import Path

from ..allies import get_sheriff_confirmed_peaceful
from ..vote_format import format_votes_so_far
from ..models import ActionType, ChannelType, Player, Role, Team
from .tasks import TASKS
from .templates import USER_PROMPT

SYSTEM_PROMPTS_DIR = Path(__file__).parent / "system"

ROLE_LABELS = {
    Role.MAFIA: "мафия",
    Role.CITIZEN: "мирный житель",
    Role.SHERIFF: "шериф",
    Role.DOCTOR: "доктор",
}


class PromptBuilder:
    @staticmethod
    def get_system_prompt(player: Player) -> str:
        path = SYSTEM_PROMPTS_DIR / f"{player.role.value}.txt"
        return path.read_text(encoding="utf-8")

    @staticmethod
    def get_user_prompt(
        game,
        player: Player,
        action_type: ActionType | None = None,
        *,
        channel: ChannelType | None = None,
        speech_context: str | None = None,
        task_key: str | None = None,
        allowed_targets: list[Player] | None = None,
        votes_so_far: list | None = None,
    ) -> str:
        private_information = PromptBuilder._private_information(game, player)
        if private_information:
            private_information = private_information + "\n"
        return USER_PROMPT.format(
            player_identity=PromptBuilder._player_identity(player),
            day=game.day_number,
            stage=game.stage.value,
            alive_players=PromptBuilder._alive_players(
                game,
                allowed_targets=allowed_targets,
            ),
            history=PromptBuilder._history(game, player),
            current_votes_section=PromptBuilder._current_votes_section(
                votes_so_far,
            ),
            private_information=private_information,
            task=PromptBuilder._task(
                action_type,
                channel=channel,
                speech_context=speech_context,
                task_key=task_key,
                allowed_targets=allowed_targets,
            ),
        )

    @staticmethod
    def _player_identity(player: Player) -> str:
        lines = [
            f"Ты — игрок {player.player_number}.",
            f"Твоя роль — {ROLE_LABELS[player.role]}.",
        ]
        if player.role == Role.MAFIA:
            if player.mafia_ally_numbers:
                if len(player.mafia_ally_numbers) == 1:
                    lines.append(
                        f"Твой союзник-мафиози — игрок {player.mafia_ally_numbers[0]}."
                    )
                else:
                    allies = ", ".join(
                        f"игрок {number}"
                        for number in sorted(player.mafia_ally_numbers)
                    )
                    lines.append(f"Твои союзники-мафиози — {allies}.")
            else:
                lines.append("Ты единственный мафиози в игре.")
        elif player.role.team == Team.CITIZENS:
            lines.append("Ты на стороне мирных жителей.")
        return "\n".join(lines)

    @staticmethod
    def _current_votes_section(votes_so_far: list | None) -> str:
        if not votes_so_far:
            return ""
        return (
            "Текущее голосование (уже проголосовали):\n"
            f"{format_votes_so_far(votes_so_far)}\n\n"
        )

    @staticmethod
    def _alive_players(
        game,
        *,
        allowed_targets: list[Player] | None = None,
    ) -> str:
        players = (
            allowed_targets
            if allowed_targets is not None
            else game.alive_players
        )
        return "\n".join(
            f"- Игрок {player.player_number}"
            for player in players
        )

    @staticmethod
    def _history(game, player: Player) -> str:
        visible_messages = []

        for message in game.messages:
            if message.channel == ChannelType.PRIVATE and message.recipient == player:
                visible_messages.append(message)
            elif (
                message.channel != ChannelType.PRIVATE
                and message.channel in player.role.channels
            ):
                visible_messages.append(message)

        if not visible_messages:
            return "История пока отсутствует."

        return "\n".join(
            f"[{message.stage.value.upper()} {message.day_number}] "
            f"{'Система' if message.player is None else f'Игрок {message.player.player_number}'}: {message.text}"
            for message in visible_messages
        )

    @staticmethod
    def _private_information(game, player: Player) -> str:
        parts: list[str] = []

        if player.role == Role.MAFIA:
            parts.append(
                "Ночью убивай только мирных жителей. "
                "Нельзя убивать себя и союзников-мафиози."
            )

        if player.role == Role.SHERIFF:
            confirmed_peaceful = get_sheriff_confirmed_peaceful(game, player)
            if confirmed_peaceful:
                parts.append(
                    "Проверенные мирные жители:\n"
                    + "\n".join(
                        f"- Игрок {peaceful.player_number}"
                        for peaceful in confirmed_peaceful
                    )
                )

        return "\n\n".join(parts)

    @staticmethod
    def _task(
        action_type: ActionType | None,
        *,
        channel: ChannelType | None = None,
        speech_context: str | None = None,
        task_key: str | None = None,
        allowed_targets: list[Player] | None = None,
    ) -> str:
        if task_key == "runoff_vote" and allowed_targets is not None:
            numbers = ", ".join(
                str(candidate.player_number) for candidate in allowed_targets
            )
            return (
                TASKS[task_key].strip()
                + f"\n\nДопустимые кандидаты: {numbers}."
            )
        if task_key is not None:
            return TASKS[task_key]
        if speech_context is not None:
            return TASKS[speech_context]
        if action_type is not None:
            return TASKS[action_type]
        return TASKS[None]
