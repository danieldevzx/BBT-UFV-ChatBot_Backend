"""O painel web (front) é servido pelo próprio Flask, no mesmo endereço da API."""
from tests.base import BaseTestCase


class PainelTestCase(BaseTestCase):
    def test_pagina_inicial_e_o_gestor_de_fluxos(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.content_type)
        html = resp.get_data(as_text=True)
        self.assertIn("Gestor de Fluxos", html)
        # servido pelo Flask => usa a API pelo caminho relativo, sem CORS
        self.assertIn("'/api/dashboard'", html)
        resp.close()

    def test_imagens(self):
        for nome in ("logo.png", "capivara_UFV.png"):
            resp = self.client.get(f"/{nome}")
            self.assertEqual(resp.status_code, 200, nome)
            self.assertEqual(resp.content_type, "image/png")
            resp.close()

    def test_nao_expoe_outros_arquivos(self):
        for caminho in ("/run.py", "/.env", "/chatbot.db", "/..%2Fdb%2Fchatbot.db", "/qualquer"):
            self.assertEqual(self.client.get(caminho).status_code, 404, caminho)

    def test_api_continua_respondendo(self):
        self.assertEqual(self.client.get("/api/health").status_code, 200)
