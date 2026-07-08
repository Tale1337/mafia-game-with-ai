import requests

API_LMSTUDIO = "http://127.0.0.1:1234"
AI_MODEL = "qwen3.5-9b"
REQUEST_TIMEOUT_SECONDS = 120


class AIClientError(Exception):
    pass


def get_ai_answer(prompt: str, system_prompt: str):
    from ..logging.game_logger import AIResponse

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    try:
        response = requests.post(
            url=f"{API_LMSTUDIO}/v1/chat/completions",
            json={"model": AI_MODEL, "messages": messages},
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        message = payload["choices"][0]["message"]
        content = (message.get("content") or "").strip()
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        if isinstance(reasoning, str):
            reasoning = reasoning.strip() or None
        else:
            reasoning = None
        if not content and reasoning:
            content = reasoning
            reasoning = None
        return AIResponse(content=content, reasoning=reasoning)
    except requests.RequestException as error:
        raise AIClientError(f"Ошибка запроса к LM Studio: {error}") from error
    except (KeyError, IndexError, TypeError) as error:
        raise AIClientError("Некорректный ответ LM Studio.") from error
