import requests
import json

url = "http://localhost:11434/api/chat"
payload = {
    "model": "goekdenizguelmez/JOSIEFIED-Qwen2.5:7b",
    "messages": [{"role": "user", "content": "hi"}],
    "stream": False,
}
try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
