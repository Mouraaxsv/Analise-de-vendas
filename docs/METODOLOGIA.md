# Metodologia das análises

Todos os indicadores descrevem os dados da fonte selecionada e respeitam os filtros de datas e produtos. Não há dados de custos ou de lucro, e as leituras automáticas não fazem previsão ou inferência causal.

## Unidade de análise e filtros

Cada linha corresponde a um item de pedido. Para cada item:

```text
faturamento do item = quantidade × preço unitário
```

O período inclui a data inicial e a data final. O filtro por produto mantém apenas os itens dos produtos escolhidos; sem seleção, considera todos os produtos.

Os atalhos **Últimos 30 dias** e **Últimos 7 dias** terminam na última data da fonte selecionada, independentemente da data atual, e nunca começam antes da primeira data disponível. **Todo o período** usa o intervalo completo da fonte. **Personalizado** libera a edição das datas, inclusive para selecionar um período sem vendas. A diferença entre as datas de início e fim não pode ultrapassar 1.095 dias; intervalos maiores geram um aviso e devem ser reduzidos para continuar a análise.

Um pedido com hambúrguer e refrigerante, por exemplo, continua sendo um único pedido quando se filtra apenas hambúrguer. Nesse recorte, a receita e as unidades do refrigerante deixam de participar das medidas. Assim, o ticket médio filtrado por produto representa a receita dos **itens selecionados por pedido**, e não necessariamente o valor total originalmente pago pelo cliente.

## Indicadores principais

| Indicador | Cálculo |
| --- | --- |
| Faturamento | Soma do faturamento de todos os itens do recorte |
| Pedidos | Quantidade de identificadores `pedido_id` distintos no recorte |
| Ticket médio | Faturamento ÷ pedidos distintos |
| Unidades vendidas | Soma das quantidades dos itens |
| Produtos | Quantidade de nomes de produtos distintos no recorte |

Quando não há pedidos, o ticket médio é zero. A receita usa o preço unitário informado; o modelo não desconta taxas, impostos ou custos e não representa lucro.

## Comparação entre períodos

O período de referência é o intervalo imediatamente anterior, com o mesmo número de dias corridos, sem sobreposição. O filtro de produtos é aplicado aos dois períodos.

Exemplo: ao selecionar 24/09/2026 a 25/09/2026, com duração de dois dias, a comparação utiliza 22/09/2026 a 23/09/2026.

```text
variação (%) = (valor atual − valor anterior) ÷ valor anterior × 100
```

O painel só apresenta comparações quando **o período atual e todo o período anterior estão entre a menor e a maior data da fonte**, antes dos filtros de produto. Caso contrário, omite os percentuais e informa a falta de cobertura. Isso evita tratar datas futuras, ainda ausentes do histórico, como uma queda de vendas. A presença dos limites no arquivo não comprova que os registros entre eles estejam completos: dias sem registros dentro da base são tratados como zero.

Se o valor anterior de um indicador for zero, sua variação percentual é indefinida e não é apresentada como um crescimento de 100%. A variação não é corrigida por inflação, feriados, dias de funcionamento ou diferenças no conjunto de dias da semana.

## Evolução das vendas

As séries temporais agregam faturamento, unidades e pedidos em intervalos diários, semanais ou mensais. Os dias do calendário sem vendas são incluídos com valores zero, evitando uma linha que pule diretamente de uma venda para outra.

O ticket de cada intervalo é calculado dividindo sua receita por seus pedidos distintos. Ele não é a média simples dos tickets de dias diferentes. As semanas começam na segunda-feira e terminam no domingo; os meses seguem o calendário. A data de um agrupamento identifica seu início. Quando um intervalo semanal ou mensal é cortado pelos filtros, seu valor corresponde apenas aos dias selecionados, não à semana ou ao mês completo.

## Produtos e curva ABC

O ranking organiza os produtos por faturamento decrescente, com nome como desempate. As principais medidas são:

| Medida | Cálculo |
| --- | --- |
| Unidades | Soma da quantidade vendida do produto |
| Pedidos | Pedidos distintos que contêm o produto |
| Faturamento | Receita dos itens do produto |
| Preço médio | Faturamento ÷ unidades, ponderado pelas quantidades |
| Participação | Faturamento do produto ÷ faturamento total × 100 |
| Acumulado | Soma das participações, na ordem do ranking |

Um pedido pode aparecer no total de pedidos de mais de um produto. Por isso, somar a coluna de pedidos do ranking pode resultar em um número maior do que o total de pedidos do painel.

A curva ABC agrupa produtos conforme sua contribuição acumulada para a receita:

- **A:** produtos que formam aproximadamente os primeiros 80% do faturamento.
- **B:** produtos seguintes, até aproximadamente 95% do faturamento.
- **C:** os demais produtos.

O produto que cruza o limite permanece na faixa em que começou. A classificação utiliza o acumulado **antes** de adicionar o produto. Isso evita que o produto mais relevante fique fora da classe A quando, sozinho, representa mais de 80% da receita. Por essa regra, os percentuais finais de cada classe podem ultrapassar os limites de referência.

Exemplo: com participações de 70%, 20%, 7% e 3%, os dois primeiros produtos pertencem à classe A; o terceiro pertence à B e o último à C.

A classificação é recalculada após os filtros e muda conforme a fonte e o período. Em um recorte com faturamento total zero, a participação e o acumulado são zero e todos os produtos ficam na classe C; não há concentração econômica a interpretar.

Para manter os gráficos legíveis, o Pareto exibe no máximo os 40 produtos de maior faturamento. Seus percentuais continuam calculados sobre **todos os produtos do recorte**; a linha acumulada exibida pode terminar abaixo de 100%. A tabela e a exportação de produtos mantêm o ranking completo. No gráfico de composição da receita, os sete líderes aparecem individualmente e os demais são somados em **Outros produtos (agrupados)**.

## Dia da semana

O painel agrega as vendas por dia da semana e calcula:

```text
receita média diária = receita do dia da semana no período
                      ÷ número de ocorrências desse dia no calendário selecionado
```

Um intervalo com três segundas-feiras inclui as três no denominador, mesmo que o arquivo só contenha vendas em uma delas. A medida reduz o efeito de comparar períodos com quantidades diferentes de cada dia da semana.

Não há calendário de funcionamento. Um dia sem registros pode ser um dia fechado, um dia sem vendas ou uma lacuna do arquivo. A média trata essas situações como receita zero; avalie a qualidade da base antes de usar o resultado para decisões operacionais.

## Leituras automáticas e limites

As leituras destacam fatos derivados dos cálculos, como o produto que concentra mais faturamento e o desempenho observado no período. Elas não explicam por que um resultado ocorreu e não indicam necessariamente uma ação comercial.

- Variações dependem de uma base de comparação completa e representativa.
- O nome do produto define sua identidade: grafias diferentes podem criar produtos distintos.
- O modelo não possui descontos, devoluções, clientes, forma de pagamento, custos ou margem.
- Dados fictícios servem para demonstrar a interface e os cálculos, não para orientar um negócio real.

Consulte o [contrato dos arquivos](DADOS.md) para preparar uma base própria e o [README](../README.md) para executar o projeto.
