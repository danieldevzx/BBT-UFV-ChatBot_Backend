"""Base dos testes: cada teste roda numa CÓPIA do db/chatbot.db real
(schema, árvore, textos e config do jeito que vão para produção).
O arquivo original nunca é alterado."""
import shutil
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.config import DB_DIR
from app.core.database.extensions import db

BANCO_REAL = DB_DIR / "chatbot.db"


def make_config(caminho: str):
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test"
        DB_PATH = caminho
        DB_SCHEMA_PATH = str(DB_DIR / "sqlite_schema.sql")
        DB_MIGRATIONS_DIR = str(DB_DIR / "migrations")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{caminho}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        JWT_SECRET = "test-secret-key-with-at-least-32-bytes"
        WHATSAPP_VERIFY_TOKEN = "bbt_verify"
        WHATSAPP_APP_SECRET = ""
        WHATSAPP_REQUIRE_SIGNATURE = False
        WHATSAPP_TOKEN = "test-token"
        WHATSAPP_PHONE_NUMBER_ID = "test-phone"
        ENCRYPTION_KEY = ""

    return TestConfig


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="bbt-test-")
        self.db_path = str(Path(self.tmpdir) / "chatbot.db")
        shutil.copyfile(BANCO_REAL, self.db_path)

        self.app = create_app(make_config(self.db_path))
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.engine.dispose()
        self.ctx.pop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def sql(self, consulta, **params):
        return db.session.execute(db.text(consulta), params).all()

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
