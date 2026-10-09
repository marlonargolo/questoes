"""Coletor web genérico e educado (robots.txt, intervalo entre requisições, cache).

Duas funções:
  * baixar_pdfs: percorre páginas de listagem e baixa PDFs de provas/gabaritos
    publicados pelas bancas ou por repositórios públicos de provas.
  * raspar_questoes: extrai questões de páginas HTML com seletores CSS definidos
    em YAML (para sites cujos termos de uso permitam a coleta).

Antes de apontar para qualquer site, leia os termos de uso dele. Sites
comerciais de questões (QConcursos, TEC Concursos, etc.) proíbem a raspagem e os
comentários de professores são obra protegida — não use este módulo neles.
"""
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
import yaml
from bs4 import BeautifulSoup

from ..schema import Questao

AGENTE = "questoes-bot/0.1 (+coleta de provas publicas)"


class Coletor:
    def __init__(self, intervalo=2.0, cache_dir=".cache/web", agente=AGENTE):
        self.intervalo = intervalo
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.sessao = requests.Session()
        self.sessao.headers["User-Agent"] = agente
        self._robots: dict[str, RobotFileParser] = {}
        self._ultimo = 0.0

    def permitido(self, url):
        dominio = "{0.scheme}://{0.netloc}".format(urlparse(url))
        if dominio not in self._robots:
            rp = RobotFileParser(dominio + "/robots.txt")
            try:
                rp.read()
            except Exception:
                rp = None
            self._robots[dominio] = rp
        rp = self._robots[dominio]
        return rp is None or rp.can_fetch(self.sessao.headers["User-Agent"], url)

    def obter(self, url, binario=False):
        arq = self.cache / hashlib.sha1(url.encode()).hexdigest()
        if arq.exists():
            return arq.read_bytes() if binario else arq.read_text(encoding="utf-8")
        if not self.permitido(url):
            print(f"[web] bloqueado por robots.txt: {url}")
            return None
        espera = self.intervalo - (time.monotonic() - self._ultimo)
        if espera > 0:
            time.sleep(espera)
        for tentativa in range(4):
            try:
                r = self.sessao.get(url, timeout=60)
                self._ultimo = time.monotonic()
                if r.status_code == 429 or r.status_code >= 500:
                    time.sleep(2 ** (tentativa + 2))
                    continue
                r.raise_for_status()
                break
            except requests.RequestException as e:
                print(f"[web] erro {url}: {e}")
                time.sleep(2 ** (tentativa + 1))
        else:
            return None
        if binario:
            arq.write_bytes(r.content)
            return r.content
        r.encoding = r.apparent_encoding or r.encoding
        arq.write_text(r.text, encoding="utf-8")
        return r.text


def _paginas(coletor, inicio, seletor_proxima, max_paginas):
    url, vistas = inicio, 0
    while url and vistas < max_paginas:
        html = coletor.obter(url)
        if html is None:
            return
        sopa = BeautifulSoup(html, "html.parser")
        yield url, sopa
        vistas += 1
        prox = sopa.select_one(seletor_proxima) if seletor_proxima else None
        url = urljoin(url, prox["href"]) if prox and prox.get("href") else None


def baixar_pdfs(config):
    """config: {paginas: [url...], seletor_proxima?, padrao_link: regex, destino, intervalo?, max_paginas?}"""
    c = Coletor(config.get("intervalo", 2.0))
    destino = Path(config.get("destino", "provas"))
    destino.mkdir(parents=True, exist_ok=True)
    padrao = re.compile(config.get("padrao_link", r"\.pdf($|\?)"), re.I)
    baixados = 0
    for inicio in config["paginas"]:
        for url, sopa in _paginas(c, inicio, config.get("seletor_proxima"), config.get("max_paginas", 50)):
            for a in sopa.select("a[href]"):
                link = urljoin(url, a["href"])
                if not padrao.search(link):
                    continue
                nome = re.sub(r"[^\w.\-]+", "_", Path(urlparse(link).path).name) or "arquivo.pdf"
                alvo = destino / nome
                if alvo.exists():
                    continue
                dados = c.obter(link, binario=True)
                if dados and dados[:4] == b"%PDF":
                    alvo.write_bytes(dados)
                    baixados += 1
    print(f"[web] {baixados} PDFs baixados em {destino}")


def _texto(no, seletor):
    if not seletor:
        return ""
    alvo = no.select_one(seletor)
    return alvo.get_text("\n", strip=True) if alvo else ""


def raspar_questoes(config):
    """Extrai questões de HTML. Ver exemplos/web_config.yaml para o formato."""
    c = Coletor(config.get("intervalo", 2.0))
    s = config["seletores"]
    fixos = config.get("fixos", {})
    for inicio in config["paginas"]:
        for _url, sopa in _paginas(c, inicio, config.get("seletor_proxima"), config.get("max_paginas", 50)):
            for no in sopa.select(s["questao"]):
                d = {k: _texto(no, s.get(k)) or str(fixos.get(k, "")) for k in
                     ("Banca", "Orgao", "Ano", "Disciplina", "Assunto", "Enunciado", "Gabarito",
                      "Comentario_Professor")}
                alts = [a.get_text(" ", strip=True) for a in no.select(s["alternativas"])] if s.get("alternativas") else []
                if len(alts) == 2 and [a.lower() for a in alts] == ["certo", "errado"]:
                    gab = d.pop("Gabarito")
                    yield Questao.certo_errado(gab, **d)
                else:
                    yield Questao.de_alternativas(alts, **d)


def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)
