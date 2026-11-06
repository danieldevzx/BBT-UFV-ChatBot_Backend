-- =====================================================================
-- 001 — Ajustes para integração com o backend (user_version 0 -> 1)
--
-- Aplica os "ajustes finos" da seção 2.5 do relatório e as chaves de
-- config_bot que o backend usa. Rode com:  flask db upgrade
-- (o comando aplica só as migrações cujo número é maior que o
-- PRAGMA user_version do arquivo).
-- =====================================================================

-- Modo WAL: leitura e escrita simultâneas entre o bot e o painel.
-- Fica gravado no arquivo; precisa rodar fora de transação.
PRAGMA journal_mode = WAL;

-- A recriação de usuario exige FKs desligadas (passo oficial do SQLite).
PRAGMA foreign_keys = OFF;

BEGIN;

-- E-mail sem diferenciar maiúsculas de minúsculas ------------------------
create table usuario_nova (
  id         integer primary key autoincrement,
  nome       text not null,
  email      text not null unique collate nocase,
  senha_hash text not null,
  perfil_id  integer not null references perfil(id),
  ativo      integer not null default 1 check (ativo in (0,1)),
  created_at text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
insert into usuario_nova (id, nome, email, senha_hash, perfil_id, ativo, created_at)
  select id, nome, lower(trim(email)), senha_hash, perfil_id, ativo, created_at from usuario;
drop table usuario;
alter table usuario_nova rename to usuario;

-- Índices para as consultas do bot e do painel ---------------------------
create index if not exists atendimento_status_idx      on atendimento(status);
create index if not exists atendimento_atendente_idx   on atendimento(usuario_atendente_id);
create index if not exists atendimento_telefone_idx    on atendimento(telefone_solicitante, status);
create index if not exists mensagem_atendimento_idx    on mensagem(atendimento_id, enviado_em);
create index if not exists feedback_no_fluxo_idx       on feedback(no_fluxo_id);
create index if not exists conteudo_categoria_idx      on conteudo(categoria_id);
create index if not exists log_criado_em_idx           on log(criado_em);

-- updated_at automático para quem editar o banco fora do backend ---------
-- (o backend já atualiza o campo; o WHEN evita sobrescrever esse valor)
create trigger if not exists conteudo_updated_at
after update on conteudo
for each row when new.updated_at = old.updated_at
begin
  update conteudo
     set updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
   where id = new.id;
end;

-- Textos fixos usados pelo backend que faltavam no seed ------------------
insert or ignore into config_bot (chave, valor) values
  ('feedback_pergunta',   'Essa resposta te ajudou?'),
  ('feedback_obrigado',   'Obrigado pelo seu feedback!'),
  ('feedback_sim',        'Ajudou'),
  ('feedback_nao',        'Não ajudou'),
  ('voltar',              'Voltar'),
  ('menu_inicial',        'Menu inicial'),
  ('atendente_ja_aberto', 'Seu atendimento já está aberto. É só escrever por aqui que a atendente responde assim que possível.');

PRAGMA user_version = 1;

COMMIT;

PRAGMA foreign_keys = ON;
