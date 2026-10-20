# Fase 2 — C. Histórico do posto e OEE (`indicadores`)

Módulo `src/modulos/indicadores/` (prefixo `/api/indicadores`, só leitura).
Depende de `cadastros`; assina `maquina.*` e `producao.etapa_{iniciada,apontada,concluida,falhou}`
(listados um a um: `ev::casa` só aceita curinga `.*`). Não importa produção nem manutenção.

- `oee.cryo` — cálculo puro (janela, sobreposição, segmentos, frações), testado em `tests/test_oee.cryo` (11 `test fn`).
- `indicadores.cryo` — eventos → intervalos/apontamentos gravados em `dados/indicadores/{intervalos,apontamentos,estado}.json` (retenção 8 dias; `horas` ≤ 168).

## Rotas

| Rota | Resposta |
|---|---|
| `GET /estados?posto=X&horas=8` | `[{posto, estado, inicio, fim, motivo}]`; `fim=0` = em curso; `posto` inexistente → 404 |
| `GET /oee?horas=8` | `{janela_ms, inicio, fim, linha:{disponibilidade, desempenho, qualidade, oee}, postos:[{posto, …frações, min_operando, min_parado, min_ocioso, min_teorico, boas, refugo}]}` |
| `GET /oee/serie?posto=X&horas=24&passo_min=60` | `[{inicio, fim, …frações}]`; posto vazio = linha; a última janela pode ser mais curta; máx. 500 pontos (422) |

`horas`/`passo_min` aceitam decimal (`0,5`); inválidos → 422. Campos a mais em relação ao contrato: `inicio`, `fim`, `min_teorico`.

## Fórmulas

Estado num instante: **PARADO** se há parada aberta (prevalece) › **OPERANDO** se há etapa EM_EXECUCAO › **OCIOSO**.

- Disponibilidade = (janela − parado) / janela
- Desempenho = Σ(`tempo_min` × (`delta_boas` + `delta_refugo`)) / min OPERANDO, limitado a 1; 0 se não operou
- Qualidade = Σ`delta_boas` / Σ(`delta_boas` + `delta_refugo`); 1 se nada apontado
- OEE = D × Desemp × Q
- Linha = as mesmas fórmulas sobre as **somas** de todos os postos cadastrados.

Consequência do contrato: tempo OCIOSO não penaliza nada. Apontamentos contam pelo instante do evento.

Segmentos são **derivados na consulta** a partir dos intervalos gravados (parada `P<id>`, execução
`E<op>-<etapa>-<inicio>`), então uma parada retroativa reescreve o passado sem migração.

`indicadores.oee_baixo` (`oee, limite, horas=8, disponibilidade, desempenho, qualidade`): OEE da linha
nas últimas 8 h < `EMP_OEE_ALERTA` (padrão 0.6), no máximo um por hora (instante em `estado.json`),
e só com ≥ 15 min OPERANDO + PARADO na janela — sem essa base o primeiro evento do dia (etapa
recém-iniciada, nada apontado) dava OEE 0 e alertava (visto na 1ª rodada).

## Exemplo conferido à mão (PRENSA-03, `demo.cryo` + `demo_oee.cryo`, emp.exe em 127.0.0.1:8193)

Eventos de `/api/sistema/eventos`:

| id | evento | dados relevantes |
|---|---|---|
| 107 | maquina.liberada ts 1792500130373 | parada=4, minutos=30 |
| 110 | etapa_iniciada | inicio=1792500130393, tempo_min=0.25 |
| 118 | etapa_apontada | delta_boas=3, delta_refugo=1 |
| 126 | etapa_apontada | delta_boas=1, delta_refugo=0 |
| 130 | etapa_concluida | fim=1792500220496 |

- janela 8 h = 480 min; parado = 30 min (1 800 000 ms) → D = 450/480 = **0,9375**
- operando = 1792500220496 − 1792500130393 = 90 103 ms = 1,50172 min (sem sobreposição com a parada)
- teórico = 0,25 × 4 + 0,25 × 1 = 1,25 min → Desemp = 1,25 / 1,50172 = **0,8324**
- Q = 4/5 = **0,8**; OEE = 0,9375 × 0,83238 × 0,8 = **0,6243**

`GET /api/indicadores/oee?horas=8` devolveu para PRENSA-03 exatamente
`disponibilidade 0.9375, desempenho 0.8324, qualidade 0.8, oee 0.6243, min_operando 1.5, min_parado 30`.
A série por hora deu D = 0,5 na hora com os 30 min parados. Erros conferidos: `horas=abc`/`500` → 422,
posto inexistente → 404, 500+ pontos → 422, POST → 403 (sem perfil de escrita).

## Limites honestos

- **Reinício**: a produção não reanuncia etapas em execução. Como os intervalos ficam gravados, uma
  execução já vista sobrevive ao reinício; mas uma etapa iniciada sem o indicador ativo (ou com
  `dados/indicadores/` apagado) aparece OCIOSA até o próximo evento dela — que traz `inicio` e
  recupera o intervalo retroativamente.
- **Parada retroativa**: `maquina.parada` não traz `inicio` (só `minutos=0`). Enquanto aberta, a parada
  conta a partir do evento (ex.: SOLDA-01 e MONT-01 da demo, abertas com 42 e 15 min retroativos,
  aparecem paradas só desde o evento). Ao ser liberada, o início é corrigido para `fim − minutos`
  (precisão de 1 min). O módulo já usa `inicio`/`fim`/`motivo` se a manutenção passar a publicá-los
  (pedido à coordenadora: uma linha em `_anunciar`).
- **Reiniciar etapa EM_EXECUCAO** não publica evento: a execução velha só fecha quando a nova começa.
- Parada retroativa sobre uma execução: PARADO prevalece, então o tempo operando é engolido mas os
  apontamentos feitos ali continuam contando (PRENSA-02 da demo: desempenho 0 com peças apontadas).
- Execuções de milissegundos (demo.cryo) dão desempenho limitado a 1.

## Sem verificar

- O build final (`build.ps1`) passou **antes** de duas correções: base mínima do alerta e
  `_dir = dir` (os arquivos iam para `dados/indicadores/indicadores/` porque o registro já passa
  `dados/<id>`). Depois delas só compilei (`cryoc --backend pyro`) e rodei `test_oee.cryo` (11/11);
  falta rodar `build.ps1` de novo e repetir a conferência HTTP.
- Não testei: reinício sobre os mesmos dados, `indicadores.oee_baixo` com a base mínima
  (`EMP_OEE_ALERTA=0.95`), o limite de um por hora, poda por retenção.
- `test_oee.cryo` não está no `build.ps1` (a coordenadora liga).
