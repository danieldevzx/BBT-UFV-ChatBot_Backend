"""Testa todos os endpoints da API contra um servidor rodando (teste de fumaça).

Uso (com o servidor no ar, de preferência apontando para uma CÓPIA do banco):

    python scripts/testar_endpoints.py
    python scripts/testar_endpoints.py --base-url http://localhost:5000 --app-secret SEGREDO
    python scripts/testar_endpoints.py --admin-email admin@ufv.br --admin-password SENHA

- Banco sem usuários: o script cria o primeiro ADMIN com --admin-email/--admin-password.
- Banco com usuários: informe as credenciais de um ADMIN existente.
- --app-secret: o mesmo WHATSAPP_APP_SECRET do servidor, para assinar o webhook.
  Sem ele, o servidor precisa estar com WHATSAPP_REQUIRE_SIGNATURE=false.

ATENÇÃO: o script cria e altera registros (categoria, conteúdo, nós, um
atendimento de teste, um usuário ATENDENTE). Tudo o que ele cria é desativado
ou removido no fim, mas os registros desativados e o log ficam no banco. Não
rode em produção. Por segurança, recusa URLs que não sejam localhost sem --force.
"""
import argparse
import hashlib
import hmac
import json
import sys
import time
from urllib.parse import urlparse

import requests

VERDE, VERMELHO, CINZA, FIM = "\033[32m", "\033[31m", "\033[90m", "\033[0m"


class Testador:
    def __init__(self, base_url, app_secret, verify_token):
        self.base = base_url.rstrip("/")
        self.app_secret = app_secret
        self.verify_token = verify_token
        self.resultados = []  # (ok, metodo, rota, esperado, obtido, nota)
        self.s = requests.Session()

    # ------------------------------------------------------------ utilitários
    def req(self, metodo, rota, esperado, token=None, nome=None, checar=None, **kwargs):
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp = self.s.request(metodo, self.base + rota, headers=headers, timeout=20, **kwargs)
        except requests.RequestException as e:
            self._registrar(False, metodo, rota, esperado, "—", f"sem conexão: {e.__class__.__name__}", nome)
            return None, None
        try:
            corpo = resp.json()
        except ValueError:
            corpo = resp.text
        esperados = esperado if isinstance(esperado, (list, tuple)) else (esperado,)
        ok = resp.status_code in esperados
        nota = ""
        if ok and checar:
            try:
                resultado = checar(corpo)
                if resultado is not True:
                    ok, nota = False, resultado or "verificação falhou"
            except Exception as e:  # noqa: BLE001
                ok, nota = False, f"verificação falhou: {e}"
        if not ok and not nota:
            nota = (corpo.get("error") if isinstance(corpo, dict) else str(corpo))[:80] if corpo else ""
        self._registrar(ok, metodo, rota, esperado, resp.status_code, nota, nome)
        return resp.status_code, corpo

    def _registrar(self, ok, metodo, rota, esperado, obtido, nota, nome):
        self.resultados.append((ok, metodo, rota, esperado, obtido, nota, nome))
        cor = VERDE if ok else VERMELHO
        marca = "OK  " if ok else "FALHOU"
        descr = f" {CINZA}({nome}){FIM}" if nome else ""
        extra = f"  {VERMELHO}{nota}{FIM}" if (nota and not ok) else ""
        print(f"{cor}{marca}{FIM} {metodo:6} {rota:52} {obtido}{descr}{extra}")

    def webhook(self, mensagem, esperado=200, nome=None, assinatura=None):
        corpo = json.dumps({"entry": [{"changes": [{"value": {"messages": [mensagem]}}]}]}).encode()
        headers = {"Content-Type": "application/json"}
        if assinatura is not None:
            headers["X-Hub-Signature-256"] = assinatura
        elif self.app_secret:
            headers["X-Hub-Signature-256"] = "sha256=" + hmac.new(
                self.app_secret.encode(), corpo, hashlib.sha256
            ).hexdigest()
        return self.req("POST", "/api/whatsapp/webhook/", esperado, nome=nome, data=corpo, headers=headers)

    # ------------------------------------------------------------ roteiro
    def rodar(self, admin_email, admin_senha):
        sufixo = str(int(time.time()))
        R = self.req

        print(f"\n== Saúde e proteção ({self.base})")
        R("GET", "/api/health", 200, checar=lambda c: c.get("status") == "ok" or f"status={c.get('status')}")
        R("GET", "/api/dashboard/categorias/", 401, nome="sem token")

        print("\n== Auth")
        st, _ = R("POST", "/api/dashboard/auth/register", (201, 403), nome="1º ADMIN (403 = já existe usuário)",
                  json={"email": admin_email, "password": admin_senha, "name": "Admin"})
        st, corpo = R("POST", "/api/dashboard/auth/login", 200, json={"email": admin_email.upper(), "password": admin_senha},
                      nome="e-mail em maiúsculas", checar=lambda c: bool(c.get("token")) or "sem token")
        if st != 200:
            print(f"\n{VERMELHO}Sem login de ADMIN não dá para continuar. Confira --admin-email/--admin-password.{FIM}")
            return
        adm = corpo["token"]
        R("POST", "/api/dashboard/auth/login", 401, nome="senha errada", json={"email": admin_email, "password": "errada"})
        _, me = R("GET", "/api/dashboard/auth/me", 200, adm,
                  checar=lambda c: (c.get("perfil") == "ADMIN" and "senha_hash" not in c and "password_hash" not in c)
                  or "perfil diferente de ADMIN ou hash exposto")

        print("\n== Usuários")
        at_email, at_senha = f"atendente.teste.{sufixo}@ufv.br", "senha-teste-123"
        _, at = R("POST", "/api/dashboard/usuarios/", 201, adm,
                  json={"email": at_email, "password": at_senha, "name": "Atendente Teste", "perfil": "ATENDENTE"})
        at_id = at.get("id") if isinstance(at, dict) else None
        R("GET", "/api/dashboard/usuarios/", 200, adm, checar=lambda c: isinstance(c, list) and len(c) >= 2 or "lista curta")
        R("GET", f"/api/dashboard/usuarios/{at_id}", 200, adm, checar=lambda c: isinstance(c.get("id"), int) or "id não é inteiro")
        R("PATCH", f"/api/dashboard/usuarios/{at_id}", 200, adm, json={"name": "Atendente Teste 2"},
          checar=lambda c: c.get("name") == "Atendente Teste 2" or "nome não mudou")
        R("GET", "/api/dashboard/usuarios/999999", 404, adm)
        _, c_at = R("POST", "/api/dashboard/auth/login", 200, json={"email": at_email, "password": at_senha}, nome="login ATENDENTE")
        tok_at = c_at.get("token") if isinstance(c_at, dict) else None

        print("\n== Permissões do ATENDENTE")
        R("GET", "/api/dashboard/categorias/", 200, tok_at, nome="lê categorias")
        R("POST", "/api/dashboard/categorias/", 403, tok_at, json={"nome": "X"}, nome="não cria categoria")
        R("PATCH", "/api/dashboard/fluxo/1", 403, tok_at, json={"titulo": "X"}, nome="não edita árvore")
        R("GET", "/api/dashboard/usuarios/", 403, tok_at, nome="não lista usuários")
        R("GET", "/api/dashboard/logs/", 403, tok_at, nome="não vê logs")
        R("GET", "/api/dashboard/feedback/", 403, tok_at, nome="não vê feedback")

        print("\n== Categorias")
        R("GET", "/api/dashboard/categorias/", 200, adm, checar=lambda c: len(c) >= 8 or f"só {len(c)} categorias")
        _, cat = R("POST", "/api/dashboard/categorias/", 201, adm, json={"nome": f"Teste {sufixo}", "descricao": "smoke"})
        cat_id = cat.get("id") if isinstance(cat, dict) else None
        R("GET", f"/api/dashboard/categorias/{cat_id}", 200, adm)
        R("PATCH", f"/api/dashboard/categorias/{cat_id}", 200, adm, json={"descricao": "smoke 2"})
        R("DELETE", "/api/dashboard/categorias/1", 409, adm, nome="categoria com conteúdo")
        R("GET", "/api/dashboard/categorias/999999", 404, adm)

        print("\n== Conteúdos")
        R("GET", "/api/dashboard/conteudos/", 200, adm, checar=lambda c: len(c) >= 11 or f"só {len(c)} conteúdos")
        R("GET", "/api/dashboard/conteudos/?categoria_id=1", 200, adm, nome="filtro categoria")
        _, cont = R("POST", "/api/dashboard/conteudos/", 201, adm,
                    json={"categoria_id": cat_id, "titulo": f"Conteúdo teste {sufixo}", "texto": "Texto de teste.", "fonte": "smoke"})
        cont_id = cont.get("id") if isinstance(cont, dict) else None
        R("POST", "/api/dashboard/conteudos/", 409, adm, nome="título repetido",
          json={"categoria_id": 1, "titulo": "Valores das multas", "texto": "x"})
        R("GET", f"/api/dashboard/conteudos/{cont_id}", 200, adm)
        R("PATCH", f"/api/dashboard/conteudos/{cont_id}", 200, adm, json={"texto": "Texto alterado."},
          checar=lambda c: c.get("updated_at") != c.get("created_at") or "updated_at não mudou")

        print("\n== Árvore (fluxo)")
        R("GET", "/api/dashboard/fluxo/?raiz=true", 200, adm, checar=lambda c: len(c) >= 9 or f"só {len(c)} nós na raiz")
        R("GET", "/api/dashboard/fluxo/?parent_id=1", 200, adm)
        R("GET", "/api/dashboard/fluxo/1", 200, adm)
        _, sub = R("POST", "/api/dashboard/fluxo/", 201, adm, nome="submenu em Multas",
                   json={"titulo": "Submenu teste", "tipo": "MENU", "parent_id": 1, "ordem": 99})
        sub_id = sub.get("id") if isinstance(sub, dict) else None
        _, no = R("POST", "/api/dashboard/fluxo/", 201, adm, nome="resposta no submenu",
                  json={"titulo": "Resposta teste", "tipo": "RESPOSTA", "conteudo_id": cont_id, "parent_id": sub_id})
        no_id = no.get("id") if isinstance(no, dict) else None
        R("POST", "/api/dashboard/fluxo/", 400, adm, nome="RESPOSTA sem conteúdo", json={"titulo": "X", "tipo": "RESPOSTA", "parent_id": sub_id})
        R("POST", "/api/dashboard/fluxo/", 400, adm, nome="título > 24", json={"titulo": "x" * 25, "tipo": "ATENDENTE", "parent_id": sub_id})
        R("PATCH", "/api/dashboard/fluxo/1", 400, adm, nome="ciclo", json={"parent_id": sub_id})
        R("PATCH", f"/api/dashboard/fluxo/{no_id}", 400, adm, nome="pai não-MENU", json={"parent_id": 10})
        R("PATCH", f"/api/dashboard/fluxo/{no_id}", 200, adm, json={"ordem": 2})
        R("GET", "/api/dashboard/fluxo/999999", 404, adm)

        print("\n== Textos fixos (config)")
        R("GET", "/api/dashboard/config/", 200, adm, checar=lambda c: len(c) >= 11 or f"só {len(c)} chaves")
        R("GET", "/api/dashboard/config/boas_vindas", 200, adm)
        chave = f"teste_smoke_{sufixo}"
        R("PUT", f"/api/dashboard/config/{chave}", 200, adm, json={"valor": "x"}, nome="cria")
        R("PUT", f"/api/dashboard/config/{chave}", 200, adm, json={"valor": "y"}, nome="atualiza")
        R("DELETE", f"/api/dashboard/config/{chave}", 200, adm)
        R("GET", f"/api/dashboard/config/{chave}", 404, adm)

        print("\n== Webhook do WhatsApp")
        R("GET", f"/api/whatsapp/webhook/?hub.mode=subscribe&hub.verify_token={self.verify_token}&hub.challenge=123", 200,
          nome="verificação Meta", checar=lambda c: str(c) == "123" or f"challenge devolvido: {c}")
        R("GET", "/api/whatsapp/webhook/?hub.mode=subscribe&hub.verify_token=errado&hub.challenge=1", 403, nome="token errado")
        fone = "5599" + sufixo[-9:]
        st, _ = self.webhook({"id": f"wamid.t{sufixo}", "from": fone, "type": "text", "text": {"body": "oi"}}, nome="texto livre")
        if st in (401, 503) and not self.app_secret:
            print(f"{VERMELHO}   O servidor exige assinatura: passe --app-secret com o WHATSAPP_APP_SECRET dele,"
                  f" ou suba o servidor sem segredo e com WHATSAPP_REQUIRE_SIGNATURE=false.{FIM}")
        self.webhook({"id": f"wamid.m{sufixo}", "from": fone, "type": "interactive",
                      "interactive": {"type": "list_reply", "list_reply": {"id": "1"}}}, nome="abre submenu Multas")
        self.webhook({"id": f"wamid.a{sufixo}", "from": fone, "type": "interactive",
                      "interactive": {"type": "list_reply", "list_reply": {"id": "12"}}}, nome="pede atendente")
        self.webhook({"id": f"wamid.u{sufixo}", "from": fone, "type": "text", "text": {"body": "mensagem do aluno"}},
                     nome="texto durante atendimento")
        if self.app_secret:
            self.webhook({"from": fone, "type": "text", "text": {"body": "x"}}, 401,
                         nome="assinatura inválida", assinatura="sha256=errada")

        print("\n== Atendimentos")
        _, lista = R("GET", "/api/dashboard/atendimentos/", 200, adm)
        meu = next((a for a in (lista or []) if isinstance(a, dict) and a.get("telefone_solicitante") == fone), None)
        if not meu:
            self._registrar(False, "GET", "/api/dashboard/atendimentos/", 200, "—", "atendimento do webhook não apareceu", None)
        else:
            aid = meu["id"]
            R("GET", f"/api/dashboard/atendimentos/{aid}", 200, adm)
            R("GET", f"/api/dashboard/atendimentos/{aid}/mensagens", 200, adm,
              checar=lambda c: {m["remetente"] for m in c} >= {"BOT", "USUARIO"} or "faltam mensagens BOT/USUARIO")
            R("GET", f"/api/dashboard/atendimentos/{aid}", 200, tok_at, nome="ATENDENTE vê sem dono")
            R("PATCH", f"/api/dashboard/atendimentos/{aid}", 200, adm, json={"assumir": True},
              checar=lambda c: c.get("status") == "EM_ATENDIMENTO" or f"status={c.get('status')}")
            R("GET", f"/api/dashboard/atendimentos/{aid}", 403, tok_at, nome="ATENDENTE não vê o de outro")
            R("POST", f"/api/dashboard/atendimentos/{aid}/mensagens", 201, adm, json={"texto": "Resposta de teste."},
              nome="enviado=false sem WhatsApp configurado")
            R("PATCH", f"/api/dashboard/atendimentos/{aid}", 400, adm, json={"status": "QUALQUER"}, nome="status inválido")
            R("PATCH", f"/api/dashboard/atendimentos/{aid}", 200, adm, json={"status": "FECHADO"},
              checar=lambda c: bool(c.get("closed_at")) or "closed_at vazio")
        R("GET", "/api/dashboard/atendimentos/999999", 404, adm)

        print("\n== Feedback e logs")
        R("POST", "/api/dashboard/feedback/", 400, adm, nome="sem util", json={"no_fluxo_id": 10})
        R("POST", "/api/dashboard/feedback/", 201, adm, json={"no_fluxo_id": 10, "util": True, "comentario": "smoke"})
        R("GET", "/api/dashboard/feedback/", 200, adm)
        R("GET", "/api/dashboard/feedback/?no_fluxo_id=10", 200, adm)
        R("GET", "/api/dashboard/logs/", 200, adm, checar=lambda c: len(c) >= 1 or "log vazio")

        print("\n== Limpeza (soft delete do que foi criado)")
        R("DELETE", f"/api/dashboard/fluxo/{no_id}", 200, adm)
        R("DELETE", f"/api/dashboard/fluxo/{sub_id}", 200, adm)
        R("DELETE", f"/api/dashboard/conteudos/{cont_id}", 200, adm)
        R("PATCH", f"/api/dashboard/conteudos/{cont_id}", 200, adm, json={"categoria_id": 8}, nome="libera a categoria")
        R("DELETE", f"/api/dashboard/categorias/{cat_id}", 200, adm)
        R("DELETE", f"/api/dashboard/usuarios/{at_id}", 200, adm)
        R("GET", "/api/dashboard/auth/me", 401, tok_at, nome="token do desativado não vale")

    def resumo(self):
        total = len(self.resultados)
        falhas = [r for r in self.resultados if not r[0]]
        print(f"\n{'=' * 70}\n{total - len(falhas)}/{total} verificações OK")
        for _, metodo, rota, esperado, obtido, nota, nome in falhas:
            print(f"{VERMELHO}  {metodo} {rota} — esperado {esperado}, veio {obtido}. {nome or ''} {nota}{FIM}")
        return not falhas


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-url", default="http://localhost:5000")
    p.add_argument("--admin-email", default="admin@ufv.br")
    p.add_argument("--admin-password", default="senha-admin-teste")
    p.add_argument("--app-secret", default="", help="WHATSAPP_APP_SECRET do servidor (assina o webhook)")
    p.add_argument("--verify-token", default="bbt_verify", help="WHATSAPP_VERIFY_TOKEN do servidor")
    p.add_argument("--force", action="store_true", help="permite URL que não seja localhost")
    args = p.parse_args()

    host = urlparse(args.base_url).hostname
    if host not in ("localhost", "127.0.0.1", "0.0.0.0") and not args.force:
        sys.exit("Recusado: o script altera o banco. Use --force se tiver certeza de que não é produção.")

    t = Testador(args.base_url, args.app_secret, args.verify_token)
    t.rodar(args.admin_email, args.admin_password)
    sys.exit(0 if t.resumo() else 1)


if __name__ == "__main__":
    main()
