"""Extrai questões de provas oficiais em PDF + gabarito oficial.

As bancas (Cebraspe, FGV, FCC, Vunesp, Cesgranrio, IBFC, Quadrix...) publicam
o caderno de prova e o gabarito definitivo em PDF. Esta é a fonte primária e
pública das questões. O parser é heurístico: confira o relatório de validação
e revise amostras de cada prova nova.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..schema import Questao

# Início de questão: "QUESTÃO 12", "Questão 12", "12.", "12)", "12 -", "12 " (Cebraspe)
_INICIO_Q = re.compile(r"^\s*(?:QUEST[ÃA]O|Quest[ãa]o)\s*N?[º°o.]?\s*(\d{1,3})\b[\s.:\-–)]*(.*)$")
_INICIO_NUM = re.compile(r"^\s*(\d{1,3})\s*(?:[.)\-–]\s*|\s+)(?=\S)(.*)$")
# Alternativa: "(A) texto", "A) texto", "a) texto", "A. texto", "A - texto"
_ALT = re.compile(r"^\s*\(?([A-Ea-e])\s*[)\.\-–]\s*(.*)$")
_ALT_SOLTA = re.compile(r"^\s*([A-E])\s+(.*)$")  # Cebraspe: "A texto" (só maiúscula, letra solta)

_INICIO_CONTEXTO_CE = re.compile(
    r"^(Texto\s+[\dA-Z]+[\w-]*|Julgue|Considerando|Considere|Acerca d|Com relação|Com referência|Com base|A respeito|"
    r"No que (se refere|concerne|diz respeito)|Em relação|Tendo em vista|Quanto a|À luz d|Relativamente|"
    r"A partir d|Nos itens|No item|Cada um dos itens|Texto para os itens|Ainda (com relação|acerca|a respeito|"
    r"considerando|no que|em relação|quanto|sobre|de acordo|com base)|Julgue os (próximos )?itens|"
    r"Situação hipotética|Figura\s|Tabela\s|Quadro\s)",
    re.I,
)
_LIXO = re.compile(
    r"^(.*\bRASCUNHO\b.*|\s*(www\.\S+|\S+@\S+\.\S+)\s*|.*CADERNO\b.*|.*Página \d+.*|"
    r".*\bespaço livre\b.*|.*\bTIPO \d\b.*|CEBRASPE\s*[–-].*|\s*-+\s*PROVA (OBJETIVA|DISCURSIVA)\s*-+\s*|"
    r"\s*BLOCO\s+[IVX]+\s*|.*Aplicação:\s*\d{4}.*|\s*\(cid:\d+\).*)$",
    re.I,
)


@dataclass
class Prova:
    prova: str
    banca: str
    orgao: str
    ano: int | str
    tipo: str = "multipla_escolha"  # ou "certo_errado"
    gabarito: str | None = None  # PDF/TXT do gabarito definitivo
    gabarito_texto: str | None = None  # alternativa: "1 A 2 C 3 E ..."
    colunas: int = 1  # 2 para cadernos diagramados em duas colunas
    paginas_ignorar: list = field(default_factory=list)  # 1-based (capa, instruções)
    disciplinas: list = field(default_factory=list)  # [{de, ate, disciplina, assunto?}]
    numero_alternativas: int = 5


def _pagina_coluna_unica(pag, meio):
    """Página sem divisão em colunas: muitas linhas com palavras atravessando o meio, espalhadas pela página."""
    tops = sorted({round(w["top"]) for w in pag.extract_words() if w["x0"] < meio - 3 and w["x1"] > meio + 3})
    return len(tops) >= 5 and (tops[-1] - tops[0]) > pag.height * 0.3


def _topo_colunas(pag, meio):
    """Altura até onde há texto de largura total (palavras que cruzam o meio da página) no topo."""
    limite = 0
    for w in pag.extract_words():
        if w["x0"] < meio - 3 and w["x1"] > meio + 3 and w["top"] < pag.height * 0.5:
            limite = max(limite, w["bottom"])
    return limite


def extrair_texto_pdf(caminho, colunas=1, paginas_ignorar=()):
    import pdfplumber

    partes = []
    with pdfplumber.open(caminho) as pdf:
        for i, pag in enumerate(pdf.pages, start=1):
            if i in paginas_ignorar:
                continue
            if colunas == 1:
                partes.append(pag.extract_text() or "")
                continue
            larg = pag.width / colunas
            if colunas == 2 and _pagina_coluna_unica(pag, pag.width / 2):
                partes.append(pag.extract_text() or "")
                continue
            topo = _topo_colunas(pag, pag.width / 2) if colunas == 2 else 0
            if topo:
                partes.append(pag.crop((0, 0, pag.width, topo + 1)).extract_text() or "")
            for c in range(colunas):
                recorte = pag.crop((c * larg, topo + 1 if topo else 0, (c + 1) * larg, pag.height))
                partes.append(recorte.extract_text() or "")
    return "\n".join(partes)


def _ler_texto(caminho):
    p = Path(caminho)
    if p.suffix.lower() == ".pdf":
        return extrair_texto_pdf(p)
    return p.read_text(encoding="utf-8")


def parse_gabarito(texto):
    """Retorna {numero: letra}. 'X'/'*'/'ANULADA' viram None (questão anulada).

    Aceita pares "1 A 2 B", "1-A", "01: C" e tabelas Cebraspe em que uma linha
    traz os números dos itens e a linha seguinte os gabaritos (C/E).
    """
    gab = {}
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    tok_resp = r"(?:[A-E]|X|\*|ANULAD[AO]|NULA)"
    for i, linha in enumerate(linhas[:-1]):
        nums = re.findall(r"\d{1,3}", linha)
        if len(nums) >= 3 and re.fullmatch(r"[\D]*(\d{1,3}\s+)+\d{1,3}\s*", linha):
            seguinte = re.sub(r"^\s*(Gabarito|Resposta)s?\s*:?", "", linhas[i + 1], flags=re.I)
            resp = seguinte.split()
            if len(resp) == len(nums) and all(re.fullmatch(tok_resp, r, re.I) for r in resp):
                for n, r in zip(nums, resp):
                    gab[int(n)] = r.upper()
    if not gab:
        for n, r in re.findall(r"(?<!\d)(\d{1,3})\s*[-–:.)]?\s*(" + tok_resp + r")(?![a-zA-Z])", texto):
            gab.setdefault(int(n), r.upper())
    return {n: (r if re.fullmatch(r"[A-E]", r) else None) for n, r in gab.items()}


_CODIGO_BARRAS = re.compile(r"\|\|[^|]{3,60}\|\|")
# Rótulo de texto de apoio do Cebraspe: "Texto 1A1-I", "Caso clínico 9A1AAA", "Texto CB1A1AAA"
_ID_CONTEXTO = re.compile(r"\b(?:[A-Z]{0,3}\d+[A-Z]\d+[A-Z]*(?:-[IVX]+)?)\b")
_INICIO_CONTEXTO_ME = re.compile(r"^(Texto|Caso clínico|Caso|Situação hipotética|Figura|Tabela|Quadro|Gráfico|"
                                 r"Considere|Leia|Observe|Atenção:|Instrução:|As questões|Para responder)\b", re.I)


_CABECALHO_DISC = re.compile(
    r"^(Língua|Lingua|Noções|Nocoes|Direito|Direitos|Legislação|Legislacao|Raciocínio|Raciocinio|Matemática|Matematica|"
    r"Informática|Informatica|Ética|Etica|Atualidades|Administração|Administracao|Contabilidade|Economia|Estatística|"
    r"Arquivologia|Auditoria|Finanças|Gestão|Política|Políticas|Saúde|Física|Química|Biologia|História|Geografia|"
    r"Inglês|Espanhol|Português|Realidade|Tecnologia|Engenharia|Medicina|Enfermagem|Psicologia|Pedagogia|Fundamentos|"
    r"Teoria|Criminologia|Estatuto|Regimento|Análise|Sistemas|Segurança|Desenvolvimento|Banco de Dados|Redes|Libras|"
    r"Didática|Educação|Conhecimentos (Gerais|Específicos|Básicos|Pedagógicos|Regionais|de|sobre|em)|Matemática Financeira|"
    r"Lei |Comércio|Marketing|Orçamento|AFO|Atendimento|Vendas|Cultura|Cidadania|Ciências|Programação|Governança|"
    r"Controle|Processo|Psicopatologia|Farmacologia|Clínica|Anatomia|Fisiologia|Nutrição|Odontologia|Fisioterapia|"
    r"Serviço Social|Assistência|Políticas Públicas|Licitações|Gerenciamento|Engenharia de Software|Infraestrutura)\b"
)
_GRUPO_GENERICO = re.compile(r"^Conhecimentos (Gerais|Específicos|Básicos|Complementares)\b", re.I)


def _e_cabecalho(linha):
    l = linha.strip()
    return (3 <= len(l) <= 75 and not re.search(r"[.,;:?!]$|[,;]", l) and not re.search(r"\d", l)
            and _CABECALHO_DISC.match(l) and l[0].isupper() and len(l.split()) <= 10)


def _limpar_linhas(texto):
    from collections import Counter

    texto = _CODIGO_BARRAS.sub("", texto)
    linhas = [l for l in texto.splitlines() if l.strip() and not _LIXO.match(l)]
    # cabeçalhos/rodapés: linhas longas que se repetem em várias páginas
    freq = Counter(l.strip() for l in linhas)
    return [l for l in linhas if not (freq[l.strip()] >= 4 and len(l.strip()) > 12 and not _ALT.match(l))]


def _separar_contexto_me(alt_e):
    """Na última alternativa, separa um texto de apoio que pertence às questões seguintes."""
    linhas = alt_e
    for i in range(1, len(linhas)):
        if _INICIO_CONTEXTO_ME.match(linhas[i]) and (
                _ID_CONTEXTO.search(linhas[i]) or linhas[i - 1].rstrip().endswith((".", ";", ")", "”", "?"))):
            return linhas[:i], linhas[i:]
    return linhas, []


def segmentar(texto, usar_numero_simples=True, inicio=1):
    """Divide o texto em blocos {numero: [linhas]} exigindo numeração sequencial a partir de `inicio`."""
    blocos, atual, esperado, preambulo = {}, None, inicio, []
    linhas = _limpar_linhas(texto)
    disc_atual, segmentar.disciplinas = "", {}
    for idx, linha in enumerate(linhas):
        if _e_cabecalho(linha) and any(
                (_INICIO_Q.match(x) or _INICIO_NUM.match(x) or re.match(r"^\s*\d{1,3}\s*$", x)
                 or re.match(r"^(Texto|Leia|Considere|Atenção|Analise|Observe)\b", x)) for x in linhas[idx + 1: idx + 4]):
            disc_atual = "" if _GRUPO_GENERICO.match(linha.strip()) else linha.strip()
            continue
        so_num = re.match(r"^\s*–?\s*(\d{1,3})\s*–?\s*$", linha)
        if so_num:  # número sozinho: início de questão (FGV/FCC) ou número de página
            if int(so_num.group(1)) == esperado and "–" not in linha:
                atual = esperado
                esperado += 1
                blocos[atual] = []
                segmentar.disciplinas[atual] = disc_atual
            continue
        m = _INICIO_Q.match(linha) or (usar_numero_simples and _INICIO_NUM.match(linha))
        # aceita pular um número (item perdido na extração) se a linha começa como frase
        if m and (int(m.group(1)) == esperado or (
                int(m.group(1)) == esperado + 1 and atual and m.group(2)[:1].isupper())):
            atual = int(m.group(1))
            esperado = atual + 1
            blocos[atual] = [m.group(2)] if m.group(2).strip() else []
            segmentar.disciplinas[atual] = disc_atual
            continue
        (blocos[atual] if atual else preambulo).append(linha)
    return blocos, preambulo


def separar_alternativas(linhas, n_alts=5, padrao=None):
    """Procura, de trás para frente, a sequência A, B, C... e separa enunciado/alternativas."""
    if padrao is None:
        return _separar(linhas, n_alts, _ALT) or _separar(linhas, n_alts, _ALT_SOLTA)
    return _separar(linhas, n_alts, padrao)


def _separar(linhas, n_alts, _ALT):
    letras = "ABCDE"[:n_alts]
    pos = {}
    procurar = len(letras) - 1
    for i in range(len(linhas) - 1, -1, -1):
        m = _ALT.match(linhas[i])
        if m and m.group(1).upper() == letras[procurar]:
            pos[letras[procurar]] = i
            procurar -= 1
            if procurar < 0:
                break
    if len(pos) != len(letras):
        return None
    enunciado = "\n".join(linhas[: pos["A"]])
    alts, sobra = [], []
    for j, l in enumerate(letras):
        ini = pos[l]
        fim = pos[letras[j + 1]] if j + 1 < len(letras) else len(linhas)
        corpo = [_ALT.match(linhas[ini]).group(2)] + linhas[ini + 1 : fim]
        if j + 1 == len(letras):
            corpo, sobra = _separar_contexto_me(corpo)
        alts.append(" ".join(corpo))
    return enunciado, alts, sobra


def _disciplina_de(numero, faixas):
    for f in faixas:
        if int(f["de"]) <= numero <= int(f["ate"]):
            return f.get("disciplina", ""), f.get("assunto", "")
    return "", ""


def _separar_contexto_ce(linhas):
    """Cebraspe: textos de apoio aparecem após o último item do bloco anterior.

    Retorna (linhas_do_item, linhas_de_contexto_para_os_próximos_itens).
    """
    fim_frase = (".", "?", ")", "”", "\"", ":")
    for i in range(1, len(linhas)):
        if _INICIO_CONTEXTO_CE.match(linhas[i]) and linhas[i - 1].rstrip().endswith(fim_frase):
            return linhas[:i], linhas[i:]
    # Sem marcador conhecido: o comando "julgue os itens" começa na frase que contém "julgue"
    for j in range(1, len(linhas)):
        if re.search(r"\bjulgue\b", linhas[j], re.I):
            for k in range(j, max(0, j - 4), -1):
                if linhas[k - 1].rstrip().endswith(fim_frase):
                    return linhas[:k], linhas[k:]
            break
    return linhas, []


def linhas_tem_id(linhas, contexto):
    """A questão cita o rótulo do texto de apoio (ex.: 'texto 1A1-I')? Sem rótulo, vale só para a 1ª questão."""
    if not contexto:
        return False
    texto = " ".join(linhas)
    ids = set(_ID_CONTEXTO.findall(contexto[0]))
    if ids:
        return any(i in texto for i in ids)
    rot = re.match(r"^(Texto|Fragmento)\s+([IVX\d]+)\b", contexto[0])
    if rot:  # "Texto II": vale p/ questões que citam o texto (e não citam outro texto numerado)
        outros = set(re.findall(r"\b[Tt]exto\s+([IVX]+|\d+)\b", texto)) - {rot.group(2)}
        return not outros and bool(re.search(r"\b(texto|trecho|fragmento|segmento|parágrafo|autor|narrador|frase)\b", texto, re.I))
    return False


def importar_prova(cfg: Prova):
    texto = extrair_texto_pdf(cfg.prova, cfg.colunas, cfg.paginas_ignorar)
    if cfg.gabarito_texto:
        gabarito = parse_gabarito(cfg.gabarito_texto)
    elif cfg.gabarito:
        gabarito = parse_gabarito(_ler_texto(cfg.gabarito))
    else:
        raise ValueError(f"{cfg.prova}: informe 'gabarito' ou 'gabarito_texto'")
    yield from questoes_do_texto(texto, gabarito, cfg)


def questoes_do_texto(texto, gabarito, cfg: Prova):
    blocos, preambulo = segmentar(texto, inicio=min(gabarito) if gabarito else 1)
    base = dict(Banca=cfg.banca, Orgao=cfg.orgao, Ano=str(cfg.ano))
    contexto, contexto_me, usos_ctx = [], [], 0
    if cfg.tipo == "certo_errado":
        inicio = next((i for i, l in enumerate(preambulo) if _INICIO_CONTEXTO_CE.match(l)), None)
        contexto = preambulo[inicio:] if inicio is not None else []
    else:
        inicio = next((i for i, l in enumerate(preambulo) if _INICIO_CONTEXTO_ME.match(l)), None)
        contexto_me = preambulo[inicio:] if inicio is not None else []
    detectadas = dict(segmentar.disciplinas)
    disc_anterior = None
    for n, linhas in blocos.items():
        if detectadas.get(n) != disc_anterior and disc_anterior is not None:
            contexto_me = [] if not (contexto_me and linhas_tem_id(linhas, contexto_me) and usos_ctx == 0) else contexto_me
        disc_anterior = detectadas.get(n)
        g = gabarito.get(n, "ausente")
        disc, assunto = _disciplina_de(n, cfg.disciplinas)
        disc = disc or detectadas.get(n, "")
        if cfg.tipo == "certo_errado":
            item, novo_ctx = _separar_contexto_ce(linhas)
            if g not in (None, "ausente"):
                enunciado = "\n".join(contexto + item) if contexto else "\n".join(item)
                yield Questao.certo_errado(g, Enunciado=enunciado, Disciplina=disc, Assunto=assunto, **base)
            if novo_ctx:
                contexto = novo_ctx
        else:
            if g in (None, "ausente"):
                continue  # anulada ou sem gabarito
            if contexto_me and not linhas_tem_id(linhas, contexto_me):
                contexto_me, usos_ctx = ([], 0) if usos_ctx else (contexto_me, usos_ctx)
            sep = separar_alternativas(linhas, cfg.numero_alternativas)
            if sep is None and cfg.numero_alternativas == 5:
                sep = separar_alternativas(linhas, 4)
            if sep is None:
                contexto_me = []
                continue
            enunciado, alts, sobra = sep
            if contexto_me:
                enunciado = "\n".join(contexto_me) + "\n" + enunciado
                usos_ctx += 1
            if sobra:
                contexto_me, usos_ctx = sobra, 0
            yield Questao.de_alternativas(
                alts, Enunciado=enunciado, Gabarito=g, Disciplina=disc, Assunto=assunto, **base
            )


def importar_manifesto(caminho):
    """Lê um manifesto YAML com a lista de provas (ver exemplos/manifesto_provas.yaml)."""
    caminho = Path(caminho)
    with open(caminho, encoding="utf-8") as f:
        dados = yaml.safe_load(f)
    raiz = caminho.parent
    padrao = dados.get("padrao", {})
    for item in dados["provas"]:
        cfg = Prova(**{**padrao, **item})
        cfg.prova = str(raiz / cfg.prova)
        if cfg.gabarito:
            cfg.gabarito = str(raiz / cfg.gabarito)
        try:
            yield from importar_prova(cfg)
        except Exception as e:  # uma prova ruim não derruba o lote
            print(f"[pdf] falha em {cfg.prova}: {e}")
