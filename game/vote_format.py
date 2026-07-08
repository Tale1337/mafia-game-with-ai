from .models import Action


def format_vote_action(action: Action) -> str:
    voter_number = action.player.player_number
    if action.target is None:
        return f"Игрок {voter_number} → воздержался"
    return f"Игрок {voter_number} → Игрок {action.target.player_number}"


def format_votes_so_far(actions: list[Action]) -> str:
    if not actions:
        return "Голосов пока нет."
    return "\n".join(f"- {format_vote_action(action)}" for action in actions)
