"""Regras de qualidade exigidas pelo sistema de destino."""
import re
from collections import Counter

from .schema import LETRAS, Questao

_HTML = re.compile(r"</?[a-zA-Z][^>]*>|&(nbsp|amp|lt|gt|quot|#\d+);")
_MOJIBAKE = re.compile(r"Ã[\u0080-¿§£¡©ª³µº¢]|Â[ -¿]|â€|�")
_PREFIXO = re.compile(r"^\s*\(?[A-Ea-e]\s*[\)\.\-–—:]\s")

LIMITE_CELULA_EXCEL = 32767


def erros_questao(q: Questao) -> list[str]:
    e = []
    for col in ("Banca", "Orgao", "Ano", "Disciplina", "Enunciado", "Gabarito"):
        if not getattr(q, col):
            e.append(f"{col} vazio")
    if q.Ano and not re.fullmatch(r"\d{4}", q.Ano):
        e.append("Ano não numérico")
    if q.Gabarito and not re.fullmatch(r"[A-E]", q.Gabarito):
        e.append("Gabarito inválido")
    alts = [getattr(q, f"Alternativa_{l}") for l in LETRAS]
    preenchidas = [l for l, a in zip(LETRAS, alts) if a]
    if len(preenchidas) < 2:
        e.append("menos de 2 alternativas")
    if preenchidas != list(LETRAS[: len(preenchidas)]):
        e.append("alternativas fora de sequência (lacuna)")
    if q.Gabarito and q.Gabarito not in preenchidas:
        e.append("gabarito aponta para alternativa vazia")
    if len(set(a.lower() for a in alts if a)) != len(preenchidas):
        e.append("alternativas duplicadas")
    ce = alts[0] == "Certo" and alts[1] == "Errado"
    if ce and any(alts[2:]):
        e.append("Certo/Errado com C/D/E preenchidas")
    for col, valor in q.como_dict().items():
        if _HTML.search(valor):
            e.append(f"HTML em {col}")
        if _MOJIBAKE.search(valor):
            e.append(f"encoding quebrado em {col}")
        if len(valor) > LIMITE_CELULA_EXCEL:
            e.append(f"{col} excede limite de célula do Excel")
    for l, a in zip(LETRAS, alts):
        if a and _PREFIXO.match(a):
            e.append(f"letra misturada na Alternativa_{l}")
    if len(q.Enunciado) < 15:
        e.append("enunciado curto demais")
    return e


def relatorio(questoes) -> dict:
    total, validas, motivos = 0, 0, Counter()
    por = {"Banca": Counter(), "Disciplina": Counter(), "Ano": Counter()}
    for q in questoes:
        total += 1
        err = erros_questao(q)
        if err:
            motivos.update(err)
        else:
            validas += 1
            for k in por:
                por[k][getattr(q, k)] += 1
    return {
        "total": total,
        "validas": validas,
        "invalidas": total - validas,
        "motivos": dict(motivos.most_common()),
        **{f"por_{k.lower()}": dict(v.most_common()) for k, v in por.items()},
    }
