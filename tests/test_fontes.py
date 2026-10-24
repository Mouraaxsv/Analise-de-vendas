"""Testes de importação, validação e geração da base demonstrativa."""

import unittest
from unittest.mock import patch

import pandas as pd

from dados import pedidos
from fontes import (
    COLUNAS, csv_modelo, dataframe_para_csv, gerar_dados_demonstracao,
    ler_csv, pedidos_para_dataframe,
)


class FontesTests(unittest.TestCase):
    cabecalho = "pedido_id;data;produto;quantidade;preco_unitario\n"

    def csv(self, linhas):
        return (self.cabecalho + linhas).encode("utf-8")

    def test_converte_pedidos_originais(self):
        df = pedidos_para_dataframe(pedidos)
        self.assertEqual(df.columns.tolist(), COLUNAS)
        self.assertEqual(len(df), 4)
        self.assertEqual(df.pedido_id.nunique(), 2)
        self.assertEqual(df.faturamento.sum(), 94)
        self.assertEqual(df.quantidade.sum(), 7)

    def test_pedidos_vazios_tem_contrato(self):
        df = pedidos_para_dataframe([])
        self.assertEqual(df.columns.tolist(), COLUNAS)
        self.assertTrue(df.empty)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df.data))

    def test_modelo_e_roundtrip_normais(self):
        df = pedidos_para_dataframe(pedidos)
        pd.testing.assert_frame_equal(df, ler_csv(dataframe_para_csv(df)))
        pd.testing.assert_frame_equal(df, ler_csv(csv_modelo()))
        self.assertTrue(csv_modelo().startswith(b"\xef\xbb\xbf"))

    def test_decimal_brasileiro_e_zeros_id(self):
        df = ler_csv(self.csv('001;24/09/2026;Café;2;4,50\n'))
        self.assertEqual(df.pedido_id.iloc[0], "001")
        self.assertEqual(df.produto.iloc[0], "Café")
        self.assertEqual(df.faturamento.iloc[0], 9.0)
        self.assertEqual(df.data.iloc[0], pd.Timestamp("2026-09-24"))

    def test_virgula_separadora_com_aspas(self):
        df = ler_csv(b'pedido_id,data,produto,quantidade,preco_unitario\n01,2026-09-24,"Suco, natural",2,"4,5"\n')
        self.assertEqual(df.produto.iloc[0], "Suco, natural")
        self.assertEqual(df.faturamento.iloc[0], 9.0)

    def test_coluna_receita_fornecida_ignorada(self):
        df = ler_csv(b'pedido_id,data,produto,quantidade,preco_unitario,faturamento,extra\n01,2026-09-24,Produto,2,4.5,999,qualquer\n')
        self.assertEqual(df.faturamento.iloc[0], 9)
        self.assertEqual(df.columns.tolist(), COLUNAS)

    def test_mantem_nomes_parecidos_com_nulos_e_espacos(self):
        df = ler_csv(self.csv('NA;2026-09-24; NaN ;1;0\n'))
        self.assertEqual(df.pedido_id.iloc[0], "NA")
        self.assertEqual(df.produto.iloc[0], " NaN ")
        self.assertEqual(df.faturamento.iloc[0], 0)

    def test_datas_nao_sao_inferidas(self):
        df = ler_csv(self.csv('01;01/02/2026;Produto;1;2\n'))
        self.assertEqual(df.data.iloc[0], pd.Timestamp("2026-02-01"))
        for valor in ["02-01-2026", "2026/02/01", "31/02/2026", "2026-2-01", "9999-01-01"]:
            with self.subTest(valor=valor), self.assertRaisesRegex(ValueError, "data.*2"):
                ler_csv(self.csv(f'01;{valor};Produto;1;2\n'))

    def test_rejeita_quantidades_invalidas(self):
        for valor in ["0", "-1", "1.5", "1,5", "nan", "inf", "", "1e9", "9007199254740992"]:
            with self.subTest(valor=valor), self.assertRaisesRegex(ValueError, "quantidade.*2"):
                ler_csv(self.csv(f'01;2026-09-24;Produto;{valor};2\n'))

    def test_rejeita_precos_invalidos(self):
        for valor in ["-1", "nan", "inf", "-inf", "1.234,56", "", "R$ 2"]:
            with self.subTest(valor=valor), self.assertRaisesRegex(ValueError, "preco_unitario.*2"):
                ler_csv(self.csv(f'01;2026-09-24;Produto;1;{valor}\n'))

    def test_rejeita_campos_vazios(self):
        for campo, linha in [
            ("pedido_id", ";2026-09-24;Produto;1;2\n"),
            ("produto", "01;2026-09-24; ;1;2\n"),
            ("data", "01;;Produto;1;2\n"),
        ]:
            with self.subTest(campo=campo), self.assertRaisesRegex(ValueError, campo):
                ler_csv(self.csv(linha))

    def test_pedido_so_pode_ter_uma_data(self):
        with self.assertRaisesRegex(ValueError, "pedido_id.*2, 3"):
            ler_csv(self.csv("01;2026-09-24;A;1;2\n01;2026-09-25;B;1;2\n"))

    def test_nao_deduplica_itens_iguais(self):
        df = ler_csv(self.csv("01;2026-09-24;A;1;2\n01;2026-09-24;A;1;2\n"))
        self.assertEqual(len(df), 2)
        self.assertEqual(df.faturamento.sum(), 4)

    def test_csv_incompleto_malformado_e_encoding(self):
        casos = [b"", b"\xff", self.csv(""), self.csv("01;2026-09-24;A;1\n"),
                 self.csv('01;2026-09-24;"A;1;2\n'), b"pedido_id,data\n01,2026-09-24\n",
                 self.csv("01;2026-09-24;A;1;2\n\n"), self.csv("01;2026-09-24;A\x00;1;2\n")]
        for conteudo in casos:
            with self.subTest(conteudo=conteudo), self.assertRaises(ValueError):
                ler_csv(conteudo)

    def test_limites(self):
        with patch("fontes.LIMITE_BYTES", 8), self.assertRaisesRegex(ValueError, "10 MB"):
            ler_csv(self.csv("01;2026-09-24;A;1;2\n"))
        with patch("fontes.LIMITE_LINHAS", 1), self.assertRaisesRegex(ValueError, "100.000"):
            ler_csv(self.csv("01;2026-09-24;A;1;2\n02;2026-09-24;A;1;2\n"))

    def test_exportacao_neutraliza_formulas_sem_desfazer_apostrofos(self):
        df = ler_csv(self.csv("=1+1;2026-09-24;@SUM(A1);1;2\n"))
        exportado = dataframe_para_csv(df)
        reimportado = ler_csv(exportado)
        self.assertEqual(reimportado.pedido_id.iloc[0], "'=1+1")
        self.assertEqual(reimportado.produto.iloc[0], "'@SUM(A1)")
        pd.testing.assert_frame_equal(reimportado, ler_csv(dataframe_para_csv(reimportado)))

    def test_rejeita_overflow_agregado_quantidades(self):
        # Cada quantidade é exata em float64, mas a soma não cabe em int64.
        linha = f"01;2026-09-24;A;{2**53 - 1};0\n"
        with self.assertRaisesRegex(ValueError, "quantidade.*soma"):
            ler_csv(self.csv(linha * 1025))

    def test_rejeita_overflow_agregado_faturamento(self):
        preco = "9" + "0" * 307  # 9e307: finito por linha, soma de três é inf.
        linha = f"01;2026-09-24;A;1;{preco}\n"
        with self.assertRaisesRegex(ValueError, "faturamento.*soma"):
            ler_csv(self.csv(linha * 3))

    def test_rejeita_overflow_multiplicacao_item(self):
        preco = "9" + "0" * 307
        with self.assertRaisesRegex(ValueError, "faturamento.*faixa"):
            ler_csv(self.csv(f"01;2026-09-24;A;3;{preco}\n"))

    def test_demo_reproduzivel_e_consistente(self):
        df = gerar_dados_demonstracao()
        pd.testing.assert_frame_equal(df, gerar_dados_demonstracao())
        self.assertEqual(df.data.min(), pd.Timestamp("2026-07-01"))
        self.assertEqual(df.data.max(), pd.Timestamp("2026-09-30"))
        self.assertEqual(df.produto.nunique(), 10)
        self.assertGreater(df.pedido_id.nunique(), 450)
        self.assertLess(df.pedido_id.nunique(), 700)
        self.assertEqual(df.data.nunique(), 92)
        self.assertTrue(df.pedido_id.str.startswith("DEMO-").all())
        self.assertTrue(df.groupby("pedido_id").data.nunique().eq(1).all())
        self.assertTrue(df.faturamento.eq(df.quantidade * df.preco_unitario).all())


if __name__ == "__main__":
    unittest.main()
