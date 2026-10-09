# Banco de Questões de Concursos — entrega

| Arquivo | Conteúdo |
|---|---|
| `banco_questoes.xlsx` | banco completo, aba `Questoes`, com as 13 colunas exatas |
| `banco_questoes.csv.gz` | o mesmo banco em CSV (`;`, UTF-8, sem BOM), compactado. Descompacte com `gunzip` ou 7-Zip; tem cerca de 107 MB |
| `amostra_1000.csv` | 1.000 questões sorteadas, para conferência rápida |
| `rejeitadas.csv.gz` | questões descartadas na validação, com o motivo |
| `relatorio.json` | contagens por banca, ano e disciplina |

## Números

* **158.728 questões válidas**, de 178.408 lidas: 1.929 foram rejeitadas na validação e 17.751 duplicatas removidas.
* **Bancas:** Cebraspe 134.808 e FGV 23.920, incluindo 2.210 da 1ª fase da OAB (2010–2018).
* **Tipos:** 101.145 Certo/Errado (`Alternativa_A=Certo`, `Alternativa_B=Errado`, gabarito A/B) e
  57.583 de múltipla escolha (4 ou 5 alternativas).
* **438 órgãos**, provas de 2010 a 2026 (mais da metade de 2021 em diante) e **65 disciplinas**.

## Origem e confiabilidade de cada coluna

| Coluna | Origem |
|---|---|
| Banca, Orgao, Ano | metadados oficiais da banca (API do Cebraspe, página do concurso na FGV, dataset da OAB) |
| Enunciado, Alternativas | texto extraído do caderno de prova oficial (PDF) |
| Gabarito | **gabarito definitivo** oficial; questões anuladas foram excluídas |
| Disciplina | FGV: título da matéria no caderno; OAB: matéria do exame; **Cebraspe: prevista por classificador** (veja abaixo) |
| Assunto | tirado do comando da questão ("Acerca de X, julgue…") ou copiado da questão mais parecida; preenchido em ~50% |
| Comentario_Professor | vazio: as fontes oficiais não trazem comentários (e comentários de sites comerciais têm direitos autorais) |

Todas as linhas passaram na validação automática do formato exigido: sem HTML, sem erro de encoding,
sem letra misturada à alternativa, gabarito de uma letra (A–E), C/D/E vazias nas questões Certo/Errado.

## Limitações conhecidas

1. **Disciplina das questões do Cebraspe (~85% do banco) é inferida.** O Cebraspe não escreve o nome da
   matéria no caderno. Ela vem de um classificador treinado com os rótulos da FGV e da OAB (78,7% de acerto
   em cadernos que ele não viu no treino), da área do cargo nas provas de conhecimentos específicos e de
   palavras-chave. Calculamos algo em torno de 75–80% de acerto: confira por amostragem antes de usar a
   coluna para filtros finos.
2. **Assunto** fica vazio em cerca de metade das questões, quando o comando não cita o tema.
3. **Figuras e tabelas** dos cadernos não são reproduzidas. Tabelas viram texto corrido, e uma questão que
   depende de imagem pode ficar incompleta.
4. **Diversidade de bancas:** só Cebraspe e FGV/OAB. A FCC e o PCI Concursos proíbem a coleta no
   `robots.txt`, e Vunesp, Cesgranrio e IBFC bloqueiam robôs no servidor.

Para reproduzir ou atualizar o banco, veja o `README.md` na raiz do repositório.
