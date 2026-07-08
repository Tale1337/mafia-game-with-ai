from .models import ActionType, Player, Role, Team
from .allies import is_mafia_ally


def validate_roles_config(roles: dict[Role, int]) -> None:
    if not roles:
        raise ValueError("Нужно указать хотя бы одну роль.")

    total_players = 0
    for role, count in roles.items():
        if count < 0:
            raise ValueError(f"Количество роли {role.value} не может быть отрицательным.")
        total_players += count

    if total_players < 4:
        raise ValueError("В игре должно быть минимум 4 игрока.")

    mafia_count = roles.get(Role.MAFIA, 0)
    if mafia_count < 1:
        raise ValueError("В игре должна быть хотя бы одна мафия.")

    citizens_count = sum(
        count for role, count in roles.items() if role.team == Team.CITIZENS
    )
    if citizens_count < mafia_count:
        raise ValueError("Мирных жителей должно быть больше, чем мафии.")


def validate_action_target(
    game,
    actor: Player,
    target: Player | None,
    action_type: ActionType,
    *,
    allowed_targets: list[Player] | None = None,
) -> str | None:
    if target is None:
        if action_type == ActionType.VOTE:
            return None
        return "нужно выбрать живого игрока"

    if not target.is_alive:
        return "игрок уже мёртв"

    if (
        action_type == ActionType.KILL
        and actor.role.team == Team.MAFIA
        and (
            target.player_number == actor.player_number
            or is_mafia_ally(actor, target)
        )
    ):
        return "мафия может убивать только мирных жителей"

    if (
        action_type == ActionType.ROLE_CHECK
        and actor.role == Role.SHERIFF
        and target.player_number == actor.player_number
    ):
        return "шериф не может проверять себя"

    if (
        action_type == ActionType.VOTE
        and target.player_number == actor.player_number
    ):
        return "нельзя голосовать за себя"

    if allowed_targets is not None and target not in allowed_targets:
        numbers = ", ".join(
            str(candidate.player_number) for candidate in allowed_targets
        )
        return f"можно голосовать только за кандидатов: {numbers}"

    return None
