"""Fontes e validação de vendas, independentes da interface Streamlit.

Cada linha representa um item de pedido. Um pedido pode ocupar várias linhas,
inclusive para o mesmo produto, mas deve pertencer a uma única data.
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from io import StringIO
import random
import re

import numpy as np
import pandas as pd


COLUNAS_OBRIGATORIAS = [
    "pedido_id", "data", "produto", "quantidade", "preco_unitario"
]
COLUNAS = [*COLUNAS_OBRIGATORIAS, "faturamento"]
LIMITE_BYTES = 10 * 1024 * 1024
LIMITE_LINHAS = 100_000


def _dataframe_vazio() -> pd.DataFrame:
    return pd.DataFrame({
        "pedido_id": pd.Series(dtype="str"),
        "data": pd.Series(dtype="datetime64[ns]"),
        "produto": pd.Series(dtype="str"),
        "quantidade": pd.Series(dtype="int64"),
        "preco_unitario": pd.Series(dtype="float64"),
        "faturamento": pd.Series(dtype="float64"),
    })


def _erro(campo: str, linhas: list[int], detalhe: str) -> ValueError:
    exemplos = ", ".join(str(linha) for linha in linhas[:5])
    restante = f" e mais {len(linhas) - 5}" if len(linhas) > 5 else ""
    return ValueError(f"Campo '{campo}', linha(s) {exemplos}{restante}: {detalhe}.")


def _normalizar_registros(registros: list[dict], linhas: list[int]) -> pd.DataFrame:
    if not registros:
        return _dataframe_vazio()

    df = pd.DataFrame(registros, columns=COLUNAS_OBRIGATORIAS)
    for campo in COLUNAS_OBRIGATORIAS:
        faltantes = df[campo].map(lambda valor: valor is None or pd.isna(valor))
        if faltantes.any():
            raise _erro(campo, [linhas[i] for i in np.flatnonzero(faltantes)], "valor obrigatório ausente")
        df[campo] = df[campo].map(str)
        vazios = df[campo].str.strip().eq("")
        if vazios.any():
            raise _erro(campo, [linhas[i] for i in np.flatnonzero(vazios)], "valor obrigatório vazio")

    # Datas têm formato explícito: não usamos inferência de mês/dia.
    datas = []
    datas_invalidas = []
    for i, valor in enumerate(df["data"]):
        valor = valor.strip()
        formato = (
            "%Y-%m-%d" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor)
            else "%d/%m/%Y" if re.fullmatch(r"\d{2}/\d{2}/\d{4}", valor)
            else None
        )
        try:
            if formato is None:
                raise ValueError("formato inválido")
            parsed = pd.Timestamp(datetime.strptime(valor, formato)).as_unit("ns")
            datas.append(parsed)
        except (ValueError, OverflowError):
            datas_invalidas.append(linhas[i])
            datas.append(pd.NaT)
    if datas_invalidas:
        raise _erro("data", datas_invalidas, "use uma data válida em AAAA-MM-DD ou DD/MM/AAAA")
    df["data"] = pd.Series(datas, dtype="datetime64[ns]")

    for campo in ["quantidade", "preco_unitario"]:
        texto = df[campo].str.strip()
        formato_valido = texto.str.fullmatch(r"[+\-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)")
        numeros = pd.to_numeric(texto.str.replace(",", ".", regex=False), errors="coerce")
        invalidos = ~formato_valido | ~np.isfinite(numeros.to_numpy(dtype=float))
        if campo == "quantidade":
            invalidos |= numeros.le(0) | numeros.mod(1).ne(0) | numeros.gt(2**53 - 1)
            detalhe = "informe uma quantidade inteira positiva e finita"
        else:
            invalidos |= numeros.lt(0)
            detalhe = "informe um preço finito maior ou igual a zero, sem separador de milhar"
        if invalidos.any():
            raise _erro(campo, [linhas[i] for i in np.flatnonzero(invalidos)], detalhe)
        df[campo] = numeros.astype("int64" if campo == "quantidade" else "float64")

    datas_por_pedido = df.groupby("pedido_id")["data"].transform("nunique")
    if datas_por_pedido.gt(1).any():
        raise _erro(
            "pedido_id", [linhas[i] for i in np.flatnonzero(datas_por_pedido.gt(1))],
            "o mesmo pedido não pode aparecer em datas diferentes",
        )
    with np.errstate(over="ignore", invalid="ignore"):
        df["faturamento"] = df["quantidade"] * df["preco_unitario"]
    invalidos = ~np.isfinite(df["faturamento"].to_numpy())
    if invalidos.any():
        raise _erro("faturamento", [linhas[i] for i in np.flatnonzero(invalidos)], "valor fora da faixa numérica suportada")
    # Valores individuais válidos ainda podem estourar as somas usadas nos
    # agrupamentos. Somamos quantidades em inteiros Python antes do pandas.
    if sum(int(valor) for valor in df["quantidade"]) > np.iinfo(np.int64).max:
        raise _erro("quantidade", linhas, "a soma das quantidades ultrapassa a faixa numérica suportada")
    with np.errstate(over="ignore", invalid="ignore"):
        receita_total = df["faturamento"].to_numpy().sum()
    if not np.isfinite(receita_total):
        raise _erro("faturamento", linhas, "a soma do faturamento ultrapassa a faixa numérica suportada")
    return df[COLUNAS]


def pedidos_para_dataframe(pedidos: list[dict]) -> pd.DataFrame:
    """Converte os pedidos originais de dados.py para o contrato tabular."""
    registros = []
    for numero, pedido in enumerate(pedidos, start=1):
        try:
            pedido_id, data_pedido, itens = pedido["id"], pedido["data"], pedido["itens"]
            if not itens:
                raise ValueError(f"Pedido {numero}: o pedido deve ter ao menos um item.")
            for item in itens:
                registros.append({
                    "pedido_id": pedido_id, "data": data_pedido,
                    "produto": item["produto"], "quantidade": item["quantidade"],
                    "preco_unitario": item["preco_unitario"],
                })
        except (KeyError, TypeError) as erro:
            raise ValueError(f"Pedido {numero}: estrutura inválida ou campo obrigatório ausente.") from erro
    return _normalizar_registros(registros, list(range(1, len(registros) + 1)))


def gerar_dados_demonstracao() -> pd.DataFrame:
    """Gera vendas fictícias reproduzíveis de 01/07/2026 a 30/09/2026.

    A amostra tem sazonalidade proposital; não representa resultados reais.
    """
    rng = random.Random(20260930)
    catalogo = [
        ("Hambúrguer", 20.0), ("X-bacon", 27.0), ("X-salada", 24.0),
        ("Cachorro-quente", 12.0), ("Batata frita", 15.0),
        ("Refrigerante", 6.0), ("Suco natural", 9.0),
        ("Água mineral", 4.0), ("Milk-shake", 18.0), ("Brownie", 10.0),
    ]
    pesos = [20, 12, 10, 15, 9, 22, 7, 4, 6, 4]
    inicio, fim = date(2026, 7, 1), date(2026, 9, 30)
    pedidos = []
    data_atual = inicio
    while data_atual <= fim:
        quantidade_pedidos = rng.randint(3, 6) + (2 if data_atual.weekday() >= 4 else 0)
        if data_atual.month == 9:
            quantidade_pedidos += 1
        for _ in range(quantidade_pedidos):
            produtos = rng.choices(catalogo, weights=pesos, k=rng.randint(1, 3))
            itens = [
                {"produto": produto, "preco_unitario": preco,
                 "quantidade": rng.choices([1, 2, 3], weights=[7, 3, 1])[0]}
                for produto, preco in produtos
            ]
            pedidos.append({
                "id": f"DEMO-{len(pedidos) + 1:05d}",
                "data": data_atual.isoformat(), "itens": itens,
            })
        data_atual += timedelta(days=1)
    return pedidos_para_dataframe(pedidos)


def ler_csv(conteudo: bytes) -> pd.DataFrame:
    """Importa itens de vendas sem inferir IDs numéricos nem descartar linhas.

    Aceita UTF-8/BOM, delimitador vírgula ou ponto e vírgula e decimal ponto
    ou vírgula. Colunas extras são ignoradas; faturamento é sempre recalculado.
    """
    if len(conteudo) > LIMITE_BYTES:
        raise ValueError("O arquivo deve ter no máximo 10 MB.")
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError as erro:
        raise ValueError("Codificação inválida. Salve o CSV como UTF-8 e tente novamente.") from erro
    if not texto.strip():
        raise ValueError("O arquivo CSV está vazio.")
    if "\x00" in texto:
        raise ValueError("O arquivo contém bytes nulos; envie um CSV de texto UTF-8.")

    # O cabeçalho identifica o delimitador sem depender da frequência dos
    # separadores em nomes de produtos ou valores decimais.
    delimitador = None
    for candidato in [";", ","]:
        try:
            cabecalho = next(csv.reader(StringIO(texto), delimiter=candidato, strict=True))
        except (StopIteration, csv.Error):
            continue
        if set(COLUNAS_OBRIGATORIAS).issubset({coluna.strip() for coluna in cabecalho}):
            delimitador = candidato
            break
    if delimitador is None:
        raise ValueError("Cabeçalho inválido. Colunas obrigatórias: " + ", ".join(COLUNAS_OBRIGATORIAS) + ". Use ',' ou ';' como separador.")

    leitor = csv.reader(StringIO(texto, newline=""), delimiter=delimitador, strict=True)
    registros, linhas = [], []
    try:
        cabecalho = [coluna.strip() for coluna in next(leitor)]
        if len(set(cabecalho)) != len(cabecalho):
            raise ValueError("O cabeçalho tem nomes de colunas repetidos.")
        for valores in leitor:
            if len(registros) >= LIMITE_LINHAS:
                raise ValueError("O arquivo deve ter no máximo 100.000 linhas de itens.")
            if len(valores) != len(cabecalho):
                raise ValueError(f"Linha {leitor.line_num}: quantidade de campos diferente do cabeçalho; verifique separadores e aspas.")
            registros.append(dict(zip(cabecalho, valores)))
            linhas.append(leitor.line_num)
    except csv.Error as erro:
        raise ValueError(f"CSV inválido próximo da linha {leitor.line_num}: verifique as aspas e os separadores.") from erro
    if not registros:
        raise ValueError("O CSV contém apenas o cabeçalho, sem itens de venda.")
    return _normalizar_registros(registros, linhas)


def _texto_seguro_csv(valor: object) -> str:
    texto = str(valor)
    # Aspas CSV não impedem fórmulas em planilhas. O apóstrofo é mantido
    # deliberadamente na reimportação para não remover caracteres legítimos.
    if texto.lstrip().startswith(("=", "+", "-", "@")) or texto.startswith(("\t", "\r", "\n")):
        return "'" + texto
    return texto


def dataframe_para_csv(df: pd.DataFrame) -> bytes:
    """Exporta seis colunas em UTF-8/BOM, ';' e vírgula decimal.

    Texto que possa iniciar uma fórmula recebe um apóstrofo de segurança.
    Esse prefixo permanece ao reimportar esses casos; textos comuns têm
    roundtrip exato. Não usamos fórmulas para preservar zeros dos IDs.
    """
    exportacao = df[COLUNAS].copy()
    for coluna in ["pedido_id", "produto"]:
        exportacao[coluna] = exportacao[coluna].map(_texto_seguro_csv)
    exportacao["data"] = pd.to_datetime(exportacao["data"]).dt.strftime("%Y-%m-%d")
    return exportacao.to_csv(index=False, sep=";", decimal=",", lineterminator="\n").encode("utf-8-sig")


def csv_modelo() -> bytes:
    """Exemplo importável com os pedidos originais do projeto."""
    from dados import pedidos

    return dataframe_para_csv(pedidos_para_dataframe(pedidos))
