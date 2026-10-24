# Formato dos dados

O painel trabalha com **uma linha por item de pedido**. Um mesmo pedido pode ter vários produtos e, portanto, várias linhas. A identificação do pedido conecta esses itens para a contagem de pedidos distintos.

## Fontes disponíveis

| Fonte | Conteúdo | Finalidade |
| --- | --- | --- |
| Demonstração | Vendas fictícias e reproduzíveis de 01/07/2026 a 30/09/2026 | Explorar gráficos, sazonalidade e ranking sem um arquivo próprio |
| Pedidos originais | Os dois pedidos mantidos em `dados.py` | Reproduzir os números do projeto inicial |
| Importar CSV | Arquivo enviado na sessão | Analisar as próprias vendas |

A geração da demonstração não sobrescreve os pedidos originais. Trocar a fonte muda a base usada pelo painel; os arquivos importados não são gravados em `dados.py`.

A demonstração contém 536 pedidos, 1.083 itens e 10 produtos, com faturamento total de R$ 22.997,00 e 1.582 unidades em 92 dias. A geração é determinística: executar novamente produz os mesmos dados.

Ao carregar ou trocar uma fonte, o painel seleciona os últimos 30 dias disponíveis, contados a partir da data máxima do arquivo, e limpa o filtro de produtos. Os atalhos não dependem da data atual. Para analisar toda a demonstração, selecione **Todo o período**.

## Colunas do CSV

Utilize estes nomes no cabeçalho:

| Coluna | Obrigatória | Regra | Exemplo |
| --- | --- | --- | --- |
| `pedido_id` | Sim | Texto não vazio, identificador do pedido | `0001` |
| `data` | Sim | Data em `AAAA-MM-DD` ou `DD/MM/AAAA` | `2026-09-24` |
| `produto` | Sim | Nome não vazio | `Hambúrguer` |
| `quantidade` | Sim | Número inteiro maior que zero | `2` |
| `preco_unitario` | Sim | Número finito, maior ou igual a zero | `20,00` |
| `faturamento` | Não | Coluna calculada; se enviada, será recalculada | `40,00` |

Colunas adicionais são ignoradas. O faturamento é sempre calculado a partir da quantidade e do preço unitário, para evitar divergências entre os itens e a receita exibida.

### Exemplo com ponto e vírgula

Salve o conteúdo abaixo como `vendas.csv`, com codificação UTF-8:

```csv
pedido_id;data;produto;quantidade;preco_unitario
0001;2026-09-24;Hambúrguer;2;20,00
0001;2026-09-24;Cachorro-quente;2;12,00
0002;2026-09-25;Cachorro-quente;2;12,00
0002;2026-09-25;Refrigerante;1;6,00
```

Este arquivo contém 4 itens, pertencentes a 2 pedidos, e totaliza R$ 94,00 e 7 unidades. Zeros à esquerda no identificador são preservados.

### Exemplo com vírgula

Também é possível usar vírgula como separador e ponto como separador decimal:

```csv
pedido_id,data,produto,quantidade,preco_unitario
0001,24/09/2026,Hambúrguer,2,20.00
0001,24/09/2026,Cachorro-quente,2,12.00
```

Se uma célula contiver o próprio delimitador, use aspas duplas, conforme o formato CSV. Por exemplo, com separador vírgula, o valor decimal brasileiro `20,00` precisa ser escrito como `"20,00"`. Para evitar ambiguidade, prefira `;` ao utilizar vírgulas decimais. Não inclua `R$` ou separadores de milhar nos valores numéricos.

## Validação

O arquivo deve ser UTF-8, com ou sem BOM, e usar vírgula ou ponto e vírgula como delimitador. A importação verifica o limite de **10 MiB (10.485.760 bytes) e 100 mil linhas de itens**, as colunas obrigatórias e os valores de cada item.

São rejeitados, entre outros:

- Arquivos vazios, cabeçalhos incompletos e células obrigatórias vazias.
- Datas inexistentes ou fora dos formatos aceitos.
- Quantidades nulas, negativas ou fracionárias.
- Preços negativos ou valores numéricos não finitos, como `NaN` e infinito.
- Um mesmo `pedido_id` associado a datas diferentes.

As linhas de itens são preservadas. Duas linhas com o mesmo pedido e produto podem representar itens separados e não são removidas como duplicatas. Verifique se a origem do arquivo contém duplicações acidentais: se houver, elas também entrarão no cálculo da receita e das unidades.

Quando a importação falha, corrija o arquivo seguindo a mensagem exibida e envie-o novamente. A aplicação rejeita o arquivo inteiro em vez de remover linhas inválidas e apresentar um total parcial sem aviso.

## Exportações

As exportações usam **UTF-8 com BOM**, **ponto e vírgula** como separador e **vírgula decimal**, para facilitar a abertura em planilhas configuradas em português do Brasil.

- **Exportar vendas** baixa os itens correspondentes aos filtros globais de período e produtos, com os campos de identificação, data, produto, quantidade, preço unitário e faturamento calculado.
- **Baixar tabela exibida**, em **Histórico de vendas**, aplica também a busca por nome de produto ou identificador do pedido. A busca é literal, sem distinção entre maiúsculas e minúsculas, e não muda o recorte de **Exportar vendas**.
- **Exportar análise de produtos** contém as medidas agregadas e a classificação ABC. Ele é um relatório; não deve ser confundido com um arquivo de itens para reimportação.
- O modelo de importação utiliza os pedidos originais como exemplo.

Para evitar que uma planilha interprete nomes ou identificadores como fórmulas, a exportação acrescenta um apóstrofo a textos que comecem com `=`, `+`, `-` ou `@`, inclusive após espaços, ou com tabulação e quebras de linha. Esse apóstrofo permanece caso o arquivo seja reimportado. As demais células mantêm seus valores; o CSV exportado dos itens pode ser usado novamente como fonte.

Os dados enviados permanecem em memória durante a sessão. O projeto não contém uma base permanente de vendas nem sincronização automática com sistemas externos. Guarde os arquivos originais para reproduzir a análise.
