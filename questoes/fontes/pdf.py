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

_INICIO_CONTEXTO_CE = re.compile(
    r"^(Texto\s+[\dIVX]+|Julgue|Considerando|Acerca d|Com relação|Com base|A respeito|"
    r"No que (se refere|concerne|diz respeito)|Em relação|Tendo em vista|Quanto a|"
    r"A partir d|Nos itens|No item|Cada um dos itens|Texto para os itens)",
    re.I,
)
_LIXO = re.compile(
    r"^(\s*–?\s*\d+\s*–?\s*|.*\bRASCUNHO\b.*|.*www\.\S+.*|.*CADERNO\b.*|.*Página \d+.*|"
    r".*\bespaço livre\b.*|.*\bTIPO \d\b.*)$",
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


def extrair_texto_pdf(caminho, colunas=1, paginas_ignorar=()):
    import pdfplumber

    partes = []
    with pdfplumber.open(caminho) as pdf:
        for i, pag in enumerate(pdf.pages, start=1):
            if i in paginas_ignorar:
                continue
            if colunas == 1:
                partes.append(pag.extract_text() or "")
            else:
                larg = pag.width / colunas
                for c in range(colunas):
                    recorte = pag.crop((c * larg, 0, (c + 1) * larg, pag.height))
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


def _limpar_linhas(texto):
    return [l for l in texto.splitlines() if l.strip() and not _LIXO.match(l)]


def segmentar(texto, usar_numero_simples=True):
    """Divide o texto em blocos {numero: [linhas]} exigindo numeração sequencial."""
    blocos, atual, esperado, preambulo = {}, None, 1, []
    for linha in _limpar_linhas(texto):
        m = _INICIO_Q.match(linha) or (usar_numero_simples and _INICIO_NUM.match(linha))
        if m and int(m.group(1)) == esperado:
            atual = esperado
            esperado += 1
            blocos[atual] = [m.group(2)] if m.group(2).strip() else []
            continue
        (blocos[atual] if atual else preambulo).append(linha)
    return blocos, preambulo


def separar_alternativas(linhas, n_alts=5):
    """Procura, de trás para frente, a sequência A, B, C... e separa enunciado/alternativas."""
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
    alts = []
    for j, l in enumerate(letras):
        ini = pos[l]
        fim = pos[letras[j + 1]] if j + 1 < len(letras) else len(linhas)
        primeira = _ALT.match(linhas[ini]).group(2)
        alts.append(" ".join([primeira] + linhas[ini + 1 : fim]))
    return enunciado, alts


def _disciplina_de(numero, faixas):
    for f in faixas:
        if int(f["de"]) <= numero <= int(f["ate"]):
            return f.get("disciplina", ""), f.get("assunto", "")
    return "", ""


def _separar_contexto_ce(linhas):
    """Cebraspe: textos de apoio aparecem após o último item do bloco anterior.

    Retorna (linhas_do_item, linhas_de_contexto_para_os_próximos_itens).
    """
    for i in range(1, len(linhas)):
        if _INICIO_CONTEXTO_CE.match(linhas[i]) and linhas[i - 1].rstrip().endswith((".", "?", ")")):
            return linhas[:i], linhas[i:]
    return linhas, []


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
    blocos, preambulo = segmentar(texto)
    base = dict(Banca=cfg.banca, Orgao=cfg.orgao, Ano=str(cfg.ano))
    contexto = []
    if cfg.tipo == "certo_errado":
        inicio = next((i for i, l in enumerate(preambulo) if _INICIO_CONTEXTO_CE.match(l)), None)
        contexto = preambulo[inicio:] if inicio is not None else []
    for n, linhas in blocos.items():
        g = gabarito.get(n, "ausente")
        disc, assunto = _disciplina_de(n, cfg.disciplinas)
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
            sep = separar_alternativas(linhas, cfg.numero_alternativas)
            if sep is None and cfg.numero_alternativas == 5:
                sep = separar_alternativas(linhas, 4)
            if sep is None:
                continue
            enunciado, alts = sep
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
