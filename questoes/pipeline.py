"""Consolida JSONL intermediários: limpa, classifica, valida, deduplica e exporta."""
import json
from pathlib import Path

from .assuntos import assunto_do_comando, classificar, propagar_assuntos
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


def ler_brutos(entradas):
    for entrada in entradas:
        with open(entrada, encoding="utf-8") as f:
            for linha in f:
                if linha.strip():
                    yield json.loads(linha)


def atribuir_disciplinas(brutos, log=print):
    """Normaliza disciplinas rotuladas e prevê as faltantes com o classificador treinado."""
    from collections import OrderedDict

    from .classificador import Classificador, canonica

    for d in brutos:
        # cabeçalhos só são confiáveis nos cadernos da FGV (e a OAB já vem rotulada); no Cebraspe são falsos positivos
        if str(d.get("_fonte", "")).startswith("cebraspe:"):
            d["Disciplina"] = ""
        d["Disciplina"] = canonica(d.get("Disciplina", ""))
    clf = Classificador()
    rotulos = {d["Disciplina"] for d in brutos if d["Disciplina"]}
    if len(rotulos) < 2 or sum(1 for d in brutos if d["Disciplina"]) < 2 * clf.min_exemplos:
        log("poucos exemplos rotulados: classificador de disciplina não treinado")
        return brutos
    n, classes = clf.treinar(brutos)
    log(f"classificador treinado com {n} questões rotuladas, {len(clf.modelo.classes_)} disciplinas")
    cadernos = OrderedDict()
    for i, d in enumerate(brutos):
        if not d["Disciplina"]:
            cadernos.setdefault(d.get("_fonte", "?"), []).append(i)
    previstas = 0
    for idxs in cadernos.values():
        for i, (disc, prob) in zip(idxs, clf.prever_caderno([brutos[i] for i in idxs])):
            brutos[i]["Disciplina"] = disc
            brutos[i]["_disc_prob"] = round(prob, 3)
            previstas += 1
    log(f"{previstas} disciplinas previstas pelo classificador")
    log(f"{ajustar_por_cargo(brutos)} disciplinas ajustadas pela área do cargo (conhecimentos específicos)")
    log(f"{ajustar_por_palavras(brutos)} disciplinas ajustadas por palavras-chave (previsões genéricas ou fracas)")
    return brutos


def ajustar_por_palavras(brutos, minimo=6):
    """Previsão genérica/fraca (ou Português sem indício de Português) -> área indicada com força pelas palavras-chave."""
    from .classificador import GENERICAS_PREVISTAS
    from .disciplinas import pontuar

    n = 0
    for d in brutos:
        if "_disc_prob" not in d:
            continue
        atual = d["Disciplina"]
        fraca = atual in GENERICAS_PREVISTAS or d["_disc_prob"] < 0.4
        texto = d.get("Enunciado", "")[-1200:] + " " + " ".join(d.get(f"Alternativa_{l}", "") for l in "ABCDE")
        pts = pontuar(texto)
        if not pts:
            continue
        melhor, v = pts.most_common(1)[0]
        portugues_sem_indicio = atual == "Língua Portuguesa" and pts.get("Língua Portuguesa", 0) == 0
        if melhor != atual and v >= minimo and (fraca or portugues_sem_indicio) and v >= 2 * pts.get(atual, 0):
            d["Disciplina"] = melhor
            n += 1
    return n


_CARGOS_CEBRASPE = {}


def _nome_cargo_cebraspe(ident, bloco):
    """Junta ao bloco ('CONHECIMENTOS ESPECIFICOS CARGO 6') o nome do cargo da API do Cebraspe."""
    import re as _re

    if ident not in _CARGOS_CEBRASPE:
        try:
            ev = json.loads(Path(f"dados/cache/cebraspe/{ident}.json").read_text(encoding="utf-8"))
            _CARGOS_CEBRASPE[ident] = {str(int(c["idArea"])): c["area"] for c in ev.get("eventoCargos") or []
                                       if str(c.get("idArea", "")).isdigit()}
        except Exception:
            _CARGOS_CEBRASPE[ident] = {}
    m = _re.search(r"\b(?:CARGO|EMPREGO|PERFIL|AREA)S? (\d+)\b", bloco or "")
    return (bloco or "") + " " + (_CARGOS_CEBRASPE[ident].get(str(int(m.group(1))), "") if m else "")


BASICAS = {"Língua Portuguesa", "Raciocínio Lógico", "Matemática", "Língua Inglesa", "Língua Espanhola", "Redação Oficial"}


def ajustar_por_cargo(brutos):
    """Em blocos de conhecimentos específicos de cargo especializado, troca previsões genéricas pela área do cargo."""
    from .classificador import GENERICAS_PREVISTAS, disciplina_do_cargo

    n = 0
    for d in brutos:
        bloco = d.get("_bloco", "")
        fonte = str(d.get("_fonte", ""))
        if not bloco or "_disc_prob" not in d:
            continue
        if fonte.startswith("cebraspe:"):
            if "ESPECIFIC" not in bloco.upper():
                continue
            bloco = _nome_cargo_cebraspe(fonte.split(":")[1], bloco)
        area = disciplina_do_cargo(bloco)
        if not area or d["Disciplina"] == area or d["Disciplina"] in BASICAS:
            continue
        # na FGV o caderno mistura gerais e específicos: só troca categorias genéricas
        pouca_confianca = d["_disc_prob"] < 0.5 and fonte.startswith("cebraspe:")
        if d["Disciplina"] in GENERICAS_PREVISTAS or pouca_confianca:
            d["Disciplina"] = area
            n += 1
    return n


def consolidar(entradas, saidas, rejeitadas=None, relatorio_path=None, classificar_assunto=True, bom=False,
               prever_disciplina=True):
    validas, ruins = [], []
    brutos = list(ler_brutos(entradas))
    if prever_disciplina:
        brutos = atribuir_disciplinas(brutos)
    for d in brutos:
        q = limpar_questao(Questao(**{c: str(d.get(c, "") or "") for c in COLUNAS}))
        if classificar_assunto and not q.Assunto:
            q.Assunto = assunto_do_comando(q.Enunciado) or classificar(
                q.Disciplina, q.Enunciado, [getattr(q, f"Alternativa_{l}") for l in LETRAS])
        err = erros_questao(q)
        (ruins.append((q, err)) if err else validas.append(q))
    antes = len(validas)
    validas = deduplicar(validas)
    if classificar_assunto and len(validas) > 50:
        print(f"{propagar_assuntos(validas)} assuntos propagados por similaridade")
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
