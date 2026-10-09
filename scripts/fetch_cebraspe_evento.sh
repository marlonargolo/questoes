#!/bin/bash
# Baixa o JSON de um concurso da API do Cebraspe (uso: xargs -P 4 -n 1 scripts/fetch_cebraspe_evento.sh < ids)
id="$1"; out="dados/cache/cebraspe/$id.json"
[ -s "$out" ] && exit 0
curl -sS -m 120 -A "Mozilla/5.0 (compatible; questoes-bot/0.1; coleta de provas publicas)" \
  -o "$out.tmp" "https://apis.cebraspe.org.br/cebraspe/eventos/$id" && mv "$out.tmp" "$out"
sleep 1
