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
- Desempenho = Σ(`tempo_min` × (`delta_boas` + `delta_refugo`)) / min OPERANDO, limitado a 1.
  **Não medido** (`desempenho_medido: false`, vale 1) quando houve peças apontadas mas falta o tempo
  operando ou o tempo padrão (`tempo_min` 0); sem produção, 0 (medido se operou). *Correção posterior
  à fase 2: a regra original "0 se não operou" deixava a MONT-01 da demo com OEE 0 tendo 450 boas;
  agora 0,96.*
- Na **linha**, o desempenho usa só os postos medidos (Σ teórico / Σ operando deles); disponibilidade
  e qualidade continuam somando todos.
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

## Exemplo conferido à mão (`demo.cryo` + `demo_oee.cryo`, emp.exe em 127.0.0.1:8193, dados novos)

Build de `fase2-oee` com o `main` juntado (cb242c1: `maquina.*` com `motivo`, `inicio`, `fim`).
Os eventos 1..131 foram lidos de `/api/sistema/eventos` em duas tomadas (o buffer guarda 100) e
recalculados por um script independente do código Cryo.

**PRENSA-03**

| id | evento | dados relevantes |
|---|---|---|
| 105 | maquina.parada | parada=4, ha_minutos=30 → inicio=1792519996850, fim=0 |
| 106 | maquina.liberada | inicio=1792519996850, fim=1792521796860 |
| 109 | etapa_iniciada | inicio=1792521796882, tempo_min=0.25 |
| 117 | etapa_apontada | delta_boas=3, delta_refugo=1 |
| 125 | etapa_apontada | delta_boas=1, delta_refugo=0 |
| 129 | etapa_concluida | fim=1792521886970 |

- janela 8 h = 480 min; parado = 1 800 010 ms = 30,0002 min → D = (480 − 30,0002)/480 = **0,9375**
- operando = 1792521886970 − 1792521796882 = 90 088 ms = 1,50147 min (a parada termina antes)
- teórico = 0,25 × (3+1) + 0,25 × 1 = 1,25 min → Desemp = 1,25 / 1,50147 = **0,8325**
- Q = 4/5 = **0,8**; OEE = 0,9375 × 0,8325 × 0,8 = **0,6244**

`GET /api/indicadores/oee?horas=8` → PRENSA-03 `disponibilidade 0.9375, desempenho 0.8325,
qualidade 0.8, oee 0.6244, min_operando 1.5, min_parado 30, min_teorico 1.25` — igual.

**MONT-01** (parada retroativa de 15 min deixada aberta): o evento 131 traz o início real
(15 min antes), a parada cobre as duas execuções de milissegundos da demo (PARADO prevalece) →
parado 15,004 min, operando 0, D = **0,9687**, Desemp = **0**, Q = 360/363 = **0,9917**, OEE **0** —
igual à API.

Também conferido: série por hora com D = 0,5 na hora dos 30 min parados; `horas=abc`/`500` → 422,
posto inexistente → 404, 500+ pontos → 422, POST → 403 (sem perfil de escrita).

**Reinício e alerta** (mesmos dados, `EMP_OEE_ALERTA=0.95`):
- depois do reinício PRENSA-03 devolve os mesmos números e `/estados` da MONT-01 mostra a mesma
  parada (o reanúncio de paradas abertas pela manutenção não duplica o intervalo);
- abrir/encerrar uma parada na PRENSA-02 e abrir outra na PRENSA-01 (3 eventos) gerou **um**
  `indicadores.oee_baixo` (`oee=0.859&limite=0.95&…`); um novo reinício seguido de outro evento
  não gerou o segundo (o instante fica em `dados/indicadores/estado.json`).
- Na carga normal (limite 0,6) nenhum alerta saiu: o OEE da linha ficou em ~0,86.

## Limites honestos

- **Reinício**: a produção não reanuncia etapas em execução. Como os intervalos ficam gravados, uma
  execução já vista sobrevive ao reinício (conferido); mas uma etapa iniciada sem o indicador ativo
  (ou com `dados/indicadores/` apagado) aparece OCIOSA até o próximo evento dela — que traz `inicio`
  e recupera o intervalo retroativamente.
- **Parada retroativa**: com `inicio` no evento (main cb242c1) ela vale desde o início real, aberta
  ou não. Sem o campo (dados antigos), o módulo cai no fallback: conta do evento enquanto aberta e
  corrige para `fim − minutos` ao liberar (precisão de 1 min).
- **Reiniciar etapa EM_EXECUCAO** não publica evento: a execução velha só fecha quando a nova começa.
- Parada retroativa sobre uma execução: PARADO prevalece, então o tempo operando é engolido mas os
  apontamentos feitos ali continuam contando (MONT-01 e PRENSA-02 da demo: desempenho 0 com peças
  apontadas).
- Execuções de milissegundos (demo.cryo) dão desempenho limitado a 1.
- Alerta: avaliado só quando um evento muda os intervalos/apontamentos (não há timer, L-08); uma
  linha que piora só pela passagem do tempo não alerta até o próximo evento.

## Sem verificar

- Poda por retenção (8 dias) — exige dados antigos.
- O fallback sem `inicio` em `maquina.*` só foi exercido na rodada anterior ao merge do main.
- `test_oee.cryo` não está no `build.ps1` (a coordenadora liga); roda com
  `python ../Burnout/cryoc.py test tests/test_oee.cryo --backend pyro` (11/11).
