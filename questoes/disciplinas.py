"""Classificação de Disciplina por palavras-chave, com suavização pela vizinhança no caderno.

Usada quando a fonte não traz a disciplina (ex.: cadernos do Cebraspe). Cada item recebe
pontos por disciplina; depois, dentro do mesmo caderno, cada item herda a disciplina
dominante numa janela de vizinhos (as provas agrupam itens da mesma matéria).
"""
import re
import unicodedata
from collections import Counter

# Pesos: termo forte = 3, termo comum = 1 (prefixo "!" marca termo forte)
VOCAB = {
    "Língua Portuguesa": ["!texto", "!período", "!oração", "!vírgula", "!concordância", "!regência", "!crase", "!sentido original",
                          "!correção gramatical", "!coesão", "!vocábulo", "!forma verbal", "parágrafo", "sujeito", "pronome",
                          "!sintátic", "!semântic", "!ortografi", "!acento", "trecho", "!reescrit", "!locução", "conjunção"],
    "Redação Oficial": ["!manual de redação", "!redação oficial", "!comunicações oficiais", "!padrão ofício", "!pronome de tratamento",
                        "!vossa excelência", "!memorando", "!exposição de motivos"],
    "Língua Inglesa": ["!the ", "!which ", "!according to the text", "!text ", " is ", " are ", " of the "],
    "Raciocínio Lógico": ["!proposição", "!tabela-verdade", "!tautologia", "!contradição", "!silogismo", "!negação da proposição",
                          "!equivalente", "!conectivo", "!lógica", "!sequência", "!argumento válido", "conjunto", "!diagrama"],
    "Matemática": ["!equação", "!função", "!porcentagem", "!juros", "!razão", "!proporção", "!progressão", "!área", "!volume",
                   "!triângulo", "!número", "!soma", "!média aritmética", "!fração", "!regra de três", "!matriz", "!polinômio"],
    "Estatística": ["!probabilidade", "!variância", "!desvio padrão", "!média", "!mediana", "!moda", "!amostra", "!distribuição",
                    "!regressão", "!correlação", "!intervalo de confiança", "!hipótese nula", "!estimador", "!variável aleatória"],
    "Informática": ["!windows", "!linux", "!excel", "!word", "!navegador", "!internet", "!intranet", "!e-mail", "!correio eletrônico",
                    "!planilha", "!computador", "!arquivo", "!pasta", "!backup", "!vírus", "!malware", "!firewall", "!nuvem",
                    "!google", "!chrome", "!teclado", "!software", "!hardware", "!rede", "!protocolo", "!sql", "!banco de dados",
                    "!algoritmo", "!python", "!java", "!criptografia", "!phishing", "!ransomware", "!servidor"],
    "Direito Constitucional": ["!constituição", "!cf", "!constitucional", "!emenda constitucional", "!direitos fundamentais",
                               "!stf", "!supremo tribunal federal", "!mandado de segurança", "!habeas corpus", "!habeas data",
                               "!ação direta", "!adi", "!adpf", "!poder constituinte", "!federação", "!congresso nacional",
                               "!processo legislativo", "!medida provisória"],
    "Direito Administrativo": ["!administração pública", "!ato administrativo", "!servidor público", "!licitação", "!14.133",
                               "!8.666", "!8.112", "!improbidade", "!8.429", "!autarquia", "!poder de polícia",
                               "!agente público", "!concessão", "!permissão", "!processo administrativo", "!9.784",
                               "!responsabilidade civil do estado", "!desapropriação", "!bens públicos", "!cargo público"],
    "Direito Penal": ["!crime", "!pena", "!código penal", "!dolo", "!culposo", "!tipicidade", "!ilicitude", "!culpabilidade",
                      "!furto", "!roubo", "!homicídio", "!peculato", "!corrupção passiva", "!tráfico", "!estelionato",
                      "!legítima defesa", "!tentativa", "!prescrição da pretensão"],
    "Direito Processual Penal": ["!processo penal", "!inquérito policial", "!ação penal", "!denúncia", "!prisão preventiva",
                                 "!prisão temporária", "!flagrante", "!código de processo penal", "!cpp", "!tribunal do júri",
                                 "!queixa", "!delegado", "!autoridade policial", "!busca e apreensão", "!interceptação"],
    "Direito Civil": ["!código civil", "!contrato", "!posse", "!propriedade", "!usucapião", "!obrigação", "!responsabilidade civil",
                      "!casamento", "!união estável", "!sucessão", "!herança", "!testamento", "!pessoa jurídica", "!negócio jurídico",
                      "!prescrição", "!decadência", "!personalidade", "!domicílio"],
    "Direito Processual Civil": ["!código de processo civil", "!cpc", "!petição inicial", "!citação", "!contestação", "!sentença",
                                 "!apelação", "!agravo", "!recurso especial", "!tutela", "!execução", "!cumprimento de sentença",
                                 "!competência", "!litisconsórcio", "!coisa julgada", "!embargos"],
    "Direito do Trabalho": ["!empregado", "!empregador", "!clt", "!contrato de trabalho", "!jornada", "!férias", "!salário",
                            "!aviso prévio", "!fgts", "!rescisão", "!horas extras", "!trabalhista"],
    "Direito Processual do Trabalho": ["!reclamação trabalhista", "!justiça do trabalho", "!recurso ordinário", "!vara do trabalho",
                                       "!reclamante", "!reclamado", "!tst", "!dissídio", "!processo do trabalho"],
    "Direito Tributário": ["!tributo", "!tributári", "!imposto", "!icms", "!iss", "!ipi", "!iptu", "!ipva", "!itcmd", "!contribuição",
                           "!taxa", "!lançamento", "!crédito tributário", "!fato gerador", "!ctn", "!isenção", "!imunidade",
                           "!obrigação tributária", "!contribuinte"],
    "Direito Previdenciário": ["!previdência", "!previdenciári", "!aposentadoria", "!segurado", "!inss", "!benefício",
                               "!auxílio-doença", "!pensão por morte", "!salário-de-contribuição", "!rgps", "!8.213", "!8.212"],
    "Direito Empresarial": ["!empresário", "!sociedade limitada", "!sociedade anônima", "!falência", "!recuperação judicial",
                            "!título de crédito", "!cheque", "!duplicata", "!nota promissória", "!estabelecimento empresarial"],
    "Direito Ambiental": ["!meio ambiente", "!ambiental", "!licenciamento", "!unidade de conservação", "!9.605", "!código florestal"],
    "Direitos Humanos": ["!direitos humanos", "!convenção americana", "!corte interamericana", "!declaração universal", "!pacto"],
    "Legislação Especial": ["!lei maria da penha", "!estatuto do desarmamento", "!lei de drogas", "!11.343", "!abuso de autoridade",
                            "!crimes hediondos", "!estatuto da criança", "!eca", "!organização criminosa", "!lavagem de dinheiro",
                            "!código de trânsito", "!ctb"],
    "Contabilidade": ["!contábil", "!contabilidade", "!ativo", "!passivo", "!patrimônio líquido", "!balanço patrimonial", "!débito",
                      "!crédito", "!lançamento contábil", "!depreciação", "!dre", "!demonstração do resultado", "!estoque", "!cpc 00",
                      "!receita", "!despesa", "!custo"],
    "Auditoria": ["!auditoria", "!auditor", "!papéis de trabalho", "!amostragem", "!risco de auditoria", "!controle interno",
                  "!opinião do auditor", "!nbc ta", "!evidência de auditoria"],
    "Administração Financeira e Orçamentária": ["!orçamento", "!orçamentári", "!lei orçamentária", "!loa", "!ldo", "!ppa",
                                                "!crédito adicional", "!empenho", "!liquidação", "!restos a pagar",
                                                "!lei de responsabilidade fiscal", "!lrf", "!4.320", "!despesa pública", "!receita pública"],
    "Economia": ["!economia", "!econômic", "!inflação", "!pib", "!demanda", "!oferta", "!elasticidade", "!juros", "!câmbio",
                 "!política monetária", "!política fiscal", "!mercado", "!microeconomia", "!macroeconomia", "!utilidade marginal"],
    "Administração": ["!gestão", "!planejamento estratégico", "!liderança", "!motivação", "!organização", "!processos",
                      "!gestão de pessoas", "!administração", "!balanced scorecard", "!gestão de projetos", "!governança",
                      "!qualidade", "!cultura organizacional", "!avaliação de desempenho"],
    "Arquivologia": ["!arquivo corrente", "!arquivística", "!arquivologia", "!tabela de temporalidade", "!gestão de documentos",
                     "!protocolo", "!documento de arquivo", "!fundo", "!conarq"],
    "Ética no Serviço Público": ["!código de ética", "!1.171", "!ética", "!conduta ética", "!comissão de ética"],
    "Saúde Pública e SUS": ["!sus", "!sistema único de saúde", "!8.080", "!atenção básica", "!vigilância", "!epidemiológic",
                            "!saúde da família", "!humanização", "!ministério da saúde"],
    "Enfermagem": ["!enfermagem", "!enfermeiro", "!técnico de enfermagem", "!curativo", "!sinais vitais", "!administração de medicamento",
                   "!cateter", "!sonda", "!úlcera por pressão"],
    "Medicina": ["!paciente", "!diagnóstico", "!tratamento", "!sintomas", "!doença", "!síndrome", "!exame físico", "!terapia",
                 "!fármaco", "!dose", "!cirurgia", "!infecção", "!clínic"],
    "Psicologia": ["!psicolog", "!psicoterap", "!psíquic", "!comportamento", "!avaliação psicológica", "!freud", "!psicanál"],
    "Serviço Social": ["!serviço social", "!assistente social", "!assistência social", "!suas", "!cras", "!creas", "!loas"],
    "Pedagogia e Educação": ["!educação", "!ensino", "!aprendizagem", "!escola", "!professor", "!aluno", "!currículo", "!ldb",
                             "!9.394", "!didática", "!avaliação da aprendizagem", "!bncc", "!pedagóg"],
    "Engenharia": ["!engenharia", "!concreto", "!estrutura", "!viga", "!tensão", "!resistência", "!projeto", "!obra", "!solo",
                   "!hidráulic", "!elétric", "!circuito", "!motor", "!corrente", "!transformador", "!mecânic"],
    "Física": ["!velocidade", "!aceleração", "!força", "!energia", "!massa", "!campo elétrico", "!temperatura", "!onda"],
    "Química": ["!reação", "!molécula", "!ácido", "!base", "!ph", "!solução", "!concentração", "!átomo", "!ligação química"],
    "Biologia": ["!célula", "!dna", "!gene", "!espécie", "!organismo", "!ecossistema", "!proteína", "!fotossíntese"],
    "Geografia": ["!região", "!clima", "!relevo", "!bioma", "!população", "!território", "!urbanização", "!hidrografia"],
    "História": ["!século", "!império", "!república", "!colonial", "!revolução", "!guerra", "!ditadura", "!getúlio vargas"],
    "Criminologia": ["!criminologia", "!criminológic", "!vitimologia", "!escola clássica", "!escola positiva", "!labelling"],
    "Medicina Legal": ["!medicina legal", "!perícia", "!lesão corporal", "!cadáver", "!necropsia", "!traumatologia forense", "!tanatologia"],
}


def _norm(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


_PADROES = {}
for _disc, _termos in VOCAB.items():
    lista = []
    for t in _termos:
        peso = 3 if t.startswith("!") else 1
        termo = _norm(t.lstrip("!"))
        lista.append((re.compile(r"(?<![a-z0-9])" + re.escape(termo.strip()) + ("" if termo.endswith(("-", " ")) else r"")), peso))
    _PADROES[_disc] = lista


def pontuar(texto):
    t = _norm(texto)
    pts = Counter()
    for disc, lista in _PADROES.items():
        for pad, peso in lista:
            n = len(pad.findall(t))
            if n:
                pts[disc] += peso * min(n, 3)
    return pts


_ESPECIALIDADE = re.compile(r"\b(?:ESPECIALIDADE|AREA|ÁREA|PERFIL|ENFASE|ÊNFASE)\s*:?\s*([A-ZÇÃÕÁÉÍÓÚÂÊÔ ]{4,60})", re.I)


def disciplina_do_bloco(bloco):
    """'... ESPECIALIDADE PSICOLOGIA' -> 'Psicologia' (fallback para provas de cargo especializado)."""
    m = _ESPECIALIDADE.search(bloco or "")
    if not m:
        return ""
    nome = m.group(1).strip().title()
    return re.sub(r"\b(De|Da|Do|Das|Dos|E|Em)\b", lambda x: x.group(0).lower(), nome)


def classificar_caderno(itens, janela=2, bloco=""):
    """itens: lista de textos na ordem do caderno. Devolve lista de disciplinas."""
    pts = [pontuar(t) for t in itens]
    brutas = [p.most_common(1)[0][0] if p and p.most_common(1)[0][1] >= 3 else "" for p in pts]
    fallback = disciplina_do_bloco(bloco)
    saida = []
    for i in range(len(itens)):
        soma = Counter()
        for j in range(max(0, i - janela), min(len(itens), i + janela + 1)):
            peso = 2 if j == i else 1
            for d, v in pts[j].items():
                soma[d] += v * peso
        if soma and soma.most_common(1)[0][1] >= 4:
            saida.append(soma.most_common(1)[0][0])
        else:
            saida.append(brutas[i] or fallback)
    return saida
