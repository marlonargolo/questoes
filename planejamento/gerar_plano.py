"""Gera planejamento/plano_coleta.csv: provas-alvo por banca, órgão, ano e cargo.

Confiança:
  confirmada - checada por busca web (fonte em Observacoes)
  alta       - concurso conhecido; nº de questões e nome exato do cargo ainda a conferir no PDF
  verificar  - montado de memória: confirmar banca, ano, cargo e tipo antes de baixar

Rode:  python planejamento/gerar_plano.py
"""
import csv
from pathlib import Path

CE, ME, V = "certo_errado", "multipla_escolha", "verificar"
LINHAS = []


def add(banca, orgao, anos, cargos, tipo=ME, q=60, conf=V, obs="", nalt=5):
    for ano in anos if isinstance(anos, (list, range)) else [anos]:
        for cargo in cargos:
            LINHAS.append(dict(Banca=banca, Orgao=orgao, Ano=ano, Cargo_Prova=cargo, Tipo=tipo,
                               Alternativas=2 if tipo == CE else nalt, Questoes_Estimadas=q,
                               Confianca=conf, Observacoes=obs))


# Conjuntos padrão de cadernos (cada cargo/especialidade é uma prova separada)
TRIB = ["Analista Judiciário - Área Judiciária", "Analista Judiciário - Área Administrativa",
        "Analista Judiciário - Oficial de Justiça Avaliador Federal",
        "Analista Judiciário - Tecnologia da Informação", "Analista Judiciário - Contabilidade",
        "Técnico Judiciário - Área Administrativa", "Técnico Judiciário - Tecnologia da Informação"]
TRE = ["Analista Judiciário - Área Judiciária", "Analista Judiciário - Área Administrativa",
       "Analista Judiciário - Tecnologia da Informação", "Analista Judiciário - Contabilidade",
       "Técnico Judiciário - Área Administrativa", "Técnico Judiciário - Tecnologia da Informação"]
TRIB_SUP = TRE + ["Técnico Judiciário - Segurança e Transporte"]
POL = ["Agente de Polícia", "Escrivão de Polícia", "Delegado de Polícia"]
CONF = "conferir cargos/especialidades e nº de questões no edital"

# ============================== CEBRASPE ==============================
C = "Cebraspe"
add(C, "Polícia Federal", 2018, ["Agente de Polícia Federal", "Escrivão de Polícia Federal",
    "Papiloscopista Policial Federal", "Delegado de Polícia Federal"], CE, 120, "alta")
add(C, "Polícia Federal", 2018, [f"Perito Criminal Federal - Área {i}" for i in (1, 2, 3, 4, 5, 6, 7, 9, 12, 14)], CE, 120,
    "confirmada", "áreas listadas no índice de provas do pciconcursos.com.br")
add(C, "Polícia Federal", 2018, [f"Perito Criminal Federal - Área {i}" for i in (8, 10, 11, 13, 15, 16, 17, 18)], CE, 120,
    V, "área não confirmada para 2018")
add(C, "Polícia Federal", 2021, ["Agente de Polícia Federal", "Escrivão de Polícia Federal",
    "Papiloscopista Policial Federal", "Delegado de Polícia Federal"], CE, 120, "alta")
add(C, "Polícia Federal", 2025, ["Perito Criminal Federal - Contábil-Financeira", "Perito Criminal Federal - Engenharia de Minas",
    "Perito Criminal Federal - Informática", "Perito Criminal Federal - Engenharia Civil"], CE, 120, V,
    "concurso 2025 confirmado em busca; demais áreas a levantar")
add(C, "Polícia Federal", 2014, ["Agente Administrativo"], CE, 120, "alta")
add(C, "Polícia Rodoviária Federal", [2013, 2019, 2021], ["Policial Rodoviário Federal"], CE, 120, "alta")
add(C, "Depen", 2015, ["Agente Penitenciário Federal", "Especialista Federal em Assistência à Execução Penal"], CE, 120, "alta")
add(C, "Depen", 2020, ["Agente Federal de Execução Penal", "Especialista Federal em Assistência à Execução Penal"], CE, 120, "alta")
add(C, "ABIN", 2018, ["Oficial de Inteligência", "Oficial Técnico de Inteligência", "Agente de Inteligência"], CE, 120, "alta")
add(C, "ABIN", 2010, ["Oficial de Inteligência", "Agente de Inteligência"], CE, 120)
add(C, "STF", 2013, TRIB_SUP, CE, 120)
add(C, "STJ", [2015, 2018], TRIB_SUP, CE, 120, "alta", CONF)
add(C, "STM", 2018, TRIB_SUP, CE, 120, "alta", CONF)
add(C, "CNJ", 2013, TRE, CE, 120)
add(C, "TSE (Concurso Unificado da Justiça Eleitoral)", 2024, TRE, CE, 120, "confirmada",
    "120 itens C/E (50 básicos + 70 específicos), prova em 08/12/2024; " + CONF)
add(C, "MPU", [2013, 2018], ["Analista do MPU - Direito", "Analista do MPU - Gestão Pública", "Analista do MPU - Tecnologia da Informação",
    "Técnico do MPU - Administração", "Técnico do MPU - Tecnologia da Informação"], CE, 120, "alta", CONF)
add(C, "TRF 1ª Região", 2017, TRIB, CE, 120, "alta", CONF)
for org, ano in [("TRT 8ª Região (PA/AP)", 2016), ("TRT 7ª Região (CE)", 2017), ("TRT 10ª Região (DF/TO)", 2013),
                 ("TRT 17ª Região (ES)", 2013)]:
    add(C, org, ano, TRIB, CE, 120)
for org, ano in [("TRE-BA", 2017), ("TRE-PE", 2017), ("TRE-TO", 2017), ("TRE-GO", 2015), ("TRE-MT", 2015), ("TRE-PI", 2016)]:
    add(C, org, ano, TRE, CE if ano < 2017 else V, 120 if ano < 2017 else 80, V, "Cebraspe usou múltipla escolha em parte dos TREs de 2017")
add(C, "TJDFT", 2015, TRIB, CE, 120)
add(C, "TJ-PA", 2020, ["Analista Judiciário - Direito", "Analista Judiciário - Administração", "Oficial de Justiça Avaliador"], V, 80)
add(C, "TJ-AM", 2019, ["Analista Judiciário - Direito", "Assistente Judiciário"], CE, 120)
add(C, "INSS", 2016, ["Técnico do Seguro Social", "Analista do Seguro Social - Serviço Social"], CE, 120, "alta")
add(C, "INSS", 2022, ["Técnico do Seguro Social"], CE, 120, "alta")
add(C, "TCU", 2015, ["Auditor Federal de Controle Externo", "Técnico Federal de Controle Externo"], CE, 120, "alta",
    "conferir nº de itens por cargo")
for org, ano in [("TCE-PE", 2017), ("TCE-PA", 2016), ("TCE-MG", 2018), ("TCE-SC", 2016), ("TCE-PR", 2016)]:
    add(C, org, ano, ["Auditor de Controle Externo", "Analista de Gestão"], CE if org in ("TCE-PE", "TCE-SC") else ME,
        120 if org in ("TCE-PE", "TCE-SC") else 80)
add(C, "Caixa Econômica Federal", 2014, ["Técnico Bancário Novo", "Engenheiro Civil"], CE, 120, "alta")
add(C, "Câmara dos Deputados", 2014, ["Analista Legislativo - Consultor Legislativo", "Analista Legislativo - Técnico Legislativo",
    "Analista Legislativo - Informática Legislativa"], CE, 120, "alta", CONF)
add(C, "Banco Central do Brasil", 2024, ["Analista - Economia e Finanças", "Analista - Tecnologia da Informação"], CE, 120,
    "confirmada", "120 itens C/E; 50 vagas por área")
add(C, "Banco Central do Brasil", 2013, ["Analista - Área 1", "Analista - Área 2", "Técnico"], CE, 120)
add(C, "SEFAZ-RS", 2019, ["Auditor-Fiscal da Receita Estadual - Bloco I"], ME, 100, "confirmada",
    "3 provas objetivas de múltipla escolha, 02 e 03/02/2019")
add(C, "SEFAZ-RS", 2019, ["Auditor-Fiscal da Receita Estadual - Bloco II", "Auditor-Fiscal da Receita Estadual - Bloco III"], ME, 80,
    "confirmada", "3 provas objetivas de múltipla escolha, 02 e 03/02/2019")
add(C, "SEFAZ-AL", 2020, ["Auditor Fiscal da Receita Estadual"], V, 100, V, "edital SEFAZ_AL_19_AUDITOR existe no CDN do Cebraspe")
add(C, "SEFAZ-DF", 2020, ["Auditor Fiscal"], CE, 120)
add(C, "PCDF", 2021, ["Agente de Polícia"], CE, 120, "alta", "itens 97 a 102 (Estatística) anulados")
add(C, "PCDF", 2020, ["Escrivão de Polícia"], CE, 120)
add(C, "PC-PE", 2016, POL, ME, 100, V, "conferir tipo")
for org, ano in [("PC-GO", 2016), ("PC-MA", 2018), ("PC-SE", 2018), ("PC-AL", 2021), ("PC-PB", 2022)]:
    add(C, org, ano, POL, V, 100)
add(C, "PM-AL", 2021, ["Soldado Combatente"], V, 100)
add(C, "SERPRO", [2021, 2023], ["Analista - Desenvolvimento de Sistemas", "Analista - Suporte Técnico", "Analista - Negócios em TI"], CE, 120)
add(C, "EBSERH", 2018, ["Analista Administrativo - Administração", "Analista Administrativo - Contabilidade",
    "Assistente Administrativo", "Enfermeiro", "Técnico em Enfermagem"], CE, 120)
add(C, "Petrobras", 2023, ["Técnico de Operação Júnior", "Técnico de Manutenção Júnior - Mecânica",
    "Técnico de Manutenção Júnior - Elétrica", "Técnico de Manutenção Júnior - Instrumentação",
    "Técnico de Manutenção Júnior - Caldeiraria", "Técnico de Segurança Júnior", "Técnico de Enfermagem do Trabalho Júnior",
    "Técnico de Logística de Transporte Júnior", "Técnico de Suprimento de Bens e Serviços Júnior - Administração"], CE, 120, V,
    "concurso 2023.2 de nível técnico confirmado como Cebraspe (C/E); conferir ênfases")
add(C, "Petrobras", 2024, ["Profissional Petrobras de Nível Superior (várias ênfases)"], CE, 120, V)
add(C, "AGU", 2015, ["Advogado da União"], CE, 200)
add(C, "DPU", 2015, ["Defensor Público Federal"], CE, 200)
add(C, "DPU", 2016, ["Analista Técnico-Administrativo", "Agente Administrativo"], CE, 120)
add(C, "ANVISA", 2016, ["Especialista em Regulação", "Técnico Administrativo"], CE, 120)
add(C, "ANATEL", 2014, ["Especialista em Regulação", "Técnico Administrativo"], CE, 120)
add(C, "ANTT", 2013, ["Especialista em Regulação", "Técnico Administrativo"], CE, 120)
add(C, "IBAMA", 2013, ["Analista Ambiental", "Técnico Administrativo"], CE, 120)
add(C, "Correios", 2011, ["Agente de Correios - Carteiro", "Analista de Correios"], CE, 120)

# ============================== FGV ==============================
F = "FGV"
add(F, "OAB (Exame de Ordem Unificado)", range(2011, 2026), ["1ª aplicação do ano", "2ª aplicação do ano", "3ª aplicação do ano"],
    ME, 80, "alta", "4 alternativas (A-D); conferir quantas aplicações houve no ano", nalt=4)
add(F, "Receita Federal", 2022, ["Auditor-Fiscal da Receita Federal", "Analista-Tributário da Receita Federal"], ME, 100, "alta")
add(F, "TCU", 2022, ["Auditor Federal de Controle Externo"], ME, 100, "alta")
add(F, "CGU", 2022, ["Auditor Federal de Finanças e Controle", "Técnico Federal de Finanças e Controle"], ME, 100, "alta")
add(F, "Senado Federal", 2022, ["Analista Legislativo - Processo Legislativo", "Analista Legislativo - Administração",
    "Consultor Legislativo", "Técnico Legislativo", "Policial Legislativo"], ME, 80, "alta", CONF)
add(F, "Senado Federal", 2012, ["Analista Legislativo", "Técnico Legislativo", "Consultor Legislativo"], ME, 80)
add(F, "SEFAZ-AM", 2022, ["Auditor Fiscal de Tributos Estaduais", "Técnico de Arrecadação de Tributos Estaduais"], ME, 80, "alta")
add(F, "SEF-MG", 2023, ["Auditor Fiscal - Auditoria e Fiscalização", "Auditor Fiscal - Tributação",
    "Auditor Fiscal - Tecnologia da Informação"], ME, 130, "confirmada", "130 questões (80 gerais + 50 específicas), 08/01/2023")
add(F, "SEFAZ-ES", 2021, ["Auditor Fiscal da Receita Estadual"], ME, 80)
add(F, "SEFAZ-RJ", 2011, ["Auditor Fiscal da Receita Estadual"], ME, 80)
add(F, "CNU - Concurso Nacional Unificado", 2025, [f"Bloco {i}" for i in range(1, 10)], ME, 70, V,
    "banca FGV confirmada; conferir nº de blocos e de questões")
add(F, "TRF 1ª Região", 2024, ["Analista Judiciário - Área Judiciária", "Analista Judiciário - Área Administrativa",
    "Analista Judiciário - Oficial de Justiça Avaliador Federal", "Técnico Judiciário - Área Administrativa"], ME, 80,
    "confirmada", "80 questões, 5 alternativas; prova em 29/09/2024")
add(F, "TJDFT", 2022, ["Analista Judiciário - Judiciária", "Analista Judiciário - Oficial de Justiça Avaliador Federal",
    "Analista Judiciário - Administração", "Analista Judiciário - Análise de Dados", "Analista Judiciário - Análise de Sistemas",
    "Analista Judiciário - Arquivologia", "Analista Judiciário - Contabilidade", "Analista Judiciário - Engenharia Elétrica",
    "Analista Judiciário - Estatística", "Analista Judiciário - Medicina do Trabalho", "Analista Judiciário - Psiquiatria",
    "Analista Judiciário - Psicologia", "Analista Judiciário - Segurança da Informação", "Analista Judiciário - Serviço Social",
    "Analista Judiciário - Suporte em TI", "Técnico Judiciário - Administrativa", "Técnico Judiciário - Enfermagem"], ME, 80,
    "confirmada", "especialidades segundo JC Concursos; prova prevista 29/05/2022")
add(F, "TRT 24ª Região (MS)", 2025, TRIB, ME, 80, "confirmada", "edital out/2024, prova 09/03/2025 (houve reaplicação); " + CONF)
for org, ano in [("TJ-BA", 2015), ("TJ-SC", 2018), ("TJ-RO", 2021), ("TJ-PI", 2015)]:
    add(F, org, ano, ["Analista Judiciário - Direito", "Técnico Judiciário", "Oficial de Justiça"], ME, 80)
add(F, "PC-AM", 2022, ["Investigador de Polícia", "Escrivão de Polícia", "Delegado de Polícia", "Perito Criminal"], ME, 80)
add(F, "Banestes", 2018, ["Analista Econômico-Financeiro", "Técnico Bancário"], ME, 60)

# ============================== FCC ==============================
F = "FCC"
add(F, "SEFAZ-SP", 2013, ["Agente Fiscal de Rendas - Gestão Tributária", "Agente Fiscal de Rendas - TI"], ME, 80, "alta")
for org, ano, cargo in [("SEFAZ-PE", 2014, "Auditor Fiscal do Tesouro Estadual"), ("SEFAZ-BA", 2019, "Auditor Fiscal"),
                        ("SEF-SC", 2018, "Auditor Fiscal da Receita Estadual"), ("SEFAZ-RJ", 2014, "Auditor Fiscal da Receita Estadual"),
                        ("SEFAZ-MA", 2016, "Auditor Fiscal da Receita Estadual"), ("SEFAZ-PI", 2015, "Auditor Fiscal da Fazenda Estadual"),
                        ("SEFAZ-GO", 2018, "Auditor Fiscal da Receita Estadual")]:
    add(F, org, ano, [cargo + " - Prova 1", cargo + " - Prova 2"], ME, 80, "alta" if org in ("SEFAZ-PE", "SEFAZ-BA") else V,
        "fiscais da FCC costumam ter 2 ou 3 provas objetivas")
for org, ano in [("TRT 2ª Região (SP)", 2018), ("TRT 15ª Região (Campinas)", 2018), ("TRT 6ª Região (PE)", 2018),
                 ("TRT 3ª Região (MG)", 2015), ("TRT 4ª Região (RS)", 2015), ("TRT 9ª Região (PR)", 2015),
                 ("TRT 11ª Região (AM/RR)", 2017), ("TRT 16ª Região (MA)", 2014), ("TRT 20ª Região (SE)", 2016),
                 ("TRT 23ª Região (MT)", 2016), ("TRT 24ª Região (MS)", 2017), ("TRT 5ª Região (BA)", 2013),
                 ("TRT 1ª Região (RJ)", 2013), ("TRT 19ª Região (AL)", 2014), ("TRT 13ª Região (PB)", 2014),
                 ("TRT 18ª Região (GO)", 2013), ("TRT 12ª Região (SC)", 2017), ("TRT 14ª Região (RO/AC)", 2018)]:
    add(F, org, ano, TRIB, ME, 60)
add(F, "TST", 2017, TRIB_SUP, ME, 60)
add(F, "TRF 3ª Região", 2024, ["Analista Judiciário - Área Judiciária", "Técnico Judiciário - Área Administrativa"], ME, 60,
    "confirmada", "prova prevista 28/07/2024, 5 alternativas")
for org, ano in [("TRF 3ª Região", 2016), ("TRF 3ª Região", 2019), ("TRF 4ª Região", 2019), ("TRF 5ª Região", 2017)]:
    add(F, org, ano, TRIB, ME, 60)
for org, ano in [("TRE-SP", 2017), ("TRE-SP", 2012), ("TRE-PR", 2017), ("TRE-RR", 2015), ("TRE-SE", 2015)]:
    add(F, org, ano, TRE, ME, 60)
add(F, "INSS", 2012, ["Técnico do Seguro Social", "Analista do Seguro Social"], ME, 60)
add(F, "SABESP", 2018, ["Analista de Gestão", "Técnico em Gestão"], ME, 60)
add(F, "MPE-PE", 2018, ["Analista Ministerial - Área Jurídica", "Técnico Ministerial"], ME, 60)

# ============================== VUNESP ==============================
F = "Vunesp"
add(F, "TJ-SP", [2017, 2021, 2023], ["Escrevente Técnico Judiciário"], ME, 100, "alta")
add(F, "TJ-SP", [2015, 2018], ["Escrevente Técnico Judiciário"], ME, 100)
add(F, "TJ-SP", [2017, 2023], ["Oficial de Justiça", "Assistente Social Judiciário", "Psicólogo Judiciário"], ME, 80)
add(F, "PC-SP", 2023, ["Escrivão de Polícia", "Investigador de Polícia", "Delegado de Polícia", "Médico Legista", "Perito Criminal"],
    ME, 80, "confirmada", "Escrivão/Investigador 26/11/2023; Delegado/Legista/Perito 03/12/2023")
add(F, "PC-SP", 2018, ["Escrivão de Polícia", "Investigador de Polícia", "Agente Policial", "Agente de Telecomunicações",
    "Delegado de Polícia"], ME, 80)
add(F, "PM-SP", range(2015, 2025), ["Soldado PM de 2ª Classe"], ME, 60, V, "conferir anos e nº de alternativas", nalt=4)
add(F, "PM-SP", range(2017, 2025), ["Aluno-Oficial (Academia do Barro Branco)"], ME, 80)
add(F, "MPE-SP", 2016, ["Oficial de Promotoria", "Analista Jurídico"], ME, 80)
add(F, "Prefeitura de São Paulo", [2016, 2023], ["Professor de Ensino Fundamental II - Português", "Professor - Matemática",
    "Professor - História", "Professor - Geografia", "Professor - Ciências", "Professor de Educação Infantil e Fund. I"], ME, 80)

# ============================== CESGRANRIO ==============================
F = "Cesgranrio"
add(F, "Banco do Brasil", [2015, 2018, 2021], ["Escriturário"], ME, 70, "alta")
add(F, "Banco do Brasil", 2023, ["Escriturário - Agente Comercial", "Escriturário - Agente de Tecnologia"], ME, 70, "alta")
add(F, "Caixa Econômica Federal", 2021, ["Técnico Bancário Novo", "Técnico Bancário Novo - Tecnologia da Informação"], ME, 60,
    "confirmada", "60 questões; prova em 31/10/2021")
add(F, "Caixa Econômica Federal", 2024, ["Técnico Bancário Novo", "Técnico Bancário Novo - Tecnologia da Informação",
    "Engenheiro Civil", "Médico do Trabalho"], ME, 60, "alta")
add(F, "Petrobras", 2021, ["Profissional Júnior - Administração", "Profissional Júnior - Análise de Sistemas",
    "Profissional Júnior - Ciência de Dados", "Profissional Júnior - Economia", "Profissional Júnior - Contabilidade",
    "Profissional Júnior - Engenharia Civil", "Profissional Júnior - Engenharia de Produção",
    "Profissional Júnior - Engenharia de Equipamentos (Mecânica)", "Profissional Júnior - Engenharia de Equipamentos (Elétrica)",
    "Profissional Júnior - Engenharia de Processamento", "Profissional Júnior - Engenharia de Petróleo",
    "Profissional Júnior - Geologia", "Profissional Júnior - Geofísica"], ME, 70, V,
    "concurso de nível superior dez/2021 confirmado; conferir ênfases")
add(F, "Concurso Nacional Unificado (CNU)", 2024, [f"Bloco {i}" for i in range(1, 9)], ME, 90, "alta",
    "prova objetiva geral + específica do bloco; conferir nº de questões")
add(F, "Transpetro", 2018, ["Administrador Júnior", "Engenheiro Júnior", "Técnico de Operação Júnior"], ME, 60)
add(F, "Liquigás", 2018, ["Assistente Administrativo", "Técnico de Operação"], ME, 60)
add(F, "BNDES", 2013, ["Analista - Administração", "Analista - Economia", "Analista - Direito", "Analista - Contabilidade"], ME, 70)
add(F, "Banco da Amazônia", [2018, 2022], ["Técnico Bancário", "Técnico Científico"], ME, 60)

# ============================== ESAF ==============================
F = "ESAF"
add(F, "Receita Federal", [2012, 2014], ["Auditor-Fiscal da Receita Federal", "Analista-Tributário da Receita Federal"], ME, 70, "alta",
    "ESAF foi extinta; provas seguem disponíveis em acervos")
add(F, "Ministério da Fazenda", 2014, ["Assistente Técnico-Administrativo"], ME, 70, "alta")
add(F, "STN", 2013, ["Analista de Finanças e Controle"], ME, 70)
add(F, "CGU", 2012, ["Analista de Finanças e Controle"], ME, 70)
add(F, "ANAC", 2016, ["Especialista em Regulação", "Técnico Administrativo"], ME, 70)
add(F, "FUNAI", 2016, ["Indigenista Especializado", "Agente em Indigenismo"], ME, 70)

# ============================== IBFC ==============================
F = "IBFC"
add(F, "Correios", 2024, ["Agente de Correios - Carteiro", "Analista de Correios - Administrador", "Analista de Correios - Advogado",
    "Analista de Correios - Engenharia", "Analista de Correios - Desenvolvimento de Sistemas"], ME, 60, "confirmada",
    "IBFC confirmada; prova em 15/12/2024; " + CONF)
add(F, "EBSERH", 2023, ["Assistente Administrativo", "Analista Administrativo - Administração", "Analista Administrativo - Contabilidade",
    "Enfermeiro", "Técnico em Enfermagem", "Fisioterapeuta", "Farmacêutico", "Nutricionista", "Psicólogo", "Assistente Social",
    "Médico - Clínica Médica", "Médico - Pediatria", "Médico - Cirurgia Geral", "Médico - Ginecologia e Obstetrícia",
    "Médico - Anestesiologia", "Médico - Cardiologia", "Médico - Radiologia e Diagnóstico por Imagem"], ME, 60, "confirmada",
    "IBFC, prova 17/12/2023 (Radiologia reaplicada em 07/04/2024); área médica com 60 questões")
add(F, "TRF 5ª Região", 2024, ["Analista Judiciário - Área Judiciária", "Analista Judiciário - Área Administrativa",
    "Técnico Judiciário - Área Administrativa"], ME, 60, "confirmada",
    "dois processos em 2024 (provas 25/02 e 13/10); 60 questões com 4 alternativas", nalt=4)
add(F, "TJ-PE", 2017, ["Analista Judiciário - Função Judiciária", "Técnico Judiciário", "Oficial de Justiça"], ME, 60)

# ============================== OUTRAS BANCAS ==============================
add("Quadrix", "SEEDF", 2017, ["Professor - Língua Portuguesa", "Professor - Matemática", "Professor - História",
    "Professor - Geografia", "Professor - Ciências", "Professor - Atividades"], V, 120)
add("Consulplan", "TRF 2ª Região", 2017, TRIB, ME, 60)
add("Consulplan", "TRE-RJ", 2017, TRE, ME, 60)
add("Consulplan", "TJ-MG", 2017, ["Oficial Judiciário", "Oficial de Apoio Judicial"], ME, 60)
add("Instituto AOCP", "TRT 1ª Região (RJ)", 2018, TRIB, ME, 60)
add("Instituto AOCP", "PC-ES", 2019, POL, ME, 60)
add("Instituto AOCP", "PC-PA", 2021, ["Investigador de Polícia", "Escrivão de Polícia", "Delegado de Polícia"], ME, 60)
add("IADES", "PM-DF", 2018, ["Soldado"], ME, 60)
add("FUMARC", "PC-MG", 2018, ["Escrivão de Polícia", "Investigador de Polícia"], ME, 60)

# ============================== AMPLIAÇÃO (séries anuais e concursos com muitos cadernos) ==============================
add("IBFC", "EBSERH", 2023, ["Médico - " + e for e in ("Neurologia", "Ortopedia e Traumatologia", "Psiquiatria", "Infectologia",
    "Nefrologia", "Endocrinologia", "Gastroenterologia", "Hematologia e Hemoterapia", "Oncologia Clínica", "Pneumologia",
    "Dermatologia", "Oftalmologia", "Otorrinolaringologia", "Urologia", "Neonatologia", "Medicina Intensiva", "Patologia",
    "Reumatologia", "Geriatria", "Hepatologia", "Medicina do Trabalho", "Cirurgia Vascular", "Neurocirurgia")]
    + ["Terapeuta Ocupacional", "Fonoaudiólogo", "Biomédico", "Técnico em Radiologia", "Técnico em Análises Clínicas",
       "Técnico em Farmácia", "Engenheiro Clínico", "Analista de TI - Sistemas", "Técnico em Informática"], ME, 60, V,
    "EBSERH 2023 (IBFC) confirmada; conferir se a especialidade teve prova própria")
# Carreiras militares: provas anuais elaboradas pela própria instituição (banca = instituição)
add("Exército Brasileiro (EsPCEx)", "EsPCEx", range(2014, 2025), ["Cadete - Prova de conhecimentos"], ME, 80, "alta",
    "prova anual; conferir nº de questões", nalt=5)
add("Exército Brasileiro (EsSA)", "EsSA", range(2014, 2025), ["Sargento de Carreira - Combatente/Logística-Técnica/Aviação"], ME, 50, "alta")
add("Aeronáutica (EEAR)", "EEAR", range(2014, 2025), ["CFS - 1º semestre", "CFS - 2º semestre"], ME, 96, V,
    "conferir se houve duas turmas no ano", nalt=4)
add("Marinha do Brasil", "Colégio Naval", range(2014, 2025), ["Aluno do Colégio Naval"], ME, 60, "alta")
add("Marinha do Brasil", "Escola de Aprendizes-Marinheiros (EAM/CPA)", range(2014, 2025), ["Aprendiz-Marinheiro"], ME, 50, "alta", nalt=5)
# Exame de Suficiência do CFC (2 edições/ano)
add("Consulplan", "CFC - Exame de Suficiência", range(2015, 2025), ["1ª edição do ano", "2ª edição do ano"], ME, 50, V,
    "conferir banca de cada edição", nalt=4)
# Educação
add("Quadrix", "SEEDF", 2022, ["Professor - Língua Portuguesa", "Professor - Matemática", "Professor - História",
    "Professor - Geografia", "Professor - Biologia", "Professor - Atividades", "Analista de Gestão Educacional"], V, 120)
add("Vunesp", "SEDUC-SP", 2023, ["PEB II - " + d for d in ("Língua Portuguesa", "Matemática", "História", "Geografia",
    "Ciências", "Biologia", "Física", "Química", "Inglês", "Arte", "Educação Física", "Filosofia", "Sociologia")], ME, 80)
add("Cebraspe", "FUB (UnB)", 2018, ["Assistente em Administração", "Administrador", "Técnico de Laboratório",
    "Técnico em Tecnologia da Informação", "Analista de Tecnologia da Informação", "Contador"], CE, 120)
# Ministérios Públicos, defensorias e legislativos
add("FGV", "MPE-RJ", 2016, ["Analista do Ministério Público - Processual", "Analista - Administrativa", "Técnico do Ministério Público"], ME, 70)
add("FGV", "DPE-RJ", 2019, ["Técnico Superior Jurídico", "Técnico Médio de Defensoria"], ME, 70)
add("FGV", "ALERJ", 2017, ["Especialista Legislativo", "Procurador"], ME, 70)
add("Cebraspe", "MPE-PI", 2018, ["Analista Ministerial - Área Processual", "Técnico Ministerial - Administrativo"], CE, 120)
add("Cebraspe", "Telebras", 2015, ["Especialista em Gestão de Telecomunicações", "Técnico em Gestão de Telecomunicações"], CE, 120)
add("Cebraspe", "PC-RJ", 2022, ["Inspetor de Polícia", "Investigador Policial", "Delegado de Polícia"], V, 100)
add("Cebraspe", "Petrobras", 2024, ["Ênfase " + e for e in ("Administração", "Análise de Sistemas", "Ciência de Dados",
    "Engenharia Civil", "Engenharia de Produção", "Engenharia de Equipamentos - Mecânica", "Engenharia de Processamento")], CE, 120, V)
# Bancos e estatais
add("Cesgranrio", "Banco do Brasil", [2012, 2014], ["Escriturário"], ME, 70)
add("FCC", "Banco do Brasil", [2011, 2013], ["Escriturário"], ME, 70, V, "conferir banca (FCC x Cesgranrio)")
add("Cesgranrio", "Caixa Econômica Federal", 2012, ["Técnico Bancário Novo"], ME, 60)
add("Cesgranrio", "Banrisul", 2023, ["Escriturário"], ME, 70)
add("Cesgranrio", "ANP", 2016, ["Especialista em Regulação", "Analista Administrativo", "Técnico em Regulação"], ME, 70)
add("Cesgranrio", "EPE", 2014, ["Analista de Pesquisa Energética", "Assistente Administrativo"], ME, 70)
add("Cesgranrio", "Transpetro", 2012, ["Administrador Júnior", "Técnico de Operação Júnior"], ME, 60)
add("FGV", "Banco do Nordeste", 2014, ["Analista Bancário"], ME, 60)
add("IADES", "BRB", 2019, ["Escriturário"], ME, 60)

add("Cebraspe", "Polícia Federal", 2012, ["Agente de Polícia Federal", "Escrivão de Polícia Federal"], CE, 120, "alta")
add("Cebraspe", "Polícia Federal", 2013, ["Delegado de Polícia Federal", "Perito Criminal Federal (várias áreas)"], CE, 120)
add("Vunesp", "TJ-SP", [2015, 2017, 2018, 2021, 2023], ["Juiz Substituto (Magistratura)"], ME, 100)
add("Vunesp", "TJ-SP", [2016, 2018, 2021], ["Outorga de Delegações de Notas e Registro (Cartórios)"], ME, 100)
add("FCC", "DPE-SP", [2015, 2019, 2023], ["Defensor Público"], ME, 100)
add("FCC", "CLDF", 2018, ["Consultor Legislativo", "Técnico Legislativo", "Analista Legislativo"], ME, 70)
add("FCC", "SEFAZ-SP", 2025, ["Auditor Fiscal da Receita Estadual"], ME, 100)
add("FGV", "IBGE", 2022, ["Agente Censitário Municipal", "Recenseador"], ME, 60)
add("FGV", "AL-RO", 2018, ["Analista Legislativo", "Assistente Legislativo"], ME, 60)
add("FGV", "MPE-BA", 2017, ["Analista Técnico - Direito", "Assistente Técnico-Administrativo"], ME, 60)
add("FGV", "TJ-AL", 2018, ["Analista Judiciário - Judiciária", "Técnico Judiciário"], ME, 60)
add("FGV", "COMPESA", 2018, ["Analista de Saneamento - Administrador", "Assistente de Saneamento"], ME, 60)
add("FGV", "OAB (Exame de Ordem Unificado)", 2010, ["2ª aplicação do ano", "3ª aplicação do ano"], ME, 100, V,
    "primeiros exames FGV (2010.2 e 2010.3); conferir nº de questões", nalt=4)
add("Cebraspe", "Câmara dos Deputados", 2012, ["Analista Legislativo - Técnico Legislativo"], CE, 120)
add("Cebraspe", "TCDF", 2014, ["Auditor de Controle Externo"], CE, 120)
add("Cebraspe", "TCE-RO", 2019, ["Auditor de Controle Externo"], V, 100)
add("Cebraspe", "IBAMA", 2022, ["Analista Ambiental", "Analista Administrativo"], CE, 120)
add("Cebraspe", "ICMBio", 2022, ["Analista Ambiental", "Técnico Ambiental"], CE, 120)
add("Cebraspe", "Banco do Nordeste", 2018, ["Analista Bancário"], CE, 120)
add("Fundatec", "PC-RS", 2018, ["Escrivão de Polícia", "Inspetor de Polícia"], ME, 80)
add("Marinha do Brasil", "Escola Naval", range(2014, 2025), ["Aspirante - Prova de conhecimentos"], ME, 60, "alta")


def main():
    cols = ["ID", "Banca", "Orgao", "Ano", "Cargo_Prova", "Tipo", "Alternativas", "Questoes_Estimadas", "Confianca", "Status",
            "Arquivo_Prova", "Arquivo_Gabarito", "Faixas_Disciplinas", "Observacoes"]
    vistos, linhas = set(), []
    for l in sorted(LINHAS, key=lambda x: (x["Banca"], x["Orgao"], x["Ano"], x["Cargo_Prova"])):
        chave = (l["Banca"], l["Orgao"], l["Ano"], l["Cargo_Prova"])
        if chave not in vistos:
            vistos.add(chave)
            linhas.append(l)
    destino = Path(__file__).with_name("plano_coleta.csv")
    with open(destino, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        for i, l in enumerate(linhas, 1):
            w.writerow({**l, "ID": i, "Status": "a_coletar", "Arquivo_Prova": "", "Arquivo_Gabarito": "",
                        "Faixas_Disciplinas": ""})
    print(f"{len(linhas)} provas -> {destino}")


if __name__ == "__main__":
    main()
