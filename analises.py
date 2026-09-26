#FUNÇÕES PARA ANALISE DO PROJETO


def calcular_total(itens):
    total = 0
    for item in itens:
        subtotal = item["quantidade"] * item["preco_unitario"]
        total += subtotal
    return total




def calcular_faturamento(pedidos):
    faturamento = 0
    for pedido in pedidos:
        total_pedido = calcular_total(pedido["itens"])  
        faturamento += total_pedido
    return faturamento




def calcular_unidades_vendidas(pedidos):
    total_unidades = 0
    for pedido in pedidos:
        for item in pedido["itens"]:
            total_unidades += item["quantidade"]
    return total_unidades




def calcular_quantidades_por_produto(pedidos):
    quantidades = {}

    for pedido in pedidos:
        for item in pedido["itens"]:
            produto = item["produto"]
            quantidade = item["quantidade"]
            if produto not in quantidades:
                quantidades[produto] = 0
            quantidades[produto] += quantidade
    return quantidades





def calcular_faturamento_por_produto(pedidos):
    faturamento_produtos = {}

    for pedido in pedidos:
        for item in pedido["itens"]:
            produto = item["produto"]
            subtotal = item["quantidade"] * item["preco_unitario"]
            if produto not in faturamento_produtos:
                faturamento_produtos[produto] = 0
            faturamento_produtos[produto] += subtotal
    return faturamento_produtos




def encontrar_produto_mais_vendido(quantidades):
    produto_mais_vendido = None
    quantidade_maxima = 0

    for produto, quantidade in quantidades.items():
        if quantidade > quantidade_maxima:
            quantidade_maxima = quantidade
            produto_mais_vendido = produto

    return produto_mais_vendido, quantidade_maxima




def calcular_faturamento_por_dia(pedidos):
    faturamento_por_dia = {}

    for pedido in pedidos:
        data = pedido["data"]
        total_pedido = calcular_total(pedido["itens"])
        if data not in faturamento_por_dia:
            faturamento_por_dia[data] = 0
        faturamento_por_dia[data] += total_pedido
    return faturamento_por_dia