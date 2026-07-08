import re

_PLAYER_NUMBER_RE = re.compile(r"-?\d+")


def parse_player_number(content: str) -> int | None:
    """Извлекает первое целое число из ответа игрока или ИИ."""
    match = _PLAYER_NUMBER_RE.search(content.strip())
    if match is None:
        return None
    return int(match.group())
