"""Importador do dataset aberto eduagarcia/oab_exams (Hugging Face): 1ª fase do Exame de Ordem.

O exame 2010-01 foi aplicado pelo Cespe (Cebraspe); os demais pela FGV. Parte das
questões vem sem disciplina: como o caderno segue sempre a mesma ordem de matérias,
a disciplina é inferida pela posição, com desempate por palavras-chave perto das
fronteiras entre matérias.
"""
import re
import unicodedata

from ..schema import Questao

DISCIPLINAS = {
    "ETHICS": "Ética Profissional", "PHILOSOPHY": "Filosofia do Direito", "PHILOSHOPY": "Filosofia do Direito",
    "CONSTITUTIONAL": "Direito Constitucional", "HUMAN-RIGHTS": "Direitos Humanos",
    "INTERNATIONAL": "Direito Internacional", "TAXES": "Direito Tributário", "ADMINISTRATIVE": "Direito Administrativo",
    "ENVIRONMENTAL": "Direito Ambiental", "CIVIL": "Direito Civil", "CHILDREN": "Direito da Criança e do Adolescente",
    "CONSUMER": "Direito do Consumidor", "BUSINESS": "Direito Empresarial", "CIVIL-PROCEDURE": "Direito Processual Civil",
    "CRIMINAL": "Direito Penal", "CRIMINAL-PROCEDURE": "Direito Processual Penal", "LABOUR": "Direito do Trabalho",
    "LABOUR-PROCEDURE": "Direito Processual do Trabalho",
}

# Layouts das provas de 80 questões. A: confirmado nos exames rotulados 2013-12 e 2014-14.
# B: distribuição posterior (Ética com 8 questões); para cada exame sem rótulo escolhe-se
# o layout que mais concorda com as palavras-chave das questões.
LAYOUT_B = [("ETHICS", 1, 8), ("PHILOSOPHY", 9, 10), ("CONSTITUTIONAL", 11, 17), ("HUMAN-RIGHTS", 18, 20),
            ("INTERNATIONAL", 21, 22), ("TAXES", 23, 27), ("ADMINISTRATIVE", 28, 32), ("ENVIRONMENTAL", 33, 34),
            ("CIVIL", 35, 41), ("CHILDREN", 42, 43), ("CONSUMER", 44, 45), ("BUSINESS", 46, 50),
            ("CIVIL-PROCEDURE", 51, 56), ("CRIMINAL", 57, 62), ("CRIMINAL-PROCEDURE", 63, 68), ("LABOUR", 69, 74),
            ("LABOUR-PROCEDURE", 75, 80)]
LAYOUT_80 = [("ETHICS", 1, 10), ("PHILOSOPHY", 11, 12), ("CONSTITUTIONAL", 13, 19), ("HUMAN-RIGHTS", 20, 22),
             ("INTERNATIONAL", 23, 24), ("TAXES", 25, 28), ("ADMINISTRATIVE", 29, 34), ("ENVIRONMENTAL", 35, 36),
             ("CIVIL", 37, 43), ("CHILDREN", 44, 45), ("CONSUMER", 46, 47), ("BUSINESS", 48, 52),
             ("CIVIL-PROCEDURE", 53, 58), ("CRIMINAL", 59, 64), ("CRIMINAL-PROCEDURE", 65, 70), ("LABOUR", 71, 75),
             ("LABOUR-PROCEDURE", 76, 80)]

PALAVRAS = {
    "ETHICS": ["advogad", "oab", "estatuto da advocacia", "honorarios", "codigo de etica", "inscricao", "procuracao", "sociedade de advogados"],
    "PHILOSOPHY": ["filosof", "kelsen", "aristoteles", "kant", "hart", "bobbio", "justica", "positivismo", "jusnatural"],
    "CONSTITUTIONAL": ["constituicao", "constitucional", "emenda", "stf", "adi", "mandado de seguranca", "congresso", "federacao", "municipio"],
    "HUMAN-RIGHTS": ["direitos humanos", "convencao americana", "corte interamericana", "pacto de san jose", "comissao interamericana", "onu"],
    "INTERNATIONAL": ["tratado", "internacional", "extradicao", "estrangeir", "lindb", "carta rogatoria", "homologacao de sentenca estrangeira"],
    "TAXES": ["tribut", "imposto", "icms", "iss", "iptu", "contribuicao", "lancamento", "fisco", "isencao"],
    "ADMINISTRATIVE": ["administracao publica", "servidor", "licitacao", "ato administrativo", "concessao", "autarquia", "improbidade", "desapropria"],
    "ENVIRONMENTAL": ["ambient", "licenciamento", "fauna", "flora", "poluicao", "unidade de conservacao", "ibama"],
    "CIVIL": ["contrato", "posse", "propriedade", "heranca", "casamento", "obrigac", "usucapiao", "codigo civil", "testamento", "alimentos"],
    "CHILDREN": ["crianca", "adolescente", "eca", "menor", "ato infracional", "conselho tutelar", "guarda", "adocao"],
    "CONSUMER": ["consumidor", "fornecedor", "cdc", "produto", "servico defeituoso", "recall", "publicidade"],
    "BUSINESS": ["sociedade", "empresari", "falencia", "recuperacao judicial", "titulo de credito", "cheque", "duplicata", "acionist", "socio"],
    "CIVIL-PROCEDURE": ["cpc", "codigo de processo civil", "recurso", "apelacao", "agravo", "peticao inicial", "tutela", "citacao", "execucao", "sentenca"],
    "CRIMINAL": ["crime", "pena", "codigo penal", "dolo", "culpa", "furto", "roubo", "homicidio", "tipicidade", "prescricao"],
    "CRIMINAL-PROCEDURE": ["codigo de processo penal", "inquerito", "denuncia", "prisao preventiva", "flagrante", "juri", "acao penal", "habeas corpus"],
    "LABOUR": ["empregado", "empregador", "clt", "salario", "ferias", "jornada", "rescisao", "contrato de trabalho", "fgts"],
    "LABOUR-PROCEDURE": ["reclamacao trabalhista", "justica do trabalho", "recurso ordinario", "tst", "vara do trabalho", "reclamante", "reclamada", "audiencia"],
}


def _norm(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _pontuar(texto, tipo):
    return sum(len(re.findall(r"\b" + re.escape(p), texto)) for p in PALAVRAS[tipo])


def inferir_tipo(numero, texto, total=80, layout=LAYOUT_80):
    """Disciplina pela posição; nas 2 questões vizinhas de cada fronteira, desempata por palavras-chave."""
    if total != 80 or not 1 <= numero <= 80:
        return None
    idx = next(i for i, (_, de, ate) in enumerate(layout) if de <= numero <= ate)
    candidatos = [layout[idx][0]]
    tipo, de, ate = layout[idx]
    if numero - de < 2 and idx > 0:
        candidatos.append(layout[idx - 1][0])
    if ate - numero < 2 and idx < len(layout) - 1:
        candidatos.append(layout[idx + 1][0])
    if len(candidatos) == 1:
        return tipo
    texto = _norm(texto)
    pontos = {c: _pontuar(texto, c) for c in candidatos}
    melhor = max(candidatos, key=lambda c: (pontos[c], c == tipo))
    return melhor


def _tipo_por_layout(numero, layout):
    return next((t for t, de, ate in layout if de <= numero <= ate), None)


def escolher_layout(questoes):
    """Escolhe o layout com mais concordância entre posição e palavras-chave."""
    def concordancia(layout):
        n = 0
        for numero, texto in questoes:
            sc = {t: _pontuar(texto, t) for t in PALAVRAS}
            melhor = max(sc, key=sc.get)
            n += sc[melhor] > 0 and melhor == _tipo_por_layout(numero, layout)
        return n
    return max((LAYOUT_80, LAYOUT_B), key=concordancia)


def importar(caminho_parquet):
    import pyarrow.parquet as pq

    linhas = pq.read_table(caminho_parquet).to_pylist()
    totais, por_exame = {}, {}
    for r in linhas:
        totais[r["exam_id"]] = max(totais.get(r["exam_id"], 0), r["question_number"])
        por_exame.setdefault(r["exam_id"], []).append(
            (r["question_number"], _norm(r["question"] + " " + " ".join(r["choices"]["text"]))))
    layouts = {ex: escolher_layout(qs) for ex, qs in por_exame.items()}
    for r in linhas:
        if r["nullified"]:
            continue
        tipo = r["question_type"]
        if not tipo:
            texto = r["question"] + " " + " ".join(r["choices"]["text"])
            tipo = inferir_tipo(r["question_number"], texto, totais[r["exam_id"]], layouts[r["exam_id"]])
        banca = "Cebraspe" if r["exam_id"] == "2010-01" else "FGV"
        yield Questao.de_alternativas(
            r["choices"]["text"], Banca=banca, Orgao="OAB", Ano=r["exam_year"],
            Disciplina=DISCIPLINAS.get(tipo or "", ""), Enunciado=r["question"], Gabarito=r["answerKey"],
        )
