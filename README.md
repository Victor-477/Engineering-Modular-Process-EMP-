# EMP — Engineering Modular Process

ERP modular para gestão de linha de produção, escrito **somente em Cryo** e
compilado para um **executável nativo do Windows** (`emp.exe`, ~1 MB, sem
Python, Go ou VM em tempo de execução). Escopo, arquitetura e lacunas da
linguagem: **[ESCOPO.md](ESCOPO.md)** · Histórico: **[CHANGELOG.md](CHANGELOG.md)**.

![Visão geral do EMP](docs/screenshots/01-visao-geral.png)

## O que ele faz

| Módulo | Tipo | Faz |
|---|---|---|
| **Cadastros** | interno | Produtos (MP/SA/PA), estrutura de produto (BOM) com etapa de consumo para backflush, postos de trabalho |
| **Roteiros** | interno | Operações (com parâmetros medidos e limites), roteiro de etapas por produto, capacidades posto × operação |
| **Produção** | interno | Ordens de produção executadas **etapa por etapa** (copiadas do roteiro na liberação), fila por posto, medições, concorrência por versão, indicadores; recusa trabalhar em posto parado |
| **Pedidos** | interno | Clientes e pedidos de venda com itens e prazo; gera as OPs da falta (com reserva entre pedidos), fica pronto quando as OPs concluem ou o saldo cobre, expede e avisa atraso |
| **Estoque** | interno | Saldos **por endereço** (almoxarifado, linha do posto, expedição, quarentena), transferências, ajuste de inventário, **baixa automática por estrutura e etapa** (backflush na linha do posto da etapa), baixa na expedição, **reposição mín./máx.** com sugestões de compra ou produção |
| **Manutenção** | interno | Paradas de posto por categoria, registro retroativo, disponibilidade na janela de 8 h, MTTR |
| **Indicadores** | interno | Histórico de estado de cada posto (operando, parado, ocioso) e **OEE** = disponibilidade × desempenho × qualidade, por posto e da linha, com série por hora e alerta de OEE baixo — calculado só a partir dos eventos |
| **PCP / MRP** | interno | Planejamento de necessidades de materiais: explosão multinível de BOM, cálculo de necessidade líquida cruzando pedidos e reposição mínima com saldo e OPs abertas, geração automática de ordens de produção (`POST /api/mrp/gerar_ordens`) |
| **Programação (APS)** | interno | Sequenciamento e capacidade finita: carga × capacidade por posto, identificação de gargalos, fila sequenciada por prioridade e EDD (Earliest Due Date), projeção contínua de cronograma e alerta de atraso |
| **Lotes & Rastreabilidade** | interno | Rastreabilidade e genealogia industrial: controle de lotes (status/validade), árvore genealógica de insumos consumidos em cada etapa da OP, expedição a clientes e rastreamento bidirecional (backward de insumos e forward recall de clientes) |
| **Qualidade** | **plugin externo** | Não conformidades manuais e automáticas (refugo acima do limite) — processo próprio, sem recompilar o núcleo |
| **Compras** | **plugin externo** | Gestão de fornecedores, pedidos de compra, recebimento com entrada automática no estoque do EMP e reação a faltas de estoque — processo próprio |

Os módulos não se chamam: reagem a **eventos**. Quando a Manutenção abre uma
parada, publica `maquina.parada`; a Produção assina esse evento e passa a
recusar apontamento naquele posto. Nenhum dos dois importa o outro.

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

As capturas foram feitas com o `emp.exe` real, populado pelas cargas de
demonstração (abaixo) e operado pela API e pelo painel, com o Edge headless (`--headless=new --screenshot`, 1440 px de largura
no painel; o tema claro forçado com `--blink-settings=preferredColorScheme`).

## Compilar

O toolchain Cryo é procurado na pasta acima deste repositório (ou em `CRYO_HOME`).
Precisa de Python 3 e do MinGW gcc em `C:\MinGW\bin`.

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Roda os testes e gera `build\emp.exe` e os plugins `build\qualidade.exe` e `build\compras.exe`.

Durante o desenvolvimento, sem gerar o `.exe`:

```bash
python ../Burnout/cryoc.py src/main.cryo --backend pyro -o build/emp.pyro --run
```

## Rodar

```powershell
$env:ERP_TOKENS="tk-ana:ana:admin,tk-joao:joao:operador,tk-rui:rui:almoxarife,tk-lia:lia:manutencao"
$env:PYRO_HTTP_TIMEOUT_MS="2000"
.\qualidade.exe          # opcional: plugin, porta 8091
.\emp.exe                # painel em http://127.0.0.1:8080, terminal em /terminal
```

> Use **`http://127.0.0.1:8080`** (ou o IP do servidor), não `localhost`: o
> servidor nativo só escuta IPv4 e o Windows tenta IPv6 primeiro, o que custa
> ~200 ms por requisição — medido: atualização do painel em 67 ms pelo IP
> contra 669 ms por `localhost`.

| Variável | Padrão | |
|---|---|---|
| `ERP_PORTA` | `8080` | porta HTTP |
| `ERP_DADOS` | `dados` | diretório de dados |
| `ERP_PLUGINS` | `plugins` | manifestos `*.plugin` |
| `ERP_TOKENS` | vazio | `token:usuario:perfil,...` — vazio = **modo dev**, sem autenticação |
| `PYRO_HTTP_TIMEOUT_MS` | `10000` | prazo para uma requisição chegar inteira; use 1000–2000 (o servidor é sequencial e navegadores abrem conexões que não usam) |
| `PYRO_HTTP_CLIENT_TIMEOUT_MS` | `15000` | prazo de cada chamada a um plugin |
| `QUALIDADE_PORTA` / `QUALIDADE_LIMITE` | `8091` / `5` | plugin de qualidade |

Perfis: `admin`, `pcp`, `comercial`, `operador`, `almoxarife`, `manutencao`, `qualidade`, `consulta`.

### Dados de demonstração

Com o `emp.exe` em modo dev (sem `ERP_TOKENS`):

```bash
python ../Burnout/cryoc.py tools/demo.cryo --backend pyro --run
python ../Burnout/cryoc.py tools/demo_estoque.cryo --backend pyro --run
python ../Burnout/cryoc.py tools/demo_comercial.cryo --backend pyro --run
python ../Burnout/cryoc.py tools/demo_oee.cryo --backend pyro --run
```

`demo.cryo` cria uma linha de suportes metálicos: 7 produtos com estrutura,
5 postos, 4 operações com roteiros e capacidades, entradas de estoque, 6 OPs
em estados diferentes (uma passa pelas 4 etapas do SUP-02, com erro e
reinício), apontamentos, 3 paradas e NCs. As outras acrescentam endereços,
transferências e regras de reposição; clientes e pedidos em todos os estados;
e atividade com paradas retroativas para o OEE. **Rode nessa ordem**: a carga
de estoque transfere quantidades fixas e falha se a comercial já tiver
expedido as peças. `EMP_URL` muda o endereço (padrão `http://127.0.0.1:8080`).

## API (corpos em form-urlencoded)

```bash
U=http://127.0.0.1:8080; T="Authorization: Bearer tk-ana"
curl -H "$T" -X POST $U/api/cadastros/produtos -d "codigo=aco&tipo=MP&unidade=KG"
curl -H "$T" -X POST $U/api/cadastros/produtos -d "codigo=sup01&tipo=PA"
curl -H "$T" -X POST $U/api/cadastros/estrutura -d "produto=sup01&componente=aco&quantidade=1,5"
curl -H "$T" -X POST $U/api/cadastros/postos -d "codigo=PRENSA1&descricao=Prensa+80t&capacidade_h=16"
curl -H "Authorization: Bearer tk-rui" -X POST $U/api/estoque/entrada -d "produto=aco&quantidade=100"
curl -H "$T" -X POST $U/api/producao/ordens -d "produto=sup01&quantidade=50&posto=PRENSA1"
curl -H "$T" -X POST "$U/api/producao/liberar?id=1"
curl -H "Authorization: Bearer tk-joao" -X POST "$U/api/producao/apontar?id=1" -d "boa=30&refugo=2"
# roteiro e execução por etapa (a versão vem de GET /ordem ou GET /fila)
curl -H "$T" -X POST $U/api/roteiros/operacoes -d "codigo=ESTAMPAR&tipo=AUTOMATICA&parametros=espessura:mm:1.9:2.1"
curl -H "$T" -X POST $U/api/roteiros/etapa -d "produto=sup01&numero=10&operacao=ESTAMPAR&posto=PRENSA1&tempo_min=0.05"
curl -H "$T" "$U/api/producao/fila?posto=PRENSA1"
curl -H "Authorization: Bearer tk-joao" -X POST "$U/api/producao/etapa/iniciar?op=2&etapa=10" -d "versao=1"
curl -H "Authorization: Bearer tk-joao" -X POST "$U/api/producao/etapa/apontar?op=2&etapa=10" -d "versao=2&boas=40&refugo=1&medicoes=espessura%3D2.01"
curl -H "Authorization: Bearer tk-lia" -X POST $U/api/manutencao/paradas -d "posto=PRENSA1&categoria=ELETRICA&motivo=Disjuntor&ha_minutos=10"
curl -H "$T" $U/api/manutencao/postos
```

| Prefixo | Rotas |
|---|---|
| `/api/sistema` | `GET /saude`, `GET /modulos`, `GET /eventos[?n=]`, `GET /sessao` |
| `/api/cadastros` | `GET/POST /produtos`, `GET/POST /estrutura`, `GET/POST /postos` |
| `/api/roteiros` | `GET/POST /operacoes`, `GET /roteiro?produto=`, `POST /etapa`, `POST /remover_etapa?produto=&numero=`, `GET /capacidades`, `POST /capacidade` |
| `/api/producao` | `GET/POST /ordens`, `GET /ordem?id=`, `POST /liberar?id=`, `POST /apontar?id=`, `POST /cancelar?id=`, `GET /fila?posto=`, `POST /etapa/iniciar\|apontar\|concluir\|erro\|reiniciar\|pular?op=&etapa=`, `GET /indicadores` |
| `/api/pedidos` | `GET/POST /clientes`, `GET/POST /pedidos[?status=]`, `GET /pedido?id=`, `POST /gerar_ops?id=`, `POST /expedir?id=`, `POST /cancelar?id=` |
| `/api/estoque` | `GET /saldos[?produto=]`, `GET /movimentos`, `POST /entrada`, `POST /ajuste`, `GET/POST /enderecos`, `GET /posicoes[?endereco=]`, `POST /transferir`, `GET/POST /reposicao`, `GET /sugestoes` |
| `/api/manutencao` | `GET/POST /paradas`, `POST /encerrar?id=`, `GET /postos`, `GET /indicadores` |
| `/api/indicadores` | `GET /estados?posto=&horas=`, `GET /oee?horas=`, `GET /oee/serie?posto=&horas=&passo_min=` |
| `/api/mrp` | `GET /plano`, `POST /gerar_ordens` |
| `/api/qualidade` (plugin) | `GET/POST /ncs` |
| `/api/compras` (plugin) | `GET/POST /fornecedores`, `GET/POST /pedidos`, `POST /pedidos/receber?id=`, `POST /pedidos/cancelar?id=`, `GET /sugestoes` |

## Testes

```bash
python ../Burnout/cryoc.py tests/test_nucleo.cryo --backend pyro --run
python ../Burnout/cryoc.py test tests/test_eventos.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_etapas.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_pedidos.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_estoque.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_oee.cryo --backend pyro
python ../Burnout/cryoc.py test tests/test_mrp.cryo --backend pyro
```

O `build.ps1` roda todos. Detalhes de cada frente da fase 2 (decisões,
verificação e limites) em [`docs/fase2/`](docs/fase2/).
