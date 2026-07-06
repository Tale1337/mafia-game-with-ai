import requests

API_LMSTUDIO = "http://127.0.0.1:1234"
CHAT = API_LMSTUDIO + "/v1/chat/completions"
AI_MODEL = "qwen3.5-9b"


def get_ai_answer(prompt: str, system_prompt: str) -> str:
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
    response = requests.post(url=API_LMSTUDIO + '/v1/chat/completions',
                             json={"model": AI_MODEL, "messages": messages},
                             headers={"Content-Type": "application/json"})
    return response.json()["choices"][0]["message"]["content"]
