import streamlit as st

from dados import pedidos

from analises import (
    calcular_faturamento,
    calcular_unidades_vendidas,
    calcular_quantidades_por_produto,
    calcular_faturamento_por_produto,
    calcular_faturamento_por_dia,
)

from datetime import date


st.title("Painel de vendas da lanchonete")

faturamento = calcular_faturamento(pedidos)
quantidade_pedidos = len(pedidos)
unidades_vendidas = calcular_unidades_vendidas(pedidos)


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

quantidades = calcular_quantidades_por_produto(pedidos)

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

faturamento_produtos = calcular_faturamento_por_produto(pedidos)

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

faturamento_diario = calcular_faturamento_por_dia(pedidos)

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
