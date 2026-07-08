from ..models import Action, ChannelType, Player, Team


class NullPresenter:
    """Тихий presenter для тестов — не выводит ничего в консоль."""

    def show_game_start(self, human: Player) -> None:
        pass

    def show_day_start(self, day_number: int) -> None:
        pass

    def show_player_speech(self, player: Player, text: str) -> None:
        pass

    def show_vote_start(self) -> None:
        pass

    def show_votes_so_far(self, actions: list[Action]) -> None:
        pass

    def show_vote_results(
        self,
        actions: list[Action],
        *,
        title: str = "Итоги голосования",
    ) -> None:
        pass

    def show_vote_outcome(self, message: str) -> None:
        pass

    def show_runoff_start(self, candidates: list[Player]) -> None:
        pass

    def show_runoff_defense_start(self) -> None:
        pass

    def show_runoff_vote_start(self, candidates: list[Player]) -> None:
        pass

    def show_spectator_mode(self) -> None:
        pass

    def show_night_enter_prompt(self, *, spectator: bool = False) -> None:
        pass

    def show_night_processing(self) -> None:
        pass

    def show_spectator_night(self) -> None:
        pass

    def show_civilian_night(self) -> None:
        pass

    def show_channel_message(
        self,
        channel: ChannelType,
        sender: Player | None,
        text: str,
    ) -> None:
        pass

    def show_lynch(self, target: Player) -> None:
        pass

    def show_morning(self, day_number: int) -> None:
        pass

    def show_night_kill(self, target: Player) -> None:
        pass

    def show_peaceful_night(self) -> None:
        pass

    def show_sheriff_check(self, result_text: str) -> None:
        pass

    def show_game_end(self, winner: Team) -> None:
        pass

    def show_retry_prompt(self, reason: str, *, player: Player | None = None) -> None:
        pass

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
        return False
