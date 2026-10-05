# BBT-UFV ChatBot

Chatbot para a Biblioteca Central da UFV. Arquitetura com núcleo de resposta desacoplado do canal de comunicação.

## Estrutura

```
api/
├── app/
│   ├── core/           # infra compartilhada (auth, database, models, dtos, utils, audit)
│   ├── bot/            # núcleo do bot (árvore de decisão: fluxo + responder)
│   ├── whatsapp/       # canal WhatsApp (webhook + API client)
│   └── dashboard/      # painel das bibliotecárias (auth + CRUDs)
├── migrations/         # migrações do banco (Flask-Migrate)
├── tests/              # testes (unittest)
├── insomnia_collection.json     # collection para importar no Insomnia
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
| POST | `/api/dashboard/auth/register` | Registra usuário (1º vira ADMIN; depois só ADMIN) |
| POST | `/api/dashboard/auth/login` | Login (email + senha) |
| GET | `/api/dashboard/auth/me` | Dados do usuário autenticado |
| GET/POST | `/api/dashboard/usuarios/` | Listar/criar usuários (ADMIN) |
| GET/PATCH/DELETE | `/api/dashboard/usuarios/<id>` | Consultar/editar/desativar (ADMIN) |
| GET/POST | `/api/dashboard/categorias/` | Listar/criar categorias |
| GET/PATCH/DELETE | `/api/dashboard/categorias/<id>` | Consultar/editar/remover |
| GET/POST | `/api/dashboard/conteudos/` | Listar/criar respostas |
| GET/PATCH/DELETE | `/api/dashboard/conteudos/<id>` | Consultar/editar/desativar |
| GET/POST | `/api/dashboard/fluxo/` | Listar/criar nós da árvore |
| GET/PATCH/DELETE | `/api/dashboard/fluxo/<id>` | Consultar/editar/desativar nó |
| GET | `/api/dashboard/config/` | Listar textos fixos |
| GET/PUT/DELETE | `/api/dashboard/config/<chave>` | Consultar/definir/remover |
| GET | `/api/dashboard/atendimentos/` | Fila de atendimentos |
| GET/PATCH | `/api/dashboard/atendimentos/<id>` | Consultar/atualizar (assumir/fechar) |
| GET/POST | `/api/dashboard/atendimentos/<id>/mensagens` | Histórico/mensagem do atendimento |
| GET/POST | `/api/dashboard/feedback/` | Avaliações (ADMIN lista) |
| GET | `/api/dashboard/logs/` | Auditoria (ADMIN) |

> Escrita na árvore/conteúdo/categorias/config é restrita a ADMIN; ATENDENTE tem leitura. Atendimentos são restritos ao próprio atendente (ou sem dono). A autorização é aplicada no Flask (`core/auth/guards.py`); a RLS do Supabase atua como defesa adicional.

## Collection do Insomnia

O arquivo `api/insomnia_collection.json` contém todas as rotas organizadas por grupo, com ambiente e exemplos de corpo.

**Como importar:**
1. Abra o Insomnia → **Create** → **Import From** → **File**.
2. Selecione `api/insomnia_collection.json`.
3. Selecione o ambiente **Base Environment** e ajuste `base_url` (ex.: `http://localhost:5000`).
4. Faça `Auth > Login`, copie o `token` retornado e cole na variável `token` do ambiente (ou, em cada request, use o campo *Bearer Token*).

Variáveis de ambiente disponíveis: `base_url`, `token`, `usuario_id`, `categoria_id`, `conteudo_id`, `no_id`, `atendimento_id`, `chave`, `wa_id`.

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

O bot é uma árvore de decisão estática (`no_fluxo`), sem IA. O backend recebe o `id` do nó (botão/lista), consulta o Supabase e:

| Tipo do nó | Ação |
|---|---|
| `MENU` | Envia os filhos (`no_fluxo` com `parent_id` = nó) como botões (≤3) ou lista (≤10) |
| `RESPOSTA` | Envia o texto do `conteudo` associado e pergunta se ajudou (feedback) |
| `ATENDENTE` | Cria um `atendimento` (status `ABERTO`) e encaminha para humano |

Texto livre sem atendimento aberto dispara o `config_bot.fallback` e reenvia o menu inicial (`parent_id` nulo). Código em `app/bot/fluxo.py` e `app/bot/responder.py`.

Os textos fixos vêm de `config_bot` e são editáveis no dashboard: `boas_vindas`, `fallback`, `menu_botao`, `atendente_msg` e os de feedback (`feedback_pergunta`, `feedback_obrigado`, `feedback_sim`, `feedback_nao`). Se uma chave não existir, o código usa um valor padrão.

| Chave | Padrão | Uso |
|---|---|---|
| `boas_vindas` | `Olá! Sou o assistente da Biblioteca. Escolha uma opção:` | Corpo do menu inicial |
| `fallback` | `Não entendi. Vou te mostrar o menu novamente.` | Texto livre sem atendimento aberto |
| `menu_botao` | `Ver opções` | Rótulo do botão da lista |
| `atendente_msg` | `Certo! Encaminhei seu caso para um atendente...` | Ao abrir um atendimento |
| `feedback_pergunta` | `Essa resposta te ajudou?` | Pergunta enviada após uma `RESPOSTA` |
| `feedback_obrigado` | `Obrigado pelo seu feedback!` | Confirmação após avaliar |
| `feedback_sim` | `Ajudou` | Rótulo do botão "útil" |
| `feedback_nao` | `Não ajudou` | Rótulo do botão "não útil" |

## Referência das rotas

Convenções: autenticação **Bearer JWT** (`Authorization: Bearer <token>`) nas rotas do dashboard; corpo JSON salvo indicação. Erros seguem `{"error": "..."}`.

### Health

| Rota | Auth | Descrição | Retorno |
|---|---|---|---|
| `GET /api/health` | — | Checa se a API está no ar. | `200 {"status": "ok"}` |

### Auth

| Rota | Auth | Corpo | Descrição | Retorno |
|---|---|---|---|---|
| `POST /api/dashboard/auth/register` | — (1º) / Bearer ADMIN (demais) | `{email, password, name?, perfil?}` | Cria usuário. O **primeiro** usuário do banco vira `ADMIN`; os seguintes exigem token de ADMIN e usam `perfil` (`ADMIN`/`ATENDENTE`, padrão `ATENDENTE`). | `201` / `400` / `403` / `409` |
| `POST /api/dashboard/auth/login` | — | `{email, password}` | Autentica e devolve `token` (JWT, 24h). | `200 {..., token}` / `401` |
| `GET /api/dashboard/auth/me` | Bearer | — | Dados do usuário autenticado (`id, email, name, perfil, ativo, created_at`). | `200` / `401` |

### Usuarios (ADMIN)

| Rota | Auth | Corpo/Parâmetros | Descrição | Retorno |
|---|---|---|---|---|
| `GET /api/dashboard/usuarios/` | Bearer ADMIN | — | Lista todos os usuários. | `200 [...]` |
| `POST /api/dashboard/usuarios/` | Bearer ADMIN | `{email, password, name?, perfil?}` | Cria usuário. | `201` / `400` / `409` |
| `GET /api/dashboard/usuarios/<id>` | Bearer ADMIN | — | Detalha um usuário. | `200` / `404` |
| `PATCH /api/dashboard/usuarios/<id>` | Bearer ADMIN | `{name?, ativo?, password?, perfil?}` | Atualiza campos. | `200` / `400` / `404` |
| `DELETE /api/dashboard/usuarios/<id>` | Bearer ADMIN | — | **Soft delete** (`ativo=false`). | `200` / `404` |

### Categorias

| Rota | Auth | Corpo | Descrição | Retorno |
|---|---|---|---|---|
| `GET /api/dashboard/categorias/` | Bearer | — | Lista categorias. | `200 [...]` |
| `GET /api/dashboard/categorias/<id>` | Bearer | — | Detalha uma categoria. | `200` / `404` |
| `POST /api/dashboard/categorias/` | Bearer ADMIN | `{nome, descricao?}` | Cria categoria. | `201` / `400` |
| `PATCH /api/dashboard/categorias/<id>` | Bearer ADMIN | `{nome?, descricao?}` | Atualiza categoria. | `200` / `404` |
| `DELETE /api/dashboard/categorias/<id>` | Bearer ADMIN | — | Remove categoria (**hard delete**). | `200` / `404` |

### Conteudos (respostas do bot)

| Rota | Auth | Corpo/Parâmetros | Descrição | Retorno |
|---|---|---|---|---|
| `GET /api/dashboard/conteudos/` | Bearer | query `categoria_id?`, `ativo?` | Lista respostas (filtros opcionais). | `200 [...]` |
| `GET /api/dashboard/conteudos/<id>` | Bearer | — | Detalha uma resposta. | `200` / `404` |
| `POST /api/dashboard/conteudos/` | Bearer ADMIN | `{categoria_id, titulo, texto, fonte?}` | Cria resposta; grava `created_by` e auditoria. | `201` / `400` / `409` |
| `PATCH /api/dashboard/conteudos/<id>` | Bearer ADMIN | `{titulo?, texto?, fonte?, categoria_id?, ativo?}` | Atualiza resposta. | `200` / `400` / `404` / `409` |
| `DELETE /api/dashboard/conteudos/<id>` | Bearer ADMIN | — | **Soft delete** (`ativo=false`). | `200` / `404` |

### Fluxo (árvore de decisão)

| Rota | Auth | Corpo/Parâmetros | Descrição | Retorno |
|---|---|---|---|---|
| `GET /api/dashboard/fluxo/` | Bearer | query `parent_id?`, `raiz?`, `ativo?` | Lista nós. `raiz=true` retorna só o menu inicial (`parent_id` nulo). | `200 [...]` |
| `GET /api/dashboard/fluxo/<id>` | Bearer | — | Detalha um nó. | `200` / `404` |
| `POST /api/dashboard/fluxo/` | Bearer ADMIN | `{titulo, tipo, parent_id?, conteudo_id?, ordem?}` | Cria nó. `tipo`: `MENU`/`RESPOSTA`/`ATENDENTE`; `RESPOSTA` exige `conteudo_id`; `titulo` ≤ 24. | `201` / `400` |
| `PATCH /api/dashboard/fluxo/<id>` | Bearer ADMIN | `{titulo?, tipo?, parent_id?, conteudo_id?, ordem?, ativo?}` | Atualiza nó (valida tipo/conteúdo/parent). | `200` / `400` / `404` |
| `DELETE /api/dashboard/fluxo/<id>` | Bearer ADMIN | — | **Soft delete** (`ativo=false`). | `200` / `404` |

### Config do bot (textos fixos)

| Rota | Auth | Corpo/Parâmetros | Descrição | Retorno |
|---|---|---|---|---|
| `GET /api/dashboard/config/` | Bearer | — | Lista chaves/valores. | `200 [...]` |
| `GET /api/dashboard/config/<chave>` | Bearer | — | Obtém uma chave (ex.: `boas_vindas`, `fallback`, `menu_botao`, `atendente_msg`, `feedback_pergunta`, `feedback_obrigado`, `feedback_sim`, `feedback_nao`). | `200` / `404` |
| `PUT /api/dashboard/config/<chave>` | Bearer ADMIN | `{valor}` | **Upsert**: cria ou atualiza a chave. | `200` / `400` |
| `DELETE /api/dashboard/config/<chave>` | Bearer ADMIN | — | Remove a chave. | `200` / `404` |

### Atendimentos

| Rota | Auth | Corpo/Parâmetros | Descrição | Retorno |
|---|---|---|---|---|
| `GET /api/dashboard/atendimentos/` | Bearer | — | ADMIN vê todos; ATENDENTE vê os seus e os sem dono. | `200 [...]` |
| `GET /api/dashboard/atendimentos/<id>` | Bearer | — | Detalha um atendimento. | `200` / `403` / `404` |
| `PATCH /api/dashboard/atendimentos/<id>` | Bearer | `{status?, assumir?}` | Muda `status` (`ABERTO`/`EM_ATENDIMENTO`/`FECHADO`); `assumir=true` vincula o atendente logado e põe `EM_ATENDIMENTO`. Ao fechar, grava `closed_at`. | `200` / `400` / `403` / `404` |
| `GET /api/dashboard/atendimentos/<id>/mensagens` | Bearer | — | Histórico de mensagens do atendimento. | `200 [...]` / `403` / `404` |
| `POST /api/dashboard/atendimentos/<id>/mensagens` | Bearer | `{texto}` | Cria mensagem (`remetente=ATENDENTE`) **e envia ao WhatsApp** do solicitante; a resposta inclui `enviado` (`true`/`false`). | `201` / `400` / `403` / `404` |

### Feedback

| Rota | Auth | Corpo/Parâmetros | Descrição | Retorno |
|---|---|---|---|---|
| `GET /api/dashboard/feedback/` | Bearer ADMIN | query `no_fluxo_id?` | Lista avaliações (filtro opcional). | `200 [...]` |
| `POST /api/dashboard/feedback/` | Bearer | `{no_fluxo_id, util?, comentario?}` | Registra avaliação manual. | `201` / `400` |

### Logs (ADMIN)

| Rota | Auth | Descrição | Retorno |
|---|---|---|---|
| `GET /api/dashboard/logs/` | Bearer ADMIN | Auditoria das ações administrativas (últimos 500). | `200 [...]` |

### WhatsApp Webhook

| Rota | Auth | Descrição | Retorno |
|---|---|---|---|
| `GET /api/whatsapp/webhook/` | — | Verificação do webhook pela Meta (`hub.mode`, `hub.verify_token`, `hub.challenge`). | `200 <challenge>` / `403` |
| `POST /api/whatsapp/webhook/` | — (assinatura `X-Hub-Signature-256` se `WHATSAPP_APP_SECRET` definido) | Recebe a mensagem. Texto livre → `fallback` + menu inicial; clique em botão/lista → navega na árvore, envia resposta + feedback, ou abre `atendimento`; com atendimento aberto, texto é gravado em `mensagem`. | `200 "OK"` / `400` / `401` |

## Testes

```bash
cd api && python -m unittest discover -s tests -t .
```

Os testes usam `unittest` e SQLite em memória (`tests/base.py`), sem tocar o banco real.