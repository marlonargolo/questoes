"""Processa em lote os pares prova/gabarito do Cebraspe: baixa, extrai, grava JSONL e apaga os PDFs.

Uso: python -m questoes.fontes.cebraspe_lote [--limite N] [--ids ID1,ID2] [--workers 4]
Saída: dados/jsonl/cebraspe/<ID>.jsonl (um por concurso) e dados/jsonl/cebraspe/_log.jsonl (estatísticas).
"""
import argparse
import json
import re
import tempfile
import threading
import time
from concurrent.futures import ProcessPoolExecutor as ThreadPoolExecutor
from pathlib import Path

import requests

from .cebraspe import AGENTE, CDN, pares_prova_gabarito
from .pdf import Prova, _ler_texto, extrair_texto_pdf, parse_gabarito, questoes_do_texto

CACHE = Path("dados/cache/cebraspe")
SAIDA = Path("dados/jsonl/cebraspe")
_lock = threading.Lock()
_sessao = threading.local()


def _baixar(url, destino):
    s = getattr(_sessao, "s", None)
    if s is None:
        s = _sessao.s = requests.Session()
        s.headers["User-Agent"] = AGENTE
    for t in range(4):
        try:
            r = s.get(url, timeout=120)
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                destino.write_bytes(r.content)
                return True
            if r.status_code in (403, 404):
                return False
        except requests.RequestException:
            pass
        time.sleep(3 * (t + 1))
    return False


def ano_do_evento(ev):
    if ev.get("eventoAno"):
        return int(ev["eventoAno"])
    m = re.search(r"_(\d{2})(_|$)", ev["eventoURL"])
    return 2000 + int(m.group(1)) if m else None


def orgao_do_evento(ev):
    nome = (ev.get("eventoNomeCompleto") or "").strip()
    abrev = re.sub(r"\s+\d{4}\b.*$", "", (ev.get("eventoNomeAbreviado") or "").strip())
    if nome and len(nome) <= 80:
        return f"{nome} ({abrev})" if abrev and abrev.lower() not in nome.lower() and len(abrev) <= 15 else nome
    return abrev or ev["eventoURL"]


def processar_par(ev, prova, gab, chave):
    ident = ev["eventoURL"]
    with tempfile.TemporaryDirectory(dir="dados") as tmp:
        pp, pg = Path(tmp) / "p.pdf", Path(tmp) / "g.pdf"
        if not (_baixar(CDN.format(id=ident, nome=prova["nomeArquivo"]), pp)
                and _baixar(CDN.format(id=ident, nome=gab["nomeArquivo"]), pg)):
            return [], {"id": ident, "chave": chave, "erro": "download"}
        try:
            gabarito = parse_gabarito(_ler_texto(pg))
            letras = {v for v in gabarito.values() if v}
            tipo = "multipla_escolha" if letras & set("ABD") else "certo_errado"
            cfg = Prova(prova=str(pp), banca="Cebraspe", orgao=orgao_do_evento(ev), ano=ano_do_evento(ev) or "",
                        tipo=tipo, colunas=2)
            texto = extrair_texto_pdf(pp, 2)
            qs = list(questoes_do_texto(texto, gabarito, cfg))
        except Exception as e:  # PDF corrompido, escaneado etc.
            return [], {"id": ident, "chave": chave, "erro": repr(e)[:200]}
    validos = sum(1 for v in gabarito.values() if v)
    stats = {"id": ident, "chave": chave, "tipo": tipo, "gabarito": len(gabarito), "validos_gab": validos,
             "extraidas": len(qs), "taxa": round(len(qs) / validos, 3) if validos else 0}
    linhas = []
    for q in qs:
        d = q.como_dict()
        d["_fonte"] = f"cebraspe:{ident}:{prova['nomeArquivo']}"
        d["_bloco"] = chave
        linhas.append(d)
    return linhas, stats


def processar_evento(ident):
    ev = json.loads((CACHE / f"{ident}.json").read_text(encoding="utf-8"))
    saida = SAIDA / f"{ident}.jsonl"
    if saida.exists():
        return 0
    pares, _, _ = pares_prova_gabarito(ev)
    if not pares:
        return 0
    todas, logs = [], []
    for prova, gab, chave in pares:
        linhas, st = processar_par(ev, prova, gab, chave)
        todas += linhas
        logs.append(st)
    tmp = saida.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for d in todas:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    tmp.rename(saida)
    with _lock, open(SAIDA / "_log.jsonl", "a", encoding="utf-8") as f:
        for st in logs:
            f.write(json.dumps(st, ensure_ascii=False) + "\n")
    print(f"{ident}: {len(pares)} provas, {len(todas)} questões", flush=True)
    return len(todas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids")
    ap.add_argument("--limite", type=int)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)
    ids = a.ids.split(",") if a.ids else sorted(p.stem for p in CACHE.glob("*.json") if not p.stem.startswith("_"))
    if a.limite:
        ids = ids[: a.limite]
    with ThreadPoolExecutor(a.workers) as ex:
        total = sum(ex.map(processar_evento, ids))
    print(f"TOTAL {total}")


if __name__ == "__main__":
    main()
