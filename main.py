# Importações: disponibilizam os pedidos, as funções de análise e o tipo date.
from dados import pedidos
from analises import (
    calcular_faturamento,
    calcular_unidades_vendidas,
    calcular_quantidades_por_produto,
    calcular_faturamento_por_produto,
    encontrar_produto_mais_vendido,
    calcular_faturamento_por_dia,
)
from datetime import date
from analises import filtrar_pedidos_por_periodo


# Resumo geral: calcula e exibe faturamento, quantidade de pedidos, ticket médio
# e unidades vendidas. Quando não há pedidos, o ticket médio fica em zero.
faturamento = calcular_faturamento(pedidos)
qnt_pedidos = len(pedidos)
if qnt_pedidos > 0:
    ticket_medio = faturamento / qnt_pedidos
else:
    ticket_medio = 0
unidades_vendidas = calcular_unidades_vendidas(pedidos)
print(f"O faturamento total é: R$ {faturamento:.2f}")
print(f"O ticket médio é: R$ {ticket_medio:.2f}")
print(f"a quantidade de pedidos é: {qnt_pedidos}")
print(f"unidades vendidas: {unidades_vendidas}")


# Quantidades por produto: agrupa e exibe o total de unidades vendidas de cada produto.
quantidades_por_produto = calcular_quantidades_por_produto(pedidos)
print(quantidades_por_produto)


# Faturamento por produto: calcula a receita de cada produto e guarda em resultado.
resultado = calcular_faturamento_por_produto(pedidos)


# Produto mais vendido: identifica o produto com mais unidades vendidas e exibe
# seu nome e quantidade, ou uma mensagem caso nenhum produto tenha sido vendido.
quantidades = calcular_quantidades_por_produto(pedidos)
produto, quantidade = encontrar_produto_mais_vendido(quantidades)
if produto is None:
    print("Nenhum produto foi vendido.")
else:
    print(f"O produto mais vendido é: {produto} com {quantidade} unidades vendidas.")


# Faturamento por dia: agrupa e exibe a receita total de cada data com vendas.
resultado_por_dia = calcular_faturamento_por_dia(pedidos)
print(resultado_por_dia)


# Faturamento por período: filtra os pedidos entre as datas inicial e final,
# incluindo os limites, e exibe a quantidade de pedidos e a receita do intervalo.
inicio = date(2026, 9, 24)
fim = date(2026, 9, 24)
pedidos_filtrados = filtrar_pedidos_por_periodo(pedidos, inicio, fim)
print(f"pedidos no periodo: {len(pedidos_filtrados)}")
print(
    f"faturamento no periodo: R$ {calcular_faturamento(pedidos_filtrados):.2f}"
)
