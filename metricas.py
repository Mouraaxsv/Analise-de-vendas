"""Métricas de vendas sobre uma tabela de itens de pedido normalizada.

Cada linha representa um item, não um pedido. As contagens de pedidos sempre
usam IDs distintos; valores monetários representam receita bruta, não lucro.
"""

from collections.abc import Mapping
from math import isfinite

import numpy as np
import pandas as pd


COLUNAS_RESUMO = ("faturamento", "pedidos", "ticket_medio", "unidades", "produtos")
DIAS_SEMANA = (
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo",
)


def _limites(inicio, fim):
    inicio = pd.Timestamp(inicio).normalize()
    fim = pd.Timestamp(fim).normalize()
    if pd.isna(inicio) or pd.isna(fim) or inicio > fim:
        raise ValueError("Informe um intervalo de datas válido: início até fim.")
    return inicio, fim


def filtrar_vendas(df, inicio, fim, produtos=None):
    """Filtra datas inclusive e, quando fornecida, a seleção de produtos.

    Uma seleção vazia equivale a todos os produtos. Retorna uma cópia, sem
    modificar a tabela recebida.
    """
    inicio, fim = _limites(inicio, fim)
    mascara = df["data"].between(inicio, fim)
    if produtos is not None and len(produtos):
        mascara &= df["produto"].isin(produtos)
    return df.loc[mascara].copy()


def resumir_vendas(df):
    """Retorna indicadores do recorte; o ticket é receita / pedidos únicos."""
    receita = float(df["faturamento"].sum())
    pedidos = int(df["pedido_id"].nunique())
    return {
        "faturamento": receita,
        "pedidos": pedidos,
        "ticket_medio": receita / pedidos if pedidos else 0.0,
        "unidades": int(df["quantidade"].sum()),
        "produtos": int(df["produto"].nunique()),
    }


def comparar_periodos(atual, anterior):
    """Variação percentual por indicador; base zero retorna None.

    Aceita tabelas de itens ou os dicionários retornados por resumir_vendas.
    None significa comparação indisponível, inclusive quando ambos são zero
    ou quando o percentual excede a faixa de representação de float64.
    """
    atual = atual if isinstance(atual, Mapping) else resumir_vendas(atual)
    anterior = anterior if isinstance(anterior, Mapping) else resumir_vendas(anterior)
    resultado = {}
    for campo in COLUNAS_RESUMO:
        if not anterior[campo]:
            resultado[campo] = None
            continue
        variacao = (float(atual[campo]) / float(anterior[campo]) - 1) * 100
        resultado[campo] = variacao if isfinite(variacao) else None
    return resultado


def serie_temporal(df, inicio, fim, frequencia="D"):
    """Agrega por dia, semana (segunda a domingo) ou mês calendário.

    A data identifica o início do agrupamento. Primeiro e último agrupamentos
    podem ser parciais e contêm somente vendas no intervalo solicitado. Datas
    sem venda são mantidas; tickets semanais/mensais são recalculados a partir
    da receita e dos pedidos únicos, nunca pela média dos tickets diários.
    """
    inicio, fim = _limites(inicio, fim)
    periodos = {"D": "D", "W": "W-SUN", "MS": "M"}
    if frequencia not in periodos:
        raise ValueError("Frequência deve ser D (dia), W (semana) ou MS (mês).")
    periodo = periodos[frequencia]
    datas = pd.period_range(inicio, fim, freq=periodo).to_timestamp()
    recorte = filtrar_vendas(df, inicio, fim)
    recorte["data"] = recorte["data"].dt.to_period(periodo).dt.start_time
    resultado = (
        recorte.groupby("data", sort=True)
        .agg(
            pedidos=("pedido_id", "nunique"),
            unidades=("quantidade", "sum"),
            faturamento=("faturamento", "sum"),
        )
        .reindex(datas, fill_value=0)
        .rename_axis("data")
        .reset_index()
    )
    resultado["pedidos"] = resultado["pedidos"].astype(int)
    resultado["unidades"] = resultado["unidades"].astype(int)
    resultado["faturamento"] = resultado["faturamento"].astype(float)
    resultado["ticket_medio"] = resultado["faturamento"].div(
        resultado["pedidos"].replace(0, np.nan)
    ).fillna(0.0)
    return resultado


def ranking_produtos(df):
    """Receita, volume, preço médio ponderado e curva ABC de produtos.

    Participações são percentuais de 0 a 100. O item que cruza 80% integra a
    classe A; o que cruza 95% integra B. Em receita total zero, todos são C,
    pois a distribuição de receita não permite uma priorização econômica.
    """
    resultado = (
        df.groupby("produto", as_index=False)
        .agg(
            unidades=("quantidade", "sum"),
            pedidos=("pedido_id", "nunique"),
            faturamento=("faturamento", "sum"),
        )
        .sort_values(["faturamento", "produto"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    resultado["preco_medio"] = resultado["faturamento"].div(
        resultado["unidades"].replace(0, np.nan)
    ).fillna(0.0)
    total = float(resultado["faturamento"].sum())
    resultado["participacao"] = resultado["faturamento"] / total * 100 if total else 0.0
    resultado["acumulado"] = resultado["participacao"].cumsum().clip(upper=100)
    anterior = (resultado["acumulado"] - resultado["participacao"]).round(10)
    resultado["classe_abc"] = (
        np.select([anterior < 80, anterior < 95], ["A", "B"], default="C")
        if total else "C"
    )
    return resultado


def analisar_dias_semana(df, inicio, fim):
    """Inclui dias sem venda no denominador da receita média por dia da semana."""
    inicio, fim = _limites(inicio, fim)
    recorte = filtrar_vendas(df, inicio, fim)
    recorte["ordem"] = recorte["data"].dt.dayofweek
    resultado = (
        recorte.groupby("ordem")
        .agg(faturamento=("faturamento", "sum"), pedidos=("pedido_id", "nunique"))
        .reindex(range(7), fill_value=0)
        .reset_index()
    )
    contagem_dias = pd.Series(pd.date_range(inicio, fim).dayofweek).value_counts()
    resultado["dias"] = resultado["ordem"].map(contagem_dias).fillna(0).astype(int)
    resultado["dia_semana"] = resultado["ordem"].map(dict(enumerate(DIAS_SEMANA)))
    resultado["media_diaria"] = resultado["faturamento"].div(
        resultado["dias"].replace(0, np.nan)
    ).fillna(0.0)
    return resultado[["dia_semana", "ordem", "faturamento", "pedidos", "dias", "media_diaria"]]


def _moeda(valor):
    return "R$ " + f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _percentual(valor):
    return f"{valor:.1f}%".replace(".", ",")


def gerar_insights(df, anterior, inicio, fim):
    """Produz observações descritivas sem inferir causa, lucro ou previsão."""
    resumo = resumir_vendas(df)
    if not resumo["pedidos"]:
        return [{"titulo": "Período sem vendas", "texto": "Nenhum pedido corresponde aos filtros selecionados. Experimente ampliar o período ou a seleção de produtos."}]

    insights = []
    variacao = comparar_periodos(df, anterior)["faturamento"]
    if variacao is not None:
        sentido = "aumentou" if variacao > 0 else "caiu" if variacao < 0 else "permaneceu estável"
        texto = (
            f"A receita {sentido} {_percentual(abs(variacao))} em relação ao período anterior de mesma duração."
            if variacao else "A receita permaneceu estável em relação ao período anterior de mesma duração."
        )
    elif resumir_vendas(anterior)["faturamento"]:
        texto = "A variação de receita excede a faixa numérica suportada; o percentual não é exibido."
    else:
        texto = "O período anterior não tem receita. A variação percentual não é calculável com base zero."
    insights.append({"titulo": "Comparação de receita", "texto": texto})

    ranking = ranking_produtos(df)
    lider = ranking.iloc[0]
    if resumo["faturamento"]:
        insights.append({
            "titulo": "Maior participação na receita",
            "texto": f"{lider['produto']} representa {_percentual(lider['participacao'])} da receita do recorte ({_moeda(lider['faturamento'])}).",
        })
        classe_a = ranking.loc[ranking["classe_abc"].eq("A")]
        insights.append({
            "titulo": "Concentração de produtos",
            "texto": f"{len(classe_a)} de {len(ranking)} produtos compõem a classe A e concentram {_percentual(classe_a['participacao'].sum())} da receita.",
        })
    dias = analisar_dias_semana(df, inicio, fim)
    if resumo["faturamento"]:
        destaque = dias.loc[dias["media_diaria"].idxmax()]
        insights.append({
            "titulo": "Dia da semana em destaque",
            "texto": f"{destaque['dia_semana']} teve a maior receita média: {_moeda(destaque['media_diaria'])} por dia, considerando {destaque['dias']} ocorrência(s) no intervalo, inclusive dias sem vendas.",
        })
    return insights
