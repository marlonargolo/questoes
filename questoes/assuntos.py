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
