# EMP — Engineering Modular Process

ERP modular para gestão de linha de produção, escrito **somente em Cryo** e
compilado para um **executável nativo do Windows** (`emp.exe`, ~1 MB, sem
Python, Go ou VM em tempo de execução). Escopo, arquitetura e lacunas da
linguagem: **[ESCOPO.md](ESCOPO.md)** · Histórico: **[CHANGELOG.md](CHANGELOG.md)**.

![Visão geral do EMP](docs/screenshots/01-visao-geral.png)

## O que ele faz

| Módulo | Tipo | Faz |
|---|---|---|
| **Cadastros** | interno | Produtos (MP/SA/PA), estrutura de produto (BOM), postos de trabalho |
| **Produção** | interno | Ordens de produção, liberação, apontamento de boas/refugo, indicadores; recusa apontar em posto parado |
| **Estoque** | interno | Saldos, entradas, ajuste de inventário, **baixa automática por estrutura** (backflush), alerta de falta |
| **Manutenção** | interno | Paradas de posto por categoria, registro retroativo, disponibilidade na janela de 8 h, MTTR |
| **Qualidade** | **plugin externo** | Não conformidades manuais e automáticas (refugo acima do limite) — processo próprio, sem recompilar o núcleo |

Os módulos não se chamam: reagem a **eventos**. Quando a Manutenção abre uma
parada, publica `maquina.parada`; a Produção assina esse evento e passa a
recusar apontamento naquele posto. Nenhum dos dois importa o outro.

## Telas

| | |
|---|---|
| ![Ordens de produção](docs/screenshots/02-ordens.png) **Ordens** — criar, liberar, apontar e cancelar OPs; progresso por ordem | ![Estoque](docs/screenshots/03-estoque.png) **Estoque** — saldos e movimentos; o consumo dos componentes sai sozinho a cada apontamento |
| ![Manutenção](docs/screenshots/04-manutencao.png) **Manutenção** — estado de cada posto, disponibilidade, MTTR, minutos por categoria | ![Qualidade](docs/screenshots/05-qualidade.png) **Qualidade** (plugin) — NC automática quando o refugo passa de 5% |
| ![Cadastros](docs/screenshots/06-cadastros.png) **Cadastros** — produtos, estrutura (BOM) e postos | ![Eventos](docs/screenshots/07-eventos.png) **Eventos** — o que cada módulo publicou no barramento |
| ![Módulos](docs/screenshots/08-modulos.png) **Módulos** — internos e plugins, com o estado de cada um | |

As capturas foram feitas com o `emp.exe` real, populado por
[`tools/demo.cryo`](tools/demo.cryo) e depois operado pelo navegador (parada
encerrada, apontamento e OP criados pelo painel).

## Compilar

O toolchain Cryo é procurado na pasta acima deste repositório (ou em `CRYO_HOME`).
Precisa de Python 3 e do MinGW gcc em `C:\MinGW\bin`.

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Roda os testes e gera `build\emp.exe` e `build\qualidade.exe` (plugin).

Durante o desenvolvimento, sem gerar o `.exe`:

```bash
python ../Burnout/cryoc.py src/main.cryo --backend pyro -o build/emp.pyro --run
```

## Rodar

```powershell
$env:ERP_TOKENS="tk-ana:ana:admin,tk-joao:joao:operador,tk-rui:rui:almoxarife,tk-lia:lia:manutencao"
$env:PYRO_HTTP_TIMEOUT_MS="2000"
.\qualidade.exe          # opcional: plugin, porta 8091
.\emp.exe                # painel em http://127.0.0.1:8080
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

Perfis: `admin`, `pcp`, `operador`, `almoxarife`, `manutencao`, `qualidade`, `consulta`.

### Dados de demonstração

Com o `emp.exe` em modo dev (sem `ERP_TOKENS`):

```bash
python ../Burnout/cryoc.py tools/demo.cryo --backend pyro --run
```

Cria uma linha de suportes metálicos: 7 produtos com estrutura, 5 postos,
entradas de estoque, 6 OPs em estados diferentes, apontamentos, 3 paradas e
uma NC manual.

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
curl -H "Authorization: Bearer tk-lia" -X POST $U/api/manutencao/paradas -d "posto=PRENSA1&categoria=ELETRICA&motivo=Disjuntor&ha_minutos=10"
curl -H "$T" $U/api/manutencao/postos
```

| Prefixo | Rotas |
|---|---|
| `/api/sistema` | `GET /saude`, `GET /modulos`, `GET /eventos[?n=]`, `GET /sessao` |
| `/api/cadastros` | `GET/POST /produtos`, `GET/POST /estrutura`, `GET/POST /postos` |
| `/api/producao` | `GET/POST /ordens`, `GET /ordem?id=`, `POST /liberar?id=`, `POST /apontar?id=`, `POST /cancelar?id=`, `GET /indicadores` |
| `/api/estoque` | `GET /saldos[?produto=]`, `GET /movimentos`, `POST /entrada`, `POST /ajuste` |
| `/api/manutencao` | `GET/POST /paradas`, `POST /encerrar?id=`, `GET /postos`, `GET /indicadores` |
| `/api/qualidade` (plugin) | `GET/POST /ncs` |

## Testes

```bash
python ../Burnout/cryoc.py tests/test_nucleo.cryo --backend pyro --run
python ../Burnout/cryoc.py test tests/test_eventos.cryo --backend pyro
```
