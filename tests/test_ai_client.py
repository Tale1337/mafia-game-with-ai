import pytest

from game.logging.game_logger import AIResponse
from game.player_actions.ai_client import AIClientError, get_ai_answer


def test_get_ai_answer_extracts_content_and_reasoning(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Игрок 2",
                            "reasoning_content": "Сначала проверю всех...",
                        }
                    }
                ]
            }

    monkeypatch.setattr(
        "game.player_actions.ai_client.requests.post",
        lambda **kwargs: FakeResponse(),
    )

    result = get_ai_answer("user", "system")

    assert result.content == "Игрок 2"
    assert result.reasoning == "Сначала проверю всех..."


def test_get_ai_answer_raises_on_request_error(monkeypatch):
    import requests

    monkeypatch.setattr(
        "game.player_actions.ai_client.requests.post",
        lambda **kwargs: (_ for _ in ()).throw(requests.RequestException("offline")),
    )

    with pytest.raises(AIClientError, match="LM Studio"):
        get_ai_answer("user", "system")
