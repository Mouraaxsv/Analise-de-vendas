"""Regressões funcionais do dashboard usando o runner oficial do Streamlit."""

from datetime import date
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(APP)).run(timeout=30)
        self.sem_erros()

    def sem_erros(self):
        self.assertEqual([erro.value for erro in self.app.exception], [])

    def valores(self):
        return [metrica.value for metrica in self.app.metric]

    def originais(self):
        self.app.selectbox(key="fonte").set_value("Pedidos originais").run(timeout=30)
        self.sem_erros()

    def personalizado(self, inicio, fim):
        self.app.selectbox(key="periodo").set_value("Personalizado").run()
        self.app.date_input(key="data_inicio").set_value(inicio)
        self.app.date_input(key="data_fim").set_value(fim).run(timeout=30)
        self.sem_erros()

    def test_demo_identificada_e_metricas_iniciais(self):
        self.assertEqual(self.valores(), ["R$ 7.907,00", "192", "R$ 41,18", "551"])
        self.assertEqual(self.app.selectbox(key="fonte").value, "Demonstração")
        self.assertTrue(all(metrica.delta for metrica in self.app.metric))

    def test_original_conta_pedidos_nao_itens_e_filtro_parcial(self):
        self.originais()
        self.assertEqual(self.valores(), ["R$ 94,00", "2", "R$ 47,00", "7"])
        self.assertTrue(all(not metrica.delta for metrica in self.app.metric))
        self.app.multiselect(key="produtos").set_value(["Cachorro-quente"]).run()
        self.assertEqual(self.valores(), ["R$ 48,00", "2", "R$ 24,00", "4"])
        self.personalizado(date(2026, 9, 24), date(2026, 9, 24))
        self.assertEqual(self.valores(), ["R$ 24,00", "1", "R$ 24,00", "2"])

    def test_periodo_vazio_e_datas_invertidas(self):
        self.originais()
        self.personalizado(date(2026, 10, 1), date(2026, 10, 2))
        self.assertEqual(self.valores(), ["R$ 0,00", "0", "R$ 0,00", "0"])
        self.assertTrue(any("Nenhuma venda" in mensagem.value for mensagem in self.app.info))
        self.app.date_input(key="data_inicio").set_value(date(2026, 10, 3)).run()
        self.sem_erros()
        self.assertEqual(len(self.app.error), 1)
        self.assertEqual(len(self.app.metric), 0)

    def test_navegacao_produtos_historico_busca_e_guia(self):
        self.originais()
        self.app.radio(key="pagina").set_value("Produtos").run(timeout=30)
        self.sem_erros()
        self.assertEqual(len(self.app.dataframe[0].value), 3)
        self.app.radio(key="pagina").set_value("Histórico de vendas").run(timeout=30)
        self.sem_erros()
        self.assertEqual(len(self.app.dataframe[0].value), 4)
        self.app.text_input(key="busca_historico").set_value("hambúrguer").run()
        self.assertEqual(len(self.app.dataframe[0].value), 1)
        self.assertEqual(self.valores(), ["R$ 94,00", "2", "R$ 47,00", "7"])
        self.app.text_input(key="busca_historico").set_value("[inexistente]").run()
        self.assertEqual(len(self.app.dataframe), 0)
        self.app.radio(key="pagina").set_value("Guia de uso").run(timeout=30)
        self.sem_erros()
        self.assertEqual(len(self.app.subheader), 4)

    def test_troca_de_fonte_reinicia_filtros(self):
        self.originais()
        self.app.multiselect(key="produtos").set_value(["Refrigerante"]).run()
        self.personalizado(date(2026, 9, 25), date(2026, 9, 25))
        self.app.selectbox(key="fonte").set_value("Demonstração").run(timeout=30)
        self.sem_erros()
        self.assertEqual(self.app.multiselect(key="produtos").value, [])
        self.assertEqual(self.app.date_input(key="data_inicio").value, date(2026, 9, 1))
        self.assertEqual(self.valores(), ["R$ 7.907,00", "192", "R$ 41,18", "551"])

    def test_importacao_sem_arquivo_orienta_sem_usar_demo(self):
        self.app.selectbox(key="fonte").set_value("Importar CSV").run()
        self.sem_erros()
        self.assertEqual(len(self.app.metric), 0)
        self.assertTrue(any("Envie um CSV" in mensagem.value for mensagem in self.app.info))
        self.app.radio(key="pagina").set_value("Guia de uso").run()
        self.sem_erros()

    def test_agrupamentos_nao_alteram_resumo(self):
        for frequencia in ["Semana", "Mês", "Dia"]:
            self.app.segmented_control(key="frequencia").set_value(frequencia).run(timeout=30)
            self.sem_erros()
            self.assertEqual(self.valores(), ["R$ 7.907,00", "192", "R$ 41,18", "551"])

    def test_intervalo_muito_longo_tem_aviso(self):
        self.personalizado(date(2020, 1, 1), date(2026, 9, 30))
        self.assertEqual(len(self.app.warning), 1)
        self.assertEqual(len(self.app.metric), 0)

    def test_periodo_apos_fim_da_base_nao_apresenta_queda_falsa(self):
        # O período anterior existe, mas outubro não está na base demonstrativa.
        self.personalizado(date(2026, 10, 1), date(2026, 10, 30))
        self.assertEqual(self.valores(), ["R$ 0,00", "0", "R$ 0,00", "0"])
        self.assertTrue(all(not metrica.delta for metrica in self.app.metric))
        self.assertTrue(any("ultrapassa o histórico" in texto.value for texto in self.app.caption))


if __name__ == "__main__":
    unittest.main()
