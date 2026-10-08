# Banco de Questões de Concursos

Este pipeline coleta, limpa, valida e exporta questões de concursos públicos no
formato exigido: tabela planificada com **13 colunas exatas**, em `.xlsx`, em
`.csv` (separado por `;`, UTF-8) ou em `.json`.

```
Banca;Orgao;Ano;Disciplina;Assunto;Enunciado;Alternativa_A;Alternativa_B;Alternativa_C;Alternativa_D;Alternativa_E;Gabarito;Comentario_Professor
```

## Garantias de qualidade (aplicadas automaticamente)

| Regra | Como é garantida |
|---|---|
| Sem HTML | tags removidas, `<br>`/`</p>` viram quebra de linha, entidades (`&nbsp;`) decodificadas |
| Sem erro de encoding | correção de mojibake com `ftfy` (ex.: `AdministraÃ§Ã£o` → `Administração`), normalização NFC, remoção de caracteres de controle |
| Sem letra na alternativa | `A) `, `(A) `, `a. `, `A - ` removidos do início, sem quebrar textos como "A lei..." |
| Gabarito limpo | só uma letra maiúscula `A`–`E`, sem espaços; `Certo`→`A`, `Errado`→`B` |
| Certo/Errado (Cebraspe) | `Alternativa_A="Certo"`, `Alternativa_B="Errado"`, C/D/E vazias, gabarito `A`/`B` |
| Ano | apenas os 4 dígitos (número no Excel) |
| Anuladas | questões com gabarito `X`/`*`/`ANULADA` são descartadas |
| Consistência | gabarito aponta para alternativa preenchida, sem lacunas (A, B, _, D), sem alternativas repetidas |
| Duplicatas | a mesma questão vinda de fontes diferentes fica uma vez só; um comentário existente é aproveitado |

Toda questão reprovada vai para um CSV separado com o motivo, e nada é corrigido
"no chute".

## Instalação

```bash
pip install -r requirements.txt
```

## Fluxo

Cada fonte gera um `.jsonl` intermediário. No fim, o comando `consolidar` junta tudo no banco final.

```bash
# 1) (opcional) baixar PDFs de provas e gabaritos de páginas públicas de listagem
python -m questoes baixar-pdfs exemplos/baixar_pdfs.yaml

# 2) extrair questões dos PDFs oficiais (prova + gabarito definitivo)
python -m questoes pdf exemplos/manifesto_provas.yaml -o dados/provas.jsonl

# 3) importar bases já estruturadas (datasets abertos, bases licenciadas)
python -m questoes tabela oab.parquet --mapa exemplos/mapa_oab_exams.yaml -o dados/oab.jsonl

# 4) consolidar: limpar, classificar assunto, validar, deduplicar e exportar
python -m questoes consolidar dados/*.jsonl \
    -o saida/banco_questoes.xlsx -o saida/banco_questoes.csv \
    --rejeitadas saida/rejeitadas.csv --relatorio saida/relatorio.json

# validar qualquer arquivo já nas 13 colunas (código de saída 1 se houver erro)
python -m questoes validar saida/banco_questoes.csv
```

`--bom` grava o CSV com BOM, para que o Excel abra os acentos direto com
duplo clique. Deixe sem BOM se o seu sistema lê UTF-8 puro.

## Fontes e como chegar a ~100 mil questões

1. **Provas oficiais em PDF (fonte principal).** As bancas e os órgãos publicam o
   caderno de prova e o gabarito definitivo. Uma prova tem entre 50 e 120
   questões (Cebraspe costuma ter 120 itens), então são precisas cerca de
   **1.000 a 1.500 provas** para chegar a 100 mil. O manifesto
   (`exemplos/manifesto_provas.yaml`) registra banca, órgão, ano, tipo e as
   faixas de questões de cada disciplina.
2. **Datasets abertos** importados por `tabela` com um mapa YAML, por exemplo o
   das provas da OAB/FGV (`exemplos/mapa_oab_exams.yaml`).
3. **Raspagem HTML** (`web`), configurável por seletores CSS, só em sites cujos
   termos permitam. O coletor respeita o `robots.txt`, espera um intervalo entre
   requisições, guarda cache e repete a tentativa com backoff.

> **Aviso legal:** sites comerciais de questões (QConcursos, TEC Concursos,
> Estratégia etc.) proíbem a raspagem nos termos de uso, e os comentários de
> professores são obra protegida por direito autoral. Não use este projeto
> para copiá-los. A coluna `Comentario_Professor` deve vir de material próprio
> ou licenciado.

## Disciplina e Assunto

* **Disciplina:** vem das faixas declaradas no manifesto, da fonte ou de valores fixos.
* **Assunto:** quando vier vazio, um classificador por palavras-chave
  (`questoes/assuntos.py`) preenche a partir de uma taxonomia fechada
  (Português, Dir. Administrativo, Constitucional, Penal, Processo Penal,
  Raciocínio Lógico, Informática e Contabilidade). Ele é auditável, mas tem
  cobertura limitada. Para cobertura alta, estenda a taxonomia ou adicione um
  classificador por LLM usando os mesmos rótulos.

## Limitações do parser de PDF

O parser é heurístico. Ele exige numeração sequencial e localiza a sequência
de alternativas A–E de trás para frente. No caso do Cebraspe, os textos de
apoio ("Texto I", "Julgue os itens...") são anexados aos itens seguintes.
Antes de processar em lote, revise uma amostra de cada banca ou layout novo.
Provas escaneadas (imagem) precisam de OCR antes (ex.: `ocrmypdf`).
Questões que dependem de figuras, tabelas ou gráficos chegam só com o texto.

## Testes

```bash
python -m pytest -q
```
