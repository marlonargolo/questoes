"""Consolida JSONL intermediários: limpa, classifica, valida, deduplica e exporta."""
import json
from pathlib import Path

from .assuntos import classificar
from .dedup import deduplicar
from .exportacao import exportar
from .limpeza import limpar_questao
from .schema import COLUNAS, LETRAS, Questao
from .validacao import erros_questao, relatorio


def salvar_jsonl(questoes, caminho):
    n = 0
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        for q in questoes:
            f.write(json.dumps(q.como_dict(), ensure_ascii=False) + "\n")
            n += 1
    return n


def ler_jsonl(caminho):
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                d = json.loads(linha)
                yield Questao(**{c: str(d.get(c, "") or "") for c in COLUNAS})


def consolidar(entradas, saidas, rejeitadas=None, relatorio_path=None, classificar_assunto=True, bom=False):
    validas, ruins = [], []
    for entrada in entradas:
        for q in ler_jsonl(entrada):
            q = limpar_questao(q)
            if classificar_assunto and not q.Assunto:
                q.Assunto = classificar(q.Disciplina, q.Enunciado, [getattr(q, f"Alternativa_{l}") for l in LETRAS])
            err = erros_questao(q)
            (ruins.append((q, err)) if err else validas.append(q))
    antes = len(validas)
    validas = deduplicar(validas)
    for s in saidas:
        exportar(validas, s, bom=bom)
    if rejeitadas:
        import csv

        with open(rejeitadas, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(COLUNAS + ["Motivos"])
            for q, err in ruins:
                w.writerow([getattr(q, c) for c in COLUNAS] + [" | ".join(err)])
    rel = relatorio(validas)
    rel.update(lidas=antes + len(ruins), rejeitadas=len(ruins), duplicadas_removidas=antes - len(validas),
               motivos_rejeicao=_contar(ruins))
    if relatorio_path:
        Path(relatorio_path).write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    return rel


def _contar(ruins):
    from collections import Counter

    c = Counter()
    for _, err in ruins:
        c.update(err)
    return dict(c.most_common())
