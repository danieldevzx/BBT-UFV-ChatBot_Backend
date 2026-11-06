from tests.base import BaseTestCase


class AuthTestCase(BaseTestCase):
    def test_banco_real_comeca_sem_usuarios(self):
        self.assertEqual(self.sql("select count(*) from usuario")[0][0], 0)

    def test_first_register_becomes_admin(self):
        resp = self.register()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["perfil"], "ADMIN")

    def test_senha_gravada_em_senha_hash_com_bcrypt(self):
        self.register()
        (hash_,) = self.sql("select senha_hash from usuario")[0]
        self.assertTrue(hash_.startswith("$2b$"))

    def test_login_and_me(self):
        self.register()
        token = self.login()
        self.assertIsNotNone(token)
        resp = self.client.get("/api/dashboard/auth/me", headers=self.auth_header(token))
        self.assertEqual(resp.status_code, 200)
        dados = resp.get_json()
        self.assertEqual(dados["email"], "admin@ufv.br")
        self.assertIsInstance(dados["id"], int)
        self.assertTrue(dados["created_at"].endswith("+00:00"))
        self.assertNotIn("password_hash", dados)
        self.assertNotIn("senha_hash", dados)

    def test_email_sem_diferenciar_maiusculas(self):
        self.register(email="  Admin@UFV.br ")
        self.assertIsNotNone(self.login(email="ADMIN@ufv.BR"))
        self.assertEqual(self.sql("select email from usuario")[0][0], "admin@ufv.br")

    def test_second_register_requires_admin(self):
        self.register()
        resp = self.register(email="outro@ufv.br", password="x")
        self.assertEqual(resp.status_code, 403)

    def test_admin_creates_user(self):
        self.register()
        token = self.login()
        resp = self.client.post(
            "/api/dashboard/auth/register",
            json={"email": "at@ufv.br", "password": "x", "perfil": "ATENDENTE"},
            headers=self.auth_header(token),
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["perfil"], "ATENDENTE")

    def test_usuario_desativado_nao_entra(self):
        self.register()
        admin = self.auth_header(self.login())
        criado = self.client.post(
            "/api/dashboard/usuarios/",
            json={"email": "at@ufv.br", "password": "x"},
            headers=admin,
        ).get_json()
        token_at = self.login("at@ufv.br", "x")
        resp = self.client.delete(f"/api/dashboard/usuarios/{criado['id']}", headers=admin)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(self.login("at@ufv.br", "x"))
        resp = self.client.get("/api/dashboard/auth/me", headers=self.auth_header(token_at))
        self.assertEqual(resp.status_code, 401)

    def test_login_invalid(self):
        self.register()
        resp = self.client.post(
            "/api/dashboard/auth/login",
            json={"email": "admin@ufv.br", "password": "wrong"},
        )
        self.assertEqual(resp.status_code, 401)
