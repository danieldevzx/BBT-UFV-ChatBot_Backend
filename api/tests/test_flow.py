from app.bot import responder
from app.core.database.extensions import db
from app.core.models import Categoria, ConfigBot, Conteudo, NoFluxo
from tests.base import BaseTestCase


class FlowTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        db.session.add(Categoria(id=1, nome="Multas"))
        db.session.flush()
        db.session.add(
            Conteudo(id=1, categoria_id=1, titulo="Valores", texto="As multas...")
        )
        db.session.add_all(
            [
                NoFluxo(
                    id=1,
                    titulo="Ver multas",
                    tipo="RESPOSTA",
                    conteudo_id=1,
                    ordem=1,
                ),
                NoFluxo(
                    id=2, titulo="Falar atendente", tipo="ATENDENTE", ordem=2
                ),
            ]
        )
        db.session.add(ConfigBot(chave="boas_vindas", valor="Bem-vindo"))
        db.session.commit()

    def test_menu_inicial(self):
        acao = responder.acao_inicial()
        self.assertEqual(acao["tipo"], "MENU")
        self.assertEqual(acao["body"], "Bem-vindo")
        self.assertEqual(len(acao["opcoes"]), 2)

    def test_resposta(self):
        no = NoFluxo.query.filter_by(tipo="RESPOSTA").first()
        acao = responder.acao_no(no.id)
        self.assertEqual(acao["tipo"], "RESPOSTA")
        self.assertEqual(acao["body"], "As multas...")

    def test_atendente(self):
        no = NoFluxo.query.filter_by(tipo="ATENDENTE").first()
        acao = responder.acao_no(no.id)
        self.assertEqual(acao["tipo"], "ATENDENTE")

    def test_no_inexistente(self):
        self.assertIsNone(responder.acao_no(999))

    def test_fallback(self):
        self.assertIn("Não entendi", responder.fallback())

    def test_textos_config(self):
        db.session.add_all(
            [
                ConfigBot(chave="feedback_pergunta", valor="Foi útil?"),
                ConfigBot(chave="feedback_sim", valor="Sim"),
                ConfigBot(chave="menu_botao", valor="Abrir"),
            ]
        )
        db.session.commit()
        self.assertEqual(responder.feedback_pergunta(), "Foi útil?")
        self.assertEqual(responder.menu_botao(), "Abrir")
        self.assertEqual(
            responder.resposta_feedback(7),
            [("feedback:1:7", "Sim"), ("feedback:0:7", "Não ajudou")],
        )
