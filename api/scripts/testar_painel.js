// Teste do painel web: abre o gestor-fluxos.html servido pelo Flask num navegador
// simulado (jsdom) e usa a página como uma bibliotecária usaria: cria o 1º ADMIN,
// edita uma resposta, cria e desativa opções, muda a boas-vindas, entra como ATENDENTE.
//
// Precisa de Node 18+ e do jsdom (uma vez):  npm install jsdom@24
// Rode com o servidor ligado numa CÓPIA do banco SEM usuários e com
// WHATSAPP_REQUIRE_SIGNATURE=false:
//     node scripts/testar_painel.js http://localhost:5000
// O roteiro cria e altera dados (opções, textos, usuários). Nunca rode em produção.
const { JSDOM, VirtualConsole } = require('jsdom');
const BASE = (process.argv[2] || 'http://localhost:5000').replace(/\/+$/, '');

const resultados = [];
const ok = (cond, nome, extra = '') => { resultados.push([!!cond, nome]); console.log(`${cond ? 'OK    ' : 'FALHOU'} ${nome}${!cond && extra ? '  -> ' + extra : ''}`); };
const espera = ms => new Promise(r => setTimeout(r, ms));
async function ate(fn, ms = 4000) { const t = Date.now(); while (Date.now() - t < ms) { try { const v = fn(); if (v) return v; } catch (e) {} await espera(50); } return null; }

async function api(metodo, caminho, token, corpo) {
  const r = await fetch(BASE + '/api/dashboard' + caminho, { method: metodo, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) }, body: corpo ? JSON.stringify(corpo) : undefined });
  return { status: r.status, dados: await r.json().catch(() => null) };
}

async function abrirPagina() {
  const erros = [];
  const vc = new VirtualConsole();
  vc.on('jsdomError', e => erros.push(String(e.message || e)));
  vc.on('error', e => erros.push(String(e)));
  const html = await (await fetch(BASE + '/')).text();
  const dom = new JSDOM(html, {
    url: BASE + '/', runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) {
      w.fetch = (u, o) => fetch(new URL(u, BASE + '/'), o);
      w.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
      w.HTMLDialogElement.prototype.close = function () { this.open = false; };
      w.Element.prototype.scrollIntoView = function () {};
      w.scrollTo = () => {};
    },
  });
  const w = dom.window, d = w.document;
  const $ = s => d.querySelector(s);
  const enviar = form => form.dispatchEvent(new w.Event('submit', { bubbles: true, cancelable: true }));
  const clicar = el => el.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const preencher = (sel, v) => { const el = $(sel); el.value = v; el.dispatchEvent(new w.Event('input', { bubbles: true })); el.dispatchEvent(new w.Event('change', { bubbles: true })); };
  const toast = () => $('#toast').textContent;
  const ir = async hash => { w.location.hash = hash; await espera(150); };
  return { w, d, $, enviar, clicar, preencher, toast, ir, erros, dom };
}

(async () => {
  const sufixo = Date.now().toString(36);
  const email = `bibliotecaria.${sufixo}@ufv.br`, senha = 'senha-forte-123';

  console.log('\n== Primeiro acesso e login');
  let p = await abrirPagina();
  ok(p.$('#form-login'), 'abre na tela de login');
  ok(p.$('code').textContent === '/api/dashboard', 'usa a API pelo caminho relativo (sem CORS)', p.$('code').textContent);
  p.clicar(p.$('#l-alternar'));
  ok(p.$('#login-titulo').textContent === 'Criar administrador', 'alterna para "Criar administrador"');
  p.preencher('#l-nome', 'Bibliotecária'); p.preencher('#l-email', email.toUpperCase()); p.preencher('#l-senha', senha);
  p.enviar(p.$('#form-login'));
  const linhas = await ate(() => { const t = p.$('#corpo-fluxos'); return t && t.querySelectorAll('tr').length >= 5 && t; }, 6000);
  ok(linhas, 'cria o 1º ADMIN, entra e carrega a lista de fluxos', p.$('#l-erro') && p.$('#l-erro').textContent);
  const sessao = JSON.parse(p.w.localStorage.getItem('bbtSessao') || '{}');
  ok(sessao.perfil === 'ADMIN', 'sessão como ADMIN');
  const token = sessao.token;
  const nomes = [...p.d.querySelectorAll('#corpo-fluxos tr td:first-child')].map(td => td.textContent.trim());
  ok(['Menu Principal', 'Multas', 'Login e senha Sapiens', 'Biblioteca das Coisas', 'Nada Consta'].every(n => nomes.includes(n)), 'mostra os fluxos do chatbot.db', nomes.join(', '));

  console.log('\n== Ver e editar uma resposta (Multas > Valores das multas)');
  await p.ir('#/f/1');
  const opcoes = await ate(() => p.d.querySelectorAll('#corpo-msgs tr').length === 3 && p.$('#corpo-msgs'));
  ok(opcoes && opcoes.textContent.includes('Veja como funcionam as multas'), 'abre o fluxo Multas com as 3 opções e o texto do banco');
  p.clicar(p.$('[data-acao="editar-msg"][data-id="10"]'));
  ok(p.$('#dlg').open && p.$('#m-texto').value.startsWith('Veja como funcionam'), 'abre o diálogo de edição com o texto atual');
  const novoTexto = 'A multa é de R$ 1,00 por dia de atraso, por item.';
  p.preencher('#m-texto', novoTexto);
  p.enviar(p.$('#dlg form'));
  await ate(() => p.toast().includes('Alterações salvas'));
  let r = await api('GET', '/conteudos/1', token);
  ok(r.dados.texto === novoTexto, 'texto salvo no banco (conteudo 1)', r.dados && r.dados.texto);

  console.log('\n== Adicionar uma opção nova em Multas');
  p.clicar(p.$('[data-acao="nova-msg"]'));
  p.preencher('#m-titulo', 'Multa de livro raro'); p.preencher('#m-tipo', 'RESPOSTA'); p.preencher('#m-texto', 'Livros raros têm multa diferenciada.');
  p.enviar(p.$('#dlg form'));
  await ate(() => p.toast().includes('Opção adicionada'));
  r = await api('GET', '/fluxo/?parent_id=1', token);
  const novo = (r.dados || []).find(n => n.titulo === 'Multa de livro raro');
  ok(novo && novo.tipo === 'RESPOSTA' && novo.conteudo_id, 'nó RESPOSTA criado dentro de Multas com texto próprio');

  console.log('\n== Desativar e reativar a opção');
  await p.ir('#/f/1'); await espera(300);
  p.clicar(p.$(`[data-acao="apagar-msg"][data-id="${novo.id}"]`));
  p.enviar(p.$('#dlg form'));
  await ate(() => p.toast().includes('Desativado'));
  r = await api('GET', `/fluxo/${novo.id}`, token);
  ok(r.dados.ativo === false, 'desativada no banco');
  await espera(300);
  p.clicar(p.$(`[data-acao="reativar"][data-id="${novo.id}"]`));
  await ate(() => p.toast().includes('Reativado'));
  r = await api('GET', `/fluxo/${novo.id}`, token);
  ok(r.dados.ativo === true, 'reativada no banco');

  console.log('\n== Regras do backend aparecem em português no diálogo');
  await p.ir('#/f/raiz'); await espera(300);
  p.clicar(p.$('[data-acao="editar-msg"][data-id="1"]'));
  p.preencher('#m-tipo', 'RESPOSTA'); p.preencher('#m-texto', 'teste');
  const contAntes = (await api('GET', '/conteudos/', token)).dados.length;
  p.enviar(p.$('#dlg form'));
  const erroTipo = await ate(() => !p.$('#dlg .erro-campo').hidden && p.$('#dlg .erro-campo').textContent);
  ok(erroTipo && erroTipo.includes('opções ativas'), 'fluxo com opções não muda de tipo (aviso antes de gravar)', erroTipo);
  ok((await api('GET', '/conteudos/', token)).dados.length === contAntes, 'nenhum texto solto foi criado');
  p.clicar(p.$('[data-fechar]'));

  p.clicar(p.$('[data-acao="nova-msg"]'));
  p.preencher('#m-titulo', 'Eventos'); p.preencher('#m-tipo', 'MENU');
  p.enviar(p.$('#dlg form'));
  await ate(() => p.toast().includes('Opção adicionada'));
  ok(p.toast().includes('Opção adicionada'), 'cria a 10ª opção no Menu Principal (submenu "Eventos")');
  await espera(300);
  ok(p.$('#avisos').textContent.includes('o máximo permitido'), 'mostra o aviso de menu cheio');
  p.clicar(p.$('[data-acao="nova-msg"]'));
  p.preencher('#m-titulo', 'Décima primeira'); p.preencher('#m-tipo', 'ATENDENTE');
  p.enviar(p.$('#dlg form'));
  const erroLimite = await ate(() => !p.$('#dlg .erro-campo').hidden && p.$('#dlg .erro-campo').textContent);
  ok(erroLimite && erroLimite.includes('máximo de 10'), 'a 11ª opção é recusada pelo backend com mensagem clara', erroLimite);
  p.clicar(p.$('[data-fechar]'));

  console.log('\n== Mensagem de boas-vindas');
  p.clicar(p.$('[data-acao="editar-fluxo"][data-id="raiz"]'));
  p.preencher('#bv-texto', 'Olá! Sou o assistente da Biblioteca do Campus Florestal. Escolha uma opção:');
  p.enviar(p.$('#dlg form'));
  await ate(() => p.toast().includes('Mensagem salva'));
  r = await api('GET', '/config/boas_vindas', token);
  ok(r.dados.valor.includes('Campus Florestal'), 'boas-vindas salva no config_bot');

  console.log('\n== Sair');
  p.clicar(p.$('#nav-sair'));
  ok(p.$('#form-login') && !p.w.localStorage.getItem('bbtSessao'), 'volta ao login e limpa a sessão');
  ok(p.erros.length === 0, 'nenhum erro de JavaScript na página (ADMIN)', p.erros.join(' | '));

  console.log('\n== ATENDENTE só lê');
  await api('POST', '/usuarios/', token, { email: `atendente.${sufixo}@ufv.br`, password: 'senha-123', name: 'Atendente', perfil: 'ATENDENTE' });
  const q = await abrirPagina();
  q.preencher('#l-email', `atendente.${sufixo}@ufv.br`); q.preencher('#l-senha', 'senha-123');
  q.enviar(q.$('#form-login'));
  await ate(() => q.$('#corpo-fluxos') && q.$('#corpo-fluxos').querySelectorAll('tr').length >= 5, 6000);
  ok(q.d.body.classList.contains('leitura'), 'entra em modo só leitura (botões de edição ocultos)');
  ok(q.toast().includes('só leitura'), 'avisa que é só leitura');
  ok(q.erros.length === 0, 'nenhum erro de JavaScript na página (ATENDENTE)', q.erros.join(' | '));

  console.log('\n== O bot usa o que foi editado no painel');
  const corpo = JSON.stringify({ entry: [{ changes: [{ value: { messages: [{ id: 'wamid.' + sufixo, from: '5531900000000', type: 'interactive', interactive: { list_reply: { id: 'inicio' } } }] } }] }] });
  r = await fetch(BASE + '/api/whatsapp/webhook/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: corpo });
  ok(r.status === 200, 'webhook responde 200 depois das edições');

  const falhas = resultados.filter(x => !x[0]).length;
  console.log(`\n${resultados.length - falhas}/${resultados.length} verificações OK`);
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.error('ERRO NO ROTEIRO', e); process.exit(2); });
