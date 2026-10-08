"""Coleta de provas objetivas + gabaritos definitivos na API pública do Cebraspe.

API: https://apis.cebraspe.org.br/cebraspe/eventos/tipo/concursos/ (lista) e
     https://apis.cebraspe.org.br/cebraspe/eventos/<ID> (arquivos de cada concurso)
Arquivos: https://cdn.cebraspe.org.br/concursos/<ID>/arquivos/<nome>
"""
import json
import re
import time
import unicodedata
from pathlib import Path

import requests

API = "https://apis.cebraspe.org.br/cebraspe/eventos"
CDN = "https://cdn.cebraspe.org.br/concursos/{id}/arquivos/{nome}"
AGENTE = "Mozilla/5.0 (compatible; questoes-bot/0.1; coleta de provas publicas)"


class Cliente:
    def __init__(self, intervalo=1.5, cache="dados/cache/cebraspe"):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = AGENTE
        self.intervalo, self.ultimo = intervalo, 0.0
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)

    def get(self, url):
        espera = self.intervalo - (time.monotonic() - self.ultimo)
        if espera > 0:
            time.sleep(espera)
        for t in range(4):
            try:
                r = self.s.get(url, timeout=90)
                self.ultimo = time.monotonic()
                if r.status_code in (429, 500, 502, 503, 504):
                    time.sleep(5 * (t + 1))
                    continue
                return r
            except requests.RequestException:
                time.sleep(5 * (t + 1))
        return None

    def json(self, url, chave):
        arq = self.cache / f"{chave}.json"
        if arq.exists():
            return json.loads(arq.read_text(encoding="utf-8"))
        r = self.get(url)
        if r is None or r.status_code != 200:
            return None
        arq.write_text(r.text, encoding="utf-8")
        return r.json()


def listar_eventos(cli):
    dados = cli.json(f"{API}/tipo/concursos/", "_lista")
    return [e for fase in dados for e in fase["eventos"]
            if fase["faseEvento"].lower().startswith(("encerr", "em andamento"))]


def _norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", t).strip()


_TIPO_PROVA = re.compile(r"^(CADERNO DE PROVAS?|PROVAS? OBJETIVAS?( E DISCURSIVAS?)?( \(P\d\))?|PROVA DE CONHECIMENTOS"
                         r"( \(PROVA OBJETIVA\))?|PROVA)\b|^CONHECIMENTOS\b")
_TIPO_GAB = re.compile(r"^GABARITOS? (OFICIA(L|IS) )?DEFINITIVOS?\b")
_EXCLUIR = re.compile(r"\b(DISCURSIVA|ORAL|PRATICA|CURSO DE FORMACAO|PROCAP|PROGRAMA DE CAPACITACAO|LIBRAS|"
                      r"PRELIMINAR|PROVISORI|SUB ?JUDICE|REAPLICA\w*|PADRAO|REDACAO|TITULOS|AVALIACAO|DIGITACAO|"
                      r"ESTUDO DE CASO|PECA|PARECER|SENTENCA|ESCRITA)\b")


def _chave(desc):
    """Descrição sem o tipo do arquivo: 'Caderno de provas - Conhec. Específicos - cargo 9: X' -> 'CONHECIMENTOS ESPECIFICOS CARGO 9 X'."""
    d = _norm(desc)
    d = re.sub(r"\bE GABARITO\b|\bOBJETIVA E DISCURSIVA\b", "OBJETIVA", d)
    d = re.sub(r"^(GABARITOS? (OFICIA(L|IS) )?DEFINITIVOS?|CADERNO DE PROVAS?|PROVAS? OBJETIVAS?|PROVA DE CONHECIMENTOS"
               r"( \(PROVA OBJETIVA\))?|PROVA)\b", "", d)
    d = re.sub(r"\b(DA |DE )?PROVAS? OBJETIVAS?\b|\(P\d\)|\(ATUALIZAD\w*\)|\(RETIFICAD\w*\)", " ", d)
    d = re.sub(r"[^A-Z0-9 ]+", " ", d)
    d = re.sub(r"\b(DO|DA|DE|DOS|DAS|E|O|A|OS|AS|PARA|NO|NA|EM)\b", " ", d)
    return re.sub(r"\s+", " ", d).strip()


def _codigo(nome):
    """'GAB_DEFINITIVO_398_IFF009.PDF' e '398_IFF009_PAG_4.PDF' -> '398_IFF009'."""
    n = _norm(Path(nome).stem).replace(" ", "_")
    n = re.sub(r"^(GAB(ARITO)?_?(OFICIAL_)?DEFINITIVO_?(MATRIZ_)?)", "", n)
    n = re.sub(r"(_MATRIZ|_PAG_\d+|_\d{2}|_\(.*\))+$", "", n)
    return n if re.match(r"^\d{3}_", n) else None


def pares_prova_gabarito(evento):
    """Casa cada PDF de prova objetiva com o gabarito definitivo correspondente."""
    arquivos = [a for a in (evento.get("arquivosGabarito") or []) if a["nomeArquivo"].lower().endswith(".pdf")]
    provas = [a for a in arquivos if _TIPO_PROVA.search(_norm(a["descricaoArquivo"]))
              and not _TIPO_GAB.search(_norm(a["descricaoArquivo"]))
              and not _EXCLUIR.search(_norm(a["descricaoArquivo"]).replace("OBJETIVA E DISCURSIVA", "OBJETIVA")
                                      .replace("E GABARITO DEFINITIVO", ""))]
    gabs = [a for a in arquivos if _TIPO_GAB.search(_norm(a["descricaoArquivo"]))
            and not _EXCLUIR.search(_norm(a["descricaoArquivo"]))]
    por_chave, por_codigo = {}, {}
    for g in gabs:
        por_chave.setdefault(_chave(g["descricaoArquivo"]), []).append(g)
        if _codigo(g["nomeArquivo"]):
            por_codigo.setdefault(_codigo(g["nomeArquivo"]), []).append(g)
    pares, usados = [], set()
    for p in provas:
        k = _chave(p["descricaoArquivo"])
        cand = por_chave.get(k, [])
        if len(cand) != 1 and _codigo(p["nomeArquivo"]):
            cand = por_codigo.get(_codigo(p["nomeArquivo"]), [])
        if not cand and len(provas) == 1 and len(gabs) == 1:
            cand = gabs
        if len(cand) == 1 and cand[0]["nomeArquivo"] not in usados:
            usados.add(cand[0]["nomeArquivo"])
            pares.append((p, cand[0], k))
    return pares, provas, gabs


def coletar_metadados(intervalo=1.5):
    cli = Cliente(intervalo)
    eventos = listar_eventos(cli)
    print(f"{len(eventos)} concursos")
    for i, e in enumerate(eventos, 1):
        cli.json(f"{API}/{e['eventoURL']}", e["eventoURL"])
        if i % 50 == 0:
            print(f"  {i}/{len(eventos)}", flush=True)
    return eventos


if __name__ == "__main__":
    coletar_metadados()
