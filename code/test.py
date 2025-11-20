import requests

import requests

payload = {
    "question": "hola",
    "modo": "estricto"
}

r = requests.post("http://127.0.0.1:8000/chat", json=payload)

print(r.status_code)
print(r.text)
