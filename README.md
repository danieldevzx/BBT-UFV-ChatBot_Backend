# BBT-UFV ChatBot

Chatbot para a Biblioteca Central da UFV. Arquitetura com núcleo de resposta desacoplado do canal de comunicação.

## Estrutura

```
api/
├── app/
│   ├── core/           # infra compartilhada (database, models, dtos, utils)
│   ├── bot/            # núcleo puro do bot (gerar_resposta)
│   ├── whatsapp/       # canal WhatsApp (webhook + API client)
│   └── dashboard/      # painel das bibliotecárias (auth + stubs)
├── migrations/         # migrações do banco (Flask-Migrate)
├── .env                # configuração local
├── docker-compose.yml  # PostgreSQL
├── requirements.txt
└── run.py              # ponto de entrada
```

## Rotas

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/health` | Health check |
| GET | `/api/whatsapp/webhook/` | Verificação do webhook (Meta) |
| POST | `/api/whatsapp/webhook/` | Recebe mensagens do WhatsApp |
| POST | `/api/dashboard/auth/register` | Registrar bibliotecária |
| POST | `/api/dashboard/auth/login` | Login |
| GET | `/api/dashboard/auth/me` | Dados do usuário autenticado |
| GET | `/api/dashboard/archive/` | Listar arquivos (TODO) |
| GET | `/api/dashboard/users/` | Listar usuários (TODO) |

## Dependências

| Pacote | Versão | Função |
|--------|--------|--------|
| **Flask** | 3.1.1 | Framework web |
| **Flask-SQLAlchemy** | 3.1.1 | ORM — models e banco |
| **Flask-Migrate** | 4.1.0 | Migrações (Alembic) |
| **python-dotenv** | 1.1.0 | Carrega `.env` |
| **bcrypt** | 4.3.0 | Hash de senhas |
| **PyJWT** | 2.13.0 | Tokens JWT |
| **psycopg2-binary** | 2.9.10 | Driver PostgreSQL |
| **cryptography** | 44.0.0 | Criptografia (Fernet) para dados sensíveis |
| **requests** | 2.32.3 | Chamadas HTTP para API do WhatsApp |

## Setup rápido

```bash
# 1. Banco
docker compose up -d

# 2. Variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais do WhatsApp

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Rodar migrações
flask db upgrade

# 5. Iniciar
flask run --debug
```

## Migrações (Flask-Migrate)

O banco é versionado com Alembic via Flask-Migrate. As migrações ficam em `api/migrations/versions/`.

| Comando | Descrição |
|---------|-----------|
| `flask db upgrade` | Aplica todas as pendentes |
| `flask db downgrade` | Desfaz a última migração |
| `flask db migrate -m "descricao"` | Gera nova migração após alterar models |
| `flask db history` | Histórico de migrações |
| `flask db current` | Mostra a migração atual do banco |

```bash
# Após modificar um model, gere e aplique:
flask db migrate -m "descricao da alteracao"
flask db upgrade
```

## Webhook

No painel da Meta, configure o webhook para:

```
https://seu-dominio/api/whatsapp/webhook/
```

Token de verificação: `bbt_verify` (ou o que estiver em `WHATSAPP_VERIFY_TOKEN`).

### Teste local com ngrok

A Meta exige HTTPS e um URL público — o ngrok cria um túnel para seu servidor local:

```bash
# 1. Instale o ngrok: https://ngrok.com/download

# 2. Inicie o servidor Flask
flask run --debug

# 3. Em outro terminal, exponha a porta 5000
ngrok http 5000

# 4. Copie a URL gerada (ex: https://abc123.ngrok.io) e cole no painel da Meta
#    em Callback URL: https://abc123.ngrok.io/api/whatsapp/webhook/
```

> ⚠️ **Apenas para desenvolvimento local.** Em produção, use o domínio real do servidor com HTTPS configurado (ex: `https://meudominio.com/api/whatsapp/webhook/`). Não precisa de ngrok.
>
> O ngrok gera uma nova URL a cada execução no plano gratuito. Sempre que reiniciar, atualize o painel da Meta.

### Formato esperado do número

O `wa_id` enviado pela Meta vem em dígitos puros com código do país (ex: `553199456489`). A API rejeita números com `+`, espaços ou traços — a normalização é feita automaticamente por `normalize_wa_id()` em `core/utils/wa_utils.py`.

### Lista de permissão (Meta)

No plano de teste do WhatsApp Cloud API, você precisa adicionar os números de telefone dos destinatários no dashboard do Meta Business → WhatsApp → Configuração → **Números de telefone permitidos**. Use o formato exato de dígitos que aparece no `from` do payload do webhook.

## Regras de resposta

A função `gerar_resposta(texto)` em `app/bot/responder.py` usa identificação por palavra-chave:

| Palavra-chave | Intenção |
|---|---|
| `multa` | Informações sobre multas |
| `renovar`, `renovação` | Renovação de livros |
| `acervo`, `livro`, `pergamum` | Pesquisa no acervo |
| `horário`, `horario`, `abre`, `fecha` | Horários e contatos |
| (outros) | Resposta padrão "desconhecido" |