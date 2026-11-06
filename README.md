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
├── db/
│   ├── chatbot.db              # banco SQLite pronto e populado (schema v1)
│   ├── sqlite_schema.sql       # script-fonte do banco (versão 0 + seed)
│   └── migrations/NNN_*.sql    # ajustes aplicados por cima (PRAGMA user_version)
├── tests/              # testes (unittest), rodam contra cópias do chatbot.db
├── insomnia_collection.json     # collection para importar no Insomnia
├── .env                # configuração local
├── Dockerfile / docker-compose.yml  # um container + volume para o banco
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

> Escrita na árvore/conteúdo/categorias/config é restrita a ADMIN; ATENDENTE tem leitura. Atendimentos são restritos ao próprio atendente (ou sem dono). O SQLite não tem controle de acesso: toda a autorização é aplicada no Flask (`core/auth/guards.py`).

## Testar os endpoints

Com o servidor no ar, o script `scripts/testar_endpoints.py` percorre todas as rotas (76 verificações: status esperado, permissões de ADMIN e ATENDENTE, validações da árvore, webhook assinado, ciclo completo de um atendimento) e mostra um resumo no fim:

```bash
cd api
cp db/chatbot.db /tmp/teste.db                       # sempre numa cópia do banco
DB_PATH=/tmp/teste.db WHATSAPP_APP_SECRET=segredo-teste flask --app run.py run --port 5000 &
python scripts/testar_endpoints.py --app-secret segredo-teste
```

Se o banco ainda não tem usuários, o script cria o primeiro ADMIN com `--admin-email`/`--admin-password` (padrão `admin@ufv.br`/`senha-admin-teste`); se já tem, passe as credenciais de um ADMIN existente. Ele cria registros de teste e os desativa no fim, por isso recusa URLs que não sejam localhost (use `--force` só em homologação). Sai com código 1 se alguma verificação falhar, então também serve em CI.

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
| **python-dotenv** | 1.1.0 | Carrega `.env` |
| **bcrypt** | 4.3.0 | Hash de senhas |
| **PyJWT** | 2.13.0 | Tokens JWT |
| **cryptography** | 44.0.0 | Criptografia (Fernet) para dados sensíveis |
| **requests** | 2.32.3 | Chamadas HTTP para API do WhatsApp |
| **gunicorn** | 23.0.0 | Servidor de produção (1 worker, várias threads) |

O banco é SQLite (módulo `sqlite3` da biblioteca padrão), sem driver extra. Python 3.12 ou mais novo.

## Setup rápido

```bash
cd api
cp .env.example .env              # ajuste JWT_SECRET, SECRET_KEY e as credenciais do WhatsApp
pip install -r requirements.txt
flask --app run.py db upgrade     # aplica migrações pendentes no db/chatbot.db (se houver)
flask --app run.py run --debug
```

Depois crie o primeiro ADMIN com `POST /api/dashboard/auth/register` (o primeiro usuário do banco vira ADMIN automaticamente).

Com Docker: `docker compose up -d --build`. Na primeira subida o container copia o `db/chatbot.db` para o volume `chatbot-data` e, a cada subida, roda `flask db upgrade` antes do gunicorn.

## Banco de dados (SQLite)

O backend abre o arquivo indicado em `DB_PATH` (padrão `api/db/chatbot.db`). Em toda conexão ele liga `PRAGMA foreign_keys`, `busy_timeout` e o modo WAL (`core/database/extensions.py`). Os models em `core/models/` espelham o `sqlite_schema.sql` coluna a coluna; o teste `tests/test_schema.py` falha se os dois divergirem.

| Comando | Descrição |
|---------|-----------|
| `flask db init` | Cria o banco do zero a partir do `sqlite_schema.sql` + migrações (`--force` recria) |
| `flask db upgrade` | Aplica as migrações de `db/migrations/` maiores que o `PRAGMA user_version` |
| `flask db version` | Versão do schema no arquivo e a esperada pelo código |
| `flask db backup <destino>` | Cópia consistente pela API de backup do SQLite (pode rodar com o app no ar) |

Para mudar o schema: crie `db/migrations/002_descricao.sql` terminando com `PRAGMA user_version = 2;`, ajuste os models e `SCHEMA_VERSION` em `extensions.py`, rode `flask db upgrade` e os testes. O `/api/health` responde 503 se o arquivo estiver numa versão diferente da esperada.

Cuidados de implantação: manter o arquivo em volume persistente, nunca em pasta de rede (NFS/SMB), e rodar um único processo do backend (`--workers 1`) escrevendo nele. Agende `flask db backup` e guarde a cópia fora do servidor.

## Webhook

No painel da Meta, configure o webhook para:

```
https://seu-dominio/api/whatsapp/webhook/
```

Token de verificação: `bbt_verify` (ou o que estiver em `WHATSAPP_VERIFY_TOKEN`).

A assinatura `X-Hub-Signature-256` é obrigatória: sem `WHATSAPP_APP_SECRET` o webhook responde 503. Só em desenvolvimento local use `WHATSAPP_REQUIRE_SIGNATURE=false`.

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

O bot é uma árvore de decisão estática (`no_fluxo`), sem IA. O backend recebe o `id` do nó (botão/lista), consulta o `chatbot.db` e:

| Tipo do nó | Ação |
|---|---|
| `MENU` | Envia os filhos ativos (`parent_id` = nó) e, em submenus, a opção **Voltar** (vai ao menu pai) |
| `RESPOSTA` | Envia o texto do `conteudo` e os botões **Ajudou / Não ajudou / Menu inicial** |
| `ATENDENTE` | Abre um `atendimento` (`ABERTO`) e grava uma mensagem `BOT` com a opção de origem. Se o aluno já tem atendimento aberto, só avisa (não duplica) |

Botões só são usados quando cabem: até 3 opções **e** todos os títulos com até 20 caracteres. Caso contrário o menu vai como lista (até 10 linhas, títulos até 24), então nenhum título é cortado. Nós `RESPOSTA` cujo conteúdo está desativado não aparecem.

Texto livre sem atendimento aberto dispara o `config_bot.fallback` e reenvia o menu inicial; com atendimento aberto, o texto é gravado em `mensagem` para a atendente. Mensagens repetidas pela Meta (mesmo `id`) são ignoradas, e um erro ao processar uma mensagem é registrado no log sem devolver 500 (o que faria a Meta reenviar). Código em `app/bot/` e `app/whatsapp/webhook/service.py`.

Os textos fixos vêm de `config_bot` e são editáveis no dashboard. Todas as chaves abaixo já existem no `chatbot.db`; se alguma for removida, o código usa o valor padrão.

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
| `voltar` | `Voltar` | Opção que volta ao menu anterior |
| `menu_inicial` | `Menu inicial` | Botão que volta ao início |
| `atendente_ja_aberto` | `Seu atendimento já está aberto...` | Aluno pede atendente com um já aberto |

## Referência das rotas

Convenções: autenticação **Bearer JWT** (`Authorization: Bearer <token>`) nas rotas do dashboard; corpo JSON salvo indicação. Erros seguem `{"error": "..."}`. Ids são inteiros. Datas saem em ISO 8601 com fuso UTC (`2026-11-05T14:03:22.517000+00:00`). E-mails são comparados sem diferenciar maiúsculas.

### Health

| Rota | Auth | Descrição | Retorno |
|---|---|---|---|
| `GET /api/health` | — | Checa a API e a versão do schema do banco. | `200 {"status": "ok", "schema_version": 1, ...}` / `503` |

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
| `DELETE /api/dashboard/categorias/<id>` | Bearer ADMIN | — | Remove categoria (**hard delete**). Recusa com `409` se houver conteúdos nela. | `200` / `404` / `409` |

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
| `POST /api/dashboard/fluxo/` | Bearer ADMIN | `{titulo, tipo, parent_id?, conteudo_id?, ordem?, ativo?}` | Cria nó. Regras abaixo. | `201` / `400` |
| `PATCH /api/dashboard/fluxo/<id>` | Bearer ADMIN | `{titulo?, tipo?, parent_id?, conteudo_id?, ordem?, ativo?}` | Atualiza nó. Valida o estado final do nó, não só os campos enviados. | `200` / `400` / `404` |
| `DELETE /api/dashboard/fluxo/<id>` | Bearer ADMIN | — | **Soft delete** (`ativo=false`). | `200` / `404` |

Regras da árvore (todas devolvem `400` com a mensagem em `error`): `titulo` com 1 a 24 caracteres; `RESPOSTA` exige `conteudo_id` existente e os outros tipos não têm conteúdo (ao mudar de `RESPOSTA` para outro tipo o `conteudo_id` é limpo); `parent_id` precisa ser um nó `MENU` e não pode ser o próprio nó nem um descendente dele (sem ciclos); um `MENU` com opções ativas não muda de tipo; no máximo 10 opções ativas no menu inicial e 9 em cada submenu (a 10ª linha é o "Voltar").

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
| `PATCH /api/dashboard/atendimentos/<id>` | Bearer | `{status?, assumir?}` | Muda `status` (`ABERTO`/`EM_ATENDIMENTO`/`FECHADO`); `assumir=true` vincula o atendente logado e põe `EM_ATENDIMENTO`. Ao fechar, grava `closed_at`; ao reabrir, limpa. | `200` / `400` / `403` / `404` |
| `GET /api/dashboard/atendimentos/<id>/mensagens` | Bearer | — | Histórico de mensagens do atendimento. | `200 [...]` / `403` / `404` |
| `POST /api/dashboard/atendimentos/<id>/mensagens` | Bearer | `{texto}` | Cria mensagem (`remetente=ATENDENTE`) **e envia ao WhatsApp** do solicitante; a resposta inclui `enviado` (`true`/`false`). | `201` / `400` / `403` / `404` |

### Feedback

| Rota | Auth | Corpo/Parâmetros | Descrição | Retorno |
|---|---|---|---|---|
| `GET /api/dashboard/feedback/` | Bearer ADMIN | query `no_fluxo_id?` | Lista avaliações (filtro opcional). | `200 [...]` |
| `POST /api/dashboard/feedback/` | Bearer | `{no_fluxo_id, util, comentario?}` | Registra avaliação manual (`util` obrigatório: `true`/`false`). | `201` / `400` |

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

Cada teste roda numa **cópia** do `db/chatbot.db` real (`tests/base.py`): mesmo schema, mesma árvore e mesmos textos de produção. O arquivo original não é alterado. `tests/test_schema.py` confere que o `sqlite_schema.sql` + migrações recriam exatamente o `chatbot.db` e que os models batem com as tabelas.