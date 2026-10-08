"""Limpeza de texto: HTML, encoding, prefixos de alternativa, espaços."""
import html
import re
import unicodedata

import ftfy
from bs4 import BeautifulSoup

from .schema import COLUNAS, LETRAS, Questao

_TAG = re.compile(r"<[^>]+>")
_BR = re.compile(r"<\s*(br|/p|/div|/li|/tr|/h\d)\s*/?\s*>", re.I)
# "A) ", "(A) ", "a. ", "A - ", "A – " no início da alternativa
_PREFIXO_ALT = re.compile(r"^\s*\(?\s*([A-Ea-e])\s*(?:\)|[\.\-–—:](?=\s))\s*(?=\S)")
_CTRL = re.compile(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f​-‏  ﻿�]")
_ESPACOS = re.compile(r"[ \t  -   　]+")
_HIFENIZACAO = re.compile(r"(\w)-\n(\w)")


def remover_html(texto: str) -> str:
    if "<" not in texto and "&" not in texto:
        return texto
    if "<" in texto:
        texto = _BR.sub("\n", texto)
        texto = BeautifulSoup(texto, "html.parser").get_text()
        texto = _TAG.sub("", texto)
    return html.unescape(texto)


def limpar_texto(texto, multilinha=True) -> str:
    """Remove HTML, corrige mojibake (ex.: 'AdministraÃ§Ã£o'), normaliza espaços."""
    if texto is None:
        return ""
    texto = str(texto)
    texto = remover_html(texto)
    texto = ftfy.fix_text(texto, normalization="NFC")
    texto = unicodedata.normalize("NFC", texto)
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = _HIFENIZACAO.sub(r"\1\2", texto)
    texto = _CTRL.sub("", texto)
    linhas = [_ESPACOS.sub(" ", l).strip() for l in texto.split("\n")]
    if multilinha:
        texto = re.sub(r"\n{3,}", "\n\n", "\n".join(linhas))
    else:
        texto = " ".join(l for l in linhas if l)
    return texto.strip()


def limpar_alternativa(texto) -> str:
    texto = limpar_texto(texto, multilinha=False)
    return _PREFIXO_ALT.sub("", texto, count=1).strip()


def normalizar_gabarito(g) -> str:
    g = limpar_texto(g, multilinha=False).upper()
    g = {"CERTO": "A", "ERRADO": "B", "C/E": ""}.get(g, g)
    g = re.sub(r"[^A-E]", "", g)
    return g if len(g) == 1 else ""


def normalizar_ano(a) -> str:
    m = re.search(r"(19|20)\d{2}", str(a or ""))
    return m.group(0) if m else ""


def limpar_questao(q: Questao) -> Questao:
    d = q.como_dict()
    for col in ("Banca", "Orgao", "Disciplina", "Assunto"):
        d[col] = limpar_texto(d[col], multilinha=False)
    d["Enunciado"] = limpar_texto(d["Enunciado"])
    d["Comentario_Professor"] = limpar_texto(d["Comentario_Professor"])
    for letra in LETRAS:
        d[f"Alternativa_{letra}"] = limpar_alternativa(d[f"Alternativa_{letra}"])
    d["Ano"] = normalizar_ano(d["Ano"])
    d["Gabarito"] = normalizar_gabarito(d["Gabarito"])
    # Certo/Errado: garante C, D e E em branco
    if d["Alternativa_A"].lower() == "certo" and d["Alternativa_B"].lower() == "errado":
        d["Alternativa_A"], d["Alternativa_B"] = "Certo", "Errado"
        d["Alternativa_C"] = d["Alternativa_D"] = d["Alternativa_E"] = ""
    return Questao(**{c: d[c] for c in COLUNAS})
