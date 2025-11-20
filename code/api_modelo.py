# server.py
import requests
from fastapi import FastAPI
from pydantic import BaseModel

API_URL = "http://127.0.0.1:5000/v1/chat/completions"  # TGWUI o LM Studio
MODEL_NAME = "Meta-Llama-3.1-8B-Instruct.Q4_K_M.gguf"

app = FastAPI(title="Papermind Local API")

class ChatRequest(BaseModel):
    question: str
    history: list | None = None


def ask_model(message: str, history=None) -> str:
    headers = {"Content-Type": "application/json"}

    msgs = []
    if history:
        msgs.extend(history)
    msgs.append({"role": "user", "content": message})

    payload = {
        "model": MODEL_NAME,
        "messages": msgs,
        "temperature": 0.2
    }

    response = requests.post(API_URL, json=payload, headers=headers)
    data = response.json()

    if "choices" not in data:
        raise Exception(f"Respuesta inesperada del modelo: {data}")

    return data["choices"][0]["message"]["content"]


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    reply = ask_model(request.question, request.history)
    return {
        "response": reply
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
