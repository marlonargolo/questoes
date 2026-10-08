"""CLI: python -m questoes <comando> ..."""
import argparse
import json
import sys

from . import pipeline


def main(argv=None):
    p = argparse.ArgumentParser(prog="questoes", description="Banco de questões de concursos")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("pdf", help="extrai questões de provas PDF listadas num manifesto YAML")
    a.add_argument("manifesto")
    a.add_argument("-o", "--saida", required=True, help="arquivo .jsonl intermediário")

    a = sub.add_parser("tabela", help="importa CSV/XLSX/JSON/JSONL/Parquet com mapa de campos")
    a.add_argument("arquivo")
    a.add_argument("--mapa", help="YAML de mapeamento (omita se já estiver nas 13 colunas)")
    a.add_argument("-o", "--saida", required=True)

    a = sub.add_parser("baixar-pdfs", help="baixa PDFs de provas/gabaritos a partir de páginas de listagem")
    a.add_argument("config")

    a = sub.add_parser("web", help="raspa questões de HTML com seletores CSS (somente sites que permitam)")
    a.add_argument("config")
    a.add_argument("-o", "--saida", required=True)

    a = sub.add_parser("consolidar", help="limpa, valida, deduplica e exporta o banco final")
    a.add_argument("entradas", nargs="+", help="arquivos .jsonl")
    a.add_argument("-o", "--saida", action="append", required=True, help=".xlsx, .csv ou .json (repetível)")
    a.add_argument("--rejeitadas", help="CSV com as questões reprovadas e o motivo")
    a.add_argument("--relatorio", help="JSON com estatísticas")
    a.add_argument("--sem-assunto", action="store_true", help="não classificar Assunto automaticamente")
    a.add_argument("--bom", action="store_true", help="CSV com BOM (abre acentuado direto no Excel)")

    a = sub.add_parser("plano", help="resume o plano de coleta e gera o manifesto das provas prontas")
    a.add_argument("plano", help="planejamento/plano_coleta.csv ou .xlsx")
    a.add_argument("--manifesto", help="YAML a gerar com as linhas Status=pronto")
    a.add_argument("--xlsx", help="exporta o plano formatado (abas Plano e Resumo)")

    a = sub.add_parser("validar", help="valida um arquivo já nas 13 colunas")
    a.add_argument("arquivo")

    args = p.parse_args(argv)

    if args.cmd == "pdf":
        from .fontes.pdf import importar_manifesto

        print(f"{pipeline.salvar_jsonl(importar_manifesto(args.manifesto), args.saida)} questões -> {args.saida}")
    elif args.cmd == "tabela":
        from .fontes.tabular import importar

        print(f"{pipeline.salvar_jsonl(importar(args.arquivo, args.mapa), args.saida)} questões -> {args.saida}")
    elif args.cmd == "baixar-pdfs":
        from .fontes import web

        web.baixar_pdfs(web.carregar(args.config))
    elif args.cmd == "web":
        from .fontes import web

        n = pipeline.salvar_jsonl(web.raspar_questoes(web.carregar(args.config)), args.saida)
        print(f"{n} questões -> {args.saida}")
    elif args.cmd == "consolidar":
        rel = pipeline.consolidar(args.entradas, args.saida, args.rejeitadas, args.relatorio,
                                  classificar_assunto=not args.sem_assunto, bom=args.bom)
        print(json.dumps({k: rel[k] for k in ("lidas", "validas", "rejeitadas", "duplicadas_removidas")},
                         ensure_ascii=False))
    elif args.cmd == "plano":
        from . import plano

        linhas = plano.ler_plano(args.plano)
        pb, _ = plano.resumo(linhas)
        for (b,), (n, q) in sorted(pb.items(), key=lambda x: -x[1][1]):
            print(f"{b:12} {n:4} provas  ~{q:6} questões")
        print(f"{'TOTAL':12} {len(linhas):4} provas  ~{sum(v[1] for v in pb.values()):6} questões")
        if args.xlsx:
            plano.exportar_xlsx(linhas, args.xlsx)
        if args.manifesto:
            n, pend = plano.gerar_manifesto(linhas, args.manifesto)
            print(f"{n} provas no manifesto {args.manifesto}")
            for p_ in pend:
                print("  pendente:", p_)
    elif args.cmd == "validar":
        from .fontes.tabular import importar
        from .validacao import relatorio

        rel = relatorio(importar(args.arquivo))
        print(json.dumps({k: rel[k] for k in ("total", "validas", "invalidas", "motivos")}, ensure_ascii=False, indent=2))
        return 0 if rel["invalidas"] == 0 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
