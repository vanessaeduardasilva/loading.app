# loading.app — backend

Backend Flask que serve como proxy da API da Anthropic para o loading.app.

## Estrutura

```
loading-app-backend/
├── server.py           # servidor Flask
├── requirements.txt    # dependências Python
├── Procfile            # pra Railway/Render
├── .env.example        # modelo do .env
├── .gitignore
└── static/
    └── loading-app.html  # frontend
```

## Rodar localmente

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Criar o .env
cp .env.example .env
# edite o .env e coloque sua ANTHROPIC_API_KEY

# 3. Rodar
python server.py
```

Acesse em: http://localhost:5000

---

## Deploy no Railway (recomendado — gratuito)

1. Crie uma conta em [railway.app](https://railway.app)
2. Crie um novo projeto → "Deploy from GitHub repo"
3. Conecte esse repositório
4. Vá em **Variables** e adicione:
   - `ANTHROPIC_API_KEY` = sua chave
   - `FLASK_ENV` = `production`
5. Railway detecta o `Procfile` e faz o deploy automaticamente
6. Copie a URL gerada (ex: `https://loading-app-production.up.railway.app`)

---

## Deploy no Render (alternativa gratuita)

1. Crie conta em [render.com](https://render.com)
2. New → **Web Service** → conecte o repositório
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn server:app --bind 0.0.0.0:$PORT`
5. Adicione a variável `ANTHROPIC_API_KEY` nas Environment Variables

---

## API

### `POST /chat`
```json
{
  "messages": [
    { "role": "user", "content": "organize meu dia" }
  ],
  "context": "Alta prioridade: reunião 14h..."
}
```
Resposta:
```json
{ "reply": "Vamos lá! Pelo contexto..." }
```

### `GET /health`
```json
{ "status": "ok", "api_key_configured": true }
```

---

## Rate limiting

Por padrão: **15 mensagens por IP por minuto**.
Mude com a variável `RATE_LIMIT_PER_MINUTE` no `.env`.
