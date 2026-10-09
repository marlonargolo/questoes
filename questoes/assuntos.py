"""Classificação de Assunto por palavras-chave (preenche só quando vazio).

É um ponto de partida barato e auditável. Para cobertura alta em 100 mil
questões, troque/complemente por um classificador treinado ou por um LLM,
mantendo esta taxonomia como lista fechada de rótulos.
"""
import re
import unicodedata

TAXONOMIA = {
    "Língua Portuguesa": {
        "Crase": ["crase", "acento grave"],
        "Concordância": ["concordancia verbal", "concordancia nominal", "concordancia"],
        "Regência": ["regencia verbal", "regencia nominal", "regencia"],
        "Pontuação": ["pontuacao", "virgula", "ponto e virgula", "travessao", "dois-pontos"],
        "Colocação Pronominal": ["proclise", "enclise", "mesoclise", "colocacao pronominal"],
        "Ortografia": ["ortografia", "grafia", "acentuacao grafica", "hifen"],
        "Morfologia": ["classe gramatical", "substantivo", "adjetivo", "adverbio", "conjuncao", "preposicao"],
        "Sintaxe": ["sujeito", "predicado", "objeto direto", "objeto indireto", "oracao subordinada", "oracao coordenada", "aposto", "vocativo"],
        "Semântica": ["sinonimo", "antonimo", "sentido", "significado", "polissemia"],
        "Interpretação de Texto": ["de acordo com o texto", "infere-se", "depreende-se", "ideia central", "segundo o texto", "no texto"],
    },
    "Direito Administrativo": {
        "Atos Administrativos": ["ato administrativo", "atos administrativos", "anulacao", "revogacao", "convalidacao", "motivacao"],
        "Licitações e Contratos": ["licitacao", "14.133", "8.666", "pregao", "contrato administrativo", "dispensa", "inexigibilidade"],
        "Agentes Públicos": ["servidor publico", "8.112", "cargo publico", "estagio probatorio", "agente publico"],
        "Improbidade Administrativa": ["improbidade", "8.429"],
        "Responsabilidade Civil do Estado": ["responsabilidade civil do estado", "responsabilidade objetiva", "37, § 6"],
        "Poderes Administrativos": ["poder de policia", "poder hierarquico", "poder disciplinar", "poder regulamentar"],
        "Organização Administrativa": ["autarquia", "fundacao publica", "empresa publica", "sociedade de economia mista", "descentralizacao", "desconcentracao"],
        "Processo Administrativo": ["9.784", "processo administrativo"],
        "Princípios": ["principio da legalidade", "impessoalidade", "moralidade", "publicidade", "eficiencia", "limpe"],
    },
    "Direito Constitucional": {
        "Direitos e Garantias Fundamentais": ["direitos fundamentais", "art. 5", "habeas corpus", "mandado de seguranca", "habeas data"],
        "Organização do Estado": ["uniao", "estados-membros", "municipios", "competencia legislativa", "intervencao federal"],
        "Poder Legislativo": ["congresso nacional", "camara dos deputados", "senado federal", "processo legislativo", "emenda constitucional", "medida provisoria"],
        "Poder Judiciário": ["supremo tribunal federal", "stf", "stj", "poder judiciario", "cnj"],
        "Controle de Constitucionalidade": ["controle de constitucionalidade", "adi", "adpf", "adc", "inconstitucionalidade"],
        "Administração Pública": ["art. 37", "administracao publica direta"],
    },
    "Direito Penal": {
        "Crimes contra a Administração Pública": ["peculato", "concussao", "corrupcao passiva", "corrupcao ativa", "prevaricacao"],
        "Crimes contra o Patrimônio": ["furto", "roubo", "estelionato", "extorsao", "apropriacao indebita"],
        "Crimes contra a Pessoa": ["homicidio", "lesao corporal", "feminicidio"],
        "Teoria do Crime": ["tipicidade", "ilicitude", "culpabilidade", "dolo", "culpa", "tentativa", "consumacao"],
        "Penas": ["dosimetria", "pena privativa", "regime fechado", "regime semiaberto", "sursis"],
    },
    "Direito Processual Penal": {
        "Inquérito Policial": ["inquerito policial"],
        "Prisões": ["prisao preventiva", "prisao temporaria", "prisao em flagrante", "flagrante"],
        "Provas": ["prova ilicita", "cadeia de custodia", "interceptacao"],
        "Ação Penal": ["acao penal", "denuncia", "queixa-crime"],
    },
    "Raciocínio Lógico": {
        "Lógica Proposicional": ["proposicao", "tabela-verdade", "tautologia", "contradicao", "conectivo", "negacao"],
        "Probabilidade": ["probabilidade"],
        "Análise Combinatória": ["permutac", "arranjo", "combinac", "anagrama"],
        "Porcentagem": ["porcentagem", "percentual", "%"],
        "Sequências": ["sequencia", "progressao aritmetica", "progressao geometrica"],
    },
    "Informática": {
        "Segurança da Informação": ["malware", "virus", "phishing", "firewall", "backup", "criptografia", "ransomware"],
        "Redes e Internet": ["tcp/ip", "protocolo", "http", "dns", "navegador", "intranet", "e-mail"],
        "Sistemas Operacionais": ["windows", "linux"],
        "Editores de Texto e Planilhas": ["word", "excel", "writer", "calc", "planilha"],
        "Banco de Dados": ["sql", "banco de dados", "chave primaria"],
    },
    "Contabilidade": {
        "Demonstrações Contábeis": ["balanco patrimonial", "dre", "demonstracao do resultado", "dfc", "dmpl"],
        "Lançamentos Contábeis": ["lancamento", "debito", "credito", "partidas dobradas"],
    },
}


def _norm(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


_COMPILADA = {
    disc: {
        assunto: [re.compile(r"(?<!\w)" + re.escape(_norm(k)) + (r"" if k.endswith(("c", "%")) else r"(?!\w)")) for k in chaves]
        for assunto, chaves in assuntos.items()
    }
    for disc, assuntos in TAXONOMIA.items()
}
_DISC_NORM = {_norm(d): d for d in TAXONOMIA}
_DISC_ALIAS = {"portugues": "Língua Portuguesa", "lingua portuguesa": "Língua Portuguesa",
               "raciocinio logico-matematico": "Raciocínio Lógico", "nocoes de informatica": "Informática"}


def disciplina_canonica(d):
    n = _norm(d or "").strip()
    return _DISC_NORM.get(n) or _DISC_ALIAS.get(n)


def classificar(disciplina, enunciado, alternativas=()):
    disc = disciplina_canonica(disciplina)
    if not disc:
        return ""
    texto = _norm(enunciado + " " + " ".join(alternativas))
    melhor, pontos = "", 0
    for assunto, padroes in _COMPILADA[disc].items():
        p = sum(len(pad.findall(texto)) for pad in padroes)
        if p > pontos:
            melhor, pontos = assunto, p
    return melhor


# --- Assunto a partir do comando da questão ("Acerca de X, julgue os itens") ---
_ART = r"(?:d[aeo]s?|à|às|ao|aos|a|o|os|as|de|em|no|na|nos|nas)\s+"
_CMD_INICIO = re.compile(
    r"(?:^|\n|\.\s)(?:Ainda\s+)?(?:Acerca|A respeito|Com relação|Com referência|Em relação|No que (?:se refere|concerne|diz respeito)|"
    r"Quanto|Relativamente|À luz|No tocante|Sobre|No âmbito|Considerando o disposto|Com base n[ao]s?)\s+(?:" + _ART + r")?"
    r"(?P<t>[^\n]{3,140}?(?:\n[^\n]{0,80}?)?),\s*(?:julgue|assinale|é correto|é incorreto|analise|indique|considere)",
    re.I)
_CMD_FIM = re.compile(
    r"julgue\s+(?:o item|os (?:próximos |seguintes )?itens)(?:\s+(?:a seguir|seguintes|subsequentes|que se seguem))?,\s*"
    r"(?:relativos?|referentes?|acerca|a respeito|concernentes?|pertinentes?|com relação|no que se refere|quanto|sobre)"
    r"\s*(?:a|à|ao|aos|às|de|do|da|dos|das)?\s+(?P<t>[^\n]{3,140}?(?:\n[^\n]{0,80}?)?)\.\s*(?:\n|$)",
    re.I)
_GENERICO = re.compile(r"\b(texto|situação|hipotétic|informações|caso clínico|figura|tabela|quadro|gráfico|trecho|fragmento|"
                       r"exposto|apresentad|anterior|acima|a seguir|seguinte|desse|dessa|deste|desta|esse|essa|referid)\w*",
                       re.I)


def assunto_do_comando(enunciado):
    candidatos = [m.group("t") for m in _CMD_INICIO.finditer(enunciado or "")]
    candidatos += [m.group("t") for m in _CMD_FIM.finditer(enunciado or "")]
    for t in reversed(candidatos):
        t = re.sub(r"\s+", " ", t).strip(" ,;:")
        t = re.sub(r"^(?:" + _ART + r")", "", t, flags=re.I)
        t = re.sub(r"\s+e\s+(?:d[aeo]s?|à|às|ao|aos|a|o|os|as|de)\s+", " e ", t)
        if _GENERICO.search(t) or not (3 <= len(t) <= 90) or len(t.split()) > 12:
            continue
        return t[:1].upper() + t[1:]
    return ""


def propagar_assuntos(questoes, limiar=0.45):
    """Para questões sem Assunto, copia o da questão mais parecida (TF-IDF, mesma disciplina) se cos >= limiar."""
    from collections import defaultdict

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.neighbors import NearestNeighbors

    grupos = defaultdict(list)
    for i, q in enumerate(questoes):
        grupos[q.Disciplina].append(i)
    copiados = 0
    for idxs in grupos.values():
        com = [i for i in idxs if questoes[i].Assunto]
        sem = [i for i in idxs if not questoes[i].Assunto]
        if len(com) < 5 or not sem:
            continue
        texto = lambda q: q.Enunciado[-1500:] + " " + " ".join(getattr(q, f"Alternativa_{l}") for l in "ABCDE")
        vet = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, strip_accents="unicode", max_features=300000)
        Xc = vet.fit_transform([texto(questoes[i]) for i in com])
        nn = NearestNeighbors(n_neighbors=1, metric="cosine").fit(Xc)
        dist, viz = nn.kneighbors(vet.transform([texto(questoes[i]) for i in sem]))
        for i, d, v in zip(sem, dist[:, 0], viz[:, 0]):
            if 1 - d >= limiar:
                questoes[i].Assunto = questoes[com[v]].Assunto
                copiados += 1
    return copiados
