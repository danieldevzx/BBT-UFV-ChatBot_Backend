"""Webhook do WhatsApp contra a árvore real do chatbot.db."""
from unittest.mock import patch

from app.core.models import Atendimento, Feedback, Mensagem
from app.whatsapp import whatsapp
from app.whatsapp.webhook import service
from tests.base import BaseTestCase

FONE = "553199990000"


def payload(*mensagens):
    return {"entry": [{"changes": [{"value": {"messages": list(mensagens)}}]}]}


def clique(reply_id, msg_id=None, fone=FONE):
    msg = {
        "from": fone,
        "type": "interactive",
        "interactive": {"type": "list_reply", "list_reply": {"id": str(reply_id)}},
    }
    if msg_id:
        msg["id"] = msg_id
    return msg


def texto(corpo, fone=FONE):
    return {"from": fone, "type": "text", "text": {"body": corpo}}


@patch.object(whatsapp, "send_list")
@patch.object(whatsapp, "send_buttons")
@patch.object(whatsapp, "send_text")
class WebhookTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        service._ids_processados.clear()

    def test_texto_livre_envia_fallback_e_menu_em_lista(self, send_text, send_buttons, send_list):
        service.process(payload(texto("oi")))
        self.assertTrue(send_text.call_args[0][1].startswith("Não entendi sua mensagem"))
        _, body, botao, linhas = send_list.call_args[0]
        self.assertEqual(botao, "Ver opções")
        self.assertEqual(len(linhas), 9)
        self.assertNotIn("inicio", [i for i, _ in linhas])  # raiz não tem Voltar

    def test_submenu_curto_vai_em_botoes_com_voltar(self, send_text, send_buttons, send_list):
        service.process(payload(clique(3)))  # Login e senha Sapiens
        _, body, botoes = send_buttons.call_args[0]
        self.assertEqual(body, "Login e senha Sapiens")
        self.assertEqual(botoes, [(13, "Ensino Técnico"), (14, "Ensino Superior"), ("inicio", "Voltar")])

    def test_titulo_maior_que_20_vai_em_lista_sem_cortar(self, send_text, send_buttons, send_list):
        service.process(payload(clique(6)))  # Biblioteca das Coisas
        send_buttons.assert_not_called()
        linhas = send_list.call_args[0][3]
        self.assertIn((15, "Horário de funcionamento"), linhas)
        self.assertEqual(linhas[-1], ("inicio", "Voltar"))

    def test_submenu_com_3_opcoes_mais_voltar_vai_em_lista(self, send_text, send_buttons, send_list):
        service.process(payload(clique(1)))  # Multas
        self.assertEqual(len(send_list.call_args[0][3]), 4)

    def test_nenhum_titulo_do_banco_e_cortado(self, send_text, send_buttons, send_list):
        for no_id in (1, 3, 6, 8):
            service.process(payload(clique(no_id)))
        for chamada in send_buttons.call_args_list:
            for _, titulo in chamada[0][2]:
                self.assertLessEqual(len(titulo), whatsapp.MAX_BUTTON_TITLE)

    def test_voltar_e_menu_inicial(self, send_text, send_buttons, send_list):
        service.process(payload(clique("inicio")))
        self.assertEqual(len(send_list.call_args[0][3]), 9)

    def test_resposta_com_feedback_e_menu_inicial(self, send_text, send_buttons, send_list):
        service.process(payload(clique(10)))
        self.assertTrue(send_text.call_args[0][1].startswith("Veja como funcionam as multas"))
        _, body, botoes = send_buttons.call_args[0]
        self.assertEqual(body, "Essa resposta te ajudou?")
        self.assertEqual(
            botoes,
            [("feedback:1:10", "Ajudou"), ("feedback:0:10", "Não ajudou"), ("inicio", "Menu inicial")],
        )

    def test_feedback(self, send_text, send_buttons, send_list):
        service.process(payload(clique("feedback:0:10")))
        fb = Feedback.query.one()
        self.assertEqual((fb.no_fluxo_id, fb.util), (10, False))
        self.assertEqual(send_buttons.call_args[0][2], [("inicio", "Menu inicial")])

    def test_feedback_de_no_inexistente_nao_quebra(self, send_text, send_buttons, send_list):
        service.process(payload(clique("feedback:1:999")))
        self.assertEqual(Feedback.query.count(), 0)

    def test_atendente_abre_um_atendimento_so(self, send_text, send_buttons, send_list):
        service.process(payload(clique(12)))  # Problema com multa
        service.process(payload(clique(9)))   # Falar com atendente, de novo
        self.assertEqual(Atendimento.query.count(), 1)
        at = Atendimento.query.one()
        self.assertEqual((at.status, at.telefone_solicitante), ("ABERTO", FONE))
        bot = Mensagem.query.filter_by(remetente="BOT").one()
        self.assertEqual(bot.texto, "Encaminhado pelo menu: Problema com multa")
        self.assertTrue(send_text.call_args[0][1].startswith("Seu atendimento já está aberto"))

    def test_texto_durante_atendimento_vai_para_a_atendente(self, send_text, send_buttons, send_list):
        service.process(payload(clique(9)))
        send_text.reset_mock()
        service.process(payload(texto("minha multa está errada")))
        send_text.assert_not_called()
        self.assertEqual(Mensagem.query.filter_by(remetente="USUARIO").one().texto, "minha multa está errada")

    def test_mensagem_repetida_pela_meta_e_ignorada(self, send_text, send_buttons, send_list):
        service.process(payload(clique(9, msg_id="wamid.1")))
        service.process(payload(clique(9, msg_id="wamid.1")))
        self.assertEqual(send_text.call_count, 1)

    def test_erro_numa_mensagem_nao_derruba_o_webhook(self, send_text, send_buttons, send_list):
        with patch.object(service, "_handle_text", side_effect=RuntimeError("falhou")), \
                self.assertLogs("app.whatsapp.webhook.service", "ERROR"):
            resp = self.client.post("/api/whatsapp/webhook/", json=payload(texto("oi"), clique(10)))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(send_text.call_args[0][1].startswith("Veja como funcionam"))

    def test_datas_no_formato_do_banco(self, send_text, send_buttons, send_list):
        service.process(payload(clique(9)))
        (criado,) = self.sql("select created_at from atendimento")[0]
        self.assertRegex(criado, r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")


class AssinaturaTestCase(BaseTestCase):
    def test_sem_app_secret_e_com_assinatura_obrigatoria_recusa(self):
        self.app.config["WHATSAPP_REQUIRE_SIGNATURE"] = True
        with self.assertLogs("app.whatsapp.webhook.routes", "ERROR"):
            resp = self.client.post("/api/whatsapp/webhook/", json=payload(texto("oi")))
        self.assertEqual(resp.status_code, 503)

    def test_assinatura_invalida(self):
        self.app.config["WHATSAPP_APP_SECRET"] = "segredo"
        with self.assertLogs("app.whatsapp.webhook.routes", "WARNING"):
            resp = self.client.post(
                "/api/whatsapp/webhook/", json=payload(texto("oi")),
                headers={"X-Hub-Signature-256": "sha256=errada"},
            )
        self.assertEqual(resp.status_code, 401)

    def test_verificacao_meta(self):
        resp = self.client.get(
            "/api/whatsapp/webhook/?hub.mode=subscribe&hub.verify_token=bbt_verify&hub.challenge=42"
        )
        self.assertEqual(resp.get_data(as_text=True), "42")
