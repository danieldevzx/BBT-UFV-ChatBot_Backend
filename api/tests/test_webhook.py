from unittest.mock import patch

from app.core.database.extensions import db
from app.core.models import Atendimento, Categoria, ConfigBot, Conteudo, Feedback, NoFluxo
from app.whatsapp.webhook import service
from tests.base import BaseTestCase


def payload(wa_id, message):
    return {"entry": [{"changes": [{"value": {"messages": [message]}}]}]}


class WebhookTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        db.session.add(Categoria(id=1, nome="C"))
        db.session.flush()
        db.session.add(
            Conteudo(id=1, categoria_id=1, titulo="T", texto="resposta")
        )
        db.session.add(NoFluxo(id=1, titulo="raiz", tipo="MENU"))
        db.session.flush()
        db.session.add_all(
            [
                NoFluxo(id=2, parent_id=1, titulo="resp", tipo="RESPOSTA", conteudo_id=1),
                NoFluxo(id=3, parent_id=1, titulo="humano", tipo="ATENDENTE"),
            ]
        )
        db.session.commit()

    def _interactive(self, wa_id, reply_id):
        return payload(
            wa_id,
            {
                "from": wa_id,
                "type": "interactive",
                "interactive": {
                    "type": "button_reply",
                    "button_reply": {"id": reply_id},
                },
            },
        )

    @patch("app.whatsapp.webhook.service.whatsapp.send_text")
    @patch("app.whatsapp.webhook.service.whatsapp.send_buttons")
    def test_seleciona_resposta(self, send_buttons, send_text):
        service.process(self._interactive("5531", "2"))
        send_text.assert_called_once_with("5531", "resposta")
        send_buttons.assert_called_once()

    @patch("app.whatsapp.webhook.service.whatsapp.send_text")
    @patch("app.whatsapp.webhook.service.whatsapp.send_buttons")
    def test_atendente_cria_atendimento(self, send_buttons, send_text):
        service.process(self._interactive("5531", "3"))
        self.assertEqual(Atendimento.query.count(), 1)
        self.assertEqual(Atendimento.query.first().status, "ABERTO")

    @patch("app.whatsapp.webhook.service.whatsapp.send_text")
    @patch("app.whatsapp.webhook.service.whatsapp.send_buttons")
    def test_texto_livre_fallback(self, send_buttons, send_text):
        service.process(
            payload("5531", {"from": "5531", "type": "text", "text": {"body": "oi"}})
        )
        self.assertGreaterEqual(send_text.call_count, 1)

    @patch("app.whatsapp.webhook.service.whatsapp.send_text")
    @patch("app.whatsapp.webhook.service.whatsapp.send_buttons")
    def test_resposta_usa_config_feedback(self, send_buttons, send_text):
        db.session.add_all(
            [
                ConfigBot(chave="feedback_pergunta", valor="Foi útil?"),
                ConfigBot(chave="feedback_sim", valor="Sim"),
            ]
        )
        db.session.commit()
        service.process(self._interactive("5531", "2"))
        _, body, buttons = send_buttons.call_args[0]
        self.assertEqual(body, "Foi útil?")
        self.assertEqual(buttons[0], ("feedback:1:2", "Sim"))

    @patch("app.whatsapp.webhook.service.whatsapp.send_text")
    @patch("app.whatsapp.webhook.service.whatsapp.send_buttons")
    def test_feedback(self, send_buttons, send_text):
        service.process(self._interactive("5531", "feedback:1:2"))
        self.assertEqual(Feedback.query.count(), 1)
        self.assertTrue(Feedback.query.first().util)
