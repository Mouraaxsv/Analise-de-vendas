"""Verificações do contrato analítico usando itens de pedidos conhecidos."""

from datetime import date
import unittest

import pandas as pd

from metricas import (
    analisar_dias_semana, comparar_periodos, filtrar_vendas, gerar_insights,
    ranking_produtos, resumir_vendas, serie_temporal,
)


def tabela(linhas):
    df = pd.DataFrame(linhas, columns=["pedido_id", "data", "produto", "quantidade", "preco_unitario"])
    df["data"] = pd.to_datetime(df["data"])
    df["faturamento"] = df["quantidade"] * df["preco_unitario"]
    return df


class MetricasTests(unittest.TestCase):
    def setUp(self):
        self.df = tabela([
            ("1", "2026-09-21", "Hambúrguer", 2, 20.0),
            ("1", "2026-09-21", "Suco", 1, 10.0),
            ("2", "2026-09-21", "Suco", 1, 10.0),
            ("3", "2026-09-23", "Hambúrguer", 1, 20.0),
            ("4", "2026-09-28", "Suco", 2, 10.0),
        ])

    def test_resumo_conta_pedidos_distintos_e_ticket(self):
        self.assertEqual(resumir_vendas(self.df), {
            "faturamento": 100.0, "pedidos": 4, "ticket_medio": 25.0,
            "unidades": 7, "produtos": 2,
        })

    def test_filtrar_inclui_extremos_produtos_e_nao_muda_fonte(self):
        recorte = filtrar_vendas(self.df, date(2026, 9, 21), date(2026, 9, 23), ["Suco"])
        self.assertEqual(len(recorte), 2)
        self.assertEqual(len(filtrar_vendas(self.df, "2026-09-21", "2026-09-28", [])), 5)
        recorte.loc[:, "quantidade"] = 999
        self.assertEqual(self.df["quantidade"].sum(), 7)
        with self.assertRaises(ValueError):
            filtrar_vendas(self.df, "2026-09-28", "2026-09-21")

    def test_variacao_percentual_e_base_zero(self):
        atual = self.df.iloc[:3]
        anterior = self.df.iloc[3:]
        self.assertAlmostEqual(comparar_periodos(atual, anterior)["faturamento"], 50.0)
        self.assertEqual(comparar_periodos(atual, self.df.iloc[:0])["faturamento"], None)
        self.assertEqual(comparar_periodos(self.df.iloc[:0], anterior)["faturamento"], -100.0)

    def test_serie_diaria_inclui_dia_sem_venda(self):
        serie = serie_temporal(self.df, "2026-09-21", "2026-09-23")
        self.assertEqual(serie["faturamento"].tolist(), [60.0, 0.0, 20.0])
        self.assertEqual(serie["pedidos"].tolist(), [2, 0, 1])
        self.assertEqual(serie["ticket_medio"].tolist(), [30.0, 0.0, 20.0])

    def test_serie_semana_mes_recalcula_ticket(self):
        semanal = serie_temporal(self.df, "2026-09-21", "2026-09-28", "W")
        self.assertEqual(semanal["pedidos"].tolist(), [3, 1])
        self.assertAlmostEqual(semanal.iloc[0]["ticket_medio"], 80 / 3)
        mensal = serie_temporal(self.df, "2026-09-21", "2026-10-31", "MS")
        self.assertEqual(mensal["faturamento"].tolist(), [100.0, 0.0])
        self.assertEqual(mensal["ticket_medio"].tolist(), [25.0, 0.0])
        with self.assertRaises(ValueError):
            serie_temporal(self.df, "2026-09-21", "2026-09-28", "Y")

    def test_ranking_preco_ponderado_participacao_e_pedido(self):
        df = tabela([
            ("1", "2026-09-21", "A", 2, 10.0),
            ("1", "2026-09-21", "A", 1, 40.0),
            ("2", "2026-09-21", "B", 2, 20.0),
        ])
        ranking = ranking_produtos(df)
        self.assertEqual(ranking["pedidos"].tolist(), [1, 1])
        self.assertEqual(ranking["preco_medio"].tolist(), [20.0, 20.0])
        self.assertEqual(ranking["participacao"].tolist(), [60.0, 40.0])
        self.assertEqual(ranking["acumulado"].tolist(), [60.0, 100.0])

    def test_curva_abc_item_que_cruza_limiar(self):
        df = tabela([(str(i), "2026-09-21", p, 1, v) for i, (p, v) in enumerate([
            ("A", 75), ("B", 10), ("C", 8), ("D", 4), ("E", 3),
        ])])
        self.assertEqual(ranking_produtos(df)["classe_abc"].tolist(), ["A", "A", "B", "B", "C"])

    def test_curva_abc_limite_exato_e_desempate(self):
        df = tabela([(str(i), "2026-09-21", p, 1, v) for i, (p, v) in enumerate([
            ("A", 80), ("B", 15), ("D", 2.5), ("C", 2.5),
        ])])
        ranking = ranking_produtos(df)
        self.assertEqual(ranking["classe_abc"].tolist(), ["A", "B", "C", "C"])
        self.assertEqual(ranking["produto"].tolist(), ["A", "B", "C", "D"])

    def test_dia_semana_inclui_datas_sem_venda_no_denominador(self):
        dias = analisar_dias_semana(self.df, "2026-09-21", "2026-10-05").set_index("ordem")
        self.assertEqual(dias.loc[0, "dias"], 3)
        self.assertEqual(dias.loc[0, "faturamento"], 80)
        self.assertAlmostEqual(dias.loc[0, "media_diaria"], 80 / 3)
        self.assertEqual(dias.loc[1, "media_diaria"], 0)

    def test_vazios_e_receita_zero_sem_nan(self):
        vazio = self.df.iloc[:0]
        self.assertEqual(resumir_vendas(vazio)["ticket_medio"], 0)
        self.assertTrue(ranking_produtos(vazio).empty)
        self.assertEqual(len(serie_temporal(vazio, "2026-09-21", "2026-09-23")), 3)
        self.assertFalse(serie_temporal(vazio, "2026-09-21", "2026-09-23").isna().any().any())
        self.assertEqual(gerar_insights(vazio, vazio, "2026-09-21", "2026-09-23")[0]["titulo"], "Período sem vendas")
        zero = tabela([("1", "2026-09-21", "Brinde", 1, 0.0)])
        self.assertEqual(ranking_produtos(zero)["classe_abc"].tolist(), ["C"])
        self.assertEqual(ranking_produtos(zero)["participacao"].tolist(), [0.0])
        self.assertTrue(gerar_insights(zero, vazio, "2026-09-21", "2026-09-23"))

    def test_insights_contem_fatos_do_recorte(self):
        insights = gerar_insights(self.df, self.df.iloc[:0], "2026-09-21", "2026-09-28")
        self.assertEqual(len(insights), 4)
        self.assertIn("Hambúrguer", insights[1]["texto"])
        self.assertIn("60,0%", insights[1]["texto"])

    def test_datas_extremas_aceitas_pela_importacao(self):
        # Inícios da semana/mês podem anteceder o mínimo de datetime64[ns].
        # O pandas deve preservar datas corretas em resolução mais ampla.
        for data in ["1677-09-22", "2262-04-11"]:
            df = tabela([("1", data, "A", 1, 10.0)])
            for frequencia in ["D", "W", "MS"]:
                with self.subTest(data=data, frequencia=frequencia):
                    serie = serie_temporal(df, data, data, frequencia)
                    self.assertEqual(len(serie), 1)
                    self.assertEqual(serie.iloc[0]["faturamento"], 10.0)
                    self.assertEqual(serie.iloc[0]["pedidos"], 1)
            dias = analisar_dias_semana(df, data, data)
            self.assertEqual(dias["dias"].sum(), 1)
            self.assertEqual(dias["media_diaria"].sum(), 10.0)
        inicio_mes = serie_temporal(
            tabela([("1", "1677-09-22", "A", 1, 10.0)]),
            "1677-09-22", "1677-09-22", "MS",
        ).iloc[0]["data"]
        self.assertEqual(inicio_mes.date(), date(1677, 9, 1))

    def test_percentuais_nao_exibem_infinito_em_receitas_finitas(self):
        atual = tabela([("1", "2026-09-22", "A", 1, 1e308)])
        anterior = tabela([("2", "2026-09-21", "A", 1, 1.0)])
        self.assertIsNone(comparar_periodos(atual, anterior)["faturamento"])
        insights = gerar_insights(atual, anterior, "2026-09-22", "2026-09-22")
        self.assertIn("faixa numérica", insights[0]["texto"])
        self.assertAlmostEqual(comparar_periodos(atual, atual)["faturamento"], 0.0)

    def test_ranking_receitas_minusculas_mantem_participacoes(self):
        df = tabela([
            ("1", "2026-09-21", "A", 1, 1e-300),
            ("2", "2026-09-21", "B", 1, 2e-300),
        ])
        ranking = ranking_produtos(df)
        self.assertAlmostEqual(ranking["participacao"].sum(), 100.0)
        self.assertAlmostEqual(ranking.iloc[0]["participacao"], 200 / 3)
        self.assertFalse(ranking.isna().any().any())

    def test_somas_unidades_proximas_do_limite_int64(self):
        quantidade = 2**53 - 1
        df = tabela([("1", "2026-09-21", "A", quantidade, 0.0)] * 1024)
        esperado = quantidade * 1024
        self.assertEqual(resumir_vendas(df)["unidades"], esperado)
        self.assertEqual(ranking_produtos(df).iloc[0]["unidades"], esperado)
        self.assertEqual(serie_temporal(df, "2026-09-21", "2026-09-21").iloc[0]["unidades"], esperado)


if __name__ == "__main__":
    unittest.main()
