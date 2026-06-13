"""
server.py — Backend simples para o foco.app

Esse servidor faz uma coisa só: receber a mensagem do frontend,
mandar pra API da Anthropic e devolver a resposta.

Por que precisamos disso?
    A API da Anthropic exige uma chave secreta (API key).
    Se você colocar essa chave direto no HTML, qualquer um
    que abrir o código-fonte vai ver ela — e aí qualquer pessoa
    pode usar sua conta. O backend guarda a chave no servidor,
    longe dos olhos de quem usa o app.

Como rodar:
    1. pip install flask flask-cors anthropic python-dotenv
    2. Crie um arquivo .env com sua API key (veja abaixo)
    3. python server.py
    4. Abra o foco-app.html no navegador
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
# (a API key fica lá, nunca no código)
load_dotenv()

app = Flask(__name__)

# Libera o frontend pra chamar esse servidor
# (CORS = Cross-Origin Resource Sharing — sem isso o navegador bloqueia)
CORS(app)

# Inicializa o cliente da Anthropic com a chave do .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


@app.route("/chat", methods=["POST"])
def chat():
    """
    Endpoint principal — recebe a mensagem e devolve a resposta da IA.

    Espera receber um JSON assim:
        {
            "message": "o que começo primeiro?",
            "context": "Tarefas alta: reunião, deploy..."
        }

    Devolve:
        {
            "reply": "Começa pela reunião porque..."
        }
    """
    data = request.get_json()

    # Valida se veio mensagem
    if not data or not data.get("message"):
        return jsonify({"error": "Mensagem não informada"}), 400

    message = data["message"]
    context = data.get("context", "Nenhuma tarefa cadastrada ainda.")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=f"""Você é um assistente de gestão de tempo pessoal integrado a um app de produtividade.
Seja direto, prático e acolhedor — como uma amiga organizada que te ajuda a priorizar o dia.
Use linguagem informal em português brasileiro.
Nunca use bullet points com hífens longos — prefira listas curtas e respostas conversacionais.
Máximo 3-4 parágrafos curtos.

{context}""",
            messages=[
                {"role": "user", "content": message}
            ]
        )

        reply = response.content[0].text
        return jsonify({"reply": reply})

    except Exception as e:
        print(f"Erro na API: {e}")
        return jsonify({"error": "Erro ao chamar a IA. Tente novamente."}), 500


@app.route("/health", methods=["GET"])
def health():
    """Rota de verificação — só pra confirmar que o servidor está rodando."""
    return jsonify({"status": "ok", "message": "servidor rodando!"})


if __name__ == "__main__":
    # debug=True → reinicia sozinho quando você salva o arquivo
    # Mude pra False quando for colocar em produção
    print("\n🌿 foco.app backend rodando em http://localhost:5000")
    print("   Pressione Ctrl+C para parar\n")
    app.run(debug=True, port=5000)
