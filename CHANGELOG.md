# Histórico de versões

## Não lançado

### Novo — fase 8: Relatórios Executivos e BI Industrial (Analytics)
- **Módulo de Relatórios e BI Industrial** (`src/modulos/relatorios/`, prefixo `/api/relatorios`, leitura ampla e escrita restrita por admin/pcp/diretoria):
  - **KPIs Executivos Consolidados**: rota `GET /api/relatorios/kpis` integrando pedidos, produção, custos, perdas, capacidade e turnos.
  - **Nível de Serviço e Cumprimento de Prazos (OTIF)**: apuração do On-Time In-Full ($(\text{pedidos no prazo} / \text{total avaliados}) \times 100$) e lead time em dias de cada pedido (`GET /api/relatorios/pedidos_otif`).
  - **Desempenho e Custos Operacionais por Posto**: apuração de OPs processadas, horas reais apontadas vs. horas padrão da engenharia, taxa de eficiência, taxa de refugo e custo de máquina apropriado com base nas taxas horárias do módulo de custos (`GET /api/relatorios/postos`).
  - **Ranking de Perdas e Refugos Industriais**: agrupamento analítico por produto e posto com cálculo da taxa de refugo e impacto financeiro estimado em R$ das perdas (`GET /api/relatorios/refugos`).
  - **Central de Exportações Analíticas em CSV**: geração sob demanda de arquivos CSV para planilhas (`GET /api/relatorios/exportar?tipo=kpis|postos|pedidos|refugos`).
  - **Alertas Executivos Automáticos**: emissão do evento `relatorios.alerta_gerencial` quando o OTIF cair abaixo da meta de 85% ou o refugo global ultrapassar o teto de 5%.
- **Painel Web**:
  - Nova aba e seção **BI & Relatórios** no menu principal e no dashboard inicial, com Big Numbers de OTIF, refugo global e custo real, tabelas interativas de postos, refugos e pedidos com badges de status e botões de exportação direta em CSV via Blob URL.
- **Testes**: +5 casos em `test_relatorios.cryo`, totalizando **91 testes automatizados** passando no `build.ps1` e compilação nativa Windows de `emp.exe`, `compras.exe` e `qualidade.exe`.

### Novo — fase 7: Gestão de Turnos, Operadores e Eficiência Operacional
- **Módulo de Turnos e Operadores** (`src/modulos/turnos/`, prefixo `/api/turnos`, escrita por admin/pcp/qualidade):
  - **Cadastro de Turnos e Horários**: turnos industriais com início, fim e horas de jornada planejadas (`T1`, `T2`, `T3`), com definição de turno ativo da fábrica (`POST /api/turnos/definir_atual`).
  - **Cadastro e Matrícula de Operadores**: operadores de chão de fábrica com matrícula, nome, turno base e status de atividade.
  - **Alocação de Operadores nos Postos de Trabalho**: mapeamento dinâmico posto × operador (`POST /api/turnos/alocacoes`), emitindo o evento `turnos.alocacao_alterada` e possibilitando liberação do posto.
  - **Acúmulo Automático de Métricas Operacionais**: assinatura dos eventos `producao.etapa_apontada` e `producao.apontada` para acumular horas reais, peças boas, refugo e cálculo de horas padrão da engenharia associados ao operador alocado no posto e ao turno vigente.
  - **Eficiência e Qualidade por Operador**: apuração da taxa de eficiência operacional ($(\text{horas padrão} / \text{horas reais}) \times 100$) e taxa de qualidade ($(\text{boas} / \text{total}) \times 100$).
  - **Comparativo e Painel de Turnos**: métricas agregadas por turno e por operador para benchmark de produtividade e análise de rendimento por equipe (`GET /api/turnos/comparativo`).
- **Painel Web**:
  - Nova aba e seção **Turnos & Operadores** com seletor de turno ativo no topo, cards comparativos por turno, formulários de alocação rápida no posto e de cadastro de operadores, tabela de alocações vigentes com botão Liberar e tabela de eficiência e qualidade por operador com badges de desempenho e exportação CSV.
- **Testes**: +5 casos em `test_turnos.cryo`, totalizando **86 testes automatizados** passando no `build.ps1` e compilação nativa Windows de `emp.exe`, `compras.exe` e `qualidade.exe`.

### Novo — fase 6: Custos Industriais e Manutenção Preventiva por Horas e Ciclos
- **Módulo de Custos Industriais e Apropriação** (`src/modulos/custos/`, prefixo `/api/custos`, escrita por admin/pcp):
  - Configuração de tabela de preços de materiais (`POST /api/custos/precos_materiais`) e taxas horárias de postos de trabalho (`POST /api/custos/taxas_postos`).
  - **Custo Padrão da Engenharia**: apuração exata de Material Direto (MD) a partir da estrutura multinível (BOM) e Mão de Obra e Máquina (MOD/GGF) a partir dos tempos do roteiro operacional e taxas horárias dos postos.
  - **Apropriação do Custo Real da OP**: consolidação dos insumos consumidos (incluindo sobreconsumo por refugo) e horas reais apontadas nas etapas.
  - **Análise de Desvio e Refugo**: cálculo da variação de custos (absoluta e percentual), custo financeiro de refugo gerado nas etapas e classificação de situação da OP (`FAVORAVEL` ou `DESFAVORAVEL`).
  - **Fechamento Contábil de Custos**: rota `POST /api/custos/fechar?op=N` com congelamento de snapshot e publicação do evento `custos.op_fechada`.
  - **DRE Industrial / Resumo de Custos**: `GET /api/custos/resumo` com visão agregada de custos da fábrica, desvios acumulados e OPs com estouro de custo.
- **Manutenção Preventiva por Horas e Ciclos** (`src/modulos/manutencao/`, prefixo `/api/manutencao`):
  - Planos de manutenção preventiva (`PlanoPreventiva`) por posto com gatilhos de `HORAS` de operação ou `CICLOS` de produção (peças fabricadas).
  - Assinatura automática de `producao.etapa_apontada` e `producao.apontada` para acumular desgaste contínuo de cada máquina sem acoplamento direto.
  - Alerta antecipado (ao atingir 85% do limite) e marcação de `VENCIDO` com emissão imediata de `manutencao.preventiva_vencida` (ao atingir 100%).
  - Rota de execução de preventiva `POST /api/manutencao/preventivas/executar?id=N` com técnico, observações, registro de histórico (`HistoricoPreventiva`), publicação de `manutencao.preventiva_executada` e reset automático de acumulador.
- **Painel Web**:
  - Nova aba e seção **Custos Industriais** no menu e no dashboard, com KPIs de custo padrão/real/desvio/refugo, formulários de configuração de preços/taxas, tabela de apropriação com ações e modal de detalhamento da OP.
  - Seção de Manutenção enriquecida com cards visuais de planos preventivos, barras de progresso percentual, badges de estado (`OK`, `ALERTA`, `VENCIDO`), botão de execução rápida e tabela de histórico de preventivas.
- **Testes**: +10 casos (+5 em `test_custos.cryo` e +5 em `test_manutencao.cryo`), totalizando **81 testes automatizados** passando no `build.ps1`.

### Novo — fase 5: Rastreabilidade de Lotes e Genealogia Industrial (Recall)
- **Módulo de Lotes e Rastreabilidade** (`src/modulos/lotes/`, prefixo `/api/lotes`, escrita por admin/qualidade/pcp/estoque):
  - Cadastro e controle de lotes de matéria-prima e produtos acabados com controle de status (`LIBERADO`, `QUARENTENA`, `BLOQUEADO`), data de validade, quantidade inicial, quantidade atual e lote do fornecedor.
  - Bloqueio e liberação de lotes (`POST /api/lotes/status`) com publicação imediata de `lote.bloqueado` e `lote.liberado`.
  - Geração automática de lote na conclusão de OP (`LOT-OP-{id}`) vinculando o produto gerado.
  - **Genealogia Industrial**:
    - Gravação contínua dos elos pai-filho (`GenealogiaElo`) registrando insumos consumidos em cada posto/etapa com seus respectivos lotes de origem (`lote_pai`, `lote_filho`, `op`, `componente`, `quantidade`, `posto`).
    - Registro de expedição para clientes (`ExpedicaoCliente`) mapeando `lote` entregue, `pedido`, `cliente` e `quantidade`.
  - **Rastreabilidade Bidirecional**:
    - **Backward Trace (De onde veio)**: inspeciona o lote do produto acabado, identificando a OP produtora, pedido de origem, data de fabricação e a lista completa de insumos utilizados com seus lotes e fornecedores.
    - **Forward Trace / Recall (Para onde foi)**: a partir de um lote suspeito ou defeituoso (ex: matéria-prima contaminada ou fora de especificação), mapeia o saldo restante em fábrica, todas as OPs intermediárias que o consumiram e todos os clientes e pedidos que receberam o produto final.
- **Integração com Estoque e Catálogo**:
  - `catalogo.cryo` registra o módulo `lotes` como interno (`M_INTERNO`).
  - `estoque.cryo` aceita parâmetro opcional `lote` em `POST /api/estoque/entrada` e o propaga no evento `estoque.movimentado`.
- **Painel Web**:
  - Nova aba e seção **Lotes & Rastreio** no menu principal e no dashboard inicial.
  - Cadastro manual de lotes recebidos de fornecedores com data de validade e status inicial.
  - Tabela geral de lotes com saldos, datas, botões de ação rápida para Liberar/Bloquear e atalho de rastreamento.
  - Interface interativa de **Consulta de Rastreabilidade e Genealogia (Recall)** com visualização lado a lado de Origem (Backward) e Destino/Recall (Forward) com alerta visual de clientes afetados.
  - Integração com o sino de notificações e badge de contagem de lotes bloqueados/quarentena.
- **Testes**: +5 casos em `test_lotes`, totalizando 71 testes automatizados passando no `build.ps1`.

### Novo — fase 4: Programação da Produção (APS) e Backflush por Etapa
- **Módulo de Programação da Produção / APS** (`src/modulos/programacao/`, prefixo `/api/programacao`, escrita por admin/pcp):
  - Cálculo de Carga × Capacidade por posto de trabalho com ocupação percentual e identificação automática do Posto Gargalo (`gargalo: bool`).
  - Sequenciamento inteligente por prioridade do PCP, Earliest Due Date (EDD - prazo prometido do pedido comercial) e desempate FIFO.
  - Projeção de cronograma contínuo (início e fim estimados) considerando tempos unitários de roteiro ou capacidade do posto e apontamento atual.
  - Alerta antecipado de atraso previsto (`atraso_previsto: bool`) quando o fim estimado ultrapassa a entrega prometida ao cliente.
  - Rota de priorização manual `POST /api/programacao/priorizar` (`op` e `prioridade`) persistida em `dados/programacao/prioridades.json`.
  - Publica evento `programacao.sobrecarga` com `posto` e `ocupacao_pct` quando a ocupação ultrapassa 100%.
- **Backflush com Etapa de Consumo**:
  - `cadastros::ItemEstrutura` agora possui campo `etapa: int` (0 = início/geral, 1..N = etapa específica do roteiro).
  - `estoque.cryo` assina `producao.etapa_apontada` e consome no momento do apontamento os componentes vinculados àquela etapa específica diretamente do endereço `LINHA` do posto correspondente.
  - No encerramento da OP (ou apontamento de etapa única/legada), realiza a baixa final dos componentes de etapa 0 ou remanescentes.
  - Resolve o problema conhecido da fase 3.
- **Painel**:
  - Nova aba e seção **Programação (APS)** com visualização de cards de capacidade por posto, barra de ocupação, badges de `GARGALO` e `SOBRECARGA`.
  - Tabela de fila de sequenciamento com ordenação por prioridade/EDD, filtro por posto, situação (`NO PRAZO`, `EM EXECUÇÃO`, `ATRASO PREVISTO`) e edição rápida de prioridade.
  - Em Cadastros, formulário e tabela de estrutura (BOM) atualizados com campo de etapa de consumo.
  - Indicador de alerta de sobrecargas de postos no sino e badge na navegação.
- **Testes**: +5 casos em `test_programacao` e +1 caso em `test_estoque`, totalizando 66 testes automatizados no `build.ps1`.

### Corrigido (fase 4)
- **Consumo de componentes por etapa no chão de fábrica**: componentes agora saem dos postos onde são efetivamente consumidos durante o fluxo de etapas da OP, e não todos acumulados no posto da última etapa.

### Novo — fase 3: PCP / MRP e compras
- **Módulo de PCP / MRP** (`src/modulos/mrp/`, prefixo `/api/mrp`, escrita por admin/pcp):
  - Explosão de estrutura multinível (BOM) combinando demanda de pedidos comerciais abertos (`pedidos`) e regras de reposição mínima (`estoque`).
  - Cálculo de necessidade líquida: `max(0, demanda_bruta - saldo - em_producao)`.
  - Ação sugerida: `PRODUZIR` para PA e SA (com roteiro e posto padrão) ou `COMPRAR` para MP.
  - `GET /api/mrp/plano`: lista de necessidades com nível, demanda bruta, saldo, em produção, necessidade líquida e ação.
  - `POST /api/mrp/gerar_ordens`: gera automaticamente ordens de produção (`producao::criar_op`) com origem `MRP` para todas as necessidades líquidas de produção.
  - Publica evento `mrp.ordens_geradas` (`total` e lista de `ops`).
- **Plugin de Compras** (`plugins_src/compras/`, manifesto `plugins/compras.plugin`, executável `build/compras.exe`):
  - Cadastro de fornecedores (`GET/POST /api/compras/fornecedores`) com dados de contato e prazo de entrega.
  - Pedidos de compra (`GET/POST /api/compras/pedidos`) com itens, prazo e status.
  - Recebimento de compra (`POST /api/compras/pedidos/receber?id=N`): marca o pedido como `RECEBIDO` e efetua a entrada dos produtos no estoque via `POST /api/estoque/entrada`.
  - Escuta `estoque.abaixo_minimo` e `estoque.falta` gerando sugestões de compra automáticas (`GET /api/compras/sugestoes`).
- **Painel**:
  - Nova aba **MRP / PCP** no menu com tabela de necessidades, filtros por ação (PRODUZIR/COMPRAR), badges de status e botão para "Gerar Ordens de Produção (MRP)".
  - Tabela de Reposição de Estoque enriquecida com colunas "Em Prod." e "Projetado".
- **Testes**: +5 casos em `test_mrp` e +1 caso em `test_estoque`, totalizando 60 testes automatizados no `build.ps1`.

### Corrigido (fase 3)
- **/sugestoes desconta OPs já abertas**: o módulo de estoque agora assina `op.*` e rastreia `_ops_abertas`. Se o saldo projetado (`saldo + em_producao`) atingir o mínimo, a sugestão deixa de ser listada; caso contrário, sugere apenas a quantidade complementar (`maximo - saldo_projetado`). A API devolve `em_producao` e `saldo_projetado` no JSON.

### Problemas conhecidos (resolvidos na fase 4)
- Todos os componentes saíam do endereço do posto da **última** etapa no
  backflush: resolvido na fase 4 com o campo `etapa` na estrutura do produto e consumo imediato a cada etapa apontada.

### Novo — fase 2: comercial, estoque endereçado e OEE ([docs/FASE2.md](docs/FASE2.md))
Inspirada no MES4 (`tblCustomer`/`tblOrder`, `tblBuffer`/`tblBufferPos`,
`tblAutomaticOrder`, `tblMachineReport`). Detalhes, decisões e limites de cada
frente em [`docs/fase2/`](docs/fase2/).

- **Módulo de Pedidos** (`src/modulos/pedidos/`, `/api/pedidos`, escrita por
  admin/comercial/pcp): clientes; pedidos com itens `PRODUTO:qtd;...` e
  `prazo_dias`; `gerar_ops` cria as OPs da **falta** (quantidade − saldo
  livre, com reserva entre pedidos); PRONTO quando as OPs concluem ou o saldo
  cobre; `expedir` (409 com a lista de faltas se não houver saldo); cancelar
  com motivo; `atrasado` calculado. Eventos `pedido.criado`,
  `pedido.ops_geradas`, `pedido.pronto`, `pedido.expedido`, `pedido.cancelado`.
- **Produção**: a OP ganha `origem` (`PED-12`, `REPOSICAO`, vazio para manual),
  `pub fn criar_op(...)` para outros módulos e `&origem=` nos eventos `op.*`.
  OPs gravadas antes continuam sendo lidas.
- **Estoque endereçado**: endereços (`GERAL` fixo, ALMOXARIFADO, LINHA por
  posto, EXPEDICAO, QUARENTENA), saldo por produto × endereço, `GET /posicoes`,
  `POST /transferir` (exige saldo na origem), entrada/ajuste por endereço e
  movimentos com `endereco`. O backflush consome primeiro da LINHA do posto; a
  expedição baixa do endereço EXPEDICAO e depois do `GERAL` (assina
  `pedido.expedido`). `GET /saldos` sem parâmetro **não mudou**; dados antigos
  migram na leitura para o `GERAL`.
- **Reposição mín./máx.**: regras por produto (total ou de um endereço),
  `GET /sugestoes` (quantidade = máximo − saldo, tipo COMPRAR ou PRODUZIR) e o
  evento `estoque.abaixo_minimo` só no cruzamento.
- **Módulo de Indicadores** (`src/modulos/indicadores/`, `/api/indicadores`,
  só leitura): histórico de estado do posto (PARADO > OPERANDO > OCIOSO) e
  **OEE** por posto e da linha (`GET /estados`, `/oee`, `/oee/serie`), calculado
  só a partir dos eventos. `indicadores.oee_baixo` quando o OEE da linha em 8 h
  cai abaixo de `EMP_OEE_ALERTA` (padrão 0,6), no máximo um por hora.
- **Eventos mais ricos**: `producao.etapa_*` levam produto, `tempo_min`,
  entrada, `delta_boas`/`delta_refugo` e início/fim; novo
  `producao.etapa_apontada` a cada apontamento; `maquina.parada`/`liberada`
  levam motivo e início/fim reais (inclusive em parada retroativa).
- **Painel**: abas Pedidos (lista com distribuição e atraso, detalhe com itens e
  OPs ligadas), Clientes em Cadastros, Estoque com endereços e posições,
  transferência, reposição com *Criar OP* / *Registrar entrada* e detalhe do
  produto, aba **OEE** (anel da linha, cartões por posto, linha do tempo de
  estados e OEE por hora em SVG feito no próprio painel), KPI de OEE na visão
  geral e contadores no menu. [DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) 1.2.
- Cargas de demonstração `tools/demo_estoque.cryo`, `demo_comercial.cryo` e
  `demo_oee.cryo` (rodar depois de `demo.cryo`, nessa ordem).
- Testes `test_pedidos` (5), `test_estoque` (10) e `test_oee` (11), ligados no
  `build.ps1`. Capturas 14 a 21 em `docs/screenshots/`.

### Corrigido (fase 2)
- **OEE de um posto que produziu não zera mais por falta de tempo.** Com peças
  apontadas mas sem tempo operando registrado (execuções de milissegundos, ou
  uma parada retroativa que cobre a execução inteira) ou sem tempo padrão no
  roteiro (`tempo_min` 0), o desempenho **não é medido**: vale 1 e a API
  devolve `desempenho_medido: false` (em `/oee`, nos postos, na linha e na
  série). Sem produção nenhuma continua 0. O desempenho da **linha** usa só os
  postos medidos. No painel, o fator aparece como "—" no cartão do posto e
  "sem tempo" na série por hora. Na demonstração, a MONT-01 foi de OEE 0 para
  0,96. +4 casos em `test_oee`.
- **Quantidade fracionada em unidade contável é recusada** (422 "deve ser
  inteira"): pedido e OP (`POST /ordens` e `criar_op`) com 12,5 de um produto em
  `UN`, `PC`, `PÇ`, `CX` ou `PAR`. Frações continuam valendo para KG, M, L etc.
  Regra em `cadastros::quantidade_invalida`. +casos em `test_pedidos`.

### Problemas conhecidos (fase 2)
- `/sugestoes` não descontava OPs abertas nem compras (corrigido na fase 3).
- Todos os componentes saem do endereço do posto da **última** etapa no
  backflush: a estrutura não diz em que etapa cada componente entra.

### Novo — execução por etapas (fase 1 da análise do MES4, [docs/ANALISE_FACTORYVIEWS.md](docs/ANALISE_FACTORYVIEWS.md))
- **Módulo de Roteiros** (`src/modulos/roteiros/`, prefixo `/api/roteiros`,
  depende de cadastros, escrita por admin/pcp): **operações** (código,
  descrição, tipo MANUAL/AUTOMATICA, instrução e parâmetros medidos com
  limites `nome:unidade:min:max;...`), **roteiro por produto** (etapas
  numeradas: operação, posto, tempo em min/unidade, instrução; inserir,
  substituir, remover) e **capacidades** posto × operação (tempo padrão usado
  quando a etapa tem tempo 0). API Cryo: `roteiros::etapas(produto)`,
  `roteiros::operacao_json(codigo)`.
- **Produção executa por etapa** (`producao/etapas.cryo` + `producao.cryo`):
  na liberação a OP copia o roteiro (sem roteiro: etapa única `APONTAMENTO`
  no posto da OP, como antes), com início/fim planejados em sequência.
  `GET /ordem` e `GET /ordens` trazem `etapas` e `etapa_atual`.
  - Rotas novas: `GET /fila?posto=` e `POST /etapa/iniciar|apontar|concluir|erro|reiniciar|pular?op=&etapa=`.
  - Concorrência por **`versao`** da etapa: versão diferente → 409
    "a tarefa foi alterada por outra pessoa", com a etapa atualizada no corpo.
  - Posto parado recusa iniciar, apontar e concluir (409).
  - **Medições** por apontamento (`medicoes=nome=valor;...`), conferidas
    contra os limites da operação (`dentro` verdadeiro/falso).
  - A etapa seguinte recebe como entrada as boas da anterior; a última soma
    em `produzido` e publica `producao.apontada` levando junto o refugo das
    etapas anteriores, para o backflush consumir o material das peças perdidas.
  - `reiniciar` e `pular` só para pcp/admin.
  - Eventos novos: `producao.etapa_iniciada`, `producao.etapa_concluida`,
    `producao.etapa_falhou`.
- `POST /apontar?id=` continua aceito: aponta na etapa atual (iniciando-a se
  estiver aguardando), sem pedir versão. OPs liberadas por versões anteriores
  ganham na leitura uma etapa única com o que já tinham produzido.
- `tools/demo.cryo` cadastra operações, capacidades e roteiros (SUP-02 passa
  por prensa → solda → pintura → montagem) e executa OPs etapa por etapa,
  com erro + reiniciar, medição fora do limite e um 409 por versão velha.
- Testes: `tests/test_etapas.cryo` (15 casos com `test fn`: máquina de
  estados, versão/409, pular, medições e parâmetros), rodado pelo `build.ps1`.

### Alterado (comportamento)
- Uma etapa conclui sozinha quando **boas + refugo** alcançam a entrada (antes
  a OP concluía quando só as boas alcançavam a quantidade).
- Etapas depois da primeira não aceitam apontar mais peças do que entraram (422).

### Novo — interface da fase 1 (terminal do operador e painel)
- **Terminal do operador** (`GET /terminal`, `src/nucleo/terminal.cryo`):
  uma página por posto (`/terminal#PRENSA-01`) para o tablet ao lado da
  máquina, com **uma instrução por vez** (padrão dos terminais manuais do
  MES4, no visual Forja). Título da operação, instrução, OP, produto,
  "etapa n de m", entrada, boas, refugo e o que falta; botões de 84 px:
  *Iniciar* → *Apontar* (boas/refugo com − e +, e os parâmetros medidos com
  "dentro/fora do limite") / *Concluir* / *Concluir com erro* (motivos
  prontos) / *Reiniciar*. Lista de tarefas do posto, "Nenhuma tarefa" quando
  vazia, posto parado em destaque com as ações bloqueadas.
  - Atualiza a cada 1 s (2 s depois de uma mensagem), com o selo
    "atualizado às HH:MM:SS"; um toque desliga os botões na hora.
  - Envia a `versao` da etapa; um 409 de versão vira "a tarefa foi alterada
    por outra pessoa" e a tela recarrega.
  - A página é aberta sem token; a API continua exigindo, com o token do
    painel (`localStorage`). O operador fica salvo no tablet.
- **Painel**:
  - **Estado = ícone + cor** em todas as etiquetas (planejada, aguardando,
    ativa, concluída, falha, pulada) e **faixa de estado** na borda esquerda
    de linhas e cartões; uma falha pisca uma vez.
  - **Detalhe da OP com o fluxo de etapas** (`/#ordens/7`): planejado ×
    real (com atraso), entrada, boas, refugo, operador, erro e as ações
    iniciar / concluir / concluir com erro / reiniciar / pular (as duas
    últimas só para pcp e admin). Na lista de ordens, a etapa atual
    aparece sob o estado e o código da OP abre o detalhe.
  - **Aba Roteiros em Cadastros** (`/#cadastros/roteiros`, aparece quando o
    módulo `roteiros` está ativo): operações com parâmetros medidos, editor
    do roteiro por produto (incluir, editar, remover etapa; endereço próprio,
    `/#cadastros/roteiros/SUP-02`, aberto pelo produto no detalhe da OP) e capacidades
    posto × operação.
  - **Moldura de lista** em ordens, saldos, paradas, NCs, produtos, postos,
    operações e capacidades: filtro de texto e de estado, aviso
    "lista filtrada · limpar" e **Exportar CSV** gerado no navegador.
  - Link para o terminal em cada posto (cartões, cadastro, etapas), no menu
    e na tela inicial.
- Os tokens do Forja ficam em `painel::tokens_css()`, usado pelas duas
  páginas. [DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md) 1.1 documenta os
  componentes novos.

### Alterado
- **Novo sistema de design próprio: "Forja"** ([docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md)),
  aplicado em todo o painel (`src/nucleo/painel.cryo`). Substitui o visual
  inspirado no MES4/FactoryViews.
  - Fundo de papel técnico com grade de pontos; navegação num console grafite
    flutuante; laranja-forja como única cor de marca.
  - Postos com **medidor circular** de disponibilidade; posto parado com
    **faixa de perigo**; progresso das OPs em **barra de LED** segmentada;
    estado "em produção" com ponto pulsando; eventos numa **linha do tempo**.
  - Tela inicial com um destaque escuro que **resume a linha em uma frase**
    ("1 posto parado e 3 ordens em produção agora") e blocos por módulo.
  - Contadores de paradas e NCs abertas no próprio menu; relógio "ao vivo";
    botão "+ Novo" que leva ao formulário da tela.
  - Tipografia: Space Grotesk (títulos e números), Inter (texto) e
    JetBrains Mono (rótulos e códigos), com fontes do sistema como
    alternativa sem internet.
  - **Modo escuro** automático (segue o sistema) e `prefers-reduced-motion`.
  - Contraste AA medido nos pares de texto; texto grafite sobre o laranja.
- Rotas, IDs dos formulários e chamadas à API continuam os mesmos.
- As capturas em `docs/screenshots/` foram refeitas no visual Forja (fases 1 e 2).

## 0.2.0 — 2026-10-16

### Novo
- **Módulo de Manutenção** (`src/modulos/manutencao/`): paradas de posto com
  categoria (mecânica, elétrica, setup, falta de material, qualidade, outros),
  registro retroativo (`ha_minutos`), encerramento com solução, estado de cada
  posto, disponibilidade numa janela móvel de 8 h, MTTR e minutos por categoria.
- **Integração por evento entre Manutenção e Produção**: `maquina.parada` /
  `maquina.liberada`. Um posto parado recusa apontamento (409). Ao reiniciar,
  a Manutenção reanuncia as paradas abertas e o núcleo entrega esses eventos
  antes da primeira requisição.
- **Painel web completo** (`src/nucleo/painel.cryo`): menu lateral; abas de
  visão geral, ordens, estoque, manutenção, qualidade, cadastros, eventos e
  módulos; formulários para todas as operações; indicadores; atualização a
  cada 6 s; abas de módulos inativos ficam ocultas.
- **Feed de eventos**: `GET /api/sistema/eventos` (últimos 100) e
  `GET /api/sistema/sessao`.
- **Carga de demonstração em Cryo**: `tools/demo.cryo`.
- Produção valida o posto da OP contra o cadastro; Cadastros expõe a API
  pública de postos.
- Capturas de tela em `docs/screenshots/`.

### Corrigido
- **Uma entrada inválida podia derrubar o servidor**: `to_int("abc")` aborta o
  processo e não é capturável. Todo texto vindo de fora agora passa por
  `parse_int`/`parse_number` (devolvem opcional): `?id=abc` dá 404.
- O painel não apaga mais o que o usuário está digitando num campo de tabela
  (apontamento, solução da parada) durante a atualização automática.

### Medido
- O servidor nativo só escuta IPv4: abrir o painel por `localhost` custa
  ~200 ms por requisição no Windows (669 ms contra 67 ms por atualização). A
  documentação e a mensagem de inicialização passam a usar `127.0.0.1`.

## 0.1.0 — 2026-10-16

- Núcleo modular (contrato de módulo, registro, eventos, RBAC, auditoria,
  persistência atômica), módulos de Cadastros, Produção e Estoque, plugin
  externo de Qualidade, build para `.exe` e documento de escopo.
