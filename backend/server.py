import os
import time
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)
CORS(app)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", 15))
rate_store = defaultdict(list)


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    minute_ago = now - 60
    rate_store[ip] = [t for t in rate_store[ip] if t > minute_ago]

    if len(rate_store[ip]) >= RATE_LIMIT:
        return True

    rate_store[ip].append(now)
    return False


@app.route("/chat", methods=["POST"])
def chat():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if is_rate_limited(ip):
        return jsonify({"error": "Muitas requisições. Tente novamente."}), 429

    data = request.get_json()

    messages = data.get("messages", [])
    context = data.get("context", "")

    if not messages:
        return jsonify({"error": "Mensagem não informada"}), 400

    # monta conversa simples
    conversation = ""
    for m in messages:
        role = "Usuário" if m["role"] == "user" else "Assistente"
        conversation += f"{role}: {m['content']}\n"

    prompt = f"""
Você é um assistente de produtividade pessoal.

Seja direto, prático e acolhedor.

Contexto do dia:
{context}

Conversa:
{conversation}

Responda em português do Brasil.
"""

    try:
        response = model.generate_content(prompt)
        return jsonify({"reply": response.text})

    except Exception as e:
        print("ERRO GEMINI:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)