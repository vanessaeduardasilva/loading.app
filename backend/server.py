"""
server.py — Backend do loading.app

Esse servidor faz o meio de campo entre o frontend e a API da Anthropic.
A chave da API fica aqui no servidor, protegida, longe do navegador.

Como rodar localmente:
    1. pip install -r requirements.txt
    2. Crie um .env com ANTHROPIC_API_KEY=sk-ant-...
    3. python server.py

Como fazer deploy (Railway, Render, Fly.io):
    - Suba esse repositório
    - Configure a variável de ambiente ANTHROPIC_API_KEY no painel
    - Pronto! O servidor sobe automaticamente
"""

import os
import time
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Rate limiting simples ──────────────────────────────────────────────────────
# Limita quantas mensagens cada IP pode mandar por minuto
# pra evitar que alguém abuse e estoure sua conta
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", 15))
rate_store = defaultdict(list)  # { "ip": [timestamp, timestamp, ...] }

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    minute_ago = now - 60
    # Remove timestamps antigos (mais de 1 minuto atrás)
    rate_store[ip] = [t for t in rate_store[ip] if t > minute_ago]
    if len(rate_store[ip]) >= RATE_LIMIT:
        return True
    rate_store[ip].append(now)
    return False


# ── Rota principal: chat ───────────────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    """
    Recebe a conversa do frontend e devolve a resposta da IA.

    Espera um JSON assim:
    {
        "messages": [
            { "role": "user", "content": "organize meu dia" },
            { "role": "assistant", "content": "Claro! Pelo que vejo..." },
            { "role": "user", "content": "e os blocos de tempo?" }
        ],
        "context": "Alta prioridade: reunião 14h, deploy. Blocos: 09:00 — estudar..."
    }

    Devolve:
    {
        "reply": "Começa pela reunião porque..."
    }
    """
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if is_rate_limited(ip):
        return jsonify({
            "error": "Muitas mensagens em pouco tempo. Aguarde um momento e tente de novo!"
        }), 429

    data = request.get_json()

    if not data:
        return jsonify({"error": "Requisição inválida."}), 400

    messages = data.get("messages", [])
    context = data.get("context", "Nenhuma tarefa cadastrada ainda.")

    # Valida que tem pelo menos uma mensagem do usuário
    if not messages or not any(m.get("role") == "user" for m in messages):
        return jsonify({"error": "Mensagem não informada."}), 400

    # Garante que as mensagens têm o formato certo
    clean_messages = [
        {"role": m["role"], "content": str(m["content"])}
        for m in messages
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    if not clean_messages:
        return jsonify({"error": "Mensagens inválidas."}), 400

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=f"""Você é um assistente de gestão de tempo pessoal integrado ao loading.app, um app de produtividade.
Seja direto, prático e acolhedor — como uma amiga organizada que ajuda a priorizar o dia.
Use linguagem informal em português brasileiro. Máximo 3-4 parágrafos curtos.
Nunca use bullet points com hífens longos — prefira listas curtas e respostas conversacionais.

{context}""",
            messages=clean_messages
        )

        reply = response.content[0].text
        return jsonify({"reply": reply})

    except Exception as e:
        print(f"[ERRO] API Anthropic: {e}")
        return jsonify({"error": "Erro ao chamar a IA. Tente novamente."}), 500



# ── Health check ───────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    """Confirma que o servidor tá de pé. Útil pra monitoramento."""
    api_key_ok = bool(os.getenv("ANTHROPIC_API_KEY"))
    return jsonify({
        "status": "ok",
        "api_key_configured": api_key_ok
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    print(f"\n✦ loading.app backend rodando em http://localhost:{port}")
    print("  Pressione Ctrl+C para parar\n")
    app.run(debug=debug, port=port, host="0.0.0.0")
