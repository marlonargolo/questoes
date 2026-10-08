#!/bin/bash
# Baixa a página de um concurso da FGV (uso: xargs -P 3 -n 1 scripts/fetch_fgv_concurso.sh < slugs)
s="$1"; out="dados/cache/fgv/c_$s.html"
[ -s "$out" ] && exit 0
curl -sS -m 120 -A "Mozilla/5.0 (compatible; questoes-bot/0.1; coleta de provas publicas)" -o "$out.tmp" "https://conhecimento.fgv.br/concursos/$s" && mv "$out.tmp" "$out"
sleep 1
