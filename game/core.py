import random
from collections import Counter
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from .action_parser import parse_player_number
from .allies import assign_mafia_allies, get_valid_action_targets
from .models import (
    Action,
    ActionType,
    ChannelType,
    GameEvent,
    GameStage,
    Message,
    Player,
    PlayerType,
    Role,
    Team,
)
from .player_actions.ai_client import AIClientError, get_ai_answer
from .player_actions.human_input import HumanPlayerInput
from .prompts.prompt_builder import PromptBuilder
from .logging.game_logger import NullGameLogger
from .ui.null_presenter import NullPresenter
from .validation import validate_action_target, validate_roles_config
from .vote_format import format_votes_so_far

MAX_ACTION_ATTEMPTS = 5


class Game(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    stage: GameStage = GameStage.DAY
    day_number: int = 1
    roles: dict[Role, int]
    messages: list[Message] = Field(default_factory=list)
    players: list[Player] = Field(default_factory=list)
    is_active: bool = True
    actions: list[Action] = Field(default_factory=list)
    game_events: list[GameEvent] = Field(default_factory=list)
    presenter: Any = Field(default_factory=NullPresenter, repr=False)
    human_input: HumanPlayerInput = Field(default_factory=HumanPlayerInput, repr=False)
    logger: Any = Field(default_factory=NullGameLogger, repr=False)

    @property
    def alive_players(self) -> list[Player]:
        return [player for player in self.players if player.is_alive]

    @property
    def current_actions(self) -> list[Action]:
        return [
            action
            for action in self.actions
            if action.day_number == self.day_number and action.stage == self.stage
        ]

    @property
    def current_game_events(self) -> list[GameEvent]:
        return [
            event
            for event in self.game_events
            if event.day_number == self.day_number and event.stage == self.stage
        ]

    @property
    def human_player(self) -> Player | None:
        return next(
            (player for player in self.players if player.player_type == PlayerType.HUMAN),
            None,
        )

    @property
    def human_is_spectator(self) -> bool:
        return self.human_player is not None and not self.human_player.is_alive

    def distribute_roles_and_types(self) -> None:
        if self.players:
            return

        validate_roles_config(self.roles)

        roles_list: list[Role] = []
        for role, count in self.roles.items():
            roles_list.extend([role] * count)

        human_player_number = random.randint(1, len(roles_list))
        random.shuffle(roles_list)
        for index, role in enumerate(roles_list):
            player_number = index + 1
            player_type = (
                PlayerType.HUMAN
                if player_number == human_player_number
                else PlayerType.AI
            )
            player = Player(
                player_number=player_number,
                role=role,
                player_type=player_type,
            )
            if player_type == PlayerType.AI:
                player.system_prompt = PromptBuilder.get_system_prompt(player)
            self.players.append(player)

        assign_mafia_allies(self.players)

        self.logger.log_game_setup(self.players, self.human_player)
        self.logger.announce()

        if self.human_player:
            self.presenter.show_game_start(self.human_player)

    def change_stage(self) -> None:
        if self.check_win_cons():
            self.is_active = False
            return

        if self.stage == GameStage.NIGHT:
            self.stage = GameStage.DAY
            self.day_number += 1
        else:
            self.stage = GameStage.NIGHT
        self.logger.log_stage(self.stage, self.day_number)

    def check_win_cons(self) -> Team | None:
        teams = {team: 0 for team in Team}
        for player in self.alive_players:
            teams[player.role.team] += 1

        if not teams[Team.MAFIA] and not teams[Team.NEUTRAL]:
            return Team.CITIZENS
        if teams[Team.MAFIA] >= teams[Team.CITIZENS] and not teams[Team.NEUTRAL]:
            return Team.MAFIA
        if teams[Team.NEUTRAL] >= teams[Team.CITIZENS] and not teams[Team.MAFIA]:
            return Team.NEUTRAL
        return None

    def _get_raw_answer(
        self,
        player: Player,
        action_type: ActionType | None = None,
        *,
        channel: ChannelType | None = None,
        speech_context: str | None = None,
        task_key: str | None = None,
        allowed_targets: list[Player] | None = None,
        allow_abstain: bool = True,
        votes_so_far: list[Action] | None = None,
    ) -> str:
        if player.player_type == PlayerType.AI:
            while True:
                user_prompt = PromptBuilder.get_user_prompt(
                    self,
                    player,
                    action_type,
                    channel=channel,
                    speech_context=speech_context,
                    task_key=task_key,
                    allowed_targets=allowed_targets,
                    votes_so_far=votes_so_far,
                )
                self.logger.log_ai_request(
                    player,
                    system_prompt=player.system_prompt or "",
                    user_prompt=user_prompt,
                    action_type=action_type.value if action_type else None,
                    channel=channel.value if channel else None,
                    speech_context=speech_context,
                    task_key=task_key,
                )
                try:
                    response = get_ai_answer(
                        prompt=user_prompt,
                        system_prompt=player.system_prompt or "",
                    )
                    self.logger.log_ai_response(
                        player,
                        response.content,
                        reasoning=response.reasoning,
                    )
                    return response.content
                except AIClientError as error:
                    self.logger.log_ai_error(player, str(error))
                    continue

        if action_type is None:
            content = self.human_input.get_speech(
                player,
                self.day_number,
                self.stage,
                speech_context=speech_context,
            )
            self.logger.log_human_input(
                player,
                content,
                speech_context=speech_context,
            )
            return content
        content = self.human_input.get_action(
            self,
            player,
            action_type,
            self.day_number,
            self.stage,
            task_key=task_key,
            allowed_targets=allowed_targets,
            allow_abstain=allow_abstain,
            votes_so_far=votes_so_far,
        )
        self.logger.log_human_input(
            player,
            content,
            action_type=action_type.value,
        )
        return content

    def _get_player(self, player_number: int) -> Player | None:
        for player in self.players:
            if player.player_number == player_number:
                return player
        return None

    def _show_action_retry(self, player: Player, reason: str, *, raw_input: str | None = None, action_type: ActionType | None = None) -> None:
        self.logger.log_action_retry(
            player,
            reason,
            raw_input=raw_input,
            action_type=action_type.value if action_type else None,
        )
        if player.player_type == PlayerType.HUMAN:
            self.presenter.show_retry_prompt(reason, player=player)

    def _notify_human_elimination(self, target: Player) -> None:
        if self.human_player and target == self.human_player:
            self.presenter.show_spectator_mode()

    def _sheriff_check_result_text(self, target: Player) -> str:
        team_name = (
            "Мафия"
            if target.role.team == Team.MAFIA
            else "Мирный житель"
        )
        return f"Результат проверки: Игрок {target.player_number} — {team_name}."

    def _record_sheriff_check(self, sheriff: Player, target: Player) -> str:
        result_text = self._sheriff_check_result_text(target)
        message = Message(
            channel=ChannelType.PRIVATE,
            text=result_text,
            player=None,
            recipient=sheriff,
            stage=self.stage,
            day_number=self.day_number,
        )
        self.messages.append(message)
        self.logger.log_message(message)
        self.logger.log_text(
            "ПРОВЕРКА ШЕРИФА",
            f"Шериф (игрок {sheriff.player_number}) проверил "
            f"игрока {target.player_number}: {target.role.team.value}",
        )
        return result_text

    def get_active_night_channels(self) -> dict[Any, list[Player]]:
        channels: dict[Any, list[Player]] = {}
        for player in self.alive_players:
            if player.role.night_action is None:
                continue
            channel = player.role.night_channel
            if channel is None:
                continue

            if channel == ChannelType.PRIVATE:
                key = f"private_{player.player_number}"
            else:
                key = channel

            channels.setdefault(key, []).append(player)
        return channels

    def get_player_answer(
        self,
        player: Player,
        channel: ChannelType,
        *,
        speech_context: str | None = None,
        allowed_targets: list[Player] | None = None,
    ) -> Message:
        content = self._get_raw_answer(
            player,
            action_type=None,
            channel=channel,
            speech_context=speech_context,
            allowed_targets=allowed_targets,
        )
        message = Message(
            text=content,
            stage=self.stage,
            player=player,
            day_number=self.day_number,
            channel=channel,
        )
        self.logger.log_message(message)

        if self.presenter.should_show_channel_message(
            channel,
            self.human_player,
            message.recipient,
        ):
            self.presenter.show_channel_message(channel, player, message.text)

        return message

    def get_player_action(
        self,
        action_type: ActionType,
        player: Player,
        *,
        channel: ChannelType | None = None,
        task_key: str | None = None,
        allowed_targets: list[Player] | None = None,
        allow_abstain: bool = True,
        votes_so_far: list[Action] | None = None,
    ) -> Action:
        if action_type == ActionType.VOTE:
            allowed_targets = get_valid_action_targets(
                self,
                player,
                action_type,
                allowed_targets=allowed_targets,
            )
        for _ in range(MAX_ACTION_ATTEMPTS):
            content = self._get_raw_answer(
                player,
                action_type=action_type,
                channel=channel,
                task_key=task_key,
                allowed_targets=allowed_targets,
                allow_abstain=allow_abstain,
                votes_so_far=votes_so_far,
            )
            parsed_number = parse_player_number(content)

            if parsed_number is None:
                self._show_action_retry(
                    player,
                    "ожидается число",
                    raw_input=content,
                    action_type=action_type,
                )
                continue

            if allowed_targets is not None:
                candidate_numbers = {
                    candidate.player_number for candidate in allowed_targets
                }
                numbers_label = ", ".join(
                    str(number) for number in sorted(candidate_numbers)
                )
                if parsed_number not in candidate_numbers:
                    if task_key == "runoff_vote":
                        reason = (
                            f"можно голосовать только за кандидатов: {numbers_label}"
                        )
                    else:
                        reason = f"можно выбрать только игроков: {numbers_label}"
                    self._show_action_retry(
                        player,
                        reason,
                        raw_input=content,
                        action_type=action_type,
                    )
                    continue

            if parsed_number == 0:
                if not allow_abstain or action_type != ActionType.VOTE:
                    self._show_action_retry(
                        player,
                        "0 допустимо только при обычном голосовании с воздержанием",
                        raw_input=content,
                        action_type=action_type,
                    )
                    continue
                target = None
            else:
                target = self._get_player(parsed_number)
                if target is None:
                    self._show_action_retry(
                        player,
                        "игрок с таким номером не найден",
                        raw_input=content,
                        action_type=action_type,
                    )
                    continue

            validation_error = validate_action_target(
                self,
                player,
                target,
                action_type,
                allowed_targets=allowed_targets,
            )
            if validation_error:
                self._show_action_retry(
                    player,
                    validation_error,
                    raw_input=content,
                    action_type=action_type,
                )
                continue

            action = Action(
                stage=self.stage,
                player=player,
                day_number=self.day_number,
                target=target,
                action_type=action_type,
            )
            self.logger.log_action(action, raw_input=content)
            return action

        raise RuntimeError(
            f"Игрок {player.player_number} не смог выполнить действие {action_type.value}."
        )

    def execute_game_events(self) -> None:
        if self.stage == GameStage.DAY:
            for event in self.current_game_events:
                event.target.is_alive = False
                self.presenter.show_lynch(event.target)
                self._notify_human_elimination(event.target)
                self.logger.log_text(
                    "СОБЫТИЕ",
                    f"Игрок {event.target.player_number} ({event.target.role.value}) "
                    "изгнан голосованием.",
                )
                self.messages.append(
                    Message(
                        channel=ChannelType.DAY,
                        text=(
                            f"Игрок {event.target.player_number} "
                            "был изгнан голосованием жителей."
                        ),
                        player=None,
                        stage=self.stage,
                        day_number=self.day_number,
                    )
                )
            return

        heals = [
            event.target
            for event in self.current_game_events
            if event.action_type == ActionType.HEAL
        ]
        target_kills = [
            event.target
            for event in self.current_game_events
            if event.action_type == ActionType.KILL and event.target not in heals
        ]
        morning_day = self.day_number + 1

        self.presenter.show_morning(morning_day)
        for target in target_kills:
            target.is_alive = False
            self.presenter.show_night_kill(target)
            self._notify_human_elimination(target)
            self.logger.log_text(
                "СОБЫТИЕ",
                f"Игрок {target.player_number} ({target.role.value}) "
                "убит ночью.",
            )
            self.messages.append(
                Message(
                    channel=ChannelType.DAY,
                    text=f"Игрок {target.player_number} найден мертвым этим утром.",
                    player=None,
                    stage=GameStage.DAY,
                    day_number=morning_day,
                )
            )
        if not target_kills:
            self.presenter.show_peaceful_night()
            self.logger.log_text("СОБЫТИЕ", "Ночь прошла спокойно, убийств нет.")

    def _get_leading_candidates(
        self,
        actions: list[Action],
        *,
        abstain_blocks: bool = True,
    ) -> list[Player]:
        abstain_count = sum(1 for action in actions if action.target is None)
        votes = Counter(
            action.target.player_number
            for action in actions
            if action.target is not None
        )

        if not votes:
            return []

        top_count = max(votes.values())
        if abstain_blocks and abstain_count >= top_count:
            return []

        leaders = [
            self._get_player(number)
            for number, count in votes.items()
            if count == top_count
        ]
        return [player for player in leaders if player is not None]

    def _collect_votes(
        self,
        voters: list[Player],
        *,
        task_key: str | None = None,
        get_task_key: Callable[[Player], str | None] | None = None,
        allowed_targets: list[Player] | None = None,
        allow_abstain: bool = True,
    ) -> list[Action]:
        votes: list[Action] = []
        for voter in voters:
            voter_task_key = get_task_key(voter) if get_task_key else task_key
            action = self.get_player_action(
                ActionType.VOTE,
                voter,
                task_key=voter_task_key,
                allowed_targets=allowed_targets,
                allow_abstain=allow_abstain,
                votes_so_far=votes,
            )
            self.actions.append(action)
            votes.append(action)
            self.presenter.show_votes_so_far(votes)
            self.logger.log_text("ГОЛОС", format_votes_so_far(votes))
        return votes

    def _schedule_lynch(self, targets: list[Player]) -> None:
        for target in targets:
            self.game_events.append(
                GameEvent(
                    action_type=ActionType.VOTE,
                    stage=self.stage,
                    day_number=self.day_number,
                    target=target,
                )
            )

    def _resolve_runoff_actions(self, actions: list[Action]) -> list[Player]:
        return self._get_leading_candidates(actions, abstain_blocks=False)

    def _run_runoff(self, candidates: list[Player]) -> None:
        self.presenter.show_runoff_start(candidates)
        self.presenter.show_runoff_defense_start()

        for candidate in candidates:
            message = self.get_player_answer(
                candidate,
                channel=ChannelType.DAY,
                speech_context="runoff_defense",
            )
            self.messages.append(message)
            self.presenter.show_player_speech(candidate, message.text)

        self.presenter.show_runoff_vote_start(candidates)
        runoff_actions = self._collect_votes(
            self.alive_players,
            task_key="runoff_vote",
            allowed_targets=candidates,
            allow_abstain=False,
        )

        self.logger.log_vote_results(
            runoff_actions,
            title="Итоги переголосования",
        )
        runoff_leaders = self._resolve_runoff_actions(runoff_actions)
        if len(runoff_leaders) == 1:
            outcome = (
                f"Большинство за игрока {runoff_leaders[0].player_number} — "
                "он будет изгнан."
            )
            self.presenter.show_vote_outcome(outcome)
            self.logger.log_text("ИТОГ ГОЛОСОВАНИЯ", outcome)
        elif len(runoff_leaders) > 1:
            numbers = ", ".join(
                str(leader.player_number) for leader in runoff_leaders
            )
            outcome = f"Снова ничья между игроками {numbers} — изгоняют обоих."
            self.presenter.show_vote_outcome(outcome)
            self.logger.log_text("ИТОГ ГОЛОСОВАНИЯ", outcome)
        else:
            outcome = "Никого не изгоняют."
            self.presenter.show_vote_outcome(outcome)
            self.logger.log_text("ИТОГ ГОЛОСОВАНИЯ", outcome)

        self._schedule_lynch(runoff_leaders)

    def _vote_outcome_message(
        self,
        actions: list[Action],
        leaders: list[Player],
    ) -> str:
        abstain_count = sum(1 for action in actions if action.target is None)
        has_votes = any(action.target is not None for action in actions)

        if not has_votes:
            return "Все воздержались — никого не изгоняют."
        if not leaders:
            return "Воздержаний достаточно — никого не изгоняют."
        if len(leaders) == 1:
            return f"Большинство за игрока {leaders[0].player_number} — он будет изгнан."
        numbers = ", ".join(str(leader.player_number) for leader in leaders)
        return f"Ничья между игроками {numbers} — назначено переголосование."

    def resolve_day_vote(self) -> None:
        actions = self.current_actions
        self.logger.log_vote_results(actions, title="Итоги голосования")

        leaders = self._get_leading_candidates(actions)
        outcome = self._vote_outcome_message(actions, leaders)
        self.presenter.show_vote_outcome(outcome)
        self.logger.log_text("ИТОГ ГОЛОСОВАНИЯ", outcome)

        if not leaders:
            return
        if len(leaders) == 1:
            self._schedule_lynch(leaders)
            return
        self._run_runoff(leaders)

    def process_day(self) -> None:
        self.presenter.show_day_start(self.day_number)

        for player in self.alive_players:
            speech_context = (
                "mafia_day_speech"
                if player.role.team == Team.MAFIA
                else None
            )
            message = self.get_player_answer(
                player=player,
                channel=ChannelType.DAY,
                speech_context=speech_context,
            )
            self.messages.append(message)
            self.presenter.show_player_speech(player, message.text)

        self.presenter.show_vote_start()
        self._collect_votes(
            self.alive_players,
            get_task_key=(
                lambda player: (
                    "mafia_vote" if player.role.team == Team.MAFIA else None
                )
            ),
        )

        self.resolve_day_vote()
        self.execute_game_events()

    def _run_mafia_discussion(self, players: list[Player]) -> None:
        for player in players:
            kill_targets = get_valid_action_targets(
                self,
                player,
                ActionType.KILL,
            )
            message = self.get_player_answer(
                player,
                channel=ChannelType.MAFIA_NIGHT,
                speech_context="mafia_discussion",
                allowed_targets=kill_targets,
            )
            self.messages.append(message)

    def _collect_mafia_kill_votes(
        self,
        players: list[Player],
    ) -> list[Action] | None:
        task_key = "mafia_kill" if len(players) > 1 else None
        round_actions: list[Action] = []
        for player in players:
            kill_targets = get_valid_action_targets(
                self,
                player,
                ActionType.KILL,
            )
            action = self.get_player_action(
                ActionType.KILL,
                player,
                channel=ChannelType.MAFIA_NIGHT,
                task_key=task_key,
                allowed_targets=kill_targets,
            )
            round_actions.append(action)

        if len(players) == 1:
            return round_actions

        targets = [action.target for action in round_actions if action.target is not None]
        if len(targets) != len(players):
            return None
        first_target_number = targets[0].player_number
        if all(target.player_number == first_target_number for target in targets):
            return round_actions
        return None

    def _process_mafia_night(self, players: list[Player]) -> None:
        max_attempts = 2
        for attempt in range(max_attempts):
            if len(players) > 1:
                self._run_mafia_discussion(players)

            round_actions = self._collect_mafia_kill_votes(players)
            if round_actions is not None:
                self.actions.extend(round_actions)
                return

            if attempt < max_attempts - 1:
                self.logger.log_text(
                    "МАФИЯ",
                    "Мафия не договорилась о жертве — повторное обсуждение.",
                )
                if (
                    self.human_player
                    and self.human_player.is_alive
                    and self.human_player.role.team == Team.MAFIA
                ):
                    self.presenter.show_mafia_disagreement()

    def _process_night_channel(self, channel_key: Any, players: list[Player]) -> None:
        channel = (
            ChannelType.PRIVATE
            if str(channel_key).startswith("private_")
            else channel_key
        )

        if channel == ChannelType.MAFIA_NIGHT:
            self._process_mafia_night(players)
            return

        if len(players) > 1:
            for player in players:
                message = self.get_player_answer(player, channel=channel)
                self.messages.append(message)

        for player in players:
            action_type = player.role.night_action
            if action_type is None:
                continue
            action_targets = get_valid_action_targets(
                self,
                player,
                action_type,
            )
            action = self.get_player_action(
                action_type,
                player,
                channel=channel,
                allowed_targets=action_targets,
            )
            self.actions.append(action)
            if action_type == ActionType.ROLE_CHECK and action.target is not None:
                result_text = self._record_sheriff_check(player, action.target)
                if player.player_type == PlayerType.HUMAN:
                    self.presenter.show_sheriff_check(result_text)

    def resolve_night_actions(self) -> None:
        if not self.current_actions:
            self.logger.log_text("НОЧЬ", "Ночных действий не было.")
            return

        lines = ["Ночные действия:"]
        for action in self.current_actions:
            target_label = (
                f"игрок {action.target.player_number}"
                if action.target is not None
                else "—"
            )
            lines.append(
                f"- Игрок {action.player.player_number} "
                f"({action.player.role.value}): {action.action_type.value} → {target_label}"
            )

        mafia_votes = Counter(
            action.target.player_number
            for action in self.current_actions
            if action.player.role.team == Team.MAFIA
            and action.action_type == ActionType.KILL
            and action.target is not None
        )
        top_votes = mafia_votes.most_common()
        if top_votes:
            if len(top_votes) > 1 and top_votes[0][1] == top_votes[1][1]:
                lines.append("Мафия не смогла договориться — убийства нет.")
                self.logger.log_text("НОЧЬ", "\n".join(lines))
                return
            kill_target = top_votes[0][0]
            target_player = self._get_player(kill_target)
            if target_player is not None:
                lines.append(f"Жертва мафии: игрок {kill_target}.")
                self.game_events.append(
                    GameEvent(
                        target=target_player,
                        stage=self.stage,
                        day_number=self.day_number,
                        action_type=ActionType.KILL,
                    )
                )

        not_mafia_actions = [
            action
            for action in self.current_actions
            if action.player.role.team != Team.MAFIA and action.target is not None
        ]
        for action in not_mafia_actions:
            self.game_events.append(
                GameEvent(
                    action_type=action.action_type,
                    target=action.target,
                    stage=action.stage,
                    day_number=action.day_number,
                    player=action.player,
                )
            )
        self.logger.log_text("НОЧЬ", "\n".join(lines))

    def process_night(self) -> None:
        human = self.human_player
        if human and human.is_alive and human.role.night_action is None:
            self.presenter.show_civilian_night()
        elif self.human_is_spectator:
            self.presenter.show_spectator_night()

        for channel_key, players in self.get_active_night_channels().items():
            self._process_night_channel(channel_key, players)

        self.resolve_night_actions()
        self.execute_game_events()

    def run(self) -> Team | None:
        self.distribute_roles_and_types()
        self.logger.log_stage(self.stage, self.day_number)

        while self.is_active:
            if self.stage == GameStage.NIGHT:
                self.presenter.show_night_enter_prompt(
                    spectator=self.human_is_spectator,
                )
                self.presenter.show_night_processing()
                self.process_night()
            else:
                self.process_day()
            self.change_stage()

        winner = self.check_win_cons()
        self.logger.log_game_end(winner)
        return winner
