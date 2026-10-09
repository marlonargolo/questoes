import yaml

from questoes.plano import gerar_manifesto, parse_faixas


def test_faixas():
    assert parse_faixas("1-13:Língua Portuguesa | 14-25:Direito Administrativo | 26:Ética") == [
        {"de": 1, "ate": 13, "disciplina": "Língua Portuguesa"},
        {"de": 14, "ate": 25, "disciplina": "Direito Administrativo"},
        {"de": 26, "ate": 26, "disciplina": "Ética"},
    ]


def test_manifesto_so_com_linhas_prontas(tmp_path):
    base = dict(ID="1", Banca="FGV", Orgao="X", Ano="2022", Cargo_Prova="C", Tipo="multipla_escolha",
                Alternativas="4", Questoes_Estimadas="80", Confianca="alta", Status="pronto",
                Arquivo_Prova="p.pdf", Arquivo_Gabarito="g.pdf", Faixas_Disciplinas="1-80:Direito", Observacoes="")
    linhas = [base, {**base, "ID": "2", "Arquivo_Gabarito": ""}, {**base, "ID": "3", "Status": "a_coletar"}]
    n, pend = gerar_manifesto(linhas, tmp_path / "m.yaml")
    assert n == 1 and len(pend) == 1 and "ID 2" in pend[0]
    m = yaml.safe_load((tmp_path / "m.yaml").read_text(encoding="utf-8"))
    assert m["provas"][0]["numero_alternativas"] == 4
    assert m["provas"][0]["disciplinas"][0]["disciplina"] == "Direito"
