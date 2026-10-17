# Análise do FactoryViews / MES4 e plano de adaptação para o EMP

> Fonte: instalação local `C:\FestoDidactic\FactoryViews` (Festo MES4 v3,
> MariaDB `mes4`, app Angular em `NodeServer\pages\apps\mes4`, terminais em
> `ManualWorkstations`). Leitura apenas — nada foi copiado: o MES4 é
> **inspiração de UX e de modelo de dados**. A identidade visual continua a do
> sistema de design **Forja** ([DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)).

## 1. O que o MES4 é, em uma frase

Um MES orientado a **roteiro**: cada produto tem um plano de trabalho
(sequência de etapas, cada uma uma **operação** num **recurso**); uma ordem
copia esse plano para cada posição e o executa etapa por etapa, registrando
início e fim planejados e reais. O EMP hoje é orientado a **apontamento**: a OP
tem um posto e recebe quantidades. A maior lição do MES4 para o EMP é passar a
executar **por etapa**.

## 2. Onde estava cada coisa

| Assunto | Caminho | Observação |
|---|---|---|
| Interface principal | `NodeServer\pages\apps\mes4\` | Angular minificado; ajuda em `apps\help\mes4\*.html` |
| Terminal do operador | `ManualWorkstations\` (`workstations.php`, `WorkstationPages\`) | PHP + jQuery, polling de 1 s |
| Painéis/widgets | `NodeServer\pages\apps\dashboard\`, `Samples\queries\*.json` | consultas SQL viram cartões/gráficos |
| Planta (layout) | `Samples\layouts\*.json` | ilhas → estações → pontos de conexão |
| Banco | `MariaDB\data\mes4` (65 tabelas) | colunas reconstruídas do SQL embutido no `MES4v3.exe` |
| Migrações | `MariaDB\migrations\mes4DB\...` | só ALTERs e dados de operações |
| Energia | `MariaDB\data\festoenergydb` | séries agregadas por janela (1 s … 1 dia) |
| `Apache\htdocs`, `InfoPortal` | — | vazios / redirecionamento |

## 3. Modelo de dados do MES4 (resumo)

```
tblCustomer 1─N tblOrder 1─N tblOrderPos 1─N tblStep 1─N tblStepParameter
                                  │ (StepNo = etapa atual, ResourceID, OpNo)
tblParts N─1 tblWorkPlanDef 1─N tblStepDef 1─N tblStepParameterDef
tblStepDef / tblStep ─► tblOperation (OpNo) ─► tblOperationParameter
tblStepDef / tblStep ─► tblResource ◄─N:M─► tblOperation (tblResourceOperation: tempo, energia)
tblResource 1─N tblBuffer 1─N tblBufferPos (PNo, ONo/OPos, Quantity, Booked)
tblAutomaticOrder (PNo, LowLimit, HighLimit) → gera ordens de reposição
tblMachineReport (ResourceID, TimeStamp, modos, erros L0/L1/L2) → disponibilidade/OEE
tblFinOrder/Pos/Step/StepParameter = arquivo das ordens concluídas
```

Fluxo: **criar** (copia `StepDef → Step` para cada posição, calcula início/fim
planejados) → **liberar** (`Enabled`) → **executar** (estação pede tarefa;
`Step.Start`; ao terminar `Step.End`, `ErrorRetVal`, `StaffId`, roda o
"SQL de fim de operação", avança para `NextStepNo` ou `ErrorStepNo`) →
**concluir** (`State=100`) → **arquivar** (`tblFin*`).

Estados: 0 aguardando · 1 ativa · 10 em execução · 99 falha · 100 concluída.

## 4. Mapeamento MES4 → EMP

| MES4 | EMP hoje | EMP proposto | Fase |
|---|---|---|---|
| `tblOperation` + `tblOperationParameter` | — | **Operação**: código, descrição, tipo (MANUAL/AUTOMÁTICA), instrução, parâmetros com limites | 1 |
| `tblWorkPlanDef` + `tblStepDef` | — (só BOM) | **Roteiro** do produto: etapas numeradas (operação, posto, tempo padrão, instrução) | 1 |
| `tblResourceOperation` | — | **Capacidade** posto × operação (tempo padrão) | 1 |
| `tblOrderPos` + `tblStep` | OP com 1 posto | OP com **etapas** copiadas do roteiro na liberação, cada uma com estado, planejado × real, operador, boas/refugo | 1 |
| `tblStepParameter` (medições) | — | Medições por etapa (valor + limites → dentro/fora) | 1 |
| Concorrência via `State/StepNo` | — | `versao` por etapa: 409 "alterado por outra pessoa" | 1 |
| `tblCustomer` + `tblOrder` | — | **Clientes e pedidos**; pedido gera OPs | 2 |
| `tblAutomaticOrder` | alerta de falta | **Reposição** mín./máx. → sugestão de OP/compra | 2 |
| `tblBuffer` + `tblBufferPos` | saldo por produto | **Endereços de estoque** (local, posição) | 2 |
| `tblMachineReport` | paradas (manutenção) | **Histórico de estado do posto** → OEE completo | 2 |
| `tblServiceTimetable` | — | Manutenção **preventiva** (depende de calendário, L-12) | 3 |
| `tblSqlQuery` / queries.json | — | **Relatórios**: cartões com tabela/gráfico e atualização própria | 3 |
| `tblFin*` | — | Arquivo de OPs concluídas | 3 |

Persistência: continua JSON por coleção (L-02). As novas coleções seguem o
mesmo padrão (`dados/<modulo>/<colecao>.json`).

## 5. Padrões de UX que vamos adotar (no visual Forja)

1. **Terminal do operador** (de `ManualWorkstations`): uma página por posto,
   tela cheia, **uma instrução por vez** com título, frase curta e botões
   grandes — *Iniciar* → *Concluir* / *Concluir com erro* / *Reiniciar*. Lista
   de tarefas do posto; "Nenhuma tarefa" quando vazio. Atualiza a cada 1 s
   (2 s depois de uma mensagem); clique desabilita os botões na hora; se o
   estado mudou por outra pessoa, avisa em vez de sobrescrever; selo
   "atualizado às HH:MM:SS" pulsando. Posto parado mostra a parada em destaque.
2. **Estado = ícone + cor**, sempre juntos (nunca só cor): planejada
   (calendário), aguardando (pausa), ativa (play), concluída (check), falha
   (alerta). Cartões de OP com borda esquerda na cor do estado; falha pisca
   uma vez para chamar atenção (respeitando movimento reduzido).
3. **Detalhe da OP como fluxo de etapas**: cada etapa com planejado × real,
   operador e resultado; ações manuais por etapa (iniciar, concluir, erro,
   reiniciar, pular — as duas últimas só para pcp/admin).
4. **Moldura das listas**: barra de ações (Nova, Filtrar, Exportar CSV),
   painel lateral de filtro e aviso "lista filtrada · limpar".
5. **Prioridade do estado do posto**: sem conexão < parado (falha) < setup <
   operando < ocioso — a etiqueta mostra o mais grave.
6. **Páginas de seção com cartões de entrada** (o Forja já tem os blocos por
   módulo no início).

Não adotar: login com só dois papéis (o EMP já tem RBAC por módulo), SQL
livre em cartões (risco de injeção e sem banco — L-02), abrir detalhes em
nova aba.

## 6. Fase 1 — contrato de API (para as sessões trabalharem em paralelo)

Corpos em form-urlencoded, como o resto do EMP. Toda entrada numérica por
`parse_int`/`parse_number`.

### Módulo novo `roteiros` (prefixo `/api/roteiros`, depende de `cadastros`)

| Rota | Corpo/consulta | Resposta |
|---|---|---|
| `GET /operacoes` | — | `[{codigo, descricao, tipo, instrucao, parametros:[{nome, unidade, min, max}]}]` |
| `POST /operacoes` | `codigo, descricao, tipo=MANUAL\|AUTOMATICA, instrucao, parametros="nome:unidade:min:max;..."` | a operação |
| `GET /roteiro?produto=X` | — | `{produto, etapas:[{numero, operacao, posto, tempo_min, instrucao}]}` (vazio se não houver) |
| `POST /etapa` | `produto, numero, operacao, posto, tempo_min, instrucao` | o roteiro (insere ou substitui a etapa `numero`) |
| `POST /remover_etapa?produto=&numero=` | — | o roteiro |
| `GET /capacidades` | — | `[{posto, operacao, tempo_min}]` |
| `POST /capacidade` | `posto, operacao, tempo_min` | a capacidade |

API pública Cryo: `roteiros::etapas(produto) -> Etapa[]`, `roteiros::operacao_json(codigo)`.

### Produção (prefixo `/api/producao`) — acréscimos

Na **liberação**, a OP recebe as etapas do roteiro do produto. Sem roteiro,
recebe uma etapa única `APONTAMENTO` no posto da OP (compatível com hoje).

`GET /ordem?id=N` passa a incluir:

```
"etapas": [{ "numero":10, "operacao":"ESTAMPAR", "descricao":"...", "posto":"PRENSA-01",
             "status":"AGUARDANDO|EM_EXECUCAO|CONCLUIDA|FALHA|PULADA",
             "entrada":400, "boas":0, "refugo":0,
             "inicio_planejado":ms, "fim_planejado":ms, "inicio":ms, "fim":ms,
             "operador":"", "erro":"", "versao":3 }],
"etapa_atual": 10
```

| Rota | Corpo | Efeito |
|---|---|---|
| `GET /fila?posto=X` | — | tarefas do posto: etapa atual de cada OP liberada/em produção cujo posto é X, mais antigas primeiro, com OP, produto, instrução e `versao` |
| `POST /etapa/iniciar?op=&etapa=` | `versao, operador` | AGUARDANDO → EM_EXECUCAO; grava início real |
| `POST /etapa/apontar?op=&etapa=` | `versao, boas, refugo, operador, medicoes="nome=valor;..."` | acumula; conclui sozinha quando `boas+refugo >= entrada` |
| `POST /etapa/concluir?op=&etapa=` | `versao, operador` | conclui com o que já foi apontado; a próxima etapa recebe `entrada = boas` |
| `POST /etapa/erro?op=&etapa=` | `versao, motivo, operador` | → FALHA |
| `POST /etapa/reiniciar?op=&etapa=` | `versao` | FALHA/EM_EXECUCAO → AGUARDANDO (pcp/admin) |
| `POST /etapa/pular?op=&etapa=` | `versao, motivo` | → PULADA (pcp/admin) |

Regras: `versao` diferente → **409 "a tarefa foi alterada por outra pessoa"**;
posto parado → 409 (como hoje); concluir a **última** etapa soma as boas/refugo
ao `produzido/refugo` da OP e publica `producao.apontada` (o backflush e o plugin
de qualidade continuam funcionando). O `POST /apontar?id=` atual continua
aceito e aponta na etapa atual.

Eventos novos: `producao.etapa_iniciada`, `producao.etapa_concluida`,
`producao.etapa_falhou` (dados: `op, etapa, posto, operacao, boas, refugo, operador, motivo`).

### Interface

- `GET /terminal` (sem autenticação para a página; a API continua exigindo
  token): seleção de posto → `/terminal#PRENSA-01`. Arquivo próprio
  `src/nucleo/terminal.cryo`.
- Painel: aba **Roteiros** (operações, roteiro por produto, capacidades);
  detalhe da OP com o fluxo de etapas; ícones de estado; moldura de lista
  com filtro e exportação CSV.

## 7. Fases seguintes

- **Fase 2:** clientes e pedidos; reposição mín./máx.; endereços de estoque;
  histórico de estado do posto e OEE (disponibilidade × desempenho × qualidade,
  usando o tempo padrão das etapas).
- **Fase 3:** manutenção preventiva; relatórios em cartões; arquivo de OPs;
  importação/exportação JSON de produtos com roteiro (formato inspirado em
  `Samples\parts`).
