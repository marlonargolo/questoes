"""Estrutura exigida: 13 colunas exatas, planificadas."""
from dataclasses import dataclass, asdict, fields

COLUNAS = [
    "Banca", "Orgao", "Ano", "Disciplina", "Assunto", "Enunciado",
    "Alternativa_A", "Alternativa_B", "Alternativa_C", "Alternativa_D", "Alternativa_E",
    "Gabarito", "Comentario_Professor",
]
LETRAS = "ABCDE"


@dataclass
class Questao:
    Banca: str = ""
    Orgao: str = ""
    Ano: str = ""
    Disciplina: str = ""
    Assunto: str = ""
    Enunciado: str = ""
    Alternativa_A: str = ""
    Alternativa_B: str = ""
    Alternativa_C: str = ""
    Alternativa_D: str = ""
    Alternativa_E: str = ""
    Gabarito: str = ""
    Comentario_Professor: str = ""

    @classmethod
    def de_alternativas(cls, alternativas, **kw):
        """Cria a questão a partir de uma lista de textos de alternativas (até 5)."""
        q = cls(**kw)
        for letra, texto in zip(LETRAS, alternativas):
            setattr(q, f"Alternativa_{letra}", texto)
        return q

    @classmethod
    def certo_errado(cls, gabarito_ce, **kw):
        """Questão Certo/Errado (Cebraspe): A=Certo, B=Errado, C/D/E em branco."""
        g = str(gabarito_ce).strip().upper()[:1]
        kw["Gabarito"] = {"C": "A", "E": "B", "A": "A", "B": "B"}.get(g, "")
        return cls(Alternativa_A="Certo", Alternativa_B="Errado", **kw)

    def como_dict(self):
        return asdict(self)


assert [f.name for f in fields(Questao)] == COLUNAS
