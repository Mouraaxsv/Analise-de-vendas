"""Dashboard analítico de vendas. Execute com `streamlit run app.py`."""

from datetime import date, timedelta
from hashlib import sha256
from html import escape

import streamlit as st

from dados import pedidos
from fontes import (
    csv_modelo, dataframe_para_csv, gerar_dados_demonstracao,
    ler_csv, pedidos_para_dataframe,
)
from metricas import (
    analisar_dias_semana, comparar_periodos, filtrar_vendas, gerar_insights,
    ranking_produtos, resumir_vendas, serie_temporal,
)
from visualizacoes import (
    grafico_evolucao, grafico_mix, grafico_pareto, grafico_ranking, grafico_semana,
)

st.set_page_config(
    page_title="VendaLab · Análise de vendas", page_icon="📊",
    layout="wide", initial_sidebar_state="expanded",
)


def numero(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def moeda(valor):
    return f"R$ {numero(valor, 2)}"


def intervalo(inicio, fim):
    return f"{inicio:%d/%m/%Y} — {fim:%d/%m/%Y}"


def aplicar_estilo():
    st.html("""
    <style>
    .stApp { background: #f5f7fb; }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1560px; padding: 2.4rem 3rem 1.5rem; }
    h1, h2, h3 { color: #15233d; letter-spacing: -.035em; }
    h1 { font-size: 2.15rem !important; font-weight: 750 !important; }
    h2 { font-size: 1.32rem !important; }
    h3 { font-size: 1.1rem !important; }
    p { line-height: 1.6; }
    [data-testid="stSidebar"] { background: #12223b; }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #c3cee2; }
    [data-testid="stSidebar"] hr { border-color: #2b3d57; }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: .6rem; }
    [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { gap: .35rem; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
      padding: .65rem .7rem; border-radius: 9px; margin: 0;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
      background: #294260; color: white;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label p { color: #e5ecf7; }
    [data-testid="stSidebar"] button[kind="secondary"] { background: #203752; color: #eef4ff; border-color: #38516f; }
    [data-testid="stSidebar"] [data-testid="stExpander"] { border-color: #38516f; }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary { color: #c3cee2; }
    [data-testid="stMain"] [class*="st-key-card_"],
    [data-testid="stMain"] [class*="st-key-kpi_"] {
      background: white; border-color: #e4e9f2 !important; border-radius: 13px;
    }
    [data-testid="stMetricLabel"] { color: #66758d; font-size: .85rem; }
    [data-testid="stMetricValue"] { color: #172740; font-size: 1.85rem; font-weight: 700; letter-spacing: -.04em; }
    [data-testid="stCaptionContainer"] { opacity: 1; }
    [data-testid="stCaptionContainer"] p { color: #5b6880; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #aebed5; }
    [data-testid="stMain"] button { border-radius: 8px; }
    .eyebrow { color: #7b889c; font-size: .69rem; font-weight: 650; letter-spacing: .15em; margin-bottom: .55rem; }
    .brand { display: flex; align-items: center; gap: 11px; padding: .5rem 0 1.6rem; }
    .brand-mark { display: flex; align-items: end; justify-content: center; gap: 3px; width: 39px; height: 39px; padding: 10px; background: #5677ee; border-radius: 11px; }
    .brand-mark i { display: block; width: 5px; background: white; border-radius: 2px; }
    .brand-name { color: white; font-size: 1.5rem; font-weight: 750; letter-spacing: -.04em; }
    .brand-caption { font-size: .57rem; letter-spacing: .15em; color: #95aac6; margin-top: -2px; }
    .source-badge { display: inline-block; font-size: .66rem; font-weight: 650; letter-spacing: .07em; padding: 5px 9px; border-radius: 5px; color: #0b766e; background: #e4f5ef; }
    .period-label { display: inline-block; color: #6a7890; margin-left: 12px; font-size: .8rem; }
    .insight { padding: .8rem 0; border-bottom: 1px solid #edf0f6; }
    .insight:last-child { border: 0; }
    .insight strong { display: block; color: #273b58; font-size: .83rem; margin-bottom: .3rem; }
    .insight p { margin: 0; color: #5b6880; font-size: .83rem; line-height: 1.6; }
    .footer { color: #8190a6; font-size: .72rem; padding: 1.6rem 0 .4rem; border-top: 1px solid #e5eaf2; margin-top: 1rem; }
    .st-key-kpi_faturamento [data-testid="stMetricValue"] { color: #315bdf; }
    @media (max-width: 760px) {
      .block-container { padding: 1.7rem 1rem 1rem; }
      h1 { font-size: 1.8rem !important; }
      .period-label { display: block; margin: 8px 0; }
    }
    </style>
    """)


@st.cache_data(show_spinner=False)
def base_demonstracao():
    return gerar_dados_demonstracao()


def ajuda_csv():
    st.caption("Uma linha por item vendido. Um pedido pode ter vários itens.")
    st.code(
        "pedido_id;data;produto;quantidade;preco_unitario\n"
        "001;2026-09-24;Hambúrguer;2;20,00\n"
        "001;2026-09-24;Refrigerante;1;6,00", language="text",
    )
    st.caption("CSV em UTF-8, até 10 MB e 100 mil itens. Datas em AAAA-MM-DD ou DD/MM/AAAA. Preços sem separador de milhar.")
    st.download_button(
        "Baixar CSV de exemplo", csv_modelo(), "modelo_vendas.csv", "text/csv",
        icon=":material/download:", key="modelo_csv", width="stretch",
    )


def carregar_fonte():
    fonte = st.selectbox(
        "Fonte de dados", ["Demonstração", "Pedidos originais", "Importar CSV"], key="fonte",
    )
    if fonte == "Demonstração":
        st.caption("Base fictícia para explorar as análises.")
        return base_demonstracao(), fonte, "demonstracao", None
    if fonte == "Pedidos originais":
        return pedidos_para_dataframe(pedidos), fonte, "originais", None
    arquivo = st.file_uploader("Seu arquivo de vendas", type=["csv"], max_upload_size=10)
    if arquivo is None:
        return None, fonte, None, "Envie um CSV na barra lateral para começar a análise."
    conteudo = arquivo.getvalue()
    identificador = sha256(conteudo).hexdigest()
    if st.session_state.get("_csv_identificador") == identificador:
        return st.session_state["_csv_dataframe"], fonte, identificador, None
    try:
        # Cache privado por sessão: filtros não precisam revalidar todo o CSV.
        dataframe = ler_csv(conteudo)
        st.session_state["_csv_identificador"] = identificador
        st.session_state["_csv_dataframe"] = dataframe
        return dataframe, fonte, identificador, None
    except ValueError as erro:
        return None, fonte, None, str(erro)


def configurar_filtros(df, identificador):
    minimo, maximo = df["data"].min().date(), df["data"].max().date()
    if st.session_state.get("_base_atual") != identificador:
        st.session_state["_base_atual"] = identificador
        st.session_state["periodo"] = "Últimos 30 dias"
        st.session_state["data_inicio"] = max(minimo, maximo - timedelta(days=29))
        st.session_state["data_fim"] = maximo
        st.session_state["produtos"] = []
    st.markdown("**Filtros da análise**")
    periodo = st.selectbox(
        "Período", ["Últimos 30 dias", "Últimos 7 dias", "Todo o período", "Personalizado"], key="periodo",
    )
    if periodo != "Personalizado":
        dias = 6 if periodo == "Últimos 7 dias" else 29
        st.session_state["data_inicio"] = minimo if periodo == "Todo o período" else max(minimo, maximo - timedelta(days=dias))
        st.session_state["data_fim"] = maximo
    inicio = st.date_input("Data de início", key="data_inicio", format="DD/MM/YYYY", disabled=periodo != "Personalizado", min_value=date(1677, 9, 22), max_value=date(2262, 4, 11))
    fim = st.date_input("Data de fim", key="data_fim", format="DD/MM/YYYY", disabled=periodo != "Personalizado", min_value=date(1677, 9, 22), max_value=date(2262, 4, 11))
    st.caption("Atalhos usam a última data da base, não a data de hoje.")
    produtos = st.multiselect("Produtos", sorted(df["produto"].unique()), placeholder="Todos os produtos", key="produtos")
    st.caption("Seleção vazia inclui todos os produtos.")
    return inicio, fim, produtos


def cabecalho(pagina):
    descricoes = {
        "Visão geral": "Os principais números do seu negócio, em um só lugar.",
        "Produtos": "Entenda o mix de vendas e os produtos que sustentam sua receita.",
        "Histórico de vendas": "Explore os itens vendidos e leve os dados para sua próxima análise.",
        "Guia de uso": "Conheça seus indicadores e prepare os dados para a análise.",
    }
    st.html('<div class="eyebrow">VENDALAB &nbsp; / &nbsp; INTELIGÊNCIA DE VENDAS</div>')
    st.title(pagina)
    st.caption(descricoes[pagina])


def mostrar_indicadores(resumo, variacoes, comparavel):
    indicadores = [
        ("faturamento", "Faturamento", moeda, "Receita bruta: quantidade × preço unitário. Não representa lucro."),
        ("pedidos", "Pedidos", numero, "Pedidos distintos com pelo menos um item no recorte."),
        ("ticket_medio", "Ticket médio", moeda, "Receita dos itens selecionados ÷ pedidos distintos. Com filtro de produto, é um ticket parcial."),
        ("unidades", "Unidades vendidas", numero, "Soma das quantidades vendidas, não da quantidade de linhas."),
    ]
    for coluna, (campo, titulo, formatar, ajuda) in zip(st.columns(4, gap="medium"), indicadores):
        with coluna, st.container(border=True, key=f"kpi_{campo}"):
            valor = variacoes[campo] if comparavel else None
            delta = f"{numero(valor, 1)}%" if valor is not None else None
            st.metric(titulo, formatar(resumo[campo]), delta=delta, help=ajuda)
            st.caption("vs. período anterior" if valor is not None else "Sem base comparável")


def visao_geral(df, anterior, inicio, fim, comparavel, ranking):
    esquerda, direita = st.columns([2.15, 1], gap="medium")
    with esquerda, st.container(border=True, key="card_evolucao"):
        st.subheader("Evolução das vendas")
        st.caption("Receita, volume e ticket ao longo do período.")
        controles = st.columns([1, 1.4])
        metrica = controles[0].selectbox(
            "Indicador", ["Faturamento", "Pedidos", "Ticket médio", "Unidades"], label_visibility="collapsed", key="metrica_evolucao",
        )
        frequencia = controles[1].segmented_control(
            "Agrupamento", ["Dia", "Semana", "Mês"], default="Dia", required=True, label_visibility="collapsed", key="frequencia",
        )
        campos = {"Faturamento": "faturamento", "Pedidos": "pedidos", "Ticket médio": "ticket_medio", "Unidades": "unidades"}
        serie = serie_temporal(df, inicio, fim, {"Dia": "D", "Semana": "W", "Mês": "MS"}[frequencia])
        st.altair_chart(grafico_evolucao(serie, campos[metrica]), width="stretch")
        st.caption("Dias sem registros entram como zero. Semanas começam na segunda; agrupamentos nas pontas podem ser parciais.")
    with direita, st.container(border=True, key="card_insights"):
        st.subheader("Leitura rápida")
        st.caption("Observações calculadas a partir do recorte.")
        insights = gerar_insights(df, anterior, inicio, fim)
        if not comparavel:
            insights = [i for i in insights if i["titulo"] != "Comparação de receita"]
        for insight in insights:
            st.html('<div class="insight"><strong>' + escape(insight["titulo"]) + '</strong><p>' + escape(insight["texto"]) + '</p></div>')
        st.caption("Análise descritiva · sem previsão de resultados.")
    esquerda, direita = st.columns([1.25, 1], gap="medium")
    with esquerda, st.container(border=True, key="card_ranking"):
        st.subheader("Produtos em destaque")
        st.caption("Os 8 líderes em faturamento no período selecionado.")
        st.altair_chart(grafico_ranking(ranking), width="stretch")
    with direita, st.container(border=True, key="card_semana"):
        st.subheader("O ritmo da semana")
        st.caption("Faturamento médio por dia da semana.")
        st.altair_chart(grafico_semana(analisar_dias_semana(df, inicio, fim)), width="stretch")
        st.caption("Total de cada dia da semana ÷ suas ocorrências no intervalo, incluindo dias sem vendas.")


def tabela_produtos(ranking):
    nomes = {
        "produto": "Produto", "unidades": "Unidades", "pedidos": "Pedidos",
        "faturamento": "Faturamento", "preco_medio": "Preço médio",
        "participacao": "Participação", "acumulado": "% acumulada", "classe_abc": "Classe ABC",
    }
    tabela = ranking.rename(columns=nomes)
    st.dataframe(tabela.style.format({
        "Faturamento": moeda, "Preço médio": moeda, "Participação": lambda x: numero(x, 1) + "%",
        "% acumulada": lambda x: numero(x, 1) + "%", "Unidades": numero, "Pedidos": numero,
    }), hide_index=True, width="stretch")


def analisar_produtos(ranking):
    esquerda, direita = st.columns([1.8, 1], gap="medium")
    with esquerda, st.container(border=True, key="card_abc"):
        st.subheader("Curva ABC de produtos")
        st.caption("Identifique onde sua receita está concentrada.")
        st.altair_chart(grafico_pareto(ranking), width="stretch")
        st.caption("A: até cruzar 80% da receita · B: até cruzar 95% · C: restante. O produto que cruza o limite permanece na classe anterior.")
        if len(ranking) > 40:
            st.caption("O gráfico exibe os 40 líderes; os percentuais consideram todos os produtos.")
    with direita, st.container(border=True, key="card_mix"):
        st.subheader("Composição da receita")
        st.caption("Participação de cada produto no faturamento.")
        if ranking["faturamento"].sum() > 0:
            st.altair_chart(grafico_mix(ranking), width="stretch")
            st.caption("Até 7 produtos; os demais aparecem como Outros produtos.")
        else:
            st.info("Os itens deste recorte não geraram receita. Não há participação a calcular.")
    with st.container(border=True, key="card_produtos"):
        st.subheader("Desempenho por produto")
        st.caption("Clique nos títulos das colunas para ordenar. Preço médio ponderado pelas unidades vendidas.")
        tabela_produtos(ranking)
        st.caption("Pedidos por produto não devem ser somados: o mesmo pedido pode conter produtos diferentes.")
        exportacao = ranking.copy()
        exportacao["produto"] = exportacao["produto"].map(
            lambda x: "'" + x if x.lstrip().startswith(("=", "+", "-", "@")) or x.startswith(("\t", "\n", "\r")) else x
        )
        st.download_button(
            "Exportar análise de produtos", exportacao.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            "analise_produtos.csv", "text/csv", icon=":material/download:",
        )


def historico_vendas(df):
    with st.container(border=True, key="card_historico"):
        st.subheader("Detalhamento das vendas")
        busca = st.text_input("Buscar produto ou pedido", placeholder="Digite um produto ou número de pedido…", key="busca_historico")
        tabela = df.copy()
        if busca.strip():
            termo = busca.strip()
            tabela = tabela.loc[
                tabela["produto"].str.contains(termo, case=False, regex=False)
                | tabela["pedido_id"].str.contains(termo, case=False, regex=False)
            ]
        tabela = tabela.sort_values(["data", "pedido_id"], ascending=[False, True], kind="stable")
        st.caption(f"{numero(len(tabela))} itens · {numero(tabela['pedido_id'].nunique())} pedidos · A busca afeta apenas esta tabela e seu download.")
        if tabela.empty:
            st.info("Nenhum produto ou pedido corresponde à busca.")
        else:
            exibicao = tabela.rename(columns={
                "pedido_id": "Pedido", "data": "Data", "produto": "Produto", "quantidade": "Quantidade",
                "preco_unitario": "Preço unitário", "faturamento": "Faturamento",
            })
            st.dataframe(
                exibicao.style.format({"Quantidade": numero, "Preço unitário": moeda, "Faturamento": moeda}),
                hide_index=True, width="stretch", height=440,
                column_config={"Data": st.column_config.DateColumn(format="DD/MM/YYYY")},
            )
        st.download_button(
            "Baixar tabela exibida", dataframe_para_csv(tabela), "historico_vendas.csv", "text/csv",
            icon=":material/download:", disabled=tabela.empty,
        )


def guia_de_uso():
    with st.container(border=True, key="card_guia_fonte"):
        st.subheader("1. Escolha sua base de vendas")
        st.markdown("Explore a **Demonstração**, confira os **Pedidos originais** ou escolha **Importar CSV** na barra lateral para analisar seu próprio arquivo. A demonstração usa dados fictícios de julho a setembro de 2026.")
        ajuda_csv()
    with st.container(border=True, key="card_guia_indicadores"):
        st.subheader("2. Entenda os indicadores")
        st.markdown("""
        - **Faturamento:** soma de quantidade × preço unitário. É receita bruta, sem desconto de custos, impostos ou devoluções.
        - **Pedidos:** quantidade de IDs de pedido distintos; várias linhas podem pertencer à mesma venda.
        - **Ticket médio:** faturamento do recorte ÷ pedidos distintos.
        - **Unidades:** soma das quantidades dos itens.
        - **Curva ABC:** prioriza produtos pela participação acumulada na receita, não pela margem de lucro.
        """)
        st.info("Ao selecionar produtos, analisamos apenas esses itens. Pedidos com outros itens continuam contados se contiverem algum produto selecionado; o ticket passa a representar um carrinho parcial.")
    with st.container(border=True, key="card_guia_comparacao"):
        st.subheader("3. Compare períodos com contexto")
        st.markdown("O período anterior tem a mesma quantidade de dias e termina na véspera do atual. A comparação só aparece quando o período atual e o anterior estão inteiramente dentro do intervalo da base; receita anterior zero não gera percentual. Dias sem registros são tratados como zero — confira se seu arquivo contém o histórico completo.")
        st.caption("Os gráficos podem agrupar semanas e meses parciais. Use a mesma duração para comparar totais; a análise por dia da semana usa médias por ocorrência.")
    with st.container(border=True, key="card_guia_dados"):
        st.subheader("Seus dados e os limites da análise")
        st.markdown("Os arquivos são processados em memória durante a sessão, sem banco de dados nem gravação de uploads no projeto. Atualizar a página ou encerrar a sessão pode exigir novo envio. Esta versão não tem autenticação, cadastro de vendas, custos, estoque ou previsão. Em uma implantação, use dados adequados ao nível de acesso do servidor.")
        st.caption("Exports usam UTF-8, ponto e vírgula e vírgula decimal. Campos de texto que possam ser interpretados como fórmulas recebem um apóstrofo; esse prefixo é mantido se o arquivo for reimportado.")


def main():
    aplicar_estilo()
    with st.sidebar:
        st.html('<div class="brand"><div class="brand-mark"><i style="height:9px"></i><i style="height:15px"></i><i style="height:21px"></i></div><div><div class="brand-name">VendaLab</div><div class="brand-caption">INTELIGÊNCIA DE VENDAS</div></div></div>')
        pagina = st.radio("Navegação", ["Visão geral", "Produtos", "Histórico de vendas", "Guia de uso"], label_visibility="collapsed", key="pagina")
        st.divider()
        df, fonte, identificador, erro = carregar_fonte()
        if df is not None:
            st.divider()
            inicio, fim, produtos = configurar_filtros(df, identificador)
            st.divider()
            st.caption(f"BASE DISPONÍVEL\n\n{intervalo(df['data'].min(), df['data'].max())}\n\n{numero(df['pedido_id'].nunique())} pedidos · {numero(df['produto'].nunique())} produtos")
        with st.expander("Formato do arquivo CSV"):
            st.caption("Colunas: pedido_id, data, produto, quantidade, preco_unitario. Separador vírgula ou ponto e vírgula. UTF-8, até 10 MB e 100 mil itens.")
            st.download_button("Baixar modelo", csv_modelo(), "modelo_vendas.csv", "text/csv", key="modelo_sidebar", width="stretch")

    cabecalho(pagina)
    if pagina == "Guia de uso":
        guia_de_uso()
        return
    if df is None:
        if erro and "Envie um CSV" in erro:
            st.info(erro)
        else:
            st.error(f"Não foi possível importar o arquivo. {erro}")
        with st.container(border=True, key="card_importacao"):
            st.subheader("Prepare seu arquivo de vendas")
            ajuda_csv()
        return
    if inicio > fim:
        st.error("A data inicial não pode ser posterior à data de fim. Ajuste as datas na barra lateral.")
        return
    if (fim - inicio).days > 1095:
        st.warning("Selecione um intervalo de até 3 anos para explorar os gráficos. Seu arquivo permanece carregado.")
        return
    duracao = (fim - inicio).days + 1
    fim_anterior = inicio - timedelta(days=1)
    inicio_anterior = fim_anterior - timedelta(days=duracao - 1)
    vendas = filtrar_vendas(df, inicio, fim, produtos)
    minimo, maximo = df["data"].min().date(), df["data"].max().date()
    cobertura_atual = inicio >= minimo and fim <= maximo
    cobertura_anterior = inicio_anterior >= minimo and fim_anterior <= maximo
    comparavel = cobertura_atual and cobertura_anterior
    anterior = filtrar_vendas(df, inicio_anterior, fim_anterior, produtos) if comparavel else df.iloc[:0].copy()
    resumo = resumir_vendas(vendas)
    variacoes = comparar_periodos(vendas, anterior)

    esquerda, direita = st.columns([3, 1], vertical_alignment="center")
    badge = "DADOS DEMONSTRATIVOS" if fonte == "Demonstração" else "PEDIDOS ORIGINAIS" if fonte == "Pedidos originais" else "CSV IMPORTADO"
    with esquerda:
        st.html(f'<span class="source-badge">{badge}</span><span class="period-label">{intervalo(inicio, fim)}</span>')
    with direita:
        st.download_button(
            "Exportar vendas", dataframe_para_csv(vendas), f"vendas_{inicio}_{fim}.csv", "text/csv",
            icon=":material/download:", width="stretch", disabled=vendas.empty,
        )
    st.write("")
    mostrar_indicadores(resumo, variacoes, comparavel)
    if comparavel:
        st.caption(f"Comparação com {intervalo(inicio_anterior, fim_anterior)} · {duracao} dias em cada período. Histórico ausente dentro da base é tratado como zero.")
    elif not cobertura_atual:
        st.caption(f"O período selecionado ultrapassa o histórico disponível ({intervalo(minimo, maximo)}). A comparação foi omitida.")
    else:
        st.caption(f"Período anterior: {intervalo(inicio_anterior, fim_anterior)}. A base não cobre todo esse intervalo; a comparação foi omitida.")
    if produtos:
        st.caption("Filtro de produtos ativo: receita e ticket consideram apenas os itens selecionados, não o carrinho completo.")
    if vendas.empty:
        st.info("Nenhuma venda encontrada para estes filtros. Amplie o período ou altere os produtos selecionados.")
        return

    ranking = ranking_produtos(vendas)
    if pagina == "Visão geral":
        visao_geral(vendas, anterior, inicio, fim, comparavel, ranking)
    elif pagina == "Produtos":
        analisar_produtos(ranking)
    else:
        historico_vendas(vendas)
    st.html('<div class="footer">VendaLab &nbsp;·&nbsp; Análise de vendas &nbsp; / &nbsp; Indicadores calculados sobre os filtros selecionados.</div>')


if __name__ == "__main__":
    main()
