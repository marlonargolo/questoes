"""Remoção de duplicatas (mesma questão vinda de fontes diferentes)."""
import hashlib
import re
import unicodedata

from .schema import LETRAS, Questao


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", t)


def chave(q: Questao) -> str:
    base = _norm(q.Enunciado) + "|" + "|".join(_norm(getattr(q, f"Alternativa_{l}")) for l in LETRAS)
    return hashlib.sha1(base.encode()).hexdigest()


def deduplicar(questoes):
    """Mantém a primeira ocorrência; prefere quem tem comentário se a duplicata tiver."""
    vistas: dict[str, Questao] = {}
    for q in questoes:
        k = chave(q)
        atual = vistas.get(k)
        if atual is None:
            vistas[k] = q
        elif not atual.Comentario_Professor and q.Comentario_Professor:
            atual.Comentario_Professor = q.Comentario_Professor
    return list(vistas.values())
