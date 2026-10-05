from unittest.mock import patch

from app.core.database.extensions import db
from app.core.models import Atendimento
from tests.base import BaseTestCase


class DashboardTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.admin_token = self.login()

    def test_categoria_crud(self):
        headers = self.auth_header(self.admin_token)
        resp = self.client.post(
            "/api/dashboard/categorias/", json={"nome": "Multas"}, headers=headers
        )
        self.assertEqual(resp.status_code, 201)
        categoria_id = resp.get_json()["id"]

        resp = self.client.get("/api/dashboard/categorias/", headers=headers)
        self.assertEqual(len(resp.get_json()), 1)

        resp = self.client.patch(
            f"/api/dashboard/categorias/{categoria_id}",
            json={"nome": "Multas2"},
            headers=headers,
        )
        self.assertEqual(resp.get_json()["nome"], "Multas2")

    def test_atendente_somente_leitura(self):
        headers = self.auth_header(self.admin_token)
        self.client.post(
            "/api/dashboard/auth/register",
            json={"email": "at@ufv.br", "password": "x", "perfil": "ATENDENTE"},
            headers=headers,
        )
        token = self.login("at@ufv.br", "x")
        at_headers = self.auth_header(token)

        resp = self.client.post(
            "/api/dashboard/categorias/", json={"nome": "X"}, headers=at_headers
        )
        self.assertEqual(resp.status_code, 403)

        resp = self.client.get("/api/dashboard/categorias/", headers=at_headers)
        self.assertEqual(resp.status_code, 200)

    def test_conteudo_e_fluxo(self):
        headers = self.auth_header(self.admin_token)
        categoria = self.client.post(
            "/api/dashboard/categorias/", json={"nome": "C"}, headers=headers
        ).get_json()

        conteudo = self.client.post(
            "/api/dashboard/conteudos/",
            json={"categoria_id": categoria["id"], "titulo": "T", "texto": "texto"},
            headers=headers,
        )
        self.assertEqual(conteudo.status_code, 201)
        conteudo_id = conteudo.get_json()["id"]

        no = self.client.post(
            "/api/dashboard/fluxo/",
            json={"titulo": "Resp", "tipo": "RESPOSTA", "conteudo_id": conteudo_id},
            headers=headers,
        )
        self.assertEqual(no.status_code, 201)

        bad = self.client.post(
            "/api/dashboard/fluxo/",
            json={"titulo": "Bad", "tipo": "RESPOSTA"},
            headers=headers,
        )
        self.assertEqual(bad.status_code, 400)

    def test_rota_protegida(self):
        resp = self.client.get("/api/dashboard/categorias/")
        self.assertEqual(resp.status_code, 401)

    @patch("app.dashboard.atendimentos.service.whatsapp.send_text")
    def test_mensagem_atendimento_envia_whatsapp(self, send_text):
        send_text.return_value = True
        headers = self.auth_header(self.admin_token)
        atendimento = Atendimento(telefone_solicitante="553199456489")
        db.session.add(atendimento)
        db.session.commit()

        resp = self.client.post(
            f"/api/dashboard/atendimentos/{atendimento.id}/mensagens",
            json={"texto": "Olá, vou te ajudar."},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.get_json()["enviado"])
        send_text.assert_called_once_with("553199456489", "Olá, vou te ajudar.")
