"""Exportação para CSV (; UTF-8), XLSX e JSON."""
import csv
import json
from pathlib import Path

from .schema import COLUNAS


def exportar_csv(questoes, caminho, bom=False):
    with open(caminho, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for q in questoes:
            w.writerow(q.como_dict())


def exportar_xlsx(questoes, caminho):
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook(write_only=True)
    ws = wb.create_sheet("Questoes")
    ws.append(COLUNAS)
    for q in questoes:
        d = q.como_dict()
        linha = [d[c] for c in COLUNAS]
        linha[COLUNAS.index("Ano")] = int(d["Ano"]) if d["Ano"].isdigit() else d["Ano"]
        ws.append(linha)
    wb.save(caminho)


def exportar_json(questoes, caminho):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump([q.como_dict() for q in questoes], f, ensure_ascii=False, indent=1)


def exportar(questoes, caminho, bom=False):
    caminho = Path(caminho)
    ext = caminho.suffix.lower()
    if ext == ".csv":
        exportar_csv(questoes, caminho, bom=bom)
    elif ext == ".xlsx":
        exportar_xlsx(questoes, caminho)
    elif ext == ".json":
        exportar_json(questoes, caminho)
    else:
        raise ValueError(f"formato não suportado: {ext}")
