import streamlit as st

from dados import pedidos

from analises import (
    calcular_faturamento,
    calcular_unidades_vendidas,
    calcular_quantidades_por_produto,
    calcular_faturamento_por_produto,
    calcular_faturamento_por_dia,
    filtrar_pedidos_por_periodo,
    encontrar_produto_mais_vendido,
)

from datetime import date


st.title("Painel de vendas da lanchonete")


data_inicio = st.date_input(
    "Data de início",
    value=date(2026, 9, 24),
    format="DD/MM/YYYY",
)

data_fim = st.date_input(
    "Data de fim",
    value=date(2026, 9, 24),
    format="DD/MM/YYYY",
)

st.write("Inicio escolhido: ", data_inicio)
st.write("Fim escolhido: ", data_fim)

if data_inicio > data_fim:
    st.error("A data inicial não pode ser posterior à data de fim.")
    st.stop()

pedidos_filtrados = filtrar_pedidos_por_periodo(
    pedidos, 
    data_inicio, 
    data_fim
)


faturamento = calcular_faturamento(pedidos_filtrados)
quantidade_pedidos = len(pedidos_filtrados)
unidades_vendidas = calcular_unidades_vendidas(pedidos_filtrados)


st.write(f"Pedidos no período:", len(pedidos_filtrados))


if quantidade_pedidos> 0:
    ticket_medio = faturamento / quantidade_pedidos

else:
    ticket_medio = 0



coluna1, coluna2, coluna3, coluna4 = st.columns(4)

coluna1.metric(
    label="faturamento",
    value=f"R$ {faturamento:.2f}"
)

coluna2.metric(
    label="pedidos",
    value = quantidade_pedidos,
)

coluna3.metric(
    label="ticket médio",
    value=f"R$ {ticket_medio:.2f}"
)

coluna4.metric(
    label="unidades vendidas",
    value=unidades_vendidas,
)


#GRAFICOS

#UNIDADES VENDIDAS POR PRODUTO

st.subheader("unidades vendidas por produto")

quantidades = calcular_quantidades_por_produto(pedidos_filtrados)

produto_mais_vendido, quantidade_vendida, = encontrar_produto_mais_vendido(
    quantidades
)

if produto_mais_vendido is None:
    st.info("Nenhum produto foi vendido, portanto não há dados para exibir no gráfico.")
else:
    st.write(f"produto mais vendido: {produto_mais_vendido} com ",
             f"{quantidade_vendida} unidades vendidas"
    )


dados_grafico = []

for produto, quantidade in quantidades.items():
    dados_grafico.append({
        "produto": produto,
        "quantidade": quantidade
    })

if dados_grafico:
    st.bar_chart(
        dados_grafico,
        x="produto",
        y="quantidade",
    )

else:
    st.info("Nenhum produto foi vendido, portanto não há dados para exibir no gráfico.")




#FATURAMENTO POR PRODUTO

st.subheader("faturamento por produto")

faturamento_produtos = calcular_faturamento_por_produto(pedidos_filtrados)

dados_faturamento = []

for produto, faturamento in faturamento_produtos.items():
    dados_faturamento.append({
        "produto": produto,
        "faturamento": faturamento
    })

if dados_faturamento:
    st.bar_chart(
        dados_faturamento,
        x="produto",
        y="faturamento",
        y_label="Faturamento (R$)",
    )
else:
    st.info("nenhuma venda registrada")



#FATURAMENTO POR DIA

st.subheader("faturamento por dia")

faturamento_diario = calcular_faturamento_por_dia(pedidos_filtrados)

dados_diarios = []

for data_venda, valor in sorted(faturamento_diario.items()):
    dados_diarios.append({
        "data": date.fromisoformat(data_venda),
        "faturamento": valor,
    })

if dados_diarios:
    st.line_chart(
        dados_diarios,
        x="data",
        y="faturamento",
        x_label="Data",
        y_label="Faturamento (R$)",
    )
else:
    st.info("nenhuma venda registrada")
