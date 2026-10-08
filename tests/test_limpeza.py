from questoes.limpeza import limpar_alternativa, limpar_questao, limpar_texto, normalizar_gabarito
from questoes.schema import Questao
from questoes.validacao import erros_questao


def test_remove_html_e_entidades():
    assert limpar_texto("<p>Assinale&nbsp;a <b>correta</b>.<br>Fim</p>") == "Assinale a correta.\nFim"


def test_corrige_mojibake():
    assert limpar_texto("AdministraÃ§Ã£o PÃºblica") == "Administração Pública"


def test_remove_letra_da_alternativa():
    for bruto in ["A) O juiz decidiu", "(A) O juiz decidiu", "a. O juiz decidiu", "A - O juiz decidiu", "<p>A) O juiz decidiu</p>"]:
        assert limpar_alternativa(bruto) == "O juiz decidiu"


def test_nao_remove_inicio_legitimo():
    assert limpar_alternativa("A lei é clara") == "A lei é clara"
    assert limpar_alternativa("E.coli é uma bactéria") == "E.coli é uma bactéria"


def test_gabarito():
    assert normalizar_gabarito(" b ") == "B"
    assert normalizar_gabarito("Certo") == "A"
    assert normalizar_gabarito("Errado") == "B"
    assert normalizar_gabarito("AB") == ""


def test_certo_errado_padrao_cebraspe():
    q = limpar_questao(Questao.certo_errado("E", Banca="Cebraspe", Orgao="Órgão X", Ano="2024",
                                            Disciplina="Português", Enunciado="Item de teste para validação."))
    assert (q.Alternativa_A, q.Alternativa_B, q.Alternativa_C, q.Gabarito) == ("Certo", "Errado", "", "B")
    assert erros_questao(q) == []


def test_validacao_aponta_problemas():
    q = Questao(Banca="FGV", Orgao="X", Ano="23", Disciplina="D", Enunciado="Enunciado <b>sujo</b> aqui",
                Alternativa_A="A) um", Alternativa_B="dois", Alternativa_D="quatro", Gabarito="C")
    e = erros_questao(q)
    assert "Ano não numérico" in e
    assert "HTML em Enunciado" in e
    assert "letra misturada na Alternativa_A" in e
    assert "alternativas fora de sequência (lacuna)" in e
    assert "gabarito aponta para alternativa vazia" in e
