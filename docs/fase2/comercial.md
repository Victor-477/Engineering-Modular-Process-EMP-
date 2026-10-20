# Fase 2 — A. Comercial (módulo `pedidos`)

Branch `fase2-comercial`. Contrato: [../FASE2.md](../FASE2.md) §A.
Inspiração: MES4 `tblCustomer` / `tblOrder`.

## Arquivos

| Arquivo | O quê |
|---|---|
| `src/modulos/pedidos/pedidos.cryo` | módulo novo, prefixo `/api/pedidos` |
| `src/modulos/catalogo.cryo` | import + `pedidos::descritor()` na lista |
| `src/modulos/producao/producao.cryo` | `origem` na OP, `criar_op`, `&origem=` nos `op.*` (versão 1.2.0) |
| `tests/test_pedidos.cryo` | `test fn`: regras puras + fluxo completo pelos módulos |
| `tools/demo_comercial.cryo` | carga comercial, roda depois de `tools/demo.cryo` |

## Rotas (`/api/pedidos`)

Escrita: `admin`, `comercial`, `pcp`. Corpos form-urlencoded.

| Rota | Corpo/consulta | Resposta/efeito |
|---|---|---|
| `GET /clientes` | — | `[{codigo, nome, documento, contato, email, telefone, endereco}]` por código |
| `POST /clientes` | os campos acima | 201 o cliente; 400 sem `codigo` ou `nome`. Mesmo código = atualiza. Código em maiúsculas |
| `GET /pedidos[?status=]` | — | lista, mais novos primeiro (cada item igual ao `GET /pedido`) |
| `GET /pedido?id=N` | — | ver abaixo; 404 se não existe (id não numérico também) |
| `POST /pedidos` | `cliente, itens="PRODUTO:qtd;...", prazo_dias, observacao` | 201 pedido ABERTO; 422 cliente/produto inexistente, matéria-prima, item ou prazo inválido |
| `POST /gerar_ops?id=N` | `posto` (opcional; corpo ou consulta) | 200 pedido; OP da falta por item; 409 se não estiver ABERTO; 422 posto inexistente |
| `POST /expedir?id=N` | — | 200 EXPEDIDO + `pedido.expedido`; 409 `{"erro", "faltas":[{produto, quantidade, saldo}]}` se faltar saldo; 409 se já EXPEDIDO/CANCELADO |
| `POST /cancelar?id=N` | `motivo` (opcional) | 200 CANCELADO; 409 se EXPEDIDO/CANCELADO. As OPs não são canceladas |

Pedido devolvido:

```
{id, cliente, nome_cliente, itens:[{produto, quantidade, saldo, ops:[n]}],
 status, criado_em, entrega_prevista, atrasado, ops:[n], expedido_em,
 observacao, motivo, atualizado_em}
```

`saldo` do item = **saldo livre** para este pedido (nunca negativo).
`ops` no topo = todas as OPs dos itens. Datas em ms; `expedido_em` 0
enquanto não expedido. `nome_cliente`, `observacao`, `motivo` (do
cancelamento) e `atualizado_em` são acréscimos ao contrato.

Estados: `ABERTO → EM_PRODUCAO → PRONTO → EXPEDIDO`, e `CANCELADO` a partir
de qualquer um dos três primeiros.

## Eventos

Publicados (todos com `pedido, cliente, itens="PRODUTO:qtd;..."`):

| Evento | Extra |
|---|---|
| `pedido.criado` | `entrega_prevista` |
| `pedido.ops_geradas` | `ops="3,4"` (vazio se o saldo cobriu tudo) |
| `pedido.pronto` | `por=ops` ou `por=saldo` |
| `pedido.expedido` | — (o estoque da fase 2 baixa os itens) |
| `pedido.cancelado` | `motivo` |

Assinados: `op.*` (concluída/cancelada das OPs do pedido),
`producao.apontada` (quanto cada OP do pedido já produziu) e
`estoque.movimentado` (um pedido EM_PRODUCAO fica PRONTO quando o saldo
passa a cobrir).

## Produção (alteração pequena)

- `OrdemProducao` ganha `string origem` no **fim** da struct: `"PED-12"`
  quando veio de um pedido, vazio para OP manual. `POST /ordens` aceita
  `origem=` opcional (para a interface marcar, p.ex., uma OP de reposição).
- `pub fn criar_op(string produto, number quantidade, string posto, string origem) -> int`:
  mesmas validações do `POST /ordens` (produto cadastrado e não MP, posto
  cadastrado se informado, quantidade > 0); devolve o id ou **0** em erro.
  Publica `op.criada` como a rota.
- `op.criada/liberada/cancelada/concluida` levam `&origem=`.
- **OPs antigas** (v0.2/fase 1, sem `origem` no JSON): `json_decode` deixaria
  o campo nulo e o primeiro uso abortaria; `_ler` acrescenta `"origem":""`
  ao texto antes de decodificar. A OP só é regravada na próxima ação.
  Testado com uma OP no formato antigo gravada antes do `iniciar`.

## Decisões

- **Saldo livre** = `estoque::saldo(produto)` − reservas dos OUTROS pedidos:
  PRONTO reserva a quantidade inteira do item; EM_PRODUCAO reserva
  `quantidade − pendente das suas OPs abertas` (pendente = planejada −
  boas já apontadas, via `producao.apontada`); ABERTO, EXPEDIDO e
  CANCELADO não reservam. Sem isso dois pedidos contariam com a mesma
  peça da prateleira. Usado em `gerar_ops` (falta), `expedir` e no
  `saldo` do item.
- **Falta** = `quantidade − saldo livre` (≥ 0). Item sem falta não gera OP;
  se nenhum item gerar, o pedido passa por EM_PRODUCAO e fica PRONTO na
  mesma requisição (`por=saldo`).
- **PRONTO**: todas as OPs do pedido concluídas (`op.concluida`) — mesmo
  que o refugo deixe faltar peça; nesse caso o `expedir` dá 409 — **ou** o
  saldo livre cobre todos os itens (conferido em `gerar_ops`, em
  `op.concluida` e em `estoque.movimentado` do produto). OP cancelada não
  conta como concluída: o pedido só fica PRONTO pelo saldo.
- **Expedir** aceita ABERTO, EM_PRODUCAO e PRONTO desde que o saldo livre
  cubra todos os itens (o 409 de “sem saldo” vale para qualquer um deles).
- **`depende`** inclui `estoque` além de `cadastros` e `producao`: o saldo vem
  de `estoque::saldo` (import direto, como produção importa cadastros).
  A sessão B foi avisada para manter `pub fn saldo(string) -> number` (saldo
  total) — nota em side-session-notes `fase2-comercial-para-estoque.md`.
- **Itens**: produto em maiúsculas, quantidade com ponto ou vírgula, só por
  `form::eh_numero` + `parse_number` (nunca `to_number`). O mesmo produto
  repetido soma. Matéria-prima é recusada (422): o pedido é de SA/PA, que
  podem virar OP.
- **`prazo_dias`** vazio = 7 dias; não numérico ou negativo = 422; aceita
  fração (`0.5`). `entrega_prevista = agora + prazo_dias × 86 400 000`.
- **`atrasado`** = status não EXPEDIDO/CANCELADO e `agora > entrega_prevista`
  (calculado na leitura, não gravado).
- **`gerar_ops`** não libera as OPs (fica com o PCP). Se `criar_op` falhar no
  meio, as OPs já criadas ficam ligadas ao pedido, que continua ABERTO (500).
- **Persistência** em `dados/pedidos/`: `clientes.json`, `pedidos.json`,
  `ops.json` (OP → pedido, quantidade, produzido, status).

## Verificação (2026-10-20, neste worktree)

- `powershell -ExecutionPolicy Bypass -File build.ps1`: passa (núcleo 7/7,
  eventos 2/2, etapas 15/15, `emp.exe` e `qualidade.exe` gerados). O
  `test_pedidos.cryo` ainda **não** está no `build.ps1` (a coordenadora liga).
- `python ..\Burnout\cryoc.py test tests/test_pedidos.cryo --backend pyro`:
  5/5. Além das regras puras, `fluxo_pedido_completo` sobe cadastros,
  roteiros, produção, estoque e pedidos pelo `registro` num diretório novo
  em `build/` e passa por: validações 400/422, falta (50 − 30 = OP de 20),
  reserva entre pedidos, gerar duas vezes (409), PRONTO por OPs concluídas,
  expedir (200, depois 409), cancelar expedido (409), PRONTO pelo saldo sem
  OP, cancelar com motivo, filtro `?status=`, `id=abc` → 404, OP manual sem
  origem, `criar_op` inválido → 0, e uma **OP no formato da fase 1** (sem
  `origem`) gravada antes do `iniciar`: lida, listada, cancelada e regravada.
  Uma asserção trocada de propósito fez o teste falhar (o teste morde).
- HTTP com `build/emp.exe` em `127.0.0.1:8191`, modo dev, dados novos,
  `tools/demo.cryo` + `tools/demo_comercial.cryo` (0 falha cada):
  - pedido 1 (SUP-02:150; SUP-01:300, saldos 110 e 250): ABERTO →
    `gerar_ops` → EM_PRODUCAO com OP 7 (SUP-02, 40) e OP 8 (SUP-01, 50),
    ambas `origem=PED-1` → OPs executadas etapa por etapa (SUP-02 nas 4
    etapas do roteiro) → PRONTO (`pedido.pronto … por=ops`) → EXPEDIDO
    (`pedido.expedido pedido=1&cliente=HORIZONTE&itens=SUP-02:150;SUP-01:300`);
  - pedido 2 (SUP-02:400): `POST /expedir` → **409** com `faltas`; OP 9 da
    falta (400 − 150 livres = 250);
  - pedido 3 (BASE-SUP:30, saldo 37): PRONTO sem OP; pedido 4 (prazo 0):
    ABERTO e `atrasado:true`; pedido 5: CANCELADO com motivo;
  - eventos `op.*` conferidos com `&origem=PED-n`.
- **Reinício**: `emp.exe` parado e subido de novo nos mesmos dados; o pedido 2
  continuou EM_PRODUCAO, a OP 9 foi liberada e apontada pela rota antiga
  `/apontar` (4 etapas) e o pedido foi a PRONTO e EXPEDIDO — o vínculo
  OP → pedido (`ops.json`) sobrevive ao reinício.
- Painel `/` responde 200 com o módulo novo.

## Não verificado / limites

- Sem o estoque da fase 2 (sessão B) o `pedido.expedido` não baixa o saldo:
  neste branch, depois de expedir, o saldo continua e só a reserva some.
  A baixa é responsabilidade do `estoque` após o merge.
- O merge com `fase2-oee` mexe nas mesmas linhas de `catalogo.cryo` (+1
  import e +1 descritor de cada lado): conflito trivial, manter as duas.
- `tools/demo_comercial.cryo` encerra a parada aberta da SOLDA-01 deixada
  pela `demo.cryo` (a OP do SUP-02 do pedido 1 passa por ela).
- Não verificado: o fluxo com o `estoque` da fase 2 (endereços, baixa na
  expedição), com a interface da sessão D e com tokens/perfil `comercial`
  de verdade (só modo dev). Nem os backends `go`/`node`: só Pyro VM e o
  `.exe` AOT.
- A demo aponta todas as peças como boas; refugo numa OP de pedido deixa o
  pedido PRONTO (OPs concluídas) com saldo curto — o `expedir` dá 409, por
  projeto; isso está coberto só pela regra, não por um teste HTTP.
- Não há `pedido.atrasado` como evento (o contrato não pede); o atraso é
  só um campo calculado.
