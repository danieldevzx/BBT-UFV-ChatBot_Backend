# Integração backend ↔ chatbot.db (SQLite)

O backend foi escrito para PostgreSQL com schema próprio (Alembic). Esta
alteração liga o backend ao `chatbot.db` descrito no Relatório Geral, que
passa a ser a fonte da verdade. Todos os 56 testes rodam contra cópias do
banco real.

## O que mudou

**Conexão e schema**
- `config.py`: URI de PostgreSQL → `sqlite:///{DB_PATH}` (padrão `api/db/chatbot.db`).
- `extensions.py`: `PRAGMA foreign_keys = ON`, `busy_timeout`, WAL e `synchronous=NORMAL` em toda conexão.
- Flask-Migrate/Alembic removidos (a migração inicial criava um schema diferente e falhava com `table categoria already exists`). No lugar: `flask db init | upgrade | version | backup`, usando `db/sqlite_schema.sql` + `db/migrations/NNN_*.sql` e o `PRAGMA user_version`.
- `db/migrations/001_ajustes_integracao.sql` (já aplicada no `db/chatbot.db`): WAL, índices, e-mail `COLLATE NOCASE`, trigger de `updated_at`, chaves de `config_bot` que o backend usa (`feedback_*`, `voltar`, `menu_inicial`, `atendente_ja_aberto`) e `user_version = 1`.

**Models alinhados ao banco**
- `usuario.id`: UUID em texto → INTEGER (e as FKs em `atendimento`, `log`, `conteudo.created_by`). Remove o `uuid7`, que só existe no Python 3.14.
- Coluna `password_hash` mapeada para `senha_hash`.
- Datas em TEXT ISO 8601 com `Z` (`IsoDateTime`), o mesmo formato do seed; antes o backend gravava outro formato e sem fuso.
- `feedback.util` NOT NULL e `conteudo.categoria_id` opcional, como no banco.

**Correções de comportamento**
- JWT: `sub` como string e id convertido de volta para inteiro; rotas `/usuarios/<int:id>`.
- E-mail normalizado (minúsculas, sem espaços) no cadastro e no login.
- Editor da árvore valida o estado final do nó: sem ciclos, pai precisa ser MENU, MENU com filhos não muda de tipo, troca de tipo limpa/exige `conteudo_id`, limite de 10 opções na raiz e 9 nos submenus. Antes, vários casos davam erro 500 no CHECK do banco.
- Categoria com conteúdos não é apagada (409); antes deixava conteúdos órfãos.
- Feedback sem `util` devolve 400 em vez de 500.
- Reabrir atendimento limpa `closed_at`.

**Bot / WhatsApp**
- Opção **Voltar** nos submenus e **Menu inicial** depois de cada resposta e do feedback (seção 3.1 do relatório).
- Botões só quando todos os títulos cabem em 20 caracteres; senão, lista. Antes "Horário de funcionamento" e "Problema no Nada Consta" eram cortados.
- Não abre atendimento duplicado; registra uma mensagem BOT com a opção de origem.
- RESPOSTA com conteúdo desativado some do menu.
- Mensagens repetidas pela Meta são ignoradas; erro numa mensagem não devolve 500.
- Assinatura do webhook obrigatória (503 sem `WHATSAPP_APP_SECRET`, a menos que `WHATSAPP_REQUIRE_SIGNATURE=false`).

**Infra**
- `Dockerfile` + `docker-compose.yml` com um container e volume persistente para o banco; gunicorn com 1 worker.
- `requirements.txt` sem `psycopg2` e `flask-migrate`, com `gunicorn`.
- README atualizado.

**Painel web (front) — integrado ao mesmo produto**
- `frontend/gestor-fluxos.html` + imagens, servidos pelo Flask em `/` (`app/painel.py`). Um único servidor, sem CORS; só os arquivos do painel são expostos.
- Ajustes mínimos na página: endereço da API relativo (antes só funcionava na porta 5000 e quebraria atrás de proxy), limites do bot atual (sem aviso de "título cortado", 10 opções no Menu Principal e 9 nos submenus), aviso antes de mudar o tipo de um fluxo com opções, e tradução das mensagens de validação do backend.
- Testado de ponta a ponta com `scripts/testar_painel.js` (24 verificações).
- O painel cobre fluxos, respostas e boas-vindas. Atendimentos, usuários e os demais textos fixos continuam pela API.

## O que continua pendente (fora do código)
- Preencher os textos com `[PREENCHER]` (os 11 conteúdos) e revisar `config_bot`.
- Criar o primeiro ADMIN em produção (`POST /api/dashboard/auth/register`).
- Telefone do aluno ainda em texto puro (LGPD). O `EncryptedText` existe mas não é usado; se for adotado, a busca por atendimento aberto precisa de uma coluna com hash do telefone, porque o Fernet gera um texto cifrado diferente a cada vez.
- O controle de mensagens repetidas fica em memória; vale só com um processo, que é a configuração recomendada para SQLite.
