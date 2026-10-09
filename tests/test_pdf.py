from questoes.fontes.pdf import Prova, parse_gabarito, questoes_do_texto
from questoes.limpeza import limpar_questao
from questoes.validacao import erros_questao

TEXTO_ME = """
CONCURSO PÚBLICO - CADERNO DE PROVA
LÍNGUA PORTUGUESA
1. Assinale a alternativa em que o uso do acento grave indicativo
de crase está correto.
(A) Fui à pé.
(B) Refiro-me à professora.
(C) Ela começou à cantar.
(D) Entreguei à ele.
(E) Vou à Brasília de 1990.
– 2 –
QUESTÃO 2
Considere a lista: 1. item; 2. item.
Qual alternativa está correta?
A) primeira opção
que continua aqui
B) segunda opção
C) terceira opção
D) quarta opção
E) quinta opção
3. Questão anulada pela banca, sem alternativas válidas.
(A) a (B) b
"""


def _cfg(**kw):
    base = dict(prova="x.pdf", banca="FGV", orgao="Órgão Exemplo", ano=2024,
                disciplinas=[{"de": 1, "ate": 3, "disciplina": "Língua Portuguesa"}])
    base.update(kw)
    return Prova(**base)


def test_multipla_escolha():
    gab = parse_gabarito("1 B 2 A 3 X")
    qs = [limpar_questao(q) for q in questoes_do_texto(TEXTO_ME, gab, _cfg())]
    assert len(qs) == 2  # a 3 foi anulada
    q1, q2 = qs
    assert q1.Enunciado.startswith("Assinale a alternativa")
    assert q1.Alternativa_B == "Refiro-me à professora."
    assert q1.Gabarito == "B"
    assert q2.Enunciado == "Considere a lista: 1. item; 2. item.\nQual alternativa está correta?"
    assert q2.Alternativa_A == "primeira opção que continua aqui"
    for q in qs:
        assert erros_questao(q) == [], erros_questao(q)


def test_gabarito_tabela_cebraspe():
    texto = "Item 1 2 3 4\nGabarito C E X C\n"
    assert parse_gabarito(texto) == {1: "C", 2: "E", 3: None, 4: "C"}


def test_certo_errado_com_texto_de_apoio():
    texto = """Texto I
O servidor público deve observar os princípios da administração.
Julgue os itens a seguir, a respeito do texto I.
1 O texto defende a observância de princípios.
2 O texto trata de direito penal.
Acerca de atos administrativos, julgue os itens seguintes.
3 A revogação incide sobre atos válidos.
"""
    gab = parse_gabarito("1 C 2 E 3 C")
    qs = [limpar_questao(q) for q in questoes_do_texto(texto, gab, _cfg(banca="Cebraspe", tipo="certo_errado"))]
    assert [q.Gabarito for q in qs] == ["A", "B", "A"]
    assert qs[0].Enunciado.startswith("Texto I")
    assert qs[1].Enunciado.endswith("O texto trata de direito penal.")
    assert qs[2].Enunciado == "Acerca de atos administrativos, julgue os itens seguintes.\nA revogação incide sobre atos válidos."
    assert all(q.Alternativa_C == "" for q in qs)
