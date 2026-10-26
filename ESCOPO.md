# EMP — Escopo, Arquitetura e Lacunas da Linguagem

> ERP modular para gestão de linha de produção, escrito **somente em Cryo**,
> executado num servidor Windows como **executável nativo** (`emp.exe`).
>
> Estado: **esqueleto funcional (v0.1.0)**. O núcleo, três módulos internos e um
> plugin externo compilam, rodam e foram exercitados por HTTP. As seções 10 e 11
> listam o que falta na linguagem para que isso vá para produção.

---

## 1. Objetivo

Gerenciar o ciclo produtivo de uma linha de produção — do cadastro do produto à
ordem de produção, apontamento no chão de fábrica, consumo de materiais e
qualidade — num servidor único, com módulos que podem ser **acrescentados sem
reescrever o sistema**.

Requisitos que orientaram a arquitetura:

| # | Requisito | Como é atendido |
|---|---|---|
| R1 | Só Cryo | Núcleo, módulos, plugin e até a página do painel são `.cryo` |
| R2 | Executável Windows | `.cryo → .pyro → C (AOT) → gcc → .exe`, sem Python/Go/VM em runtime |
| R3 | Modular | Contrato de módulo + registro dinâmico + barramento de eventos (§3) |
| R4 | Novos módulos sem "grandes atualizações" | Módulo interno = 1 arquivo novo + 2 linhas no catálogo; plugin externo = 1 `.exe` + 1 manifesto, **sem recompilar** (§9) |
| R5 | Servidor | API HTTP + painel web, configurado por variáveis de ambiente |

## 2. Escopo funcional

### 2.1 Entregue (v0.2 + fases 1 e 2)

| Módulo | Tipo | Responsabilidade | Eventos publicados | Assina |
|---|---|---|---|---|
| **Cadastros** | interno | Produtos (MP/SA/PA), estrutura de produto (BOM), postos de trabalho | `produto.salvo`, `estrutura.alterada` | — |
| **Roteiros** | interno | Operações (tipo, instrução, parâmetros medidos com limites), roteiro de etapas por produto, capacidades posto × operação | `operacao.salva`, `roteiro.alterado`, `capacidade.salva` | — |
| **Produção** | interno | Ordens de produção (OP) executadas por **etapa** (cópia do roteiro na liberação), fila por posto, medições, concorrência por `versao`, apontamento boa/refugo, `origem` da OP (pedido, reposição), indicadores; recusa trabalhar em posto parado | `op.criada`, `op.liberada`, `op.cancelada`, `op.concluida`, `producao.apontada`, `producao.etapa_iniciada`, `producao.etapa_apontada`, `producao.etapa_concluida`, `producao.etapa_falhou` | `maquina.*` |
| **Pedidos** | interno | Clientes; pedidos com itens e prazo; OPs da falta com reserva entre pedidos; pronto por OPs concluídas ou saldo; expedição; atraso | `pedido.criado`, `pedido.ops_geradas`, `pedido.pronto`, `pedido.expedido`, `pedido.cancelado` | `op.*`, `producao.apontada`, `estoque.movimentado` |
| **Estoque** | interno | Saldos por produto × **endereço**, transferências, entrada e ajuste por endereço, **backflush** (primeiro da linha do posto), baixa na expedição, alerta de falta, **reposição mín./máx.** com sugestões (descontando OPs abertas) | `estoque.movimentado`, `estoque.falta`, `estoque.negativo`, `estoque.abaixo_minimo` | `producao.apontada`, `op.*`, `pedido.expedido` |
| **Manutenção** | interno | Paradas corretivas por categoria, registro retroativo, MTTR, disponibilidade na janela de 8 h; e **manutenção preventiva** com planos por horas ou ciclos acumulados a partir do chão de fábrica, alertas e histórico | `maquina.parada`, `maquina.liberada`, `manutencao.preventiva_vencida`, `manutencao.preventiva_executada` | `producao.etapa_apontada`, `producao.apontada` |
| **Indicadores** | interno, só leitura | Histórico de estado do posto (PARADO > OPERANDO > OCIOSO) e **OEE** por posto e da linha, série por hora, alerta de OEE baixo — só a partir dos eventos | `indicadores.oee_baixo` | `maquina.*`, `producao.etapa_*` |
| **PCP / MRP** | interno | Explosão de estrutura multinível (BOM), cálculo de necessidade líquida cruzando pedidos e reposição com saldo e produção aberta, geração automática de OPs com origem `MRP` | `mrp.ordens_geradas` | `op.*`, `pedido.*`, `estoque.movimentado` |
| **Programação (APS)** | interno | Carga × capacidade por posto, ocupação percentual, detecção de gargalo, sequenciamento inteligente por prioridade/EDD, cronograma contínuo e alerta de atraso | `programacao.sobrecarga` | `op.*`, `producao.etapa_*` |
| **Lotes & Rastreabilidade** | interno | Controle de lotes (status/validade), árvore genealógica industrial pai-filho no consumo de etapas, geração de lote em OP, expedição a clientes e rastreamento bidirecional (backward e forward recall) | `lote.criado`, `lote.bloqueado`, `lote.liberado`, `lote.consumido` | `op.concluida`, `producao.etapa_apontada`, `pedido.expedido`, `estoque.movimentado` |
| **Custos Industriais** | interno | Custo padrão da engenharia (MD + MOD/GGF) vs. custo real da OP, apropriação de materiais e horas, taxa de refugo, análise de desvio e fechamento contábil | `custos.op_fechada` | `op.concluida`, `producao.apontada` |
| **Turnos & Operadores** | interno | Gestão de escalas de turnos, alocação de operadores aos postos, turno ativo, acumulação de métricas por apontamento, eficiência e qualidade por operador | `turnos.alocacao_alterada`, `turnos.atual_alterado` | `producao.etapa_apontada`, `producao.apontada` |
| **Relatórios e BI** | interno | Painel analítico executivo, nível de serviço de pedidos (OTIF), ranking de perdas/refugos, desempenho e custo de postos e exportações analíticas em CSV | `relatorios.alerta_gerencial` | `pedido.expedido`, `producao.apontada`, `custos.op_fechada` |
| **Coleta Automática & IoT** | interno | Contadores de pulsos de CLP, telemetria de sensores (temperatura/pressão), intertravamento de segurança com parada automática e apontamento automático de chão de fábrica | `coleta.pulso_registrado`, `coleta.alerta_critico`, `coleta.estado_alterado`, `maquina.parada` | `maquina.parada`, `maquina.liberada` |
| **Arquivamento e Histórico** | interno | Expurgar/congelar OPs concluídas antigas em arquivo histórico permanente (`tblFinOrder`, `tblFinStep`) com retenção temporal, reversibilidade total para auditoria e garantia de alta performance operacional | `arquivamento.op_arquivada`, `arquivamento.lote_concluido`, `arquivamento.op_desarquivada` | `op.concluida` |
| **Qualidade** | **plugin externo** (processo próprio) | Não conformidades (NC) manuais e automáticas (refugo acima do limite) | — | `producao.apontada` |
| **Compras** | **plugin externo** (processo próprio) | Fornecedores, pedidos de compra, recebimento com entrada automática no estoque do EMP e reação a faltas | — | `estoque.falta`, `estoque.abaixo_minimo` |
| **Sistema** | núcleo | Saúde, módulos e estado, feed de eventos, sessão, autenticação, perfis, auditoria, painel web com abas e formulários | — | — |

Máquina de estados da OP:

```
PLANEJADA --liberar--> LIBERADA --iniciar/apontar--> EM_PRODUCAO --(última etapa termina)--> CONCLUIDA
    |                     |
    +------cancelar-------+------cancelar------> CANCELADA
```

Máquina de estados de cada **etapa** da OP (`producao/etapas.cryo`). Só a
etapa atual — a primeira não concluída nem pulada — aceita ações; toda mudança
soma 1 à `versao`, e uma ação com versão diferente recebe 409 ("a tarefa foi
alterada por outra pessoa").

```
AGUARDANDO  --iniciar-->  EM_EXECUCAO
EM_EXECUCAO --apontar (boas+refugo >= entrada)--> CONCLUIDA
EM_EXECUCAO --concluir (com o que já foi apontado)--> CONCLUIDA
AGUARDANDO | EM_EXECUCAO --erro (motivo)--> FALHA
FALHA | EM_EXECUCAO --reiniciar (pcp/admin)--> AGUARDANDO
não final e sem apontamentos --pular (pcp/admin, motivo)--> PULADA
```

Quantidades: a 1ª etapa recebe a quantidade da OP; cada etapa seguinte recebe
as boas da anterior (ou a entrada inteira, se a anterior foi pulada). Todo
refugo apontado entra no `refugo` da OP; só a **última** etapa soma em
`produzido` e publica `producao.apontada`, levando junto o refugo das etapas
anteriores ainda não publicado — o backflush consome o material de boas + todo
o refugo. Peças que "somem" num `concluir` com menos que a entrada não são
baixadas do estoque.

### 2.2 Planejado (próximas fases e extensões modulares)

Todas as 10 fases modulares planejadas inicialmente foram integralmente implementadas e validadas (101 testes automatizados). Extensões futuras podem incluir:

| Módulo / Recurso | Interno/Plugin | Depende de | Observação |
|---|---|---|---|
| Gateway OPC-UA / MQTT | plugin externo | coleta | Conexão de rede industrial padronizada para CLP Siemens/Rockwell |
| Algoritmos Genéticos de APS | interno | programacao | Otimização heurística avançada de sequenciamento multidimensional |

### 2.3 Fora do escopo

Contabilidade fiscal/SPED, folha de pagamento, NF-e, multiempresa e
alta disponibilidade (cluster). São possíveis mais tarde como plugins, mas
dependem de criptografia/TLS (L-04) e de banco de dados (L-02).

## 3. Arquitetura

```
                        navegador / terminal de apontamento / integrações
                                          │  HTTP (Bearer token)
┌─────────────────────────────────────────▼─────────────────────────────────────────┐
│ emp.exe  (um processo, um laço de requisições)                                   │
│                                                                                    │
│  main.cryo ── http_accept ─► seguranca (token→usuário:perfil)                      │
│                               │                                                    │
│                               ▼                                                    │
│                         registro.despachar(path)  ──► RBAC (perfis_escrita)         │
│                               │  escolhe o módulo pelo PREFIXO                     │
│        ┌──────────────────────┼───────────────────────┬────────────────────┐       │
│        ▼                      ▼                       ▼                    ▼       │
│   cadastros               producao                 estoque        [proxy de plugin]│
│   (fn values)             (fn values)              (fn values)    closures c/ URL  │
│        │                      │ ev.publicar            ▲                   │       │
│        └──────────────────────┴──────► eventos (fila) ─┘                   │       │
│                                         │ drenar após responder            │       │
│   persist (JSON atômico por coleção)    │ entrega a quem assina            │       │
│   auditoria (arquivos imutáveis)        └──────────────────────────────────┤       │
└────────────────────────────────────────────────────────────────────────────┼───────┘
                                                                             │ HTTP localhost
                                                         ┌───────────────────▼───────┐
                                                         │ qualidade.exe (plugin)    │
                                                         │ /saude  /req  /evento     │
                                                         └───────────────────────────┘
```

### 3.1 Princípio central: o núcleo nunca importa um módulo

O compilador recusa ciclos de import. Se o núcleo importasse os módulos e os
módulos importassem o núcleo, haveria ciclo. Por isso cada módulo **entrega um
descritor** (`k::Modulo`) cujas operações são **valores de função**; o
registro guarda esses valores e os chama. O núcleo é compilado sem saber quais
módulos existem.

### 3.2 Dois níveis de modularidade

| | Módulo **interno** | Módulo **externo (plugin)** |
|---|---|---|
| Onde roda | Dentro de `emp.exe` | Processo separado (`<id>.exe`) |
| Como entra | Import + 1 linha em `modulos/catalogo.cryo` | Manifesto `plugins/<id>.plugin` |
| Exige recompilar o núcleo | Sim (build de ~1 min) | **Não** — reiniciar o serviço |
| Custo por chamada | Chamada de função | Requisição HTTP local (ms) |
| Falha do módulo | Afeta o processo | Isolada: vira `503`, disjuntor abre |
| Acesso a outros módulos | API `pub` direta (dependência declarada) | Só pela API HTTP do ERP e por eventos |
| Indicado para | Núcleo do negócio, alta frequência | Funções opcionais, por cliente, de terceiros |

Para o registro um plugin é **indistinguível** de um módulo interno: o
carregador fabrica um `k::Modulo` cujas funções são *closures* que capturam a URL
do plugin (`nucleo/plugins.cryo`).

### 3.3 Fluxo de uma requisição

1. `http_accept()` devolve o mapa da requisição (método, path, query, corpo, `header:*`).
2. `seguranca::identificar` resolve o token `Bearer` em `usuario:perfil` (401 se falhar).
3. `/api/sistema/*` é atendido pelo núcleo; o resto vai a `registro::despachar`.
4. O registro acha o módulo pelo prefixo, confere se está **ativo** (503 se não) e,
   para métodos de escrita, se o perfil está em `perfis_escrita` (403 se não).
5. O módulo recebe uma `k::Requisicao` com `rota` **relativa ao prefixo**.
6. O núcleo responde, grava a trilha de auditoria (escritas bem-sucedidas) e
   **só então** drena a fila de eventos.

### 3.4 Barramento de eventos

- `ev::publicar(tipo, origem, dados)` apenas **enfileira**.
- Após cada resposta, `registro::drenar_eventos(1000)` entrega cada evento a todo
  módulo ativo cuja assinatura casa (`"op.liberada"`, `"op.*"` ou `"*"`), exceto à origem.
- Eventos publicados durante a entrega vão para o fim da fila; o limite de 1000
  entregas por ciclo corta laços infinitos entre módulos.
- `dados` usa *form-encoding* (`op=3&produto=X`), não JSON — ver L-05.

Catálogo de eventos:

| Evento | Origem | Dados |
|---|---|---|
| `produto.salvo` | cadastros | `codigo` |
| `estrutura.alterada` | cadastros | `produto` |
| `op.criada` / `op.liberada` / `op.cancelada` / `op.concluida` | produção | `op`, `produto`, `quantidade`, `origem` |
| `producao.apontada` | produção | `op`, `produto`, `boa`, `refugo`, `posto`, `operador` |
| `producao.etapa_iniciada` / `_apontada` / `_concluida` / `_falhou` | produção | `op`, `produto`, `etapa`, `posto`, `operacao`, `tempo_min`, `entrada`, `boas`, `refugo` (acumulados), `delta_boas`, `delta_refugo` (desta ação), `inicio`, `fim`, `operador`, `motivo`, `status` |
| `pedido.criado` / `.ops_geradas` / `.pronto` / `.expedido` / `.cancelado` | pedidos | `pedido`, `cliente`, `itens="PRODUTO:qtd;..."` (+ `entrega_prevista`, `ops`, `por`, `motivo`) |
| `operacao.salva` | roteiros | `codigo` |
| `roteiro.alterado` | roteiros | `produto`, `etapas` |
| `capacidade.salva` | roteiros | `posto`, `operacao` |
| `estoque.movimentado` | estoque | `produto`, `quantidade`, `saldo`, `endereco`, `saldo_endereco` |
| `estoque.falta` | estoque | `op`, `componente`, `necessario`, `disponivel` |
| `estoque.negativo` | estoque | `produto`, `saldo` (do endereço), `endereco`, `saldo_total` |
| `estoque.abaixo_minimo` | estoque | `produto`, `saldo`, `minimo`, `maximo`, `sugerido`, `tipo`, `endereco` |
| `maquina.parada` / `maquina.liberada` | manutenção | `parada`, `posto`, `categoria`, `motivo`, `inicio`, `fim`, `minutos` |
| `indicadores.oee_baixo` | indicadores | `oee`, `limite`, `horas`, `disponibilidade`, `desempenho`, `qualidade` |

## 4. Contrato de módulo (ABI) — `src/nucleo/contrato.cryo`

```cryo
pub struct Modulo {
    string id;  string nome;  string versao;
    int contrato;            // versão do contrato para a qual foi escrito
    string prefixo;          // "/api/producao"
    string[] depende;        // módulos que precisam estar ativos antes
    string[] assina;         // eventos de interesse
    string[] perfis_escrita; // quem pode POST
    fn(string)->bool iniciar;                // recebe o diretório de dados
    fn(Requisicao)->Resposta rotear;
    fn(Evento)->bool ao_evento;
}
```

Regras:

1. **Campos só são acrescentados ao fim** das structs do contrato; ao mudar algo
   incompatível, sobe `VERSAO_CONTRATO`. O registro recusa um módulo que exige um
   contrato mais novo que o do núcleo.
2. Cada módulo grava **somente** em `dados/<id>/`.
3. Comunicação entre módulos: **eventos** para reagir a fatos; API `pub` direta
   apenas para consulta, com dependência declarada em `depende`.
4. Ordem de inicialização é derivada de `depende`. Módulo cuja dependência não
   subiu fica `falhou: dependência ausente` e o resto do ERP continua no ar.
5. Entrada externa (corpo HTTP) é **form-urlencoded** e passa por `nucleo/form.cryo`.

## 5. Estrutura de diretórios

```
Engineering-Modular-Process-EMP-/
├── ESCOPO.md                  este documento
├── README.md                  como compilar, rodar e usar a API (com capturas)
├── CHANGELOG.md               histórico de versões
├── build.ps1                  testes + build dos .exe
├── src/
│   ├── main.cryo              bootstrap, configuração, laço HTTP, rotas /api/sistema
│   ├── nucleo/
│   │   ├── contrato.cryo      ABI: Modulo, Requisicao, Resposta, Evento
│   │   ├── registro.cryo      registro, ordem de dependência, roteamento, entrega de eventos
│   │   ├── eventos.cryo       fila de eventos e casamento de assinaturas
│   │   ├── seguranca.cryo     tokens e perfis (RBAC)
│   │   ├── auditoria.cryo     trilha de auditoria em arquivos imutáveis
│   │   ├── persist.cryo       coleções JSON com gravação atômica
│   │   ├── form.cryo          leitura segura de form-urlencoded e números
│   │   ├── plugins.cryo       descoberta de plugins, proxy HTTP, disjuntor
│   │   └── painel.cryo        painel web gerado em Cryo
│   └── modulos/
│       ├── catalogo.cryo      ÚNICO arquivo editado para incluir módulo interno
│       ├── cadastros/cadastros.cryo
│       ├── roteiros/roteiros.cryo   operações, roteiros, capacidades
│       ├── producao/producao.cryo
│       ├── producao/etapas.cryo     máquina de estados das etapas (funções puras)
│       ├── pedidos/pedidos.cryo     clientes, pedidos, OPs da falta, expedição
│       ├── estoque/estoque.cryo     saldos por endereço, transferência, reposição
│       ├── estoque/regras.cryo      regras puras do estoque (repartição, mínimo, sugestão)
│       ├── manutencao/manutencao.cryo
│       ├── indicadores/indicadores.cryo  eventos → histórico do posto, rotas de OEE
│       ├── indicadores/oee.cryo     cálculo puro do OEE
│       ├── mrp/mrp.cryo             planejamento de necessidades (BOM, pedidos, ordens)
│       └── programacao/programacao.cryo  sequenciamento e capacidade finita (APS, EDD, gargalos)
├── plugins/                   manifestos lidos em tempo de execução
│   ├── qualidade.plugin
│   └── compras.plugin
├── plugins_src/
│   ├── qualidade/qualidade.cryo
│   └── compras/compras.cryo
├── tests/
│   ├── test_nucleo.cryo       harness em programa comum
│   ├── test_eventos.cryo      `test fn` rodado por `cryoc test`
│   ├── test_etapas.cryo       `test fn`: etapas, versão/409, medições, roteiros
│   ├── test_pedidos.cryo      pedidos, reserva, falta, expedição, OP antiga
│   ├── test_estoque.cryo      endereços, migração, backflush por etapa, reposição, expedição
│   ├── test_oee.cryo          janela, sobreposição, limites do OEE
│   ├── test_mrp.cryo          plano multinível, cobertura, ordens automáticas
│   └── test_programacao.cryo  capacidade, gargalo, fila EDD, projeção de cronograma
├── tools/                     cargas de demonstração (via HTTP, modo dev), nesta ordem:
│   ├── demo.cryo              linha base: produtos, roteiros, OPs, paradas
│   ├── demo_estoque.cryo      endereços, transferências, reposição
│   ├── demo_comercial.cryo    clientes e pedidos em todos os estados
│   └── demo_oee.cryo          atividade e paradas retroativas para o OEE
├── docs/
│   ├── ANALISE_FACTORYVIEWS.md  análise do MES4 e fase 1
│   ├── FASE2.md               contrato da fase 2
│   ├── fase2/                 decisões, verificação e limites de cada frente
│   ├── DESIGN_SYSTEM.md       sistema de design Forja
│   └── screenshots/           capturas do painel e do terminal
└── build/                     emp.exe, compras.exe, qualidade.exe (gerados)
```

Instalação no servidor:

```
C:\EMP\
├── emp.exe
├── compras.exe
├── qualidade.exe
├── plugins\
│   ├── compras.plugin
│   └── qualidade.plugin
└── dados\                     criado na primeira execução
    ├── cadastros\produtos.json  estrutura.json  postos.json
    ├── roteiros\operacoes.json  roteiros.json  capacidades.json
    ├── producao\ordens.json  etapas.json
    ├── pedidos\clientes.json  pedidos.json  ops.json
    ├── estoque\saldos.json  posicoes.json  enderecos.json  movimentos.json  reposicao.json  ops_abertas.json
    ├── manutencao\paradas.json
    ├── indicadores\intervalos.json  apontamentos.json  estado.json
    ├── programacao\prioridades.json
    ├── compras\fornecedores.json  pedidos.json
    ├── qualidade\ncs.json
    └── auditoria\<ms>-<seq>.log
```

## 6. Dados e persistência

- Cada coleção é um objeto JSON `id → registro` em `dados/<modulo>/<colecao>.json`.
- Toda gravação usa `write_file_atomic` (arquivo temporário + rename): uma queda de
  energia no meio da escrita deixa a versão anterior intacta.
- O estado fica em memória (estado de módulo) e é recarregado no `iniciar`.
- Ids continuam crescendo após reinício (`persist::maior_id`).
- **Limites conhecidos** (L-02): cada gravação regrava a coleção inteira, não há
  índice, transação entre coleções nem trava de arquivo. Dimensionado para
  milhares de registros por coleção. Backup = copiar `dados\` com o serviço parado.

## 7. Segurança

| Controle | Implementação | Limite atual |
|---|---|---|
| Autenticação | `Authorization: Bearer <token>`; `ERP_TOKENS="tok:usuario:perfil,..."` | Tokens em texto puro; sem hash (L-04) |
| Autorização | Leitura: autenticado. Escrita: perfil ∈ `perfis_escrita` do módulo | Granularidade por módulo, não por rota |
| Modo dev | Sem `ERP_TOKENS` → tudo liberado como `dev:admin`, com aviso no console | Nunca usar em produção |
| Auditoria | Toda escrita bem-sucedida: ms, usuário, método+rota, query | Buffer em memória perdido se o processo morrer (L-08) |
| Transporte | HTTP puro | Sem TLS no servidor nativo: usar proxy reverso HTTPS (L-04) |
| Entrada | form-urlencoded validado; números validados por `form::eh_numero` | `json_decode` aborta a VM (L-05) — não usado em entrada externa |
| Plugins | Só via HTTP local; manifesto chave=valor; prefixo obrigatório `/api/` | Plugin roda com os mesmos privilégios do usuário do serviço |
| Sandbox | `PYRO_POLICY` (capabilities) disponível no runtime | A definir por instalação: `fs.read/fs.write=./dados`, `net=127.0.0.1` |

Perfis previstos: `admin`, `pcp`, `operador`, `almoxarife`, `manutencao`, `qualidade`, `consulta`.

## 8. Build e implantação no Windows

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

O script roda os testes do núcleo na VM e gera `build\emp.exe` (~770 KB) e um
`.exe` por pasta em `plugins_src\`. Requisitos **de build**: Python 3, MinGW gcc
(`C:\MinGW\bin`) e o toolchain Cryo (por padrão a pasta acima deste
repositório; ou `CRYO_HOME`). Requisitos **de execução**: nenhum além do Windows.
Plugins em `http://` são chamados por socket nativo; só `https://` usaria o
`curl.exe` do Windows.

Execução:

```powershell
$env:ERP_PORTA="8080"; $env:ERP_DADOS="C:\EMP\dados"
$env:ERP_TOKENS="tk-ana:ana:admin,tk-joao:joao:operador"
$env:PYRO_HTTP_TIMEOUT_MS="2000"          # prazo para cada requisição chegar inteira
$env:PYRO_HTTP_CLIENT_TIMEOUT_MS="5000"   # prazo de cada chamada a plugin
C:\EMP\emp.exe
```

Como serviço: a linguagem não tem integração com o Service Control Manager
(L-21). Usar um *wrapper* (NSSM ou WinSW) com reinício automático. Plugins também
precisam ser iniciados pelo wrapper — o `exec` da linguagem bloqueia e não
supervisiona processos (L-18).

## 9. Como acrescentar um módulo

### 9.1 Módulo interno

1. Criar `src/modulos/<id>/<id>.cryo` com `iniciar`, `rotear`, `ao_evento` e
   `pub fn descritor() -> k::Modulo` (copiar `estoque.cryo` como modelo).
2. Em `src/modulos/catalogo.cryo`: uma linha `import` e uma linha na lista.
3. `build.ps1`. Nenhum outro arquivo muda; os existentes nem sabem que ele existe.

### 9.2 Plugin externo (sem recompilar o núcleo)

1. Escrever `plugins_src/<id>/<id>.cryo` implementando `GET /saude`, `POST /req`,
   `POST /evento` (modelo: `qualidade.cryo`).
2. Compilar para `<id>.exe`, copiar para o servidor e iniciar.
3. Criar `plugins/<id>.plugin` (id, prefixo, url, assina, perfis_escrita).
4. Reiniciar o `emp.exe`. O módulo aparece em `/api/sistema/modulos` e no painel.

## 10. Recursos em falta na linguagem

Legenda — **Verificado**: reproduzido durante a construção deste esqueleto.
**Código**: lido no runtime/compilador, não reproduzido em execução.
**✅ Corrigido**: resolvido no toolchain (branch `dev`) e reconferido no EMP.

| ID | Lacuna | Evidência | Impacto no ERP | Contorno usado no esqueleto | Prioridade |
|---|---|---|---|---|---|
| **L-01** | ✅ *Corrigido em `Cryo` af8eb26 (otimizador e inliner) e `Burnout` 8cf4104 (testes pyro/go/node); reprodução original conferida no EMP. As funções-ponte `_chamar_*` do registro continuam válidas, só deixaram de ser obrigatórias.* Original: o otimizador AST **apaga** uma variável local do tipo função cujo único uso é uma chamada (`fn(T)->R h = m.f; h(x);`) — gera código que referencia `h` inexistente | Verificado (pyro e node; some com `--no-opt`). Causa: `_read_counts` em `Cryo/optimize.py` conta só `Identifier`, não o nome de um `Call` | Despacho dinâmico de módulos — o coração da arquitetura — quebra em silêncio. `pyro build` não tem `--no-opt` | Chamar sempre via **parâmetro** (`_chamar_rotear(f, r)`) | **Crítica** |
| **L-02** | Sem banco de dados, índices, transações, travas de arquivo | Código (tabela de natives) | Regravação O(n) por escrita; saldo e histórico podem divergir se a 2ª gravação falhar; duas instâncias corrompem dados | JSON por coleção + `write_file_atomic` | **Crítica** para escala |
| **L-03** | Sem *append* em arquivo | Código | Log/auditoria exige regravar tudo | Cada descarga cria um arquivo novo e imutável | Média |
| **L-04** | Sem hash (SHA-256/bcrypt), HMAC, aleatório criptográfico, comparação em tempo constante; servidor sem TLS | Código | Tokens/senhas em texto puro; sessão não assinável; tráfego em claro na rede da fábrica | Tokens fixos em variável de ambiente; proxy HTTPS externo | **Crítica** |
| **L-05** | 🟡 *`to_int`/`to_number` têm o mesmo defeito (abortam em texto inválido, sem captura); `parse_int`/`parse_number` (Cryo ad3c869) devolvem opcional e o EMP v0.2 passou a usá-los em toda entrada externa.* Original: `json_decode` em texto inválido **aborta a VM e o `try/catch` não captura**; `as T` **não valida** (campo ausente vira `null`, `"codigo":5` entra como int em campo `string`) | Verificado | Um POST malformado derrubaria o servidor inteiro; dados de tipo errado persistidos em silêncio | Entrada externa só em form-urlencoded; JSON só para dados que o próprio ERP gravou | **Crítica** |
| **L-06** | Sem carregamento dinâmico de código (carregar `.pyro`/DLL em runtime) | Código | Módulo interno exige recompilar o núcleo | Plugins como processos HTTP | Alta |
| **L-07** | **Sem atribuição a campo de struct** (`op.status = "X"` é erro de sintaxe) | Verificado | Toda mudança de estado reconstrói a struct campo a campo; esquecer um campo zera o dado | Funções `_com(...)` que reconstroem a struct num só lugar | Alta |
| **L-08** | Sem tratamento de sinais / desligamento gracioso / timers; `print` de um `.exe` redirecionado é **bufferizado e perdido** ao matar o processo | Verificado (log vazio após `Stop-Process`) | Serviço sem log observável; buffer de auditoria perdido ao parar o serviço | Buffer pequeno de auditoria; nenhum para o log | Alta |
| **L-09** | 🟡 *Parcial — timeout e limites corrigidos em `Pyro` 2274a72: a requisição precisa chegar inteira em `PYRO_HTTP_TIMEOUT_MS` (padrão 10 s), cabeçalhos até 64 KB, corpo até 64 MB. Reconferido no `emp.exe`: uma conexão ociosa custa o prazo configurado (2 s com `PYRO_HTTP_TIMEOUT_MS=2000`) em vez de travar para sempre. Continuam: servidor sequencial e sem cabeçalhos de resposta.* Original: servidor HTTP **sequencial**, sem *timeout* de leitura, buffer de requisição de 64 KB, path/query truncados em 2048 bytes, sem cabeçalhos de resposta além de `Content-Type` (sem CORS, cookies, `Cache-Control`, `Content-Disposition`) | Código (`http_read_request`, `pyro_runtime.c`) + verificado (plugin parado custa ~2 s **a todas** as requisições) | Um cliente que conecta e não envia nada **congela a fábrica inteira**; uploads > 64 KB truncados; sem download de relatórios com nome | Disjuntor nos plugins; nenhum para clientes lentos | **Crítica** |
| **L-10** | Sem fila/mensageria durável | Projeto | Eventos em memória se perdem num crash entre a resposta e a drenagem (ex.: apontamento gravado, backflush não) | Drenagem imediata após cada resposta | Alta |
| **L-11** | Sem tipo decimal; `number` é binário (`0.1 + 0.2 = 0.30000000000000004`); **overflow de `int` dá a volta em silêncio na VM/AOT** (`INT64_MAX + 1` → negativo; ISSUES/27 aberta) | Verificado | Custos e valores com erro de arredondamento; contadores/somatórios corrompidos sem erro | `round(x*100)/100` na exibição | **Crítica** para custos |
| **L-12** | Sem data/hora de calendário: só `now_ms()`; sem formatar/parsear datas, fuso, dia da semana | Código | Turnos, relatórios diários, prazos de OP, MRP com datas | Epoch em ms; formatação no navegador | Alta |
| **L-13** | ✅ *Corrigido em `Burnout` 9d0a2f1 e `Cryo` f60ce96/4bb524c; `tests/test_eventos.cryo` roda com `cryoc test` no `build.ps1`.* Original: `cryoc test` **não resolve imports com namespace** (o executor chama `_compile_resolved` sem `resolve_modules` — `Burnout/testrunner.py:150`); além disso `assert(ns::f())` de topo dá "unknown function" | Verificado (31 erros num arquivo que compila normalmente) | `test fn` inutilizável para um projeto multi-módulo | Programa de testes comum com harness próprio | Alta |
| **L-14** | O mesmo arquivo importado com **aliases diferentes** em módulos diferentes falha (`unknown function 'existe' in module 'cad'`) | Verificado | Convenções de alias viram regra global do projeto | Mesmo alias em todo lugar | Média |
| **L-15** | Erro de sintaxe num arquivo importado é reportado **sem nome de arquivo nem linha** | Verificado | Diagnóstico difícil em projeto com dezenas de arquivos | Compilar arquivo a arquivo | Média |
| **L-16** | Chamar diretamente um campo-função (`m.rotear(r)`) não é suportado no backend pyro | Verificado (funciona no node) | Sintaxe natural de despacho indisponível | Função-ponte com parâmetro | Média |
| **L-17** | Paridade entre backends quebrada para este projeto: **go** emite `k::Evento` cru em tipos de array/função (não compila); **node** não tem `url_decode` | Verificado | Só a rota Pyro→AOT→`.exe` funciona; perde-se o backend go como alternativa | Usar só pyro/AOT | Média |
| **L-18** | 🟡 *Cliente corrigido em `Pyro` 2274a72: `http://` por socket nativo, prazo `PYRO_HTTP_CLIENT_TIMEOUT_MS` (padrão 15 s), `https://` via `curl` sem shell e corpo por stdin; nenhum arquivo temporário criado (reconferido). Continuam as limitações de `exec`.* Original: cliente HTTP do runtime C usa **`curl` via `popen`**: URL em `sprintf` sem limite (estouro de buffer > ~1 KB), risco de injeção de comando, corpo gravado em arquivo temporário no diretório atual, `-d` remove quebras de linha, `Content-Type` fixo JSON, **sem timeout**; `exec` só devolve stdout, sem código de saída nem execução em segundo plano | Código (`http_get_curl`/`http_post_curl`, `pyro_runtime.c`) | Um plugin travado **congela o ERP indefinidamente**; dependência de `curl.exe`; dados de requisição vazam para disco; o núcleo não consegue iniciar/supervisionar plugins | URL só de manifesto local; corpo url-encoded; disjuntor | **Crítica** se houver plugins |
| **L-19** | Sem sockets TCP/UDP crus, porta serial, nem protocolos industriais (Modbus TCP, OPC UA, MQTT) | Código | Coleta automática de CLPs/sensores (OEE, contadores de máquina) impossível nativamente | Apontamento manual por HTTP | **Crítica** para integração com máquinas |
| **L-20** | Sem regex, compressão, geração de PDF/XLSX | Código | Validações complexas e relatórios formatados | CSV/JSON; impressão pelo navegador | Baixa |
| **L-21** | Sem integração com o Service Control Manager do Windows | Código | Não roda como serviço sozinho | NSSM/WinSW | Média |
| **L-22** | O servidor nativo só escuta **IPv4** (`INADDR_ANY`), e por ser sequencial fica preso nas conexões especulativas que o navegador abre e não usa | Verificado: pelo navegador, `localhost` → 260–320 ms por requisição e 669 ms por atualização do painel; `127.0.0.1` → 12–20 ms e 67 ms. Um curl esperou 2,8 s atrás de uma conexão ociosa do navegador | Painel lento se aberto por `localhost`; picos de espera de até `PYRO_HTTP_TIMEOUT_MS` | Acessar por IP; `PYRO_HTTP_TIMEOUT_MS` 1000–2000 | Média |

## 11. Problemas que podem ocorrer se os recursos não forem criados

| Cenário | Lacuna | Consequência na fábrica | Probabilidade |
|---|---|---|---|
| Um coletor/integração envia um JSON malformado para um endpoint que use `json_decode` | L-05 | **Servidor cai**; todos os terminais de apontamento param até alguém reiniciar | Alta assim que houver integração em JSON |
| Um tablet com Wi-Fi ruim abre a conexão e não completa a requisição | L-09 | ~~ERP congelado para sempre~~ → todos esperam até `PYRO_HTTP_TIMEOUT_MS` (servidor ainda sequencial) | Alta em chão de fábrica — mitigado |
| Plugin trava (laço infinito, disco cheio) sem fechar a conexão | L-18, L-09 | ~~ERP congela indefinidamente~~ → ERP espera até `PYRO_HTTP_CLIENT_TIMEOUT_MS` por chamada; o disjuntor corta após 3 | Média — mitigado |
| Plugin cai | L-09 | ~2 s de atraso por chamada até o disjuntor abrir (3 falhas) | Média — mitigado |
| Queda de energia entre gravar o apontamento e drenar o evento | L-10 | OP mostra produção, mas estoque não deu baixa/entrada: saldo errado | Baixa, mas silenciosa |
| Falha na 2ª gravação de um movimento | L-02 | Saldo e histórico divergentes | Baixa |
| Duas instâncias do `emp.exe` apontando para o mesmo `dados\` | L-02 | Última gravação vence; registros perdidos | Média (erro operacional) |
| Coleção de movimentos cresce (ex.: 200 mil linhas) | L-02 | Cada movimento regrava MBs; resposta lenta, desgaste de disco | Alta em meses de uso |
| Somatórios de custo/quantidade em `number` | L-11 | Centavos divergentes em relatórios e fechamento | Alta |
| Contador inteiro passa de 2⁶³ ou multiplicação grande | L-11 | Valor negativo sem erro (VM não verifica overflow) | Baixa, grave |
| Token capturado na rede (HTTP em claro) | L-04 | Acesso com perfil de outro usuário | Média sem proxy HTTPS |
| Serviço parado/reiniciado pelo Windows | L-08 | Últimas linhas de auditoria e todo o log perdidos | Alta |
| Variável local de tipo função em código novo de módulo | L-01 | Compila, e em runtime "função desconhecida" ou comportamento errado | Alta para quem não conhece a armadilha |
| Necessidade de contar peças direto do CLP | L-19 | Impossível sem um gateway escrito em outra linguagem (fere R1) | Alta em OEE |
| Relatório por turno/dia | L-12 | Cálculo de calendário manual em ms, propenso a erro de fuso/horário de verão | Alta |
| ~~Equipe escreve testes com `test fn`~~ | L-13 | ✅ Corrigido | — |

## 12. Roadmap sugerido

**Fase A — Linguagem (bloqueadores de produção).** ✅ L-01, L-13 e o grosso
de L-09/L-18 (timeouts, cliente nativo) já entraram. Faltam:
L-05 (`json_decode` que devolve erro capturável + validação de `as T`),
cabeçalhos de resposta HTTP (L-09), L-07 (atribuição a campo), L-08
(flush de stdout/stderr e `on_shutdown`), L-11 (overflow verificado na VM; tipo
`decimal`).

**Fase B — ERP v0.2.** Testes de integração HTTP; reconciliação de estoque a partir
dos movimentos; journal de eventos persistido (contorno de L-10); painel com
formulários; módulo de rastreabilidade de lotes.

**Fase C — Linguagem (capacidades).** Data/hora de calendário (L-12), hash/HMAC/TLS
(L-04), servidor HTTP concorrente ou com `spawn` por conexão, append em arquivo,
sockets TCP (base para Modbus/MQTT — L-19), integração com serviço Windows.

**Fase D — ERP v1.0.** PCP/MRP, OEE com coleta de máquina, manutenção, compras;
avaliar banco embarcado (SQLite via biblioteca nativa no runtime) para L-02.

## 13. O que foi verificado de fato

Executado nesta máquina (Windows 11, MinGW gcc, VM Pyro em C):

- `main.cryo` compila para bytecode Pyro (23 KB) e para **`emp.exe` nativo (~770 KB)**;
  o plugin para **`qualidade.exe` (~270 KB)** — último build com o runtime HTTP endurecido.
- Com o runtime endurecido: conexão ociosa aberta durante um apontamento → a
  requisição esperou o prazo (10 s padrão; 2 s com `PYRO_HTTP_TIMEOUT_MS=2000`) e
  foi atendida; plugin parado → 502 em ~2 s; nenhum `pyro_tmp_post_*` criado.
- Fluxo HTTP completo na VM **e** no `.exe`: cadastro de MP/PA, estrutura (BOM com
  quantidade decimal `1,5`), entrada de estoque, criação → liberação → dois
  apontamentos → OP `CONCLUIDA`; backflush correto (aço 100 − 1,5 × 52 = 22;
  parafuso −208 com evento `estoque.negativo`); indicadores (refugo 3,85%).
- RBAC: operador recebe 403 ao escrever em estoque e em qualidade; token inválido → 401.
- Entrada malformada (`{"isso nao e form`, `quantidade=abc`) → 422, servidor segue no ar.
- Persistência: arquivos por coleção gravados e relidos após reinício.
- Plugin: descoberto pelo manifesto, `ativo`, NC automática aberta pelo evento
  (refugo 16,7% > 5%), NC manual via proxy; plugin parado → 502/503 e o resto do
  ERP continua; plugin ausente na partida → `falhou` e 503 em ~1 ms.
- Testes do núcleo: 7/7 na VM Pyro (`tests/test_nucleo.cryo`) e 2/2 com `cryoc test`.

**v0.2 (painel e manutenção)**, com `emp.exe` e `qualidade.exe` reais:
- `tools/demo.cryo` popula tudo sem falhas; a Produção recusou apontar na
  SOLDA-01 parada (409) — integração só por evento.
- Após reinício, a recusa continua (a Manutenção reanuncia as paradas abertas).
- `POST /api/producao/apontar?id=abc` → 404, servidor no ar (antes abortaria).
- Pelo navegador (painel): parada encerrada com solução, apontamento de 45/2
  na OP #4 (liberada após a parada), OP #7 criada, parada de Qualidade aberta
  retroativamente — refletidos em todas as abas e no feed de eventos.
- Disponibilidade conferida à mão: PINTURA-01 com 160 min parados em 480 → 66,7%.
- Capturas em `docs/screenshots/` feitas desse estado.

**Fase 2 (comercial, estoque endereçado, OEE)**, conferido pela coordenadora
no branch combinado, além do que cada frente registrou em `docs/fase2/`:
- `build.ps1` passa e os 54 testes passam (núcleo 7, eventos 2, etapas 15,
  pedidos 5, estoque 10, OEE 11).
- As quatro cargas de demonstração rodam juntas num só `emp.exe` sem falha na
  ordem `demo → demo_estoque → demo_comercial → demo_oee`; na ordem
  comercial → estoque a carga de estoque falha 2 transferências (a expedição
  já baixou o saldo — recusa correta, dependência entre os scripts).
- Pedidos em todos os estados (ABERTO atrasado, EM_PRODUCAO, PRONTO sem OP,
  EXPEDIDO, CANCELADO); sugestões de reposição COMPRAR e PRODUZIR; OEE da linha
  0,862 com valores por posto coerentes com a demonstração.
- A frente C conferiu o OEE da PRENSA-03 à mão a partir dos eventos
  (D 0,9375 × Desemp 0,8325 × Q 0,8 = 0,6244), igual à API.
- Os dois defeitos achados nessa verificação (OEE zerado com tempo operando
  zero; quantidade fracionada em produto UN) foram corrigidos e conferidos por
  HTTP: MONT-01 de OEE 0 para 0,96 com `desempenho_medido: false`; 12,5 UN →
  422 no pedido e na OP. Os limites restantes estão no CHANGELOG.

**Não verificado:** carga/concorrência, execução como serviço Windows, backends
go/node para o ERP completo (L-17), navegadores além do Chromium/Edge, perfis
reais com `ERP_TOKENS` nas telas da fase 2, celular (375 px) na fase 2.
