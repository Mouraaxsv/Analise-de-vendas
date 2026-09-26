from dados import pedidos

from analises import (calcular_faturamento, 
                      calcular_unidades_vendidas, 
                      calcular_quantidades_por_produto,
                      calcular_faturamento_por_produto,
                      encontrar_produto_mais_vendido
)


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



quantidades_por_produto = calcular_quantidades_por_produto(pedidos)
print(quantidades_por_produto)


resultado = calcular_faturamento_por_produto(pedidos)


quantidades = calcular_quantidades_por_produto(pedidos)
produto, quantidade = encontrar_produto_mais_vendido(quantidades)

if produto is None:
    print("Nenhum produto foi vendido.")

else:
    print(f"O produto mais vendido é: {produto} com {quantidade} unidades vendidas.")



