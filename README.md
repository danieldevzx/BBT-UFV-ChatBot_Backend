# BBT-UFV ChatBot Backend

Sistema de chatbot para WhatsApp da **Biblioteca Universitária (BBT-UFV)**.  
Dividido em dois módulos independentes: **ChatBot-BBT** (prova de conceito CLI) e **api/** (REST API em Flask).

---

## Repositório

```
BBT-UFV-ChatBot_Backend/
├── README.md
├── LICENSE
├── ChatBot-BBT/              ← Prova de conceito do bot (CLI, intocado)
│   ├── app/
│   │   ├── agent.py          #   OpenAI (gpt-5) com base de conhecimento
│   │   ├── dtree_test.py     #   Árvore de decisão (regras offline)
│   │   ├── knowledge_base.py #   Carrega data/biblioteca.txt
│   │   ├── main.py           #   CLI do bot com OpenAI
│   │   └── respostas.py      #   Respostas fixas da árvore de decisão
│   ├── data/biblioteca.txt   # Base de conhecimento texto
│   └── .gitignore
│
└── api/                      ← REST API (Flask, Feature-Based)
    ├── app/
    │   ├── __init__.py       # create_app, registra blueprints
    │   ├── config.py         # Configurações via .env
    │   ├── extensions.py     # SQLAlchemy instance
    │   ├── core/             # Infraestrutura compartilhada
    │   │   ├── health/       # GET /api/health
    │   │   ├── models/       # ORM (SQLAlchemy)
    │   │   │   ├── user/         # User, UserData
    │   │   │   └── conversation/ # Conversation, Message
    │   │   ├── dtos/         # Dataclasses (um arquivo por DTO)
    │   │   │   ├── register_request_dto.py
    │   │   │   ├── login_request_dto.py
    │   │   │   ├── auth_response_dto.py
    │   │   │   ├── user_response_dto.py
    │   │   │   ├── error_response_dto.py
    │   │   │   ├── result_dto.py
    │   │   │   ├── send_request_dto.py
    │   │   │   ├── message_response_dto.py
    │   │   │   ├── conversation_response_dto.py
    │   │   │   └── webhook_response_dto.py
    │   │   └── utils/
    │   │       └── crypto.py # Criptografia Fernet
    │   └── features/         # Regras de negócio (Feature-Based)
    │       ├── dashboard/    # Módulo do bibliotecário
    │       │   ├── auth/     #   register, login, me
    │       │   ├── archive/  #   (placeholder) gestão de arquivos
    │       │   └── users/    #   (placeholder) gestão de usuários
    │       └── bot/          # Módulo de comunicação WhatsApp
    │           ├── whatsapp.py      # Cliente Meta Cloud API
    │           ├── responder.py     # Árvore de decisão + respostas fixas
    │           ├── webhook/         # GET/POST /webhook
    │           ├── messages/        # POST /send
    │           └── conversations/   # GET /, GET /<id>
    ├── run.py                # Entry point
    ├── .env / .env.example
    ├── docker-compose.yml    # PostgreSQL
    └── requirements.txt
```

---

## ChatBot-BBT (CLI)

Prova de conceito com dois modos de operação — **nada foi alterado**:

```bash
cd ChatBot-BBT

# Modo offline — árvore de decisão por palavra-chave
python app/dtree_test.py

# Modo com IA — OpenAI (gpt-5) + base de conhecimento
python app/main.py
```

---

## API (REST)

### Endpoints

| Método | Rota | Módulo | Descrição |
|---|---|---|---|
| GET | `/api/health` | `core/health` | `{"status": "ok"}` |
| POST | `/api/dashboard/auth/register` | `dashboard/auth` | Criar conta (`wa_id`, `password`, `name`) |
| POST | `/api/dashboard/auth/login` | `dashboard/auth` | Autenticar, retorna JWT |
| GET | `/api/dashboard/auth/me` | `dashboard/auth` | Dados do usuário autenticado |
| GET | `/api/dashboard/archive/` | `dashboard/archive` | Placeholder |
| GET | `/api/dashboard/users/` | `dashboard/users` | Placeholder |
| GET | `/api/bot/webhook/` | `bot/webhook` | Verificação Meta Cloud API |
| POST | `/api/bot/webhook/` | `bot/webhook` | Receber mensagem + responder automaticamente |
| POST | `/api/bot/send` | `bot/messages` | Enviar mensagem via WhatsApp (autenticado) |
| GET | `/api/bot/conversations/` | `bot/conversations` | Listar conversas (autenticado) |
| GET | `/api/bot/conversations/\<id\>` | `bot/conversations` | Histórico de mensagens (autenticado) |

---

## Modelos (ORM)

### User
| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `VARCHAR(36)` PK | UUID v7 |
| `wa_id` | `VARCHAR(20)` UNIQUE | ID do WhatsApp |
| `name` | `VARCHAR(200)` | Nome |
| `password_hash` | `VARCHAR(256)` | Hash bcrypt |
| `created_at` | `DATETIME` | Timestamp |
| `updated_at` | `DATETIME` | Timestamp |
| `deleted_at` | `DATETIME` | Soft delete |

### UserData
| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `VARCHAR(36)` PK | UUID v7 |
| `user_id` | `VARCHAR(36)` FK → users | Relação 1:1 |
| `email` | `TEXT` (encrypted) | Email criptografado (Fernet) |
| `phone` | `TEXT` (encrypted) | Telefone criptografado (Fernet) |
| `bio` | `TEXT` (encrypted) | Bio criptografada (Fernet) |
| `created_at` / `updated_at` / `deleted_at` | Timestamps | |

### Conversation
| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `VARCHAR(36)` PK | UUID v7 |
| `wa_id` | `VARCHAR(20)` | Usuário do WhatsApp |
| `status` | `VARCHAR(20)` | `active` (bot ou human) |
| `created_at` / `updated_at` / `deleted_at` | Timestamps | |

### Message
| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `VARCHAR(36)` PK | UUID v7 |
| `conversation_id` | `VARCHAR(36)` FK → conversations | |
| `role` | `VARCHAR(10)` | `user`, `bot`, `staff` |
| `content` | `TEXT` | Conteúdo da mensagem |
| `created_at` / `deleted_at` | Timestamps | |

---

## Segurança

### Soft delete
Todas as entidades têm `deleted_at` (DateTime, nullable).  
As queries nos services filtram com `.filter_by(deleted_at=None)`, garantindo que dados deletados logicamente não sejam expostos.

### Autenticação
- **bcrypt** — `password_hash` armazenado com `bcrypt.hashpw` + salt automático
- **JWT (HS256)** — tokens com 24h de expiração, assinados com `JWT_SECRET`
- Bearer token exigido em todas as rotas de listagem/envio

### Criptografia de dados pessoais
`email`, `phone`, `bio` do `UserData` são criptografados com **Fernet (AES-256-CBC + HMAC-SHA256)** via `cryptography`.  
A chave `ENCRYPTION_KEY` é configurada no `.env` — gere com:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

O `TypeDecorator` customizado (`EncryptedText`) cifra/decifra automaticamente na camada ORM — o service lê e escreve texto plano, o banco armazena cifrado.

---

## Setup

```bash
# Dependências
pip install -r api/requirements.txt

# PostgreSQL
docker compose -f api/docker-compose.yml up -d

# Config
cp api/.env.example api/.env
# Edite api/.env com suas credenciais e gere a ENCRYPTION_KEY

# Executar
cd api && python run.py   # → http://localhost:5000
```

---

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `DB_HOST` | Host PostgreSQL | `localhost` |
| `DB_PORT` | Porta PostgreSQL | `5432` |
| `DB_NAME` | Nome do banco | `bbt_bot` |
| `DB_USER` | Usuário do banco | `bbt` |
| `DB_PASSWORD` | Senha do banco | `bbt_secret` |
| `JWT_SECRET` | Chave JWT (mín. 32 chars em prod) | `dev-secret-key...` |
| `SECRET_KEY` | Chave Flask | `dev` |
| `WHATSAPP_TOKEN` | Token Meta Cloud API | — |
| `WHATSAPP_PHONE_NUMBER_ID` | ID do número de telefone | — |
| `WHATSAPP_VERIFY_TOKEN` | Token de verificação webhook | `bbt_verify` |
| `WHATSAPP_APP_SECRET` | App Secret Meta | — |
| `ENCRYPTION_KEY` | Chave Fernet (criptografia dados pessoais) | — |

---

## Arquitetura

### Separação core / features

```
app/core/       → Infraestrutura: models, dtos, health, crypto
app/features/   → Regras de negócio: dashboard, bot
```

As features nunca importam `core/models` e `core/dtos` — nunca dependem de implementação concreta de infraestrutura.

### Padrão de cada submódulo

```
features/<dominio>/<submodulo>/
├── __init__.py   → Blueprint
├── routes.py     → Controller: valida input, chama service, retorna resposta
└── service.py    → Regras de negócio + acesso a banco
```

**Routes nunca têm lógica de negócio.**  
**Services nunca lidam com request/response HTTP.**

### Fluxo de dados

```
Requisição → Blueprint → Routes (parse) → Service (regras) → DTO (resposta) → JSON
```

---

## Testes rápidos

```bash
cd api

# Registrar
curl -X POST http://localhost:5000/api/dashboard/auth/register \
  -H "Content-Type: application/json" \
  -d '{"wa_id":"5511999999999","password":"123456","name":"Admin"}'

# Login
curl -X POST http://localhost:5000/api/dashboard/auth/login \
  -H "Content-Type: application/json" \
  -d '{"wa_id":"5511999999999","password":"123456"}'

# Saúde
curl http://localhost:5000/api/health
```

---

## Licença

Este projeto é parte de um trabalho acadêmico da **Universidade Federal de Viçosa (UFV)**.