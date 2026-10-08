"""Classificador de Disciplina treinado com as questões que já vêm rotuladas.

Rótulos: cabeçalhos dos cadernos da FGV e disciplinas da OAB, normalizados para nomes
canônicos. Modelo: TF-IDF (palavras 1-2 + caracteres 3-5) + regressão logística. Na
predição, as probabilidades são suavizadas pelos vizinhos do mesmo caderno, já que as
provas agrupam itens da mesma matéria.
"""
import re
import unicodedata

import numpy as np

CANONICAS = [
    (r"l[ií]ngua portuguesa|portugu[eê]s|interpreta[cç][aã]o de texto|gram[aá]tica", "Língua Portuguesa"),
    (r"reda[cç][aã]o oficial", "Redação Oficial"),
    (r"l[ií]ngua inglesa|ingl[eê]s", "Língua Inglesa"),
    (r"l[ií]ngua espanhola|espanhol", "Língua Espanhola"),
    (r"racioc[ií]nio l[oó]gico|l[oó]gica", "Raciocínio Lógico"),
    (r"matem[aá]tica financeira", "Matemática Financeira"),
    (r"matem[aá]tica", "Matemática"),
    (r"estat[ií]stica|probabilidade", "Estatística"),
    (r"inform[aá]tica|tecnologia da informa[cç][aã]o|computa[cç][aã]o", "Informática"),
    (r"direito constitucional|constitucional", "Direito Constitucional"),
    (r"direito administrativo|administrativo$|licita[cç][oõ]es", "Direito Administrativo"),
    (r"processual penal|processo penal", "Direito Processual Penal"),
    (r"direito penal|penal", "Direito Penal"),
    (r"processual civil|processo civil", "Direito Processual Civil"),
    (r"processual do trabalho|processo do trabalho", "Direito Processual do Trabalho"),
    (r"direito (individual |coletivo )?do trabalho|trabalhista", "Direito do Trabalho"),
    (r"direito civil|civil", "Direito Civil"),
    (r"tribut[aá]ri", "Direito Tributário"),
    (r"previdenci[aá]ri", "Direito Previdenciário"),
    (r"empresarial|comercial", "Direito Empresarial"),
    (r"eleitoral", "Direito Eleitoral"),
    (r"ambiental", "Direito Ambiental"),
    (r"direitos humanos", "Direitos Humanos"),
    (r"consumidor", "Direito do Consumidor"),
    (r"crian[cç]a e do adolescente|\beca\b", "Direito da Criança e do Adolescente"),
    (r"internacional", "Direito Internacional"),
    (r"financeiro|or[cç]ament|\bafo\b", "Administração Financeira e Orçamentária"),
    (r"filosofia do direito", "Filosofia do Direito"),
    (r"[eé]tica profissional|estatuto da advocacia", "Ética Profissional"),
    (r"[eé]tica", "Ética no Serviço Público"),
    (r"legisla[cç][aã]o (penal )?especial|leis penais especiais", "Legislação Especial"),
    (r"legisla[cç][aã]o", "Legislação Específica"),
    (r"contabilidade|cont[aá]bil|contabil", "Contabilidade"),
    (r"auditoria", "Auditoria"),
    (r"economia|econ[oô]mic", "Economia"),
    (r"administra[cç][aã]o p[uú]blica|gest[aã]o p[uú]blica|pol[ií]ticas p[uú]blicas", "Administração Pública"),
    (r"administra[cç][aã]o|gest[aã]o|gerenciamento|governan[cç]a", "Administração"),
    (r"arquivolog", "Arquivologia"),
    (r"atualidades|realidade|conhecimentos gerais", "Atualidades"),
    (r"sa[uú]de p[uú]blica|\bsus\b|pol[ií]ticas de sa[uú]de|sa[uú]de coletiva", "Saúde Pública e SUS"),
    (r"enfermagem", "Enfermagem"),
    (r"psicolog", "Psicologia"),
    (r"servi[cç]o social|assist[eê]ncia social", "Serviço Social"),
    (r"pedagog|educa[cç][aã]o|did[aá]tica|ensino", "Pedagogia e Educação"),
    (r"criminolog", "Criminologia"),
    (r"medicina legal", "Medicina Legal"),
    (r"medicina|cl[ií]nica|cirurgia|pediatria|ginecologia", "Medicina"),
    (r"engenharia", "Engenharia"),
    (r"f[ií]sica", "Física"), (r"qu[ií]mica", "Química"), (r"biologia", "Biologia"),
    (r"hist[oó]ria", "História"), (r"geografia", "Geografia"),
]
_CANON = [(re.compile(p, re.I), n) for p, n in CANONICAS]
_GENERICAS = re.compile(r"^(no[cç][oõ]es (gerais )?de direito.*|direito|conhecimentos (b[aá]sicos|gerais|espec[ií]ficos|complementares))$", re.I)


def canonica(disciplina):
    """'Noções de Direito Administrativo' -> 'Direito Administrativo'. Genéricas ('Noções de Direito') -> ''."""
    d = (disciplina or "").strip()
    if not d or _GENERICAS.match(d):
        return ""
    for pad, nome in _CANON:
        if pad.search(d):
            return nome
    d = re.sub(r"^(No[cç][oõ]es|Conhecimentos|Fundamentos|T[oó]picos) (de|sobre|em) ", "", d, flags=re.I)
    return d[:1].upper() + d[1:]


def _texto(q):
    return " ".join([q.get("Enunciado", "")] + [q.get(f"Alternativa_{l}", "") for l in "ABCDE"])


class Classificador:
    def __init__(self, min_exemplos=40):
        self.min_exemplos = min_exemplos
        self.modelo = None

    def treinar(self, questoes):
        from collections import Counter

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline, make_union

        rot = [(q, canonica(q.get("Disciplina", ""))) for q in questoes]
        cont = Counter(r for _, r in rot if r)
        dados = [(_texto(q), r) for q, r in rot if r and cont[r] >= self.min_exemplos]
        X, y = [d[0] for d in dados], [d[1] for d in dados]
        vet = make_union(
            TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=200000, sublinear_tf=True, strip_accents="unicode"),
            TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_features=200000, sublinear_tf=True),
        )
        self.modelo = make_pipeline(vet, LogisticRegression(max_iter=2000, C=4.0))
        self.modelo.fit(X, y)
        return len(X), sorted(cont.items(), key=lambda x: -x[1])

    def prever_caderno(self, questoes, janela=2):
        """Prevê a disciplina de cada questão de um caderno (lista na ordem original)."""
        if not questoes:
            return []
        P = self.modelo.predict_proba([_texto(q) for q in questoes])
        n = len(questoes)
        suav = np.zeros_like(P)
        for i in range(n):
            ini, fim = max(0, i - janela), min(n, i + janela + 1)
            pesos = np.array([2.0 if j == i else 1.0 for j in range(ini, fim)])
            suav[i] = (P[ini:fim] * pesos[:, None]).sum(0) / pesos.sum()
        classes = self.modelo.classes_
        return [(classes[k], float(suav[i, k])) for i, k in enumerate(suav.argmax(1))]
