import pytest

from game.action_parser import parse_player_number


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("3", 3),
        ("Игрок 3", 3),
        ("  7  ", 7),
        ("Мой выбор: 2.", 2),
        ("0", 0),
        ("no numbers", None),
        ("", None),
    ],
)
def test_parse_player_number(content, expected):
    assert parse_player_number(content) == expected
