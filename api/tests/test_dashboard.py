from unittest.mock import patch

from app.core.database.extensions import db
from app.core.models import Atendimento
from tests.base import BaseTestCase

F = "/api/dashboard/fluxo/"


class DashboardTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.h = self.auth_header(self.login())

    # ---------------------------------------------------------- categorias
    def test_categoria_crud(self):
        resp = self.client.post("/api/dashboard/categorias/", json={"nome": "Eventos"}, headers=self.h)
        self.assertEqual(resp.status_code, 201)
        categoria_id = resp.get_json()["id"]

        nomes = [c["nome"] for c in self.client.get("/api/dashboard/categorias/", headers=self.h).get_json()]
        self.assertEqual(len(nomes), 9)  # 8 do seed + a nova
        self.assertIn("Eventos", nomes)

        resp = self.client.patch(f"/api/dashboard/categorias/{categoria_id}", json={"nome": "Eventos2"}, headers=self.h)
        self.assertEqual(resp.get_json()["nome"], "Eventos2")

        resp = self.client.delete(f"/api/dashboard/categorias/{categoria_id}", headers=self.h)
        self.assertEqual(resp.status_code, 200)

    def test_categoria_com_conteudo_nao_pode_ser_removida(self):
        resp = self.client.delete("/api/dashboard/categorias/1", headers=self.h)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(self.sql("select count(*) from conteudo where categoria_id = 1")[0][0], 2)

    def test_atendente_somente_leitura(self):
        self.client.post(
            "/api/dashboard/auth/register",
            json={"email": "at@ufv.br", "password": "x", "perfil": "ATENDENTE"},
            headers=self.h,
        )
        at = self.auth_header(self.login("at@ufv.br", "x"))
        self.assertEqual(self.client.post("/api/dashboard/categorias/", json={"nome": "X"}, headers=at).status_code, 403)
        self.assertEqual(self.client.patch(f"{F}1", json={"titulo": "X"}, headers=at).status_code, 403)
        self.assertEqual(self.client.get("/api/dashboard/categorias/", headers=at).status_code, 200)

    def test_rota_protegida(self):
        self.assertEqual(self.client.get("/api/dashboard/categorias/").status_code, 401)

    # ---------------------------------------------------------- conteúdos
    def test_editar_conteudo_do_seed_atualiza_updated_at_no_formato_do_banco(self):
        resp = self.client.patch(
            "/api/dashboard/conteudos/7", json={"texto": "Seg a sex, 7h às 22h."}, headers=self.h
        )
        self.assertEqual(resp.status_code, 200)
        criado, atualizado = self.sql("select created_at, updated_at from conteudo where id = 7")[0]
        self.assertRegex(atualizado, r"T\d\d:\d\d:\d\d\.\d{3}Z$")
        self.assertGreater(atualizado, criado)
        self.assertEqual(self.sql("select count(*) from log where tabela_afetada = 'conteudo'")[0][0], 1)

    def test_conteudo_e_fluxo(self):
        categoria = self.client.post("/api/dashboard/categorias/", json={"nome": "C"}, headers=self.h).get_json()
        conteudo = self.client.post(
            "/api/dashboard/conteudos/",
            json={"categoria_id": categoria["id"], "titulo": "Novo texto", "texto": "texto"},
            headers=self.h,
        )
        self.assertEqual(conteudo.status_code, 201)
        self.assertIsInstance(conteudo.get_json()["created_by"], int)

        no = self.client.post(
            F, json={"titulo": "Novo", "tipo": "RESPOSTA", "conteudo_id": conteudo.get_json()["id"], "parent_id": 3},
            headers=self.h,
        )
        self.assertEqual(no.status_code, 201)
        bad = self.client.post(F, json={"titulo": "Bad", "tipo": "RESPOSTA"}, headers=self.h)
        self.assertEqual(bad.status_code, 400)

    # ---------------------------------------------------------- árvore
    def test_mudar_resposta_para_menu_limpa_o_conteudo(self):
        resp = self.client.patch(f"{F}2", json={"tipo": "MENU"}, headers=self.h)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.get_json()["conteudo_id"])

    def test_mudar_para_resposta_exige_conteudo(self):
        resp = self.client.patch(f"{F}9", json={"tipo": "RESPOSTA"}, headers=self.h)
        self.assertEqual(resp.status_code, 400)
        resp = self.client.patch(f"{F}9", json={"tipo": "RESPOSTA", "conteudo_id": 7}, headers=self.h)
        self.assertEqual(resp.status_code, 200)

    def test_menu_com_filhos_nao_muda_de_tipo(self):
        resp = self.client.patch(f"{F}1", json={"tipo": "ATENDENTE"}, headers=self.h)
        self.assertEqual(resp.status_code, 400)

    def test_ciclo_na_arvore_e_recusado(self):
        resp = self.client.patch(f"{F}1", json={"parent_id": 1}, headers=self.h)
        self.assertEqual(resp.status_code, 400)
        # 10 é RESPOSTA: também não pode ser pai
        resp = self.client.patch(f"{F}1", json={"parent_id": 10}, headers=self.h)
        self.assertEqual(resp.status_code, 400)
        # neto: cria submenu dentro de Multas e tenta pendurar Multas nele
        sub = self.client.post(F, json={"titulo": "Sub", "tipo": "MENU", "parent_id": 1}, headers=self.h).get_json()
        resp = self.client.patch(f"{F}1", json={"parent_id": sub["id"]}, headers=self.h)
        self.assertEqual(resp.status_code, 400)
        self.assertIsNone(self.sql("select parent_id from no_fluxo where id = 1")[0][0])

    def test_limite_de_opcoes_no_menu_inicial(self):
        resp = self.client.post(F, json={"titulo": "Décima", "tipo": "ATENDENTE"}, headers=self.h)
        self.assertEqual(resp.status_code, 201)  # 9 do seed + 1 = 10
        resp = self.client.post(F, json={"titulo": "Décima primeira", "tipo": "ATENDENTE"}, headers=self.h)
        self.assertEqual(resp.status_code, 400)
        # inativa não conta
        resp = self.client.post(F, json={"titulo": "Rascunho", "tipo": "ATENDENTE", "ativo": False}, headers=self.h)
        self.assertEqual(resp.status_code, 201)

    def test_titulo_maior_que_24(self):
        resp = self.client.patch(f"{F}1", json={"titulo": "x" * 25}, headers=self.h)
        self.assertEqual(resp.status_code, 400)

    # ---------------------------------------------------------- feedback / usuários / config
    def test_feedback_exige_util(self):
        self.assertEqual(self.client.post("/api/dashboard/feedback/", json={"no_fluxo_id": 10}, headers=self.h).status_code, 400)
        resp = self.client.post("/api/dashboard/feedback/", json={"no_fluxo_id": 10, "util": True}, headers=self.h)
        self.assertEqual(resp.status_code, 201)

    def test_usuarios_por_id_inteiro(self):
        resp = self.client.get("/api/dashboard/usuarios/1", headers=self.h)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["perfil"], "ADMIN")
        self.assertEqual(self.client.get("/api/dashboard/usuarios/abc", headers=self.h).status_code, 404)

    def test_config_lista_chaves_do_banco(self):
        chaves = {c["chave"] for c in self.client.get("/api/dashboard/config/", headers=self.h).get_json()}
        self.assertTrue({"boas_vindas", "fallback", "feedback_pergunta", "voltar", "menu_inicial"} <= chaves)

    # ---------------------------------------------------------- atendimentos
    @patch("app.dashboard.atendimentos.service.whatsapp.send_text")
    def test_mensagem_atendimento_envia_whatsapp(self, send_text):
        send_text.return_value = True
        atendimento = Atendimento(telefone_solicitante="553199456489")
        db.session.add(atendimento)
        db.session.commit()

        resp = self.client.post(
            f"/api/dashboard/atendimentos/{atendimento.id}/mensagens",
            json={"texto": "Olá, vou te ajudar."},
            headers=self.h,
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.get_json()["enviado"])
        send_text.assert_called_once_with("553199456489", "Olá, vou te ajudar.")

    def test_assumir_fechar_e_reabrir(self):
        atendimento = Atendimento(telefone_solicitante="5531")
        db.session.add(atendimento)
        db.session.commit()
        url = f"/api/dashboard/atendimentos/{atendimento.id}"

        dados = self.client.patch(url, json={"assumir": True}, headers=self.h).get_json()
        self.assertEqual((dados["status"], dados["usuario_atendente_id"]), ("EM_ATENDIMENTO", 1))
        dados = self.client.patch(url, json={"status": "FECHADO"}, headers=self.h).get_json()
        self.assertIsNotNone(dados["closed_at"])
        dados = self.client.patch(url, json={"status": "ABERTO"}, headers=self.h).get_json()
        self.assertIsNone(dados["closed_at"])

    def test_chaves_estrangeiras_ativas(self):
        from sqlalchemy.exc import IntegrityError
        with self.assertRaises(IntegrityError):
            self.sql("insert into mensagem (atendimento_id, remetente, texto) values (999, 'BOT', 'x')")
            db.session.commit()
        db.session.rollback()
