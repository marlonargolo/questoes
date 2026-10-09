"""Coleta de provas objetivas (caderno Tipo 1) + gabarito definitivo no site da FGV Conhecimento.

Página de cada concurso: https://conhecimento.fgv.br/concursos/<slug>
Estrutura: "Prova Objetiva" -> <Cargo em negrito> -> links "Tipo 1..4". O gabarito definitivo
é um PDF com uma seção por "<Cargo> - TIPO N" seguida das linhas de números e letras.
"""
import html
import re
import unicodedata

AGENTE = "Mozilla/5.0 (compatible; questoes-bot/0.1; coleta de provas publicas)"


def _norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


_STOP = {"de", "da", "do", "das", "dos", "e", "a", "o", "em", "para", "area", "sem", "especialidade", "tipo", "cargo", "nivel"}


def tokens(t):
    return {w for w in _norm(t).split() if w not in _STOP and len(w) > 1}


def _texto(fragmento):
    return html.unescape(re.sub(r"<[^>]+>", " ", fragmento)).strip()


def extrair_pagina(conteudo):
    """Devolve (orgao, cadernos[(cargo, url, data)], gabaritos[(rotulo, url, data)])."""
    titulo = re.search(r"<title>(.*?)</title>", conteudo, re.S)
    orgao = _texto(titulo.group(1)).split("|")[0].strip() if titulo else ""
    orgao = re.sub(r"^(?:[IVXLC]+\s+)?Concurso Público\s+(?:para\s+(?:o\s+provimento\s+de\s+cargos\s+de\s+.*?\s+d[aoe]s?\s+)?"
                   r"(?:o|a|os|as)?\s*)?", "", orgao, flags=re.I).strip()
    cadernos, gabaritos = [], []
    padrao_bloco = r'(?:<div id="paragraph-\d+"|<tr[ >]).*?(?=<div id="paragraph-\d+"|<tr[ >]|\Z)'
    for par in re.finditer(padrao_bloco, conteudo, re.S):
        bloco = par.group(0)
        data = re.search(r'datetime="(\d{4})-', bloco) or re.search(r"<td>\s*\d{2}/\d{2}/(\d{4})\s*</td>", bloco)
        ano = int(data.group(1)) if data else None
        secao, niveis = "", {}
        for p in re.finditer(r"<p([^>]*)>(.*?)</p>", bloco, re.S):
            attrs, corpo = p.group(1), p.group(2)
            txt = _texto(corpo)
            nivel = int(re.search(r"Indent(\d)", attrs).group(1)) if re.search(r"Indent\d", attrs) else 0
            links = re.findall(r'href="([^"]+\.pdf)"[^>]*>(.*?)</a>', corpo, re.S)
            if links:
                cargo = next((niveis[n] for n in sorted(niveis, reverse=True) if n < nivel), "")
                cargo = re.sub(r"^(Curso|Cargo|Emprego|Especialidade)\s*:\s*", "", cargo)
                for url, rot in links:
                    rot = _texto(rot)
                    url = url if url.startswith("http") else "https://conhecimento.fgv.br" + url
                    if re.fullmatch(r"(?i)tipo\s*0?1", rot) and re.search(r"objetiva", secao, re.I):
                        cadernos.append((cargo, url, ano))
                    elif re.search(r"(?i)gabarito.*definitivo", rot) and not re.search(r"(?i)discursiv|preliminar|reaplica", rot):
                        gabaritos.append((rot, url, ano))
            elif nivel and txt:
                niveis = {n: v for n, v in niveis.items() if n < nivel}
                niveis[nivel] = txt
            elif txt and not nivel:
                if re.search(r"(?i)\bprovas?\b", txt):
                    secao, niveis = txt, {}
                else:  # título intermediário sem recuo ("Nível Superior"): não muda a seção
                    niveis = {0: txt}
    # gabaritos também aparecem como link direto em células de tabela (páginas antigas)
    vistos = {u for _, u, _ in gabaritos}
    for m in re.finditer(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', conteudo, re.S):
        rot, url = _texto(m.group(2)), m.group(1)
        url = url if url.startswith("http") else "https://conhecimento.fgv.br" + url
        if (url not in vistos and re.search(r"(?i)gabarito.*(definitivo|final)", rot)
                and not re.search(r"(?i)discursiv|preliminar|reaplica", rot)):
            gabaritos.append((rot, url, None))
            vistos.add(url)
    return orgao, cadernos, gabaritos


def _tipo_e_rotulo(cab):
    """'Cargo X - TIPO 1' / 'Cargo X - 1 - Turno Tarde' / 'Cargo X' -> (tipo, 'Cargo X')."""
    c = re.sub(r"(?i)[\s–-]*turno\s+(manh[ãa]|tarde|noite)\b", "", cab).strip()
    m = re.search(r"(?i)[\s–-]*\btipo\s*0?(\d)\b.*$", c) or re.search(r"\s[–-]\s*(\d)\s*(?:[–-].*)?$", c)
    if m:
        return int(m.group(1)), c[: m.start()].strip(" –-")
    return 1, c.strip(" –-")


def parse_gabarito_secoes(texto):
    """{rótulo: {num: letra|None}} só das seções do tipo 1 (ou sem tipo)."""
    secoes = {}
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    atual, cab_ant = None, ""
    for i, l in enumerate(linhas):
        nums = l.split()
        eh_nums = bool(nums) and all(n.isdigit() for n in nums)
        if eh_nums and i + 1 < len(linhas):
            resp = linhas[i + 1].split()
            if len(resp) == len(nums) and all(re.fullmatch(r"[A-E*X]|NULA|ANULADA", r, re.I) for r in resp):
                if nums[0] in ("1", "01") or atual is None:  # nova seção: cabeçalho é a linha anterior
                    tipo, rot = _tipo_e_rotulo(cab_ant)
                    atual = rot if tipo == 1 else None
                    if atual is not None:
                        secoes.setdefault(atual, {})
                if atual is not None:
                    for n, r in zip(nums, resp):
                        secoes[atual][int(n)] = r.upper() if re.fullmatch(r"[A-E]", r, re.I) else None
                continue
        if not eh_nums and not re.fullmatch(r"([A-E*X]\s*)+", l) and not l.startswith(("*", "(*")):
            cab_ant = l
    return {k: v for k, v in secoes.items() if v}


_PAPEIS = {"analista", "tecnico", "auxiliar", "assistente", "agente", "auditor", "fiscal", "professor", "medico",
           "enfermeiro", "juiz", "promotor", "defensor", "procurador", "delegado", "escrivao", "investigador", "inspetor",
           "perito", "oficial", "especialista", "guarda", "soldado", "advogado", "consultor", "policial", "escriturario"}


def casar_secao(cargo, secoes):
    """Escolhe a seção do gabarito cujo rótulo mais se parece com o nome do cargo.

    Exige o mesmo cargo-base (analista x técnico...) e Jaccard >= 0.5; empate entre seções = descarta.
    """
    if len(secoes) == 1 and not cargo:
        return next(iter(secoes.values()))
    tc = tokens(cargo)
    papel_c = tc & _PAPEIS
    melhor, pontos, empate = None, 0.0, False
    for rot, gab in secoes.items():
        tr = tokens(rot)
        if not tr or not tc or (papel_c and tr & _PAPEIS and not papel_c & tr):
            continue
        p = len(tc & tr) / len(tc | tr)
        if p > pontos:
            melhor, pontos, empate = gab, p, False
        elif p == pontos and p > 0:
            empate = True
    return melhor if pontos >= 0.5 and not empate else None
