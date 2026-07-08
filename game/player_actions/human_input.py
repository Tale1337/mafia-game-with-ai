from ..allies import get_valid_action_targets
from ..models import ActionType, GameStage, Player, Role
from ..prompts.tasks import TASKS
from ..vote_format import format_votes_so_far

ROLE_LABELS = {
    Role.MAFIA: "Мафия",
    Role.CITIZEN: "Мирный житель",
    Role.DOCTOR: "Доктор",
    Role.SHERIFF: "Шериф",
}

SPEECH_PROMPTS = {
    None: "Выскажите одну реплику (не более 50 слов):",
    "mafia_discussion": (
        "Секретный чат мафии — обсудите с союзниками, кого убить. "
        "Предложите мирного жителя (не себя и не союзника-мафиози). "
        "Назовите номер жертвы и кратко объясните (не более 50 слов):"
    ),
    "runoff_defense": (
        "Вас выдвинули на переголосование. "
        "Объясните, почему не стоит голосовать против вас (не более 50 слов):"
    ),
}


class HumanPlayerInput:
    def get_speech(
        self,
        player: Player,
        day_number: int,
        stage: GameStage,
        *,
        speech_context: str | None = None,
    ) -> str:
        print(
            f"\n--- Ваш ход: {ROLE_LABELS[player.role]} "
            f"(Игрок {player.player_number}, {stage.value.upper()} {day_number}) ---"
        )
        print(SPEECH_PROMPTS.get(speech_context, SPEECH_PROMPTS[None]))
        return input("> ").strip()

    def get_action(
        self,
        game,
        player: Player,
        action_type: ActionType,
        day_number: int,
        stage: GameStage,
        *,
        task_key: str | None = None,
        allowed_targets: list[Player] | None = None,
        allow_abstain: bool = True,
        votes_so_far: list | None = None,
    ) -> str:
        print(
            f"\n--- Ваш ход: {ROLE_LABELS[player.role]} "
            f"(Игрок {player.player_number}, {stage.value.upper()} {day_number}) ---"
        )
        if votes_so_far:
            print("\nУже проголосовали:")
            print(format_votes_so_far(votes_so_far))
        prompt_key = task_key if task_key is not None else action_type
        print(TASKS[prompt_key].strip())
        valid_targets = get_valid_action_targets(
            game,
            player,
            action_type,
            allowed_targets=allowed_targets,
        )
        if task_key == "runoff_vote":
            numbers = ", ".join(
                str(target.player_number) for target in valid_targets
            )
            print(f"\nМожно голосовать ТОЛЬКО за кандидатов: {numbers}")
        else:
            print("\nДоступные игроки:")
        for target in valid_targets:
            print(f"  {target.player_number}. Игрок {target.player_number}")
        if action_type == ActionType.VOTE and allow_abstain:
            print("  0. Воздержаться")
        return input("> ").strip()


def get_human_answer() -> str:
    """Совместимость со старым API."""
    return input("Введите свой ответ:\n")
