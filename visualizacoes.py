"""Gráficos interativos de vendas; recebem apenas resultados já calculados.

Os gráficos não alteram os DataFrames recebidos. O Pareto exibe os primeiros
40 produtos, mantendo os percentuais da base completa, e o mix reúne os itens
após os sete maiores em uma única fatia para preservar a legibilidade.
"""

from math import isfinite

import altair as alt
import pandas as pd


AZUL = "#315bdf"
VERDE = "#0d9488"
CINZA = "#94a3b8"
PALETA = [AZUL, VERDE, "#8b5cf6", "#f59e0b", "#38bdf8", "#db7093", "#64748b", "#cbd5e1"]
ROTULOS = {
    "faturamento": "Receita",
    "ticket_medio": "Ticket médio",
    "pedidos": "Pedidos",
    "unidades": "Unidades",
}


def _moeda(valor):
    return "R$ " + f"{float(valor):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _numero(valor):
    return f"{int(valor):,}".replace(",", ".")


def _estilo(grafico):
    return (
        grafico.configure(background="transparent", font="sans-serif")
        .configure_view(stroke=None)
        .configure_axis(
            labelColor="#64748b", titleColor="#64748b", labelFontSize=11,
            titleFontSize=11, domain=False, ticks=False,
            gridColor="#edf1f7", gridOpacity=1, labelPadding=10,
        )
        .configure_legend(
            labelColor="#64748b", labelFontSize=11, title=None,
            symbolType="circle", labelLimit=170,
        )
    )


def _eixo(metrica):
    if metrica in {"faturamento", "ticket_medio", "media_diaria"}:
        return alt.Axis(title=None, labelExpr="'R$ ' + format(datum.value, '.0f')", tickCount=5)
    return alt.Axis(title=None, format="d", tickCount=5)


def _validar_metrica(metrica, permitidas):
    if metrica not in permitidas:
        raise ValueError(f"Métrica deve ser uma de: {', '.join(permitidas)}.")


def grafico_evolucao(serie, metrica="faturamento"):
    """Série temporal com marcação interativa e valores monetários em reais."""
    _validar_metrica(metrica, ROTULOS)
    dados = serie.copy()
    dados["valor_exibido"] = dados[metrica].map(
        _moeda if metrica in {"faturamento", "ticket_medio"} else _numero
    )
    dados["data_exibida"] = pd.to_datetime(dados["data"]).dt.strftime("%d/%m/%Y")
    tooltip = [
        alt.Tooltip("data_exibida:N", title="Data"),
        alt.Tooltip("valor_exibido:N", title=ROTULOS[metrica]),
    ]
    base = alt.Chart(dados).encode(
        x=alt.X("data:T", axis=alt.Axis(title=None, format="%d/%m", grid=False, tickCount=7)),
        y=alt.Y(f"{metrica}:Q", axis=_eixo(metrica), scale=alt.Scale(zero=True)),
    )
    area = base.mark_area(
        interpolate="monotone",
        color=alt.Gradient(
            gradient="linear", x1=0, x2=0, y1=0, y2=1,
            stops=[alt.GradientStop(color="#315bdf33", offset=0),
                   alt.GradientStop(color="#315bdf00", offset=1)],
        ),
    )
    linha = base.mark_line(color=AZUL, strokeWidth=2.5, interpolate="monotone")
    hover = alt.selection_point(
        name="evolucao_hover", nearest=True, on="pointerover",
        fields=["data"], empty=False, clear="pointerout",
    )
    seletores = base.mark_point(opacity=0).encode(tooltip=tooltip).add_params(hover)
    pontos = base.mark_point(color=AZUL, filled=True, size=55).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0)), tooltip=tooltip,
    )
    regra = base.mark_rule(color="#cbd5e1", strokeDash=[3, 3]).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0)), tooltip=tooltip,
    )
    return _estilo((area + linha + seletores + pontos + regra).properties(height=290))


def grafico_ranking(ranking, metrica="faturamento", limite=8):
    """Ranking em barras; ordenação por métrica e nome para desempates."""
    _validar_metrica(metrica, ("faturamento", "unidades", "pedidos"))
    dados = ranking.sort_values([metrica, "produto"], ascending=[False, True]).head(limite).copy()
    dados["valor_exibido"] = dados[metrica].map(_moeda if metrica == "faturamento" else _numero)
    ordem = dados["produto"].tolist()
    maior_valor = float(dados[metrica].max()) if not dados.empty else 0.0
    # Reserva espaço à direita para os rótulos sem expandir o domínio abaixo
    # de zero, o que ocorreria com padding em uma escala quantitativa estreita.
    limite_superior = maior_valor * 1.55 if maior_valor > 0 else 1
    if not isfinite(limite_superior):
        limite_superior = maior_valor
    escala = alt.Scale(domainMin=0, domainMax=limite_superior, nice=False)
    base = alt.Chart(dados).encode(
        x=alt.X(f"{metrica}:Q", axis=_eixo(metrica), scale=escala),
        y=alt.Y("produto:N", sort=ordem, axis=alt.Axis(title=None, labelLimit=180, grid=False)),
        tooltip=[
            alt.Tooltip("produto:N", title="Produto"),
            alt.Tooltip("valor_exibido:N", title=ROTULOS[metrica]),
            alt.Tooltip("participacao:Q", title="Participação na receita (%)", format=".1f"),
        ],
    )
    barras = base.mark_bar(color=AZUL, cornerRadiusEnd=4, size=19)
    rotulos = base.mark_text(align="left", dx=8, color="#475569", fontSize=10).encode(text="valor_exibido:N")
    return _estilo((barras + rotulos).properties(height=290))


def grafico_pareto(ranking, limite=40):
    """Curva ABC: receita e percentual acumulado real dos até 40 primeiros."""
    dados = ranking.head(limite).copy()
    dados["receita_exibida"] = dados["faturamento"].map(_moeda)
    ordem = dados["produto"].tolist()
    base = alt.Chart(dados).encode(
        x=alt.X("produto:N", sort=ordem, axis=alt.Axis(title=None, labelAngle=-35, labelLimit=110, grid=False)),
    )
    tooltip = [
        alt.Tooltip("produto:N", title="Produto"),
        alt.Tooltip("receita_exibida:N", title="Receita"),
        alt.Tooltip("acumulado:Q", title="Receita acumulada (%)", format=".1f"),
        alt.Tooltip("classe_abc:N", title="Classe ABC"),
    ]
    barras = base.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        y=alt.Y("faturamento:Q", axis=_eixo("faturamento"), scale=alt.Scale(zero=True)),
        color=alt.Color(
            "classe_abc:N", scale=alt.Scale(domain=["A", "B", "C"], range=[AZUL, VERDE, CINZA]),
            legend=alt.Legend(orient="top", title="Classe ABC"),
        ),
        tooltip=tooltip,
    )
    linha = base.mark_line(color="#d97706", point=alt.OverlayMarkDef(filled=True, size=32), strokeWidth=2).encode(
        y=alt.Y("acumulado:Q", scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(title=None, orient="right", labelExpr="datum.value + '%'", grid=False)),
        tooltip=tooltip,
    )
    return _estilo((barras + linha).resolve_scale(y="independent").properties(height=300))


def grafico_semana(dias):
    """Receita média por ocorrência do dia, incluindo dias sem vendas."""
    dados = dias.sort_values("ordem").copy()
    dados["media_exibida"] = dados["media_diaria"].map(_moeda)
    dados["dia_curto"] = dados["dia_semana"].str[:3]
    grafico = alt.Chart(dados).mark_bar(color=VERDE, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=32).encode(
        x=alt.X("dia_curto:N", sort=dados["dia_curto"].tolist(), axis=alt.Axis(title=None, labelAngle=0, grid=False)),
        y=alt.Y("media_diaria:Q", axis=_eixo("media_diaria"), scale=alt.Scale(zero=True)),
        tooltip=[
            alt.Tooltip("dia_semana:N", title="Dia da semana"),
            alt.Tooltip("media_exibida:N", title="Receita média"),
            alt.Tooltip("dias:Q", title="Ocorrências no intervalo", format="d"),
            alt.Tooltip("pedidos:Q", title="Pedidos", format="d"),
        ],
    ).properties(height=250)
    return _estilo(grafico)


def grafico_mix(ranking):
    """Participação de receita dos sete líderes; demais produtos agrupados."""
    dados = ranking[["produto", "faturamento", "participacao"]].head(7).copy()
    restantes = ranking.iloc[7:]
    if not restantes.empty:
        # Evita colisão com um produto realmente chamado "Outros produtos".
        rotulo = "Outros produtos (agrupados)"
        while rotulo in ranking["produto"].values:
            rotulo += " ·"
        dados = pd.concat([dados, pd.DataFrame([{
            "produto": rotulo,
            "faturamento": restantes["faturamento"].sum(),
            "participacao": restantes["participacao"].sum(),
        }])], ignore_index=True)
    dados["receita_exibida"] = dados["faturamento"].map(_moeda)
    dados["ordem"] = range(len(dados))
    grafico = alt.Chart(dados).mark_arc(innerRadius=55, outerRadius=85, cornerRadius=3, padAngle=0.025).encode(
        theta=alt.Theta("faturamento:Q", stack=True),
        color=alt.Color("produto:N", scale=alt.Scale(domain=dados["produto"].tolist(), range=PALETA),
                        legend=alt.Legend(orient="bottom", columns=2, title=None,
                                          labelLimit=115, columnPadding=12, symbolSize=70)),
        order=alt.Order("ordem:Q"),
        tooltip=[
            alt.Tooltip("produto:N", title="Produto"),
            alt.Tooltip("receita_exibida:N", title="Receita"),
            alt.Tooltip("participacao:Q", title="Participação (%)", format=".1f"),
        ],
    ).properties(height=310)
    return _estilo(grafico)
