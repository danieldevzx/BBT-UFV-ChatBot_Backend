import unittest

from app import create_app
from app.core.database.extensions import db
from app.core.models import Perfil


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = "test-secret-key-with-at-least-32-bytes"
    WHATSAPP_VERIFY_TOKEN = "bbt_verify"
    WHATSAPP_APP_SECRET = ""
    WHATSAPP_TOKEN = "test-token"
    WHATSAPP_PHONE_NUMBER_ID = "test-phone"
    ENCRYPTION_KEY = ""


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add_all(
            [Perfil(id=1, nome="ADMIN"), Perfil(id=2, nome="ATENDENTE")]
        )
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def register(self, email="admin@ufv.br", password="secret", **extra):
        return self.client.post(
            "/api/dashboard/auth/register",
            json={"email": email, "password": password, **extra},
        )

    def login(self, email="admin@ufv.br", password="secret"):
        resp = self.client.post(
            "/api/dashboard/auth/login", json={"email": email, "password": password}
        )
        return resp.get_json().get("token")

    @staticmethod
    def auth_header(token):
        return {"Authorization": f"Bearer {token}"}
