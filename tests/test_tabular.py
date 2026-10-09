import json

from questoes.fontes.tabular import importar
from questoes.limpeza import limpar_questao
from questoes.validacao import erros_questao


def test_mapa_com_lista_de_alternativas(tmp_path):
    arq = tmp_path / "d.jsonl"
    regs = [
        {"exam_year": "2019", "question": "Pergunta de exemplo número um?", "answerKey": "C", "nullified": False,
         "choices": {"label": list("ABCD"), "text": ["um", "dois", "três", "quatro"]}},
        {"exam_year": "2019", "question": "Anulada", "answerKey": "A", "nullified": True,
         "choices": {"label": list("ABCD"), "text": ["1", "2", "3", "4"]}},
    ]
    arq.write_text("\n".join(json.dumps(r) for r in regs), encoding="utf-8")
    mapa = {"fixos": {"Banca": "FGV", "Orgao": "OAB", "Disciplina": "Direito"},
            "campos": {"Ano": "exam_year", "Enunciado": "question", "Gabarito": "answerKey"},
            "alternativas": "choices.text", "ignorar_se_verdadeiro": "nullified"}
    qs = [limpar_questao(q) for q in importar(arq, mapa)]
    assert len(qs) == 1
    assert (qs[0].Alternativa_C, qs[0].Alternativa_E, qs[0].Gabarito) == ("três", "", "C")
    assert erros_questao(qs[0]) == []
