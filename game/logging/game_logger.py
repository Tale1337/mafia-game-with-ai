from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import Action, GameStage, Message, Player, Team

_LOGS_DIR = Path("logs")
_SEPARATOR = "=" * 72


@dataclass(frozen=True)
class AIResponse:
    content: str
    reasoning: str | None = None


class _LogWriter:
    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, section: str, body: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n{_SEPARATOR}\n")
            handle.write(f"[{timestamp}] {section}\n")
            handle.write(f"{_SEPARATOR}\n")
            handle.write(body.rstrip())
            handle.write("\n")


class NullGameLogger:
    @property
    def log_file(self) -> Path | None:
        return None

    @property
    def session_dir(self) -> Path | None:
        return None

    @property
    def players_log_dir(self) -> Path | None:
        return None

    def announce(self) -> None:
        pass

    def log(self, section: str, body: str) -> None:
        pass

    def log_game_setup(self, players: list[Player], human: Player | None) -> None:
        pass

    def log_stage(self, stage: GameStage, day_number: int) -> None:
        pass

    def log_ai_request(
        self,
        player: Player,
        *,
        system_prompt: str,
        user_prompt: str,
        action_type: str | None = None,
        channel: str | None = None,
        speech_context: str | None = None,
        task_key: str | None = None,
    ) -> None:
        pass

    def log_ai_response(
        self,
        player: Player,
        response: str,
        *,
        reasoning: str | None = None,
    ) -> None:
        pass

    def log_ai_error(self, player: Player, error: str) -> None:
        pass

    def log_human_input(
        self,
        player: Player,
        content: str,
        *,
        action_type: str | None = None,
        speech_context: str | None = None,
    ) -> None:
        pass

    def log_message(self, message: Message) -> None:
        pass

    def log_action(self, action: Action, *, raw_input: str | None = None) -> None:
        pass

    def log_action_retry(
        self,
        player: Player,
        reason: str,
        *,
        raw_input: str | None = None,
        action_type: str | None = None,
    ) -> None:
        pass

    def log_vote_results(self, actions: list[Action], *, title: str) -> None:
        pass

    def log_text(self, section: str, text: str) -> None:
        pass

    def log_game_end(self, winner: Team | None) -> None:
        pass


class FileGameLogger(NullGameLogger):
    def __init__(self, log_dir: Path | str = _LOGS_DIR) -> None:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._session_dir = Path(log_dir) / f"session_{session_id}"
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._players_log_dir = self._session_dir / "players"
        self._players_log_dir.mkdir()
        self._main = _LogWriter(self._session_dir / "game.log")
        self._player_writers: dict[int, _LogWriter] = {}
        self._log_main(
            "СЕССИЯ",
            f"Главный лог: {self.log_file.resolve()}\n"
            f"Логи игроков: {self.players_log_dir.resolve()}",
        )

    @property
    def log_file(self) -> Path:
        return self._main.path

    @property
    def session_dir(self) -> Path:
        return self._session_dir

    @property
    def players_log_dir(self) -> Path:
        return self._players_log_dir

    def announce(self) -> None:
        print(f"\n📝 Главный лог игры: {self.log_file.resolve()}")
        print(f"🤖 Логи игроков (промпты и ответы ИИ): {self.players_log_dir.resolve()}\n")

    def _log_main(self, section: str, body: str) -> None:
        self._main.write(section, body)

    def _player_writer(self, player: Player) -> _LogWriter:
        if player.player_number not in self._player_writers:
            filename = (
                f"player_{player.player_number:02d}_"
                f"{player.role.value}_{player.player_type.value}.log"
            )
            self._player_writers[player.player_number] = _LogWriter(
                self._players_log_dir / filename
            )
        return self._player_writers[player.player_number]

    def _log_player(self, player: Player, section: str, body: str) -> None:
        self._player_writer(player).write(section, body)

    def log(self, section: str, body: str) -> None:
        self._log_main(section, body)

    def _player_label(self, player: Player) -> str:
        return (
            f"Игрок {player.player_number} "
            f"({player.role.value}, {player.player_type.value})"
        )

    def _init_player_log(self, player: Player, human: Player | None) -> None:
        lines = [
            self._player_label(player),
            f"Роль: {player.role.value}",
            f"Тип: {player.player_type.value}",
        ]
        if human and player == human:
            lines.append("Это человек за столом.")
        if player.mafia_ally_numbers:
            allies = ", ".join(
                str(number) for number in sorted(player.mafia_ally_numbers)
            )
            lines.append(f"Известные союзники-мафиози: {allies}")
        lines.append(
            "\nЗдесь — промпты, рассуждения и ответы модели для этого игрока."
        )
        self._log_player(player, "ПРОФИЛЬ", "\n".join(lines))

    def log_game_setup(self, players: list[Player], human: Player | None) -> None:
        lines = ["Состав игры (полная правда о ролях):"]
        for player in sorted(players, key=lambda item: item.player_number):
            marker = " [ЧЕЛОВЕК]" if human and player == human else ""
            allies = ""
            if player.mafia_ally_numbers:
                allies = (
                    ", союзники: "
                    + ", ".join(
                        str(number) for number in sorted(player.mafia_ally_numbers)
                    )
                )
            lines.append(
                f"- Игрок {player.player_number}: {player.role.value} "
                f"({player.player_type.value}){marker}{allies}"
            )
        if human:
            lines.append(f"\nЧеловек играет за игрока {human.player_number}.")
        self._log_main("НАЧАЛО ИГРЫ", "\n".join(lines))

        for player in players:
            self._init_player_log(player, human)

    def log_stage(self, stage: GameStage, day_number: int) -> None:
        self._log_main("СТАДИЯ", f"День {day_number}, стадия: {stage.value.upper()}")

    def log_ai_request(
        self,
        player: Player,
        *,
        system_prompt: str,
        user_prompt: str,
        action_type: str | None = None,
        channel: str | None = None,
        speech_context: str | None = None,
        task_key: str | None = None,
    ) -> None:
        context_parts = [
            part
            for part in (
                f"action_type={action_type}" if action_type else None,
                f"channel={channel}" if channel else None,
                f"speech_context={speech_context}" if speech_context else None,
                f"task_key={task_key}" if task_key else None,
            )
            if part
        ]
        context = ", ".join(context_parts) if context_parts else "реплика"
        body = (
            f"Контекст: {context}\n\n"
            f"--- SYSTEM PROMPT ---\n{system_prompt}\n\n"
            f"--- USER PROMPT ---\n{user_prompt}"
        )
        self._log_player(player, "ЗАПРОС К ИИ", body)

    def log_ai_response(
        self,
        player: Player,
        response: str,
        *,
        reasoning: str | None = None,
    ) -> None:
        parts = []
        if reasoning:
            parts.append(f"--- REASONING ---\n{reasoning}")
        parts.append(f"--- RESPONSE ---\n{response}")
        self._log_player(player, "ОТВЕТ ИИ", "\n\n".join(parts))

    def log_ai_error(self, player: Player, error: str) -> None:
        self._log_player(player, "ОШИБКА ИИ", error)

    def log_human_input(
        self,
        player: Player,
        content: str,
        *,
        action_type: str | None = None,
        speech_context: str | None = None,
    ) -> None:
        context_parts = [
            part
            for part in (
                f"action_type={action_type}" if action_type else None,
                f"speech_context={speech_context}" if speech_context else None,
            )
            if part
        ]
        context = ", ".join(context_parts) if context_parts else "реплика"
        self._log_player(
            player,
            "ВВОД ИГРОКА",
            f"Контекст: {context}\n\n--- INPUT ---\n{content}",
        )

    def log_message(self, message: Message) -> None:
        sender = (
            f"Игрок {message.player.player_number}"
            if message.player is not None
            else "Система"
        )
        recipient = (
            f"Игрок {message.recipient.player_number}"
            if message.recipient is not None
            else "все"
        )
        body = (
            f"[{message.stage.value.upper()} {message.day_number}] "
            f"Канал: {message.channel.value}\n"
            f"От: {sender}\n"
            f"Кому: {recipient}\n\n"
            f"{message.text}"
        )
        self._log_main("СООБЩЕНИЕ", body)

    def log_action(self, action: Action, *, raw_input: str | None = None) -> None:
        target_label = (
            f"Игрок {action.target.player_number}"
            if action.target is not None
            else "воздержался"
        )
        main_body = (
            f"[{action.stage.value.upper()} {action.day_number}] "
            f"{action.action_type.value}\n"
            f"Игрок {action.player.player_number} ({action.player.role.value}) "
            f"→ {target_label}"
        )
        self._log_main("ДЕЙСТВИЕ", main_body)

        if raw_input is not None:
            player_body = (
                f"[{action.stage.value.upper()} {action.day_number}] "
                f"{action.action_type.value}\n"
                f"Результат: {target_label}\n"
                f"Сырой ввод: {raw_input}"
            )
            self._log_player(action.player, "ДЕЙСТВИЕ", player_body)

    def log_action_retry(
        self,
        player: Player,
        reason: str,
        *,
        raw_input: str | None = None,
        action_type: str | None = None,
    ) -> None:
        lines = [f"Причина: {reason}"]
        if action_type:
            lines.append(f"Действие: {action_type}")
        if raw_input is not None:
            lines.append(f"Сырой ввод: {raw_input}")
        self._log_player(player, "ПОВТОР ВВОДА", "\n".join(lines))

    def log_vote_results(self, actions: list[Action], *, title: str) -> None:
        lines = [title + ":"]
        for action in actions:
            voter = action.player.player_number
            if action.target is None:
                lines.append(f"  Игрок {voter} → воздержался")
            else:
                lines.append(
                    f"  Игрок {voter} → Игрок {action.target.player_number}"
                )
        self._log_main("ГОЛОСОВАНИЕ", "\n".join(lines))

    def log_text(self, section: str, text: str) -> None:
        self._log_main(section, text)

    def log_game_end(self, winner: Team | None) -> None:
        if winner is None:
            body = "Игра завершена без победителя."
        else:
            body = f"Победила команда: {winner.value.upper()}"
        self._log_main("КОНЕЦ ИГРЫ", body)
