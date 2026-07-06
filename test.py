import requests

API_LMSTUDIO = "http://127.0.0.1:1234"

messages = [{"role": "user", "content": ""}]

response = requests.post(url=API_LMSTUDIO + '/v1/chat/completions', json={"model": "qwen3.5-9b", "messages": messages, "system_prompt": "You are pirat"},
                         headers={"Content-Type": "application/json"})

messages.append(response.json()["choices"][0]["message"])
messages.append({"role": "user", "content": "А ты кто?"})

response = requests.post(url=API_LMSTUDIO + '/v1/chat/completions', json={"model": "qwen3.5-9b", "messages": messages, "system_prompt": "You are pirat"},
                         headers={"Content-Type": "application/json"})
print(response.json())