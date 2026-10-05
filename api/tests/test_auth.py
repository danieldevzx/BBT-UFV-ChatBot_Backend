from tests.base import BaseTestCase


class AuthTestCase(BaseTestCase):
    def test_first_register_becomes_admin(self):
        resp = self.register()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["perfil"], "ADMIN")

    def test_login_and_me(self):
        self.register()
        token = self.login()
        self.assertIsNotNone(token)
        resp = self.client.get(
            "/api/dashboard/auth/me", headers=self.auth_header(token)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["email"], "admin@ufv.br")

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

    def test_login_invalid(self):
        self.register()
        resp = self.client.post(
            "/api/dashboard/auth/login",
            json={"email": "admin@ufv.br", "password": "wrong"},
        )
        self.assertEqual(resp.status_code, 401)
