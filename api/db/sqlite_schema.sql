-- =====================================================================
-- Chatbot da Biblioteca — Schema SQLite (versão local, tudo-em-um)
-- Rode com: sqlite3 chatbot.db < sqlite_schema.sql
--
-- Diferenças em relação à versão Supabase:
--   - Sem Auth/RLS: login e perfil (ADMIN/ATENDENTE) são checados no
--     código do backend, não no banco.
--   - usuario guarda senha_hash diretamente (bcrypt), não referencia
--     auth.users.
--   - Tipos adaptados: INTEGER PRIMARY KEY AUTOINCREMENT no lugar de
--     identity; 0/1 no lugar de boolean; TEXT para datas (ISO 8601).
--   - O app DEVE rodar "PRAGMA foreign_keys = ON;" em cada conexão
--     aberta — o SQLite não aplica chaves estrangeiras por padrão.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- perfil
create table perfil (
  id   integer primary key autoincrement,
  nome text not null unique check (nome in ('ADMIN','ATENDENTE'))
);
insert into perfil (id, nome) values (1,'ADMIN'), (2,'ATENDENTE');

-- ---------------------------------------------------------------- usuario
-- senha_hash: gerado com bcrypt no backend, nunca a senha em texto puro.
create table usuario (
  id         integer primary key autoincrement,
  nome       text not null,
  email      text not null unique,
  senha_hash text not null,
  perfil_id  integer not null references perfil(id),
  ativo      integer not null default 1 check (ativo in (0,1)),
  created_at text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ---------------------------------------------------------------- categoria / conteudo
create table categoria (
  id        integer primary key autoincrement,
  nome      text not null,
  descricao text
);

create table conteudo (
  id           integer primary key autoincrement,
  categoria_id integer references categoria(id),
  titulo       text not null unique,
  texto        text not null,
  fonte        text,
  ativo        integer not null default 1 check (ativo in (0,1)),
  created_by   integer references usuario(id),
  created_at   text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at   text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ---------------------------------------------------------------- no_fluxo (a árvore)
create table no_fluxo (
  id          integer primary key autoincrement,
  parent_id   integer references no_fluxo(id),
  titulo      text not null check (length(titulo) <= 24),
  tipo        text not null check (tipo in ('MENU','RESPOSTA','ATENDENTE')),
  conteudo_id integer references conteudo(id),
  ordem       integer not null default 0,
  ativo       integer not null default 1 check (ativo in (0,1)),
  check ((tipo = 'RESPOSTA') = (conteudo_id is not null))
);
create index no_fluxo_parent_idx on no_fluxo(parent_id, ordem);

-- ---------------------------------------------------------------- config_bot
create table config_bot (
  chave text primary key,
  valor text not null
);

-- ---------------------------------------------------------------- atendimento / mensagem
create table atendimento (
  id                    integer primary key autoincrement,
  telefone_solicitante  text not null,
  usuario_atendente_id  integer references usuario(id),
  status                text not null default 'ABERTO'
                        check (status in ('ABERTO','EM_ATENDIMENTO','FECHADO')),
  canal                 text not null default 'WHATSAPP',
  created_at            text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  closed_at             text
);

create table mensagem (
  id             integer primary key autoincrement,
  atendimento_id integer not null references atendimento(id),
  remetente      text not null check (remetente in ('USUARIO','BOT','ATENDENTE')),
  texto          text not null,
  enviado_em     text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ---------------------------------------------------------------- log / feedback
create table log (
  id             integer primary key autoincrement,
  usuario_id     integer references usuario(id),
  acao           text not null,
  tabela_afetada text,
  registro_id    integer,
  criado_em      text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

create table feedback (
  id          integer primary key autoincrement,
  no_fluxo_id integer not null references no_fluxo(id),
  util        integer not null check (util in (0,1)),
  comentario  text,
  criado_em   text not null default (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- =====================================================================
-- SEED: textos fixos, categorias, conteúdo e a árvore inicial (RF01–RF09)
-- IDs fixados manualmente porque o SQLite não tem blocos DO/PL como o
-- Postgres; como a tabela está vazia, os ids batem com a ordem de insert.
-- =====================================================================

insert into config_bot (chave, valor) values
  ('boas_vindas',   'Olá! Sou o assistente virtual da Biblioteca. Como posso ajudar? Escolha uma das opções abaixo.'),
  ('fallback',      'Não entendi sua mensagem. Por favor, escolha uma das opções do menu.'),
  ('menu_botao',    'Ver opções'),
  ('atendente_msg', 'Certo! Vou encaminhar você para uma atendente. Ela responderá assim que possível, dentro do horário de funcionamento.');

insert into categoria (id, nome, descricao) values
  (1,'Multas',               'Valores e pagamento de multas'),
  (2,'Renovação',            'Renovação de empréstimos'),
  (3,'Sapiens',              'Login e senha do Sapiens'),
  (4,'Pergamum',             'Pesquisa no acervo'),
  (5,'Informações gerais',   'Horários e contatos'),
  (6,'Biblioteca das Coisas','Empréstimo e doação de itens'),
  (7,'Minha Biblioteca',     'Acesso à plataforma Minha Biblioteca'),
  (8,'Nada Consta',          'Emissão de certidão/declaração');

insert into conteudo (id, categoria_id, titulo, texto, fonte) values
 (1,1,'Valores das multas',
  'Veja como funcionam as multas por atraso: [PREENCHER valor por dia/item e regras do regimento].', 'Regimento da biblioteca'),
 (2,1,'Como pagar a multa',
  'Para pagar sua multa, siga estes passos: 1) [PREENCHER] 2) [PREENCHER] 3) [PREENCHER].', 'Regimento da biblioteca'),
 (3,2,'Como renovar livros',
  'Você pode renovar seus empréstimos assim: 1) [PREENCHER] 2) [PREENCHER]. Lembre-se dos limites de renovação: [PREENCHER].', 'bbt.caf.ufv.br'),
 (4,3,'Login Sapiens - Técnico',
  'Para alunos do ensino técnico, o login é [PREENCHER formato]. Atenção ao dígito 0 inicial: [PREENCHER se deve ou não incluir].', 'bbt.caf.ufv.br'),
 (5,3,'Login Sapiens - Superior',
  'Para alunos do ensino superior, o login é [PREENCHER formato]. Atenção ao dígito 0 inicial: [PREENCHER se deve ou não incluir].', 'bbt.caf.ufv.br'),
 (6,4,'Pesquisar no acervo',
  'Para consultar um livro no Pergamum: 1) Acesse [PREENCHER link] 2) [PREENCHER] 3) [PREENCHER].', 'bbt.caf.ufv.br'),
 (7,5,'Horários e contatos',
  'Horário de funcionamento: [PREENCHER]. Contatos: e-mail [PREENCHER], telefone [PREENCHER].', 'bbt.caf.ufv.br'),
 (8,6,'Horário Biblioteca das Coisas',
  'A Biblioteca das Coisas funciona em: [PREENCHER dias e horários].', 'bbt.caf.ufv.br'),
 (9,6,'Itens para doação',
  'Você pode doar os seguintes itens: [PREENCHER lista]. Não aceitamos: [PREENCHER].', 'bbt.caf.ufv.br'),
 (10,7,'Acesso à Minha Biblioteca',
  'Para acessar a Minha Biblioteca: 1) [PREENCHER link] 2) [PREENCHER como entrar].', 'bbt.caf.ufv.br'),
 (11,8,'Como emitir Nada Consta',
  'Para emitir seu Nada Consta: 1) Preencha o formulário em [PREENCHER link] 2) [PREENCHER] 3) [PREENCHER prazo].', 'bbt.caf.ufv.br');

-- Menu inicial (parent_id NULL): 9 opções
insert into no_fluxo (id, parent_id, titulo, tipo, conteudo_id, ordem) values
  (1, null,'Multas','MENU', null, 1),
  (2, null,'Renovação de livros','RESPOSTA', 3, 2),
  (3, null,'Login e senha Sapiens','MENU', null, 3),
  (4, null,'Pesquisar no acervo','RESPOSTA', 6, 4),
  (5, null,'Horários e contatos','RESPOSTA', 7, 5),
  (6, null,'Biblioteca das Coisas','MENU', null, 6),
  (7, null,'Minha Biblioteca','RESPOSTA', 10, 7),
  (8, null,'Nada Consta','MENU', null, 8),
  (9, null,'Falar com atendente','ATENDENTE', null, 9);

-- Submenu: Multas (id 1)
insert into no_fluxo (id, parent_id, titulo, tipo, conteudo_id, ordem) values
  (10, 1,'Valores das multas','RESPOSTA', 1, 1),
  (11, 1,'Como pagar a multa','RESPOSTA', 2, 2),
  (12, 1,'Problema com multa','ATENDENTE', null, 3);

-- Submenu: Login Sapiens (id 3)
insert into no_fluxo (id, parent_id, titulo, tipo, conteudo_id, ordem) values
  (13, 3,'Ensino Técnico','RESPOSTA', 4, 1),
  (14, 3,'Ensino Superior','RESPOSTA', 5, 2);

-- Submenu: Biblioteca das Coisas (id 6)
insert into no_fluxo (id, parent_id, titulo, tipo, conteudo_id, ordem) values
  (15, 6,'Horário de funcionamento','RESPOSTA', 8, 1),
  (16, 6,'O que posso doar','RESPOSTA', 9, 2);

-- Submenu: Nada Consta (id 8)
insert into no_fluxo (id, parent_id, titulo, tipo, conteudo_id, ordem) values
  (17, 8,'Como emitir','RESPOSTA', 11, 1),
  (18, 8,'Problema no Nada Consta','ATENDENTE', null, 2);

-- =====================================================================
-- Criação do primeiro ADMIN: gere o hash da senha no backend (bcrypt)
-- e rode o insert abaixo manualmente, trocando os valores.
-- Exemplo (Node): await bcrypt.hash('sua-senha', 10)
-- =====================================================================
-- insert into usuario (nome, email, senha_hash, perfil_id)
-- values ('Administrador', 'admin@ufv.br', '$2b$10$...hash...', 1);
