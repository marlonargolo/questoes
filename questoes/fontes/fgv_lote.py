"""Processa em lote os concursos da FGV: gabarito definitivo + caderno Tipo 1 de cada cargo.

Uso: python -m questoes.fontes.fgv_lote [--slugs a,b] [--workers 3]
Saída: dados/jsonl/fgv/<slug>.jsonl e dados/jsonl/fgv/_log.jsonl
"""
import argparse
import json
import tempfile
import threading
import time
from concurrent.futures import ProcessPoolExecutor as ThreadPoolExecutor
from pathlib import Path

import requests

from .fgv import AGENTE, casar_secao, extrair_pagina, parse_gabarito_secoes
from .pdf import Prova, _ler_texto, extrair_texto_pdf, questoes_do_texto

CACHE = Path("dados/cache/fgv")
SAIDA = Path("dados/jsonl/fgv")
_lock = threading.Lock()
_local = threading.local()


def baixar(url, destino):
    s = getattr(_local, "s", None)
    if s is None:
        s = _local.s = requests.Session()
        s.headers["User-Agent"] = AGENTE
    for t in range(4):
        try:
            r = s.get(url, timeout=120)
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                destino.write_bytes(r.content)
                time.sleep(0.5)
                return True
            if r.status_code in (403, 404):
                return False
        except requests.RequestException:
            pass
        time.sleep(3 * (t + 1))
    return False


def processar(slug):
    saida = SAIDA / f"{slug}.jsonl"
    if saida.exists():
        return 0
    orgao, cadernos, gabaritos = extrair_pagina((CACHE / f"c_{slug}.html").read_text(encoding="utf-8"))
    logs, linhas = [], []
    if cadernos and gabaritos:
        with tempfile.TemporaryDirectory(dir="dados") as tmp:
            secoes = {}
            for i, (_, url, _) in enumerate(gabaritos):
                arq = Path(tmp) / f"g{i}.pdf"
                if baixar(url, arq):
                    try:
                        secoes.update(parse_gabarito_secoes(_ler_texto(arq)))
                    except Exception:
                        pass
            for cargo, url, ano in cadernos:
                gab = casar_secao(cargo, secoes)
                st = {"slug": slug, "cargo": cargo, "url": url}
                if not gab:
                    logs.append({**st, "erro": "sem gabarito"})
                    continue
                arq = Path(tmp) / "c.pdf"
                if not baixar(url, arq):
                    logs.append({**st, "erro": "download"})
                    continue
                try:
                    cfg = Prova(prova=str(arq), banca="FGV", orgao=orgao, ano=ano or "", colunas=2)
                    qs = list(questoes_do_texto(extrair_texto_pdf(arq, 2), gab, cfg))
                except Exception as e:
                    logs.append({**st, "erro": repr(e)[:200]})
                    continue
                validos = sum(1 for v in gab.values() if v)
                logs.append({**st, "validos_gab": validos, "extraidas": len(qs),
                             "taxa": round(len(qs) / validos, 3) if validos else 0})
                for q in qs:
                    d = q.como_dict()
                    d["_fonte"] = f"fgv:{slug}:{url.rsplit('/', 1)[-1]}"
                    d["_bloco"] = cargo
                    linhas.append(d)
    tmpf = saida.with_suffix(".tmp")
    with open(tmpf, "w", encoding="utf-8") as f:
        for d in linhas:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    tmpf.rename(saida)
    with _lock, open(SAIDA / "_log.jsonl", "a", encoding="utf-8") as f:
        for st in logs:
            f.write(json.dumps(st, ensure_ascii=False) + "\n")
    if linhas:
        print(f"{slug}: {len(cadernos)} cadernos, {len(linhas)} questões", flush=True)
    return len(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)
    slugs = a.slugs.split(",") if a.slugs else [p.stem[2:] for p in sorted(CACHE.glob("c_*.html"))]
    with ThreadPoolExecutor(a.workers) as ex:
        total = sum(ex.map(processar, slugs))
    print(f"TOTAL {total}")


if __name__ == "__main__":
    main()
