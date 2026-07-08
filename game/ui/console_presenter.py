from collections import Counter

from ..models import Action, ChannelType, Player, PlayerType, Team
from ..vote_format import format_vote_action

class ConsolePresenter:
    def show_game_start(self, human: Player) -> None:
        from ..models import Role

        print(f"\n🎮 Игра началась! Вы — Игрок {human.player_number}.")
        print(f"Ваша роль: {human.role.value.upper()} (Команда: {human.role.team.value})")
        if human.role == Role.MAFIA and human.mafia_ally_numbers:
            allies = ", ".join(
                f"Игрок {number}" for number in sorted(human.mafia_ally_numbers)
            )
            print(f"Ваши союзники-мафиози: {allies}")
        elif human.role == Role.MAFIA:
            print("Вы единственный мафиози в игре.")
        print("--------------------------------------------------\n")

    def show_day_start(self, day_number: int) -> None:
        print(f"\n=== ДЕНЬ {day_number} ===")
        print("Игроки начинают обсуждение:")

    def show_player_speech(self, player: Player, text: str) -> None:
        print(f"Игрок {player.player_number}: {text}")

    def show_vote_start(self) -> None:
        print("\nНачинается голосование...")

    def show_votes_so_far(self, actions: list[Action]) -> None:
        print("\n📊 Голоса:")
        for action in actions:
            print(f"  {format_vote_action(action)}")

        abstain_count = sum(1 for action in actions if action.target is None)
        votes = Counter(
            action.target.player_number
            for action in actions
            if action.target is not None
        )
        if votes or abstain_count:
            print("  Подсчёт:", end="")
            if votes:
                tally = ", ".join(
                    f"игрок {number} — {count}"
                    for number, count in sorted(votes.items())
                )
                print(f" {tally}", end="")
            if abstain_count:
                print(f"; воздержались: {abstain_count}", end="")
            print()

    def show_vote_results(
        self,
        actions: list[Action],
        *,
        title: str = "Итоги голосования",
    ) -> None:
        print(f"\n📊 {title}:")
        if not actions:
            print("  (голосов нет)")
            return

        for action in actions:
            voter_number = action.player.player_number
            if action.target is None:
                print(f"  Игрок {voter_number} → воздержался")
            else:
                print(
                    f"  Игрок {voter_number} → Игрок {action.target.player_number}"
                )

        abstain_count = sum(1 for action in actions if action.target is None)
        votes = Counter(
            action.target.player_number
            for action in actions
            if action.target is not None
        )

        print("\n  Подсчёт:")
        if votes:
            for player_number in sorted(votes):
                count = votes[player_number]
                label = "голос" if count == 1 else "голоса" if 2 <= count <= 4 else "голосов"
                print(f"    Игрок {player_number}: {count} {label}")
        else:
            print("    (нет голосов за игроков)")
        if abstain_count:
            abstain_label = (
                "воздержался"
                if abstain_count == 1
                else "воздержались"
            )
            print(f"    {abstain_label.capitalize()}: {abstain_count}")

    def show_vote_outcome(self, message: str) -> None:
        print(f"  ➜ {message}")

    def show_runoff_start(self, candidates: list[Player]) -> None:
        numbers = ", ".join(str(candidate.player_number) for candidate in candidates)
        print(
            f"\n⚖️ Ничья! Назначено переголосование между игроками: {numbers}"
        )

    def show_runoff_defense_start(self) -> None:
        print("\nКандидаты оправдываются:")

    def show_runoff_vote_start(self, candidates: list[Player]) -> None:
        numbers = ", ".join(str(candidate.player_number) for candidate in candidates)
        print(
            f"\nПереголосование. Голосуют все живые игроки.\n"
            f"Можно голосовать ТОЛЬКО за кандидатов: {numbers}"
        )

    def show_spectator_mode(self) -> None:
        print(
            "\n👁 Вы заканчиваете игру в роли игрока и продолжаете как зритель."
        )

    def show_night_enter_prompt(self, *, spectator: bool = False) -> None:
        if spectator:
            input("\nНажмите Enter, чтобы продолжить (режим зрителя)...")
        else:
            input("\nНажмите Enter, чтобы наступила ночь...")

    def show_night_processing(self) -> None:
        print(
            "\n🌙 Наступает ночь... Игроки совершают ночные действия, "
            "подождите немного."
        )

    def show_civilian_night(self) -> None:
        print("\n🌙 Вы мирный житель — ночью вы спите и не совершаете действий.")

    def show_spectator_night(self) -> None:
        print("\n🌙 Ночь. Вы наблюдаете за игрой как зритель.")

    def show_channel_message(
        self,
        channel: ChannelType,
        sender: Player | None,
        text: str,
    ) -> None:
        sender_label = f"Игрок {sender.player_number}" if sender else "Система"
        print(f"💬 [{channel.value.upper()}] {sender_label}: {text}")

    def show_lynch(self, target: Player) -> None:
        print(f"💀 Игрок {target.player_number} изгнан голосованием жителей!")

    def show_morning(self, day_number: int) -> None:
        print(f"\n=== НАСТУПАЕТ УТРО ДНЯ {day_number} ===")

    def show_night_kill(self, target: Player) -> None:
        print(f"💀 Ночью был убит Игрок {target.player_number}!")

    def show_peaceful_night(self) -> None:
        print("💖 Ночь прошла спокойно. Никто не погиб.")

    def show_sheriff_check(self, result_text: str) -> None:
        print(f"🔍 [Секретно] {result_text}")

    def show_game_end(self, winner: Team) -> None:
        print("\n==========================================")
        print(f"🎉 ИГРА ОКОНЧЕНА! Победила команда: {winner.value.upper()}")
        print("==========================================")

    def show_retry_prompt(self, reason: str, *, player: Player | None = None) -> None:
        if player is not None and player.player_type != PlayerType.HUMAN:
            return
        print(f"Некорректный ввод: {reason}. Повторите попытку.")

    def show_ai_retry(self, player: Player, reason: str) -> None:
        pass

    def show_mafia_disagreement(self) -> None:
        pass

    def should_show_channel_message(
        self,
        channel: ChannelType,
        human: Player | None,
        recipient: Player | None,
    ) -> bool:
        if channel == ChannelType.DAY:
            return False
        if human is None:
            return False
        if channel == ChannelType.PRIVATE and recipient == human:
            return True
        if channel == ChannelType.MAFIA_NIGHT and human.role.team == Team.MAFIA:
            return True
        return False
