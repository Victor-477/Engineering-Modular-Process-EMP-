# Fase 2 — comercial, estoque endereçado e OEE

> Continuação de [ANALISE_FACTORYVIEWS.md](ANALISE_FACTORYVIEWS.md) §4 e §7.
> Inspiração no MES4: `tblCustomer`/`tblOrder` (pedidos), `tblBuffer`/
> `tblBufferPos` (endereços), `tblAutomaticOrder` (reposição mín./máx.) e
> `tblMachineReport` (histórico de estado do posto → OEE). Este documento é o
> **contrato** entre quatro sessões que trabalham em paralelo.

Convenções de sempre: corpos form-urlencoded; números de fora só por
`parse_int`/`parse_number`/`form::numero` (`to_int` aborta o processo); sem
atribuição a campo de struct (reconstruir); datas em ms (não há calendário na
linguagem, L-12) — prazos chegam como `prazo_dias`.

## Já pronto no `main` (base comum)

Eventos de etapa enriquecidos e evento novo `producao.etapa_apontada` (a cada
apontamento, em qualquer etapa). Dados de todos os `producao.etapa_*`:

```
op, produto, etapa, posto, operacao, tempo_min (min/unidade), entrada,
boas, refugo (acumulados da etapa), delta_boas, delta_refugo (desta ação),
inicio, fim (ms; 0 se não houver), operador, motivo, status
```

E `maquina.parada` / `maquina.liberada` levam `parada, posto, categoria,
motivo, inicio, fim` (ms; `fim=0` enquanto aberta) e `minutos` — o `inicio`
é o real, inclusive em parada retroativa (`ha_minutos`).

## A. Comercial — módulo novo `pedidos` (`/api/pedidos`)

Depende de `cadastros` e `producao`. Escrita: admin, comercial, pcp.

| Rota | Corpo/consulta | Resposta/efeito |
|---|---|---|
| `GET /clientes` | — | `[{codigo, nome, documento, contato, email, telefone, endereco}]` |
| `POST /clientes` | os campos acima (`codigo` e `nome` obrigatórios) | o cliente |
| `GET /pedidos[?status=]` | — | lista, mais novos primeiro |
| `GET /pedido?id=N` | — | `{id, cliente, itens:[{produto, quantidade, saldo, ops:[n]}], status, criado_em, entrega_prevista, atrasado, ops:[n], expedido_em}` |
| `POST /pedidos` | `cliente, itens="PRODUTO:qtd;...", prazo_dias, observacao` | cria ABERTO; `entrega_prevista = agora + prazo_dias` |
| `POST /gerar_ops?id=N` | `posto` (opcional) | para cada item, OP da **falta** (`quantidade − saldo livre`); nenhuma se já houver saldo → EM_PRODUCAO |
| `POST /expedir?id=N` | — | confere saldo de todos os itens (409 se faltar) → EXPEDIDO e publica `pedido.expedido` |
| `POST /cancelar?id=N` | `motivo` | → CANCELADO (não cancela OPs) |

Estados: `ABERTO → EM_PRODUCAO → PRONTO → EXPEDIDO`, e `CANCELADO`. PRONTO
quando todas as OPs do pedido concluíram (assina `op.concluida`) **ou** o
saldo já cobre todos os itens. `atrasado` = não expedido e passou da entrega.

Produção (alteração pequena, desta sessão): a OP ganha `origem` (ex.:
`PED-12`, vazio para OP manual); `pub fn criar_op(string produto, number
quantidade, string posto, string origem) -> int` (0 em erro) usada por
`pedidos`; os eventos `op.*` passam a levar `&origem=`.

Eventos: `pedido.criado`, `pedido.ops_geradas`, `pedido.pronto`,
`pedido.expedido` (`pedido, cliente, itens="PRODUTO:qtd;..."`),
`pedido.cancelado`.

## B. Estoque endereçado e reposição — `estoque` (`/api/estoque`)

| Rota | Corpo/consulta | Resposta/efeito |
|---|---|---|
| `GET /enderecos` | — | `[{codigo, descricao, tipo, posto}]`; `tipo` ∈ ALMOXARIFADO, LINHA, EXPEDICAO, QUARENTENA |
| `POST /enderecos` | `codigo, descricao, tipo, posto` (posto só para LINHA) | o endereço |
| `GET /saldos` | — | **inalterado**: `{produto: saldo_total}` |
| `GET /saldos?produto=X` | — | `{produto, saldo, por_endereco:{END: qtd}}` |
| `GET /posicoes[?endereco=]` | — | `[{endereco, produto, quantidade}]` (só ≠ 0) |
| `POST /entrada` | `produto, quantidade, origem, endereco` (padrão `GERAL`) | como hoje + endereço |
| `POST /transferir` | `produto, de, para, quantidade` | movimento TRANSFERENCIA (saída + entrada) |
| `POST /ajuste` | `produto, saldo, motivo, endereco` | como hoje, por endereço |
| `GET /reposicao` | — | `[{produto, minimo, maximo, tipo, endereco}]`; `tipo` ∈ PRODUZIR, COMPRAR |
| `POST /reposicao` | `produto, minimo, maximo, tipo, endereco` | a regra (`maximo > minimo ≥ 0`) |
| `GET /sugestoes` | — | `[{produto, saldo, minimo, maximo, quantidade_sugerida, tipo}]` para cada regra com saldo < mínimo |

Regras: o endereço `GERAL` existe sempre. O backflush consome do endereço
LINHA do posto da etapa, se houver, senão do `GERAL`; a entrada de produção vai
para o `GERAL` (ou para o endereço LINHA do posto da última etapa). Movimentos
ganham `endereco`. Saldo negativo continua permitido e publica
`estoque.negativo`. Ao cruzar abaixo do mínimo publica `estoque.abaixo_minimo`
(`produto, saldo, minimo, sugerido, tipo`). Assina `pedido.expedido` → saída
EXPEDICAO de cada item (do endereço EXPEDICAO se tiver saldo, senão `GERAL`).
Dados v0.2 (saldo só por produto) migram na leitura para `GERAL`.

## C. Histórico do posto e OEE — módulo novo `indicadores` (`/api/indicadores`)

Somente leitura pela API; assina `maquina.*` e `producao.etapa_*`; depende de
`cadastros`. Não importa produção nem manutenção — tudo vem dos eventos.

| Rota | Consulta | Resposta |
|---|---|---|
| `GET /estados?posto=X&horas=8` | `posto` opcional | `[{posto, estado, inicio, fim, motivo}]` — `estado` ∈ OPERANDO, PARADO, OCIOSO; `fim=0` = em curso |
| `GET /oee?horas=8` | — | `{janela_ms, linha:{disponibilidade, desempenho, qualidade, oee}, postos:[{posto, disponibilidade, desempenho, qualidade, oee, min_operando, min_parado, min_ocioso, boas, refugo}]}` (frações 0..1) |
| `GET /oee/serie?posto=X&horas=24&passo_min=60` | `posto` opcional (vazio = linha) | `[{inicio, fim, disponibilidade, desempenho, qualidade, oee}]` |

Definições (escrever no código e no doc):
- **Disponibilidade** = (janela − parado) / janela.
- **Desempenho** = Σ(`tempo_min` × (`delta_boas` + `delta_refugo`)) / minutos
  OPERANDO, limitado a 1 (0 se não operou).
- **Qualidade** = Σ`delta_boas` / Σ(`delta_boas` + `delta_refugo`) (1 se nada).
- **OEE** = produto dos três.
- Estado: PARADO enquanto houver parada aberta (prevalece); OPERANDO enquanto
  houver etapa EM_EXECUCAO no posto; senão OCIOSO.

Persistência em `dados/indicadores/` (segmentos de estado e apontamentos).
Limite honesto: após reinício, etapas que já estavam em execução não são
reanunciadas pela produção — o posto aparece OCIOSO até o próximo evento
(documentar). Eventos: `indicadores.oee_baixo` quando o OEE da linha na janela
cair abaixo de `EMP_OEE_ALERTA` (padrão 0.6), no máximo um por hora.

## D. Interface — `painel.cryo`

Contra este contrato: aba **Pedidos** (lista com atraso, novo pedido com
itens, gerar OPs, expedir, cancelar; detalhe com itens, saldo e OPs ligadas),
**Clientes** em Cadastros, **Estoque** com endereços, saldo por endereço,
transferência, regras de reposição e **sugestões com "Criar OP"** (usa
`POST /api/producao/ordens`), aba **OEE** (cartões por posto com D × Desemp ×
Q, OEE da linha, linha do tempo de estados por posto, série por hora em SVG).
Visual Forja; documentar componentes novos em `DESIGN_SYSTEM.md`.

## Divisão de arquivos (quem pode editar o quê)

| Sessão | Branch / worktree | Arquivos |
|---|---|---|
| A Comercial | `fase2-comercial` / `EMP-wt-comercial` | `src/modulos/pedidos/**`, `src/modulos/producao/producao.cryo` (só `origem`, `criar_op`, eventos `op.*`), `src/modulos/catalogo.cryo` (+1 linha), `tools/demo_comercial.cryo`, `tests/test_pedidos.cryo`, `docs/fase2/comercial.md` |
| B Estoque | `fase2-estoque` / `EMP-wt-estoque` | `src/modulos/estoque/**`, `tools/demo_estoque.cryo`, `tests/test_estoque.cryo`, `docs/fase2/estoque.md` |
| C OEE | `fase2-oee` / `EMP-wt-oee` | `src/modulos/indicadores/**`, `src/modulos/catalogo.cryo` (+1 linha), `tools/demo_oee.cryo`, `tests/test_oee.cryo`, `docs/fase2/oee.md` |
| D Interface | `fase2-ui` / `EMP-wt-ui2` | `src/nucleo/painel.cryo`, `src/nucleo/terminal.cryo`, `docs/DESIGN_SYSTEM.md`, `docs/fase2/ui.md`, `docs/screenshots/**` |

Ninguém edita `CHANGELOG.md`, `README.md`, `ESCOPO.md`, `build.ps1` nem
`tools/demo.cryo`: cada sessão descreve o que fez em `docs/fase2/<area>.md`
(rotas, decisões, verificação, o que ficou sem verificar) e a coordenadora
consolida ao juntar. Testes novos entram com o nome acima; a coordenadora os
liga no `build.ps1`.

## Convivência na mesma máquina

- **Um build por vez** (a máquina não tem page file): antes de rodar
  `build.ps1` ou `pyro.py build`, crie a pasta
  `C:\Users\senai\Desktop\Projetos\Pyro_Cryo\.emp-build-lock` (`mkdir` falha se
  já existir → espere 30 s e tente de novo) e apague-a ao terminar, mesmo em
  erro. `WinError 1455` = rode de novo sozinho.
- **Portas**: A 8191, B 8192, C 8193, D 8194 (8080 é do usuário). Sempre
  `127.0.0.1`, nunca `localhost`. Pare os `emp.exe` que você subir.
- Commits só no seu branch, nunca em `main`. Não use `git stash` sem tag
  (a pilha é compartilhada entre worktrees).
- A interface faz `git merge` dos branches A, B e C no próprio worktree quando
  eles avisarem que a API está pronta, para verificar de ponta a ponta.
