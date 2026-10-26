# EMP — Engineering Modular Process

ERP modular para gestão de linha de produção, escrito **somente em Cryo** e
compilado para **executáveis nativos do Windows** (`emp.exe`, `landing.exe`,
`qualidade.exe`, `compras.exe`, ~100% C-AOT via MinGW GCC, sem Python, Go ou VM
em tempo de execução).

Documentação técnica:
- **[Landing Page & Terminal de Prompt](docs/LANDING_PAGE_E_PROMPT.md)** — Servidor web e console cognitivo (:8088)
- **[Fase 10: Arquivamento Histórico](docs/FASE10_ARQUIVAMENTO.md)** — Separação operacional e tabelas `tblFin*`
- **[Design System Forja](docs/DESIGN_SYSTEM.md)** — Tokens de design e interface industrial
- **[Escopo e Arquitetura](ESCOPO.md)** — Princípios de projeto e catálogo de eventos
- **[Histórico de Versões](CHANGELOG.md)** — Log completo de lançamentos e fases

![Visão geral do EMP](docs/screenshots/01-visao-geral.png)

## O que ele faz

| Módulo | Tipo | Faz |
|---|---|---|
| **Cadastros** | interno | Produtos (MP/SA/PA), estrutura de produto (BOM) com etapa de consumo para backflush, postos de trabalho |
| **Roteiros** | interno | Operações (com parâmetros medidos e limites), roteiro de etapas por produto, capacidades posto × operação |
| **Produção** | interno | Ordens de produção executadas **etapa por etapa** (copiadas do roteiro na liberação), fila por posto, medições, concorrência por versão, indicadores; recusa trabalhar em posto parado |
| **Pedidos** | interno | Clientes e pedidos de venda com itens e prazo; gera as OPs da falta (com reserva entre pedidos), fica pronto quando as OPs concluem ou o saldo cobre, expede e avisa atraso |
| **Estoque** | interno | Saldos **por endereço** (almoxarifado, linha do posto, expedição, quarentena), transferências, ajuste de inventário, **baixa automática por estrutura e etapa** (backflush na linha do posto da etapa), baixa na expedição, **reposição mín./máx.** com sugestões de compra ou produção |
| **Manutenção** | interno | Manutenção corretiva (paradas por categoria, disponibilidade 8 h, MTTR) e **manutenção preventiva** (planos por horas ou ciclos acumulados do chão de fábrica, alertas e histórico de execução) |
| **Indicadores** | interno | Histórico de estado de cada posto (operando, parado, ocioso) e **OEE** = disponibilidade × desempenho × qualidade, por posto e da linha, com série por hora e alerta de OEE baixo — calculado só a partir dos eventos |
| **PCP / MRP** | interno | Planejamento de necessidades de materiais: explosão multinível de BOM, cálculo de necessidade líquida cruzando pedidos e reposição mínima com saldo e OPs abertas, geração automática de ordens de produção (`POST /api/mrp/gerar_ordens`) |
| **Programação (APS)** | interno | Sequenciamento e capacidade finita: carga × capacidade por posto, identificação de gargalos, fila sequenciada por prioridade e EDD (Earliest Due Date), projeção contínua de cronograma e alerta de atraso |
| **Lotes & Rastreabilidade** | interno | Rastreabilidade e genealogia industrial: controle de lotes (status/validade), árvore genealógica de insumos consumidos em cada etapa da OP, expedição a clientes e rastreamento bidirecional (backward de insumos e forward recall de clientes) |
| **Custos Industriais** | interno | Apropriação de custos da produção: custo padrão da engenharia (MD + MOD/GGF) vs. custo real da OP, taxas horárias dos postos, custo de refugo, análise de desvio percentual e fechamento contábil |
| **Turnos & Operadores** | interno | Gestão de turnos de trabalho, alocação de operadores aos postos, turno ativo da fábrica, produtividade, taxa de qualidade e eficiência operacional por operador |
| **BI & Relatórios** | interno | Painel analítico executivo, índice OTIF de pontualidade de pedidos, ranking de refugos/perdas financeiras, desempenho de postos e exportações analíticas em CSV |
| **Coleta Automática & IoT** | interno | Contadores de pulsos de CLP, telemetria de sensores (temperatura/pressão), intertravamento com parada automática e apontamento automático no chão de fábrica |
| **Histórico & Arquivo** | interno | Arquivamento histórico e congelamento de OPs finalizadas (`tblFinOrder`, `tblFinStep`), purga periódica por retenção em dias, restauração reversível para auditoria e alta performance operacional contínua |
| **Landing & Prompt** | servidor web | Showcase completo de engenharia das 10 fases e console interativo com processamento de prompt em linguagem natural para agentes LLM e operadores (`POST /api/prompt`) |
| **Qualidade** | **plugin externo** | Não conformidades manuais e automáticas (refugo acima do limite) — processo próprio, sem recompilar o núcleo |
| **Compras** | **plugin externo** | Gestão de fornecedores, pedidos de compra, recebimento com entrada automática no estoque do EMP e reação a faltas de estoque — processo próprio |

Os módulos não se chamam: reagem a **eventos**. Quando a Manutenção abre uma
parada, publica `maquina.parada`; a Produção assina esse evento e passa a
recusar apontamento naquele posto. Nenhum dos dois importa o outro.

---

## Telas

| | |
|---|---|
| ![Ordens de produção](docs/screenshots/02-ordens.png) **Ordens** — criar, liberar, apontar e cancelar OPs; estado com ícone, etapa atual, filtro e exportação CSV | ![Estoque](docs/screenshots/03-estoque.png) **Estoque** — saldos e movimentos; o consumo dos componentes sai sozinho a cada apontamento |
| ![Manutenção](docs/screenshots/04-manutencao.png) **Manutenção** — estado de cada posto, disponibilidade, MTTR, minutos por categoria | ![Qualidade](docs/screenshots/05-qualidade.png) **Qualidade** (plugin) — NC automática quando o refugo passa de 5% |
| ![Cadastros](docs/screenshots/06-cadastros.png) **Cadastros** — produtos, estrutura (BOM) e postos, com link para o terminal de cada posto | ![Eventos](docs/screenshots/07-eventos.png) **Eventos** — o que cada módulo publicou no barramento |
| ![Módulos](docs/screenshots/08-modulos.png) **Módulos** — internos e plugins, com o estado de cada um | ![Fluxo de etapas](docs/screenshots/09-ordem-etapas.png) **Detalhe da OP** (`/#ordens/3`) — fluxo de etapas: planejado × real, operador, medições e ações por etapa |
| ![Roteiros](docs/screenshots/10-roteiros.png) **Roteiros** (Cadastros) — operações com parâmetros, roteiro por produto e capacidades | ![Postos do terminal](docs/screenshots/13-terminal-postos.png) **Terminal: escolha do posto** (`/terminal`) |
| ![Pedidos](docs/screenshots/14-pedidos.png) **Pedidos** — distribuição por estado, atraso, cobertura e ações | ![Detalhe do pedido](docs/screenshots/15-pedido-detalhe.png) **Detalhe do pedido** — itens com saldo livre e falta, OPs ligadas |
| ![Clientes](docs/screenshots/16-clientes.png) **Clientes** (Cadastros) — com os pedidos em aberto de cada um | ![Endereços e posições](docs/screenshots/17-estoque-posicoes.png) **Endereços e posições** — transferência e saldo por endereço |
| ![Reposição](docs/screenshots/18-estoque-reposicao.png) **Reposição** — regras mín./máx. e sugestões com *Criar OP* | ![Produto no estoque](docs/screenshots/19-estoque-produto.png) **Produto** — saldo por endereço, faixa de reposição, movimentos |
| ![OEE](docs/screenshots/20-oee.png) **OEE** — linha e postos, linha do tempo de estados e OEE por hora | ![OEE no tablet escuro](docs/screenshots/21-oee-24h-tablet-escuro.png) **OEE 24 h** — tablet em pé, modo escuro |

### Terminal do operador

`/terminal#PRENSA-01` é a tela do tablet ao lado da máquina: uma instrução por
vez, botões grandes, fila do posto e atualização a cada segundo. A página
abre sem token; a API usa o mesmo token do painel.

| | |
|---|---|
| ![Terminal do operador](docs/screenshots/11-terminal.png) Tablet deitado, etapa em execução | ![Terminal com posto parado](docs/screenshots/12-terminal-parado-escuro.png) Tablet em pé, modo escuro, posto parado: as ações ficam bloqueadas |

---

## Landing Page e Console de Prompt do Agente

O arquivo `src/landing.cryo` compila para `build/landing.exe` (porta `8088`) e oferece:
- Apresentação completa das 10 fases da engenharia industrial do EMP;
- Terminal interativo de prompt com suporte a comandos rápidos (`status fabrica`, `otif e kpis`, `arquivar ops`, `sensores iot`, `turnos e operadores`, `ajuda`);
- Endpoint `POST /api/prompt` que processa linguagem natural e gera respostas com badges semânticos e payloads técnicos para agentes LLM;
- Exportação estática automática para `build/landing.html`.

Mais detalhes em **[`docs/LANDING_PAGE_E_PROMPT.md`](docs/LANDING_PAGE_E_PROMPT.md)**.

---

## Compilar

O toolchain Cryo é procurado na pasta acima deste repositório (ou em `CRYO_HOME`).
Precisa de Python 3 e do MinGW gcc em `C:\MinGW\bin`.

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

O script roda a suíte de testes (101 unitários + testes de integração da landing page) e compila os binários nativos:
- `build\emp.exe` (~5.1 MB) — Núcleo do ERP, API REST e Painel Web
- `build\landing.exe` (~422 KB) — Servidor Web e Console de Prompt Cognitivo
- `build\qualidade.exe` (~297 KB) — Plugin externo de Não Conformidades
- `build\compras.exe` (~382 KB) — Plugin externo de Compras
- `build\landing.html` (~34 KB) — Página estática gerada automaticamente

---

## Rodar

Em terminais separados (ou como serviços de fundo no Windows):

```powershell
# 1. (Opcional) Plugins externos
.\build\qualidade.exe          # porta 8091
.\build\compras.exe            # porta 8092

# 2. Núcleo do ERP
$env:ERP_TOKENS="tk-ana:ana:admin,tk-joao:joao:operador,tk-rui:rui:almoxarife,tk-lia:lia:manutencao"
$env:PYRO_HTTP_TIMEOUT_MS="2000"
.\build\emp.exe                # painel em http://127.0.0.1:8080, terminal em /terminal

# 3. Landing Page & Console de Prompt do Agente
.\build\landing.exe            # landing page em http://127.0.0.1:8088
```

> Use **`http://127.0.0.1:8080`** e **`http://127.0.0.1:8088`** (ou o IP do servidor), não `localhost`: o
> servidor nativo só escuta IPv4 e o Windows tenta IPv6 primeiro, o que custa
> ~200 ms por requisição — medido: atualização do painel em 67 ms pelo IP
> contra 669 ms por `localhost`.

### Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `ERP_PORTA` | `8080` | Porta HTTP do núcleo do ERP |
| `ERP_DADOS` | `dados` | Diretório de persistência JSON |
| `ERP_PLUGINS` | `plugins` | Diretório dos manifestos `*.plugin` |
| `ERP_TOKENS` | vazio | `token:usuario:perfil,...` — vazio = **modo dev**, sem autenticação |
| `PYRO_HTTP_TIMEOUT_MS` | `10000` | Prazo para uma requisição chegar inteira (use 1000–2000) |
| `PYRO_HTTP_CLIENT_TIMEOUT_MS` | `15000` | Prazo de cada chamada a um plugin externo |
| `LANDING_PORTA` | `8088` | Porta HTTP da Landing Page e Prompt Console |
| `QUALIDADE_PORTA` / `QUALIDADE_LIMITE` | `8091` / `5` | Plugin de qualidade |
| `COMPRAS_PORTA` | `8092` | Plugin de compras |

Perfis disponíveis: `admin`, `pcp`, `comercial`, `operador`, `almoxarife`, `manutencao`, `qualidade`, `consulta`.

---

## API (corpos em form-urlencoded)

Exemplos de chamadas via cURL:

```bash
U=http://127.0.0.1:8080; T="Authorization: Bearer tk-ana"

# Cadastros e Estoque
curl -H "$T" -X POST $U/api/cadastros/produtos -d "codigo=aco&tipo=MP&unidade=KG"
curl -H "$T" -X POST $U/api/cadastros/produtos -d "codigo=sup01&tipo=PA"
curl -H "$T" -X POST $U/api/cadastros/estrutura -d "produto=sup01&componente=aco&quantidade=1,5"
curl -H "Authorization: Bearer tk-rui" -X POST $U/api/estoque/entrada -d "produto=aco&quantidade=100"

# Produção por Etapas
curl -H "$T" -X POST $U/api/producao/ordens -d "produto=sup01&quantidade=50&posto=PRENSA1"
curl -H "$T" -X POST "$U/api/producao/liberar?id=1"
curl -H "Authorization: Bearer tk-joao" -X POST "$U/api/producao/etapa/iniciar?op=1&etapa=10" -d "versao=1"
curl -H "Authorization: Bearer tk-joao" -X POST "$U/api/producao/etapa/apontar?op=1&etapa=10" -d "versao=2&boas=48&refugo=2"

# Telemetria IoT e Intertravamento
curl -H "$T" -X POST $U/api/coleta/telemetria -d "dispositivo=DISP-T01&posto=PRENSA1&tipo=TEMPERATURA&valor=98.5"

# Arquivamento Histórico (Fase 10)
curl -H "$T" -X POST "$U/api/arquivamento/op?id=1"
curl -H "$T" "$U/api/arquivamento/ordens"

# Terminal de Prompt da Landing Page (Porta 8088)
curl -X POST http://127.0.0.1:8088/api/prompt -d "prompt=status+fabrica"
```

### Catálogo de Rotas por Prefixo

| Prefixo | Principais Rotas |
|---|---|
| `/api/sistema` | `GET /saude`, `GET /modulos`, `GET /eventos[?n=]`, `GET /sessao` |
| `/api/cadastros` | `GET/POST /produtos`, `GET/POST /estrutura`, `GET/POST /postos` |
| `/api/roteiros` | `GET/POST /operacoes`, `GET /roteiro?produto=`, `POST /etapa`, `POST /remover_etapa?produto=&numero=`, `GET /capacidades`, `POST /capacidade` |
| `/api/producao` | `GET/POST /ordens`, `GET /ordem?id=`, `POST /liberar?id=`, `POST /apontar?id=`, `POST /cancelar?id=`, `GET /fila?posto=`, `POST /etapa/iniciar\|apontar\|concluir\|erro\|reiniciar\|pular?op=&etapa=`, `GET /indicadores` |
| `/api/pedidos` | `GET/POST /clientes`, `GET/POST /pedidos[?status=]`, `GET /pedido?id=`, `POST /gerar_ops?id=`, `POST /expedir?id=`, `POST /cancelar?id=` |
| `/api/estoque` | `GET /saldos[?produto=]`, `GET /movimentos`, `POST /entrada`, `POST /ajuste`, `GET/POST /enderecos`, `GET /posicoes[?endereco=]`, `POST /transferir`, `GET/POST /reposicao`, `GET /sugestoes` |
| `/api/manutencao` | `GET/POST /paradas`, `POST /encerrar?id=`, `GET /postos`, `GET /indicadores`, `GET/POST /preventivas`, `POST /preventivas/executar?id=` |
| `/api/indicadores` | `GET /estados?posto=&horas=`, `GET /oee?horas=`, `GET /oee/serie?posto=&horas=&passo_min=` |
| `/api/mrp` | `GET /plano`, `POST /gerar_ordens` |
| `/api/programacao` | `GET /plano`, `GET /gargalos`, `POST /prioridade` |
| `/api/lotes` | `GET/POST /lotes`, `POST /bloquear\|liberar`, `GET /arvore?lote=`, `GET /rastreabilidade?lote=` |
| `/api/custos` | `GET /padrao?produto=`, `POST /taxas`, `GET /op?id=`, `POST /fechar?id=`, `GET /desvios` |
| `/api/turnos` | `GET/POST /turnos`, `POST /definir_atual`, `GET/POST /operadores`, `POST /alocacoes`, `POST /liberar_posto`, `GET /comparativo` |
| `/api/relatorios` | `GET /kpis`, `GET /pedidos_otif`, `GET /postos`, `GET /refugos`, `GET /exportar?tipo=` |
| `/api/coleta` | `GET/POST /dispositivos`, `POST /pulso`, `POST /telemetria`, `POST /heartbeat`, `GET /status` |
| `/api/arquivamento` | `GET/POST /ordens`, `GET /ordem?id=`, `POST /op?id=`, `POST /lote?dias=`, `POST /desarquivar?id=`, `GET /resumo`, `GET/POST /config` |
| `/api/prompt` *(8088)* | `POST /api/prompt` (interpretação cognitiva), `GET /api/saude` |
| `/api/qualidade` *(plugin)* | `GET/POST /ncs` |
| `/api/compras` *(plugin)* | `GET/POST /fornecedores`, `GET/POST /pedidos`, `POST /pedidos/receber?id=`, `POST /pedidos/cancelar?id=`, `GET /sugestoes` |

---

## Testes e Verificação

### 1. Testes Unitários Nativos em Cryo (101 testes)
Compilados e executados via `cryoc test`:
```bash
python ../Burnout/cryoc.py tests/test_nucleo.cryo --backend pyro --run
python ../Burnout/cryoc.py test tests/test_eventos.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_etapas.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_pedidos.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_estoque.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_oee.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_mrp.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_programacao.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_lotes.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_custos.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_turnos.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_relatorios.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_coleta.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_arquivamento.cryo --backend pyro
```

### 2. Testes de Integração HTTP da Landing Page (11 testes)
```powershell
python tests/test_landing_http.py
```

### 3. Testes de Interação Cognitiva da LLM em Tempo Real (12 etapas)
Com os binários `emp.exe` e `landing.exe` em execução, valida o fluxo completo fim a fim:
```powershell
python tests/test_realtime_llm.py
```
> Executa 12 etapas automáticas: checagem de saúde dos servidores, despacho de prompt em linguagem natural, telemetria analógica com disparo de alarme crítico (98°C) e parada de segurança `maquina.parada`, bloqueio de ordens no posto interditado (HTTP 409), criação e apontamento de OP via pulsos de CLP, fechamento contábil e arquivamento permanente para `tblFinOrder`/`tblFinStep`.
