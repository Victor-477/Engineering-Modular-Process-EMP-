# Fase 2 — D. Interface (`painel.cryo`)

Branch `fase2-ui`. Contrato: [../FASE2.md](../FASE2.md) §D, mais as rotas de §A, §B e §C.
Componentes novos documentados em [../DESIGN_SYSTEM.md](../DESIGN_SYSTEM.md) (versão 1.2).
O branch contém os merges de `main` (cb242c1), `fase2-comercial` (a1cc548),
`fase2-estoque` (16898c0) e `fase2-oee` (361d17f). O único conflito foi
`src/modulos/catalogo.cryo` (um import e um descritor de cada lado): ficaram os dois.

## Arquivos

Só `src/nucleo/painel.cryo`, `docs/DESIGN_SYSTEM.md`, este arquivo e
`docs/screenshots/14-…` a `21-…`. O `terminal.cryo` não precisou mudar.

## O que entrou

| Tela | Endereço | Conteúdo |
|---|---|---|
| **Pedidos** (`data-mod="pedidos"`) | `/#pedidos` | Pedidos por estado (barra de distribuição + "N atrasado(s)", que filtra a lista), novo pedido com várias linhas de item, lista em moldura (cliente, itens, estado + **sinal de atraso**, entrega, cobertura em LED, OPs com link, ações Gerar OPs / Expedir / Cancelar) |
| Detalhe do pedido | `/#pedidos/N` | Cabeçalho (cliente, estado, atraso, criado, entrega, expedido, cobertura), itens com saldo livre, falta e OPs do item, **OPs ligadas** (estado, etapa, progresso; link para `/#ordens/N`), ações com posto opcional, motivo do cancelamento; o 409 do expedir lista as faltas |
| **Clientes** (Cadastros) | `/#cadastros/clientes` | Formulário (código, nome, documento, contato, e-mail, telefone, endereço) e lista com pedidos em aberto por cliente |
| **Estoque** — saldos | `/#estoque` | Como antes, com **endereço** na entrada, no ajuste e nos movimentos; o código do produto abre o detalhe |
| Endereços e posições | `/#estoque/posicoes` | Cartões de endereço (clique filtra as posições), transferência, novo endereço (posto só para LINHA), posições em moldura com filtro por endereço |
| Reposição | `/#estoque/reposicao` | Sugestões (saldo < mínimo) com **Criar OP** (`POST /api/producao/ordens`, `origem=REPOSICAO`) para PRODUZIR e **Registrar entrada** para COMPRAR; regras com a faixa mín./máx. e o saldo vigiado (do endereço da regra ou o total) |
| Detalhe do produto | `/#estoque/produto/X` | Saldo total, saldo por endereço (`GET /saldos?produto=X`), faixa de reposição, últimos movimentos |
| **OEE** (`data-mod="indicadores"`) | `/#oee`, `/#oee/24` | Seletor 8 h / 24 h; OEE da linha em destaque (anel + `D × Desemp × Q = OEE`); cartões por posto; linha do tempo de estados por posto (SVG); OEE por hora em colunas SVG desenhadas no painel, com dica e "ver em tabela"; seletor linha/posto |
| Visão geral | `/#geral` | KPI "OEE da linha" (8 h) quando `indicadores` está ativo |
| Menu / sino | — | Contador de pedidos atrasados em Pedidos, de sugestões em Estoque (e na aba Reposição); o sino soma paradas, NCs e pedidos atrasados |

Pedidos e Clientes só aparecem com o módulo `pedidos` ativo; OEE e o KPI, com `indicadores`.
As rotas novas do estoque são lidas com fallback (`[]`), então o painel continua funcionando
com um estoque da fase 1.

## Decisões

- **Estados do pedido**: aberto = `wait`, em produção = `act`, pronto = `ok`, expedido = `skip`
  com ícone de caminhão (fica fora do caminho), cancelado = `bad` com ✕. O atraso é um sinal à
  parte (relógio + "atrasado N h/d"), porque um pedido pode estar atrasado em qualquer estado aberto.
- **Expedir** aparece como ação principal só no PRONTO; no detalhe ele fica disponível
  (secundário) também em ABERTO/EM_PRODUCAO, como a API aceita quando o saldo livre cobre.
- **Cancelar** pede motivo na UI (na lista por `prompt`, no detalhe num campo), embora a API o aceite vazio.
- **Nível do OEE**: ≥ 85% referência, 60–85% atenção (token novo `--warn-ink`, classe
  `.st-warn`), < 60% o limite do `indicadores.oee_baixo`. Sempre ícone + texto.
- **Gráficos sem biblioteca**: linha do tempo e colunas são SVG montado em JS; as colunas usam
  a largura real do cartão (o texto não escala) e são redesenhadas a cada atualização de 6 s.
- A janela da linha do tempo usa `inicio`/`fim` devolvidos pelo `GET /oee` (relógio do servidor).
- O `painel.cryo` continua uma string por linha; o trecho novo foi escrito como HTML/CSS/JS
  e escapado para Cryo pelo mesmo padrão do arquivo (`\"`, `\\`, `\${`).

## Verificação (2026-10-20, neste worktree, com os quatro merges)

- `build.ps1` (com a pasta-trava): passa — núcleo 7/7, eventos 2/2, etapas 15/15,
  `emp.exe` e `qualidade.exe`. À mão com `cryoc test --backend pyro`: `test_pedidos` 5/5,
  `test_estoque` 10/10, `test_oee` 11/11 (não estão no `build.ps1`; não o editei).
  Depois dos últimos ajustes do painel só o `emp.exe` foi recompilado (`pyro.py build`).
- A página gerada foi conferida a cada mudança: compila em Cryo e o `<script>` passa `node --check`.
- `emp.exe` em `127.0.0.1:8194`, modo dev, dados novos, sem plugins, carregado com
  `tools/demo.cryo` (0 falha), `demo_comercial` (0), `demo_estoque` (2 falhas, ver abaixo) e
  `demo_oee` (0). No navegador embutido, contra a API real:
  - **Pedidos**: criei um pedido com duas linhas (SUP-01 × 40, SUP-02 × 12,5, prazo 3 dias) →
    abriu `/#pedidos/6` ABERTO com saldo e falta por item; **Expedir** → 409, o aviso listou
    "SUP-01 falta 21, SUP-02 falta 12,5"; **Gerar OPs** → EM_PRODUCAO com OP-012 e OP-013
    ligadas (links para o detalhe da OP). Lista com distribuição por estado, PED-004 com
    "atrasado", PED-001 expedido (caminhão), PED-005 cancelado, contador de atrasados no menu.
  - **Clientes**: lista com os três da demo e os pedidos em aberto de cada um.
  - **Estoque**: transferência de 10 PARAF-M6 GERAL → LINHA-MONT (cartão do endereço foi de
    964,4 para 974,4); clique no cartão filtra as posições; **Criar outra OP** na sugestão do
    SUP-01 criou a OP-014 com `quantidade 381` e `origem REPOSICAO`; **Registrar entrada** na
    sugestão do PARAF-M6 (COMPRAR) abriu a entrada com produto e 3.286 preenchidos; detalhe
    `/#estoque/produto/PARAF-M6` com GERAL 3.744 + LINHA-MONT 970 = 4.714.
  - **OEE**: 8 h e 24 h, seis postos, linha do tempo e série; os números batem com
    `GET /api/indicadores/oee` (linha 87,9% × 100% × 97,9% = 86%). KPI na visão geral (86,1%).
  - Sem erro de JavaScript no console (só o 409 esperado do expedir).
- Visual (Edge headless, `--virtual-time-budget`): 1440 px claro, 1024 px, tablet 768 px claro e
  escuro (pedidos, reposição, OEE). Capturas em `docs/screenshots/`:
  14 pedidos · 15 detalhe do pedido · 16 clientes · 17 endereços e posições · 18 reposição ·
  19 detalhe do produto · 20 OEE 8 h · 21 OEE 24 h, tablet em pé, escuro.

## Não verificado / limites

- `demo_estoque.cryo` depois de `demo_comercial.cryo` dá 2 falhas: as duas transferências para
  QUAR-01/EXP-01 pedem saldo que a expedição do pedido 1 já baixou. É interação entre as demos
  (cada uma foi escrita sobre a `demo.cryo` sozinha), não da interface.
- A dica do gráfico por hora foi conferida com um `mouseover` disparado na coluna (mostrou
  "14:58 → 15:58 / OEE 45,3% / disponibilidade 46,3% / desempenho 100% / qualidade 97,9%"),
  não com o mouse de verdade: o navegador embutido estava oculto e não roda animações nem hover
  de forma confiável. Toque no tablet não testado.
- Perfis reais: só modo dev (admin). Com `ERP_TOKENS`, as ações de pedido somem para quem não é
  `admin`/`pcp`/`comercial` pela lógica (`podeVender`), não testado ao vivo.
- Celular (375 px) não foi capturado nesta fase; o layout herda as regras da fase 1.
- O download real do CSV das molduras novas (pedidos, clientes, posições, regras).
- Na série por hora, os dados da demo caem quase todos na última hora (as demos rodam em
  minutos); um dia real de produção não foi visto.
- O gráfico é redesenhado a cada 6 s, então redimensionar a janela leva até 6 s para refletir.
