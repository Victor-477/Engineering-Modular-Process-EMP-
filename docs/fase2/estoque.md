# Fase 2 · B — Estoque endereçado e reposição

> Frente B do contrato [FASE2.md](../FASE2.md). Branch `fase2-estoque`.
> Inspiração no MES4: `tblBuffer`/`tblBufferPos` (endereços e posições) e
> `tblAutomaticOrder` (reposição mín./máx.).

Arquivos: `src/modulos/estoque/estoque.cryo` (módulo, estado, rotas, eventos),
`src/modulos/estoque/regras.cryo` (regras puras: validação, repartição,
leitura de itens, mínimo/sugestão), `tests/test_estoque.cryo`,
`tools/demo_estoque.cryo`. Nenhum outro arquivo foi tocado; o módulo continua
com `depende: ["cadastros"]` e não importa produção nem pedidos. Versão do
módulo: 1.1.0 (só acréscimos; `GET /saldos` inalterado).

## Rotas (`/api/estoque`)

Corpos form-urlencoded; números só por `form::numero`. Códigos de produto e de
endereço são passados para maiúsculas.

| Rota | Corpo/consulta | Resposta/efeito |
|---|---|---|
| `GET /saldos` | — | **inalterado**: `{produto: "saldo_total"}` (valores em texto, como na v0.2) |
| `GET /saldos?produto=X` | — | `{produto, saldo, por_endereco:{END: qtd}}` — só endereços com saldo ≠ 0 |
| `GET /enderecos` | — | `[{codigo, descricao, posto, tipo}]` por código; `GERAL` sempre presente |
| `POST /enderecos` | `codigo, descricao, tipo, posto` | 201 o endereço (cria ou regrava). 422 tipo inválido, LINHA sem posto, posto não cadastrado, código com espaço ou `\|`; 409 `GERAL` ou segundo LINHA para o mesmo posto |
| `GET /posicoes[?endereco=]` | — | `[{endereco, produto, quantidade}]` (só ≠ 0), por endereço e produto |
| `GET /movimentos` | — | como antes + `endereco` e `saldo_endereco`; movimentos da v0.2 saem com `"endereco":"GERAL"` |
| `POST /entrada` | `produto, quantidade, origem, endereco` (padrão `GERAL`) | 201 `{produto, saldo, endereco, saldo_endereco}`; 422 endereço inexistente |
| `POST /ajuste` | `produto, saldo, motivo, endereco` (padrão `GERAL`) | 200 idem; o `saldo` é o alvo **naquele endereço** |
| `POST /transferir` | `produto, de, para, quantidade` | 201 `{produto, de, para, quantidade, saldo_de, saldo_para, saldo}`; dois movimentos `TRANSFERENCIA` (−de, +para). 409 se `de` não tem a quantidade; 422 endereços iguais/inexistentes |
| `GET /reposicao` | — | `[{endereco, maximo, minimo, produto, tipo}]` |
| `POST /reposicao` | `produto, minimo, maximo, tipo, endereco` | 201 a regra; uma regra por produto (regravar substitui). `maximo > minimo ≥ 0`; `tipo` padrão: COMPRAR para MP, PRODUZIR para o resto; `endereco` vazio = vigia o saldo total |
| `GET /sugestoes` | — | `[{produto, saldo, minimo, maximo, quantidade_sugerida, tipo, endereco}]` para cada regra com saldo < mínimo; `quantidade_sugerida = maximo − saldo` |

Tipos de endereço: `ALMOXARIFADO`, `LINHA` (exige `posto`), `EXPEDICAO`,
`QUARENTENA`. `GERAL` é um ALMOXARIFADO fixo (não pode ser regravado).

## Eventos

Publicados:

- `estoque.movimentado` — `produto, quantidade, saldo` (total) + **`endereco, saldo_endereco`**.
- `estoque.negativo` — quando o saldo **do endereço** movimentado fica < 0:
  `produto, saldo` (o do endereço), `endereco, saldo_total`. Com só o `GERAL`
  (v0.2) é o mesmo que antes.
- `estoque.abaixo_minimo` — `produto, saldo, minimo, sugerido, tipo` (+ `maximo,
  endereco`), quando uma operação leva o saldo vigiado de ≥ mínimo para < mínimo.
  Só no cruzamento: enquanto continua abaixo, não repete.
- `estoque.falta` — inalterado (op.liberada, saldo total).

Assinados: `producao.apontada`, `op.liberada`, **`pedido.expedido`**.

## Decisões

1. **Modelo.** Coleção nova `posicoes.json` (`"ENDERECO|PRODUTO" → saldo`) é a
   verdade; `saldos.json` (total por produto) continua gravado no formato da v0.2.
   O total é somado incrementalmente (`saldo + qtd`), igual à v0.2 — assim os
   totais não mudam nem na última casa decimal. Ordem de gravação: posições,
   totais, histórico (sem transação, L-02). Ao iniciar, um total que diverge da
   soma das posições em mais de 1e-6 é recalculado.
2. **Migração v0.2 na leitura.** Sem `posicoes.json`, cada saldo de
   `saldos.json` vira posição no `GERAL`, só em memória; o primeiro movimento
   grava `posicoes.json`. `enderecos.json` ausente → só o `GERAL`.
3. **Backflush.** Consome cada componente primeiro do endereço LINHA do posto
   do `producao.apontada` (o posto da última etapa, onde a produção publica o
   evento) **até o saldo positivo que ele tiver**; o resto sai do `GERAL`, que
   pode ficar negativo. Sem LINHA para o posto (ou sem saldo nela) é exatamente
   o movimento único da v0.2. Preferimos isso a deixar a LINHA negativa: o
   material que não estava na linha veio, de fato, do estoque geral.
4. **Entrada de produção no `GERAL`.** O contrato permitia GERAL ou a LINHA do
   posto da última etapa; escolhemos GERAL porque é dele que a expedição e o
   saldo livre do pedido (frente A) leem — produto acabado parado num endereço
   de linha faria a expedição tirar do GERAL e deixá-lo negativo.
5. **Um endereço LINHA por posto** (409 no segundo), para o backflush não ter de
   escolher.
6. **Transferência exige saldo na origem** (409): não se tira de uma prateleira
   o que não está nela. Entrada/ajuste/backflush/expedição continuam podendo
   deixar saldo negativo, como antes.
7. **`pedido.expedido`.** `itens="PRODUTO:qtd;..."` (vírgula decimal aceita; item
   malformado ou ≤ 0 é ignorado). Para cada item, sai dos endereços EXPEDICAO
   (em ordem de código) até o saldo deles; o resto do `GERAL`. Movimento
   `EXPEDICAO`, origem `pedido <n>`.
8. **Reposição.** Uma regra por produto. `endereco` vazio vigia o total;
   preenchido, só aquele endereço. O cruzamento é medido sobre a operação
   inteira (a transferência, que são dois movimentos, não "cruza" o total).
   Criar uma regra com o saldo já abaixo não publica evento (não houve
   cruzamento), mas a sugestão aparece em `/sugestoes`.

## Verificação

- `build.ps1` no worktree: passou (núcleo 7/7, eventos 2/2, etapas 15/15,
  `emp.exe` e `qualidade.exe` gerados). `tests/test_estoque.cryo` ainda não está
  ligado no `build.ps1` (a coordenadora liga).
- `python ../Burnout/cryoc.py test tests/test_estoque.cryo --backend pyro`:
  **10 passed, 0 failed** (regras puras; migração v0.2; endereços, entrada,
  transferência, ajuste e reinício; backflush da LINHA com resto do GERAL e
  negativo; reposição com cruzamento, sem repetição, transferência e regra por
  endereço; `pedido.expedido` simulado entregando o evento ao módulo). Uma
  asserção alterada de propósito fez a suíte falhar (1 failed), conferindo que
  os testes mordem.
- HTTP, `emp.exe` na 8192 em modo dev, dados limpos:
  - `tools/demo.cryo` (0 falha) e depois `GET /saldos` **byte a byte igual** ao
    do `emp.exe` compilado do commit base `a9b9aff` com a mesma demo:
    `{"ACO-CH2":"506.45","BASE-SUP":"87","BUCHA-08":"1020","PARAF-M6":"5014","SUP-01":"250","SUP-02":"110","TINTA-PO":"46.41"}`.
  - `tools/demo_estoque.cryo`: **0 falha(s)**. Endereços criados (segundo LINHA
    no MONT-01 recusado); entrada no ALMOX-MP soma no total; transferência de
    1000 PARAF-M6 GERAL→LINHA-MONT sem mudar o total
    (`{"produto":"PARAF-M6","saldo":5014,"por_endereco":{"GERAL":4014,"LINHA-MONT":1000}}`);
    transferência sem saldo recusada; soma das posições = total para todos os
    produtos (três vezes ao longo da demo); OP de 20 SUP-01 no MONT-01 →
    movimentos `CONSUMO` de −40 PARAF-M6 e −0,6 TINTA-PO com `endereco:"LINHA-MONT"`
    e −20 BASE-SUP no `GERAL`; PARAF-M6 cruzou o mínimo → sugestão
    `{"produto":"PARAF-M6","saldo":4974,"minimo":5004,"maximo":8000,"quantidade_sugerida":3026,"tipo":"COMPRAR","endereco":""}`
    e evento `estoque.abaixo_minimo` (`produto=PARAF-M6&saldo=4974&minimo=5004&sugerido=3026&tipo=COMPRAR&maximo=8000&endereco=`).
  - Migração: o `emp.exe` novo subiu sobre o diretório de dados gravado pelo
    `emp.exe` da base (v0.2, só `saldos.json` e `movimentos.json`):
    `GET /saldos` idêntico, tudo em `GERAL` em `/posicoes`, os 21 movimentos
    antigos saem com `endereco`.

## Não verificado

- `pedido.expedido` publicado de verdade pelo módulo `pedidos` (frente A): só
  com o evento simulado no teste. O formato seguido é o do contrato
  (`pedido, cliente, itens="PRODUTO:qtd;..."`).
- Entrega repetida do mesmo `pedido.expedido`: o barramento não reentrega, então
  não há proteção contra baixa dupla.
- Painel: as telas novas são da frente D; o painel atual continua lendo
  `GET /saldos` e `/movimentos`, cujos formatos foram mantidos (não abri o
  navegador).
- Reinício com gravação interrompida no meio de um movimento (reconciliação dos
  totais): coberto só por leitura de código.

## Limites honestos

- O backflush acontece no `producao.apontada` (última etapa), então todos os
  componentes são consumidos do endereço do posto da **última** etapa — o aço do
  SUP-02, estampado na PRENSA-02, sai da linha da MONT-01 se houver. A estrutura
  não diz em que etapa cada componente entra.
- `op.liberada` confere a falta pelo saldo **total**, não pelo endereço de onde o
  backflush vai tirar.
- `/sugestoes` não desconta OPs já abertas nem compras: depois de "Criar OP" a
  sugestão continua até a produção entrar.
- Não há rota para apagar endereço ou regra.
