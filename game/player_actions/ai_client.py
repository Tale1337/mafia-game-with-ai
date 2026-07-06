import requests

API_URL = "http://127.0.0.1:1234/v1"
CHAT_URL = API_URL + "/chat/completions"
AI_MODEL = "qwen3.5-9b"


def get_ai_answer(messages: list[dict]) -> str:
    response = requests.post(
        CHAT_URL,
        json={
            "model": AI_MODEL,
            "messages": messages,
            "temperature": 0.8
        },
        headers={
            "Content-Type": "application/json"
        }
    )

    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]
