# EMP — Engineering Modular Process
## Plano de implementação de um ERP escrito em Cryo

> Versão 0.1 — 16/10/2026. Documento vivo: atualizar a cada fase concluída.

---

## 1. Objetivo

Construir um **ERP modular** (cadastros, estoque, compras, vendas, financeiro e
produção/engenharia) escrito **inteiramente em Cryo**, compilado pelo Burnout
para bytecode Pyro, e distribuído como **um único executável nativo**
(`pyro app build`) com a interface web embutida.

O projeto tem dois papéis:

1. **Produto**: um ERP utilizável por uma pequena/média empresa (inicialmente
   uma empresa, poucos usuários simultâneos).
2. **Prova da linguagem**: o EMP é o "Phase 15" do Cryo. O `taskapp`
   (roadmap 11.10) provou que dá para fazer *uma* aplicação; o EMP prova que dá
   para fazer *um sistema grande*. Toda lacuna encontrada na linguagem vira uma
   issue/PR nos repositórios `Cryo`, `Burnout` ou `pyro`.

---

## 2. Diagnóstico da linguagem (o que foi verificado)

Analisei os repositórios `Cryo`, `Burnout`, `pyro` e `Cryo-Pyro-Documentation`
e compilei/executei código de verdade neste ambiente.

### 2.1 O que o Cryo já oferece e o EMP vai usar

| Recurso | Uso no ERP |
|---|---|
| `struct`, `enum` com dados, `match` exaustivo | Entidades (Pedido, Título) e estados (`Rascunho`, `Aprovado`, `Faturado`, `Cancelado`) |
| Erros `?`, `try/catch`, opcionais `T?` | Validação de regras de negócio sem `null` espalhado |
| Módulos com namespace (`import "x.cryo" as x`) + `pub` | Um módulo do ERP = um diretório com API pública e estado privado |
| Estado de módulo (`var` top‑level, 11.1) | Repositórios em memória por módulo |
| Generics + traits | `Repo<T>`, `trait Entity { fn id() }`, validações reutilizáveis |
| Funções de 1ª classe e closures | Barramento de eventos entre módulos, middlewares HTTP |
| Formatação `${v:.2f}`, separador de milhar | Relatórios e moeda |
| `json_encode`/`json_decode` | API REST e persistência |
| `http_listen`/`http_accept`/`http_respond` + headers | Servidor da API (`Authorization: Bearer`) |
| `write_file_atomic`, `read_file`, `list_dir`, `env` | Persistência durável |
| `test fn` + `cryoc test` | Testes unitários das regras de negócio |
| Front‑end em Cryo (`>html(`, `>CSS(`, `>javascript(`), WASM | Interface web |
| `pyro app build --assets` | Um executável com UI embutida |
| Sandbox por capacidades (`PYRO_POLICY`) | Restringir o ERP a rede + diretório de dados |
| `llm`, `agent`, `tools` | Assistente de IA sobre os dados do ERP (diferencial) |

### 2.2 Lacunas e riscos encontrados

| # | Lacuna | Impacto no ERP | Decisão proposta |
|---|---|---|---|
| L1 | **Branches `main` incompatíveis entre si**: o `main` do Burnout chama `semantic.check(ast, source, path)`, mas o `main` do Cryo tem `check(program)`. Só os branches **`dev`** compilam juntos (verificado). | Build quebrado para quem clonar `main`. | Fixar commits exatos dos 3 repos (`toolchain/versions.lock`) e um script de bootstrap. Sincronizar `main` nos repos da linguagem. |
| L2 | **Sem banco de dados** (nenhum driver SQL/SQLite). Persistência = JSON em arquivo, tudo em memória. | Volume de dados limitado à RAM; sem transações multi-arquivo. | Camada `store` própria: uma coleção por arquivo + **journal append‑only** (log de eventos) para auditoria e recuperação. Tudo atrás de uma interface `Repo<T>` para poder trocar por SQLite depois. |
| L3 | **Sem tipo decimal** (`number` é double). | Erros de arredondamento em valores monetários. | **Dinheiro sempre em `int` centavos**; quantidades em `int` milésimos; alíquotas em pontos‑base (1% = 100). Biblioteca `money.cryo` com regra de arredondamento única. `number` proibido em domínio financeiro (checado em revisão/teste). |
| L4 | **Sem hash criptográfico / random seguro** (não há `sha256`, `hmac`, `random_bytes` nativos). | Não dá para guardar senha com segurança nem assinar tokens. | Preferível: adicionar natives `sha256`, `hmac_sha256`, `random_bytes` no Pyro (Go VM + C runtime, com paridade). Paliativo: SHA‑256 em Cryo puro (há operadores bit a bit). |
| L5 | **Datas**: só `now_ms()`. | Vencimentos, competência, relatórios por período. | Biblioteca `date.cryo` em Cryo puro (algoritmo *days‑from‑civil*), datas como `int` (dias desde 1970) e `string` ISO‑8601 na API. |
| L6 | **HTTP de uma requisição por vez**, corpo lido inteiro em buffer fixo, **sem TLS**. | Poucos usuários simultâneos; uploads grandes impossíveis. | Aceitável no MVP. Rodar atrás de **nginx/Caddy** (TLS, compressão, limite de corpo). Requisições devem ser curtas (paginação obrigatória). |
| L7 | Concorrência apenas cooperativa (`spawn`/`await`). | Jobs longos (MRP, relatórios) bloqueiam o servidor. | Jobs em lotes curtos intercalados com o loop de accept, ou processo separado (CLI `emp job ...`) usando os mesmos módulos. |
| L8 | Fiscal brasileiro (NF‑e) exige XML assinado (certificado A1), SOAP e TLS cliente. | Inviável em Cryo puro hoje. | Fora do MVP. Fase própria, via serviço externo/API de emissão ou bloco estrangeiro isolado. |
| L9 | `json_decode` é dinâmico no Pyro (`as T` não valida). | Payload malformado pode virar dado corrompido. | Validação explícita na borda (`validate.cryo`) — nada entra no domínio sem passar por ela. |

---

## 3. Arquitetura

### 3.1 Visão geral

```text
 Navegador ──HTTPS──► nginx/Caddy ──HTTP──► emp (executável único, Pyro AOT)
                                              │
                         ┌────────────────────┼─────────────────────┐
                         ▼                    ▼                     ▼
                     core/http          módulos de domínio      web/ (UI)
                  roteador + auth   cadastros, estoque, vendas,  páginas Cryo
                  + middlewares     compras, financeiro, produção
                         │                    │
                         └──────► core/store + core/events ◄──────┘
                                     │
                                     ▼
                               data/*.json + data/journal/*.log
```

### 3.2 Princípios

1. **Módulo = diretório com contrato fixo.** Cada módulo expõe:
   - `pub fn init(string data_dir)` — carrega seus dados;
   - `pub fn route(Request req) -> Response?` — responde às suas rotas ou devolve `null`;
   - `pub fn subscribe()` — registra-se nos eventos que lhe interessam.
   O `app.cryo` só conhece essa lista; adicionar módulo = 1 import + 1 linha.
2. **Módulos não importam uns aos outros** (exceto `core` e `cadastros`, que é
   leitura). Integração por **eventos de domínio**:
   `vendas` publica `PedidoFaturado` → `estoque` baixa saldo, `financeiro` gera
   títulos a receber.
3. **Estoque e financeiro são livros‑razão** (ledger): saldo é derivado de
   movimentos imutáveis; correção = movimento de estorno, nunca edição.
4. **Valores inteiros** para dinheiro/quantidade (ver L3).
5. **Validação na borda, tipos no domínio**: a camada HTTP converte JSON em
   structs validados; o domínio só recebe structs.
6. **Tudo auditado**: toda escrita gera uma linha no journal
   (`quem, quando, entidade, id, antes, depois`).
7. **Paridade de engines**: testes rodam no Go VM e no C VM/AOT, como o
   `test_taskapp.py` já faz.

### 3.3 Estrutura do repositório

```text
Engineering-Modular-Process-EMP-/
├── cryo.toml                  # pacote EMP
├── toolchain/
│   ├── versions.lock          # commits fixos de Cryo / Burnout / pyro
│   └── bootstrap.sh           # clona, cria layout cryo/ burnout/ pyro/, builda a VM
├── src/
│   ├── app.cryo               # config, registro de módulos, loop HTTP
│   ├── core/
│   │   ├── http.cryo          # Request/Response, parsing, respostas JSON
│   │   ├── router.cryo        # rotas por método+prefixo, parâmetros de path
│   │   ├── auth.cryo          # sessões/tokens, usuários, perfis (RBAC)
│   │   ├── store.cryo         # coleções, índices, journal, gravação atômica
│   │   ├── events.cryo        # publish/subscribe síncrono
│   │   ├── money.cryo         # centavos, arredondamento, rateio, formatação BRL
│   │   ├── date.cryo          # datas civis, períodos, ISO-8601
│   │   ├── validate.cryo      # CPF, CNPJ, e-mail, obrigatórios, faixas
│   │   ├── ids.cryo           # sequências por coleção, códigos legíveis
│   │   └── audit.cryo         # trilha de auditoria
│   ├── modules/
│   │   ├── cadastros/         # empresas, parceiros, produtos, unidades
│   │   ├── estoque/           # depósitos, movimentos, saldos, inventário
│   │   ├── compras/           # pedidos de compra, recebimento
│   │   ├── vendas/            # orçamentos, pedidos, faturamento
│   │   ├── financeiro/        # títulos, baixas, caixa/bancos, fluxo
│   │   └── producao/          # estruturas (BOM), roteiros, ordens, MRP
│   └── web/                   # UI: layout, componentes, páginas por módulo
├── tests/
│   ├── unit/                  # test fn por módulo (cryoc test)
│   └── api/                   # testes de API ponta a ponta (sobe o binário)
├── data/                      # (gitignored) dados em runtime
└── docs/                      # este plano, ADRs, modelo de dados
```

---

## 4. Fases

Estimativas assumem 1 desenvolvedor + Claude. Cada fase termina com testes
verdes e uma demonstração funcionando.

### Fase 0 — Fundação e toolchain (≈1 semana)

- [ ] `toolchain/versions.lock` + `bootstrap.sh` (resolve L1)
- [ ] Esqueleto de diretórios, `cryo.toml`, `.gitignore`
- [ ] `src/app.cryo` "hello" com o contrato de módulo e uma rota `/health`
- [ ] Script de testes: `cryoc test` nos unitários + teste de API em Python
      (modelo: `Burnout/tests/test_taskapp.py`)
- [ ] CI no GitHub Actions (Ubuntu, Python 3.12, Go, gcc) executando tudo
- [ ] Convenções: `docs/CONVENCOES.md` (nomes, centavos, datas, erros, rotas)

**Pronto quando:** `git clone` + `bootstrap.sh` + `make test` funciona do zero no CI.

### Fase 1 — Núcleo (`core/`) (≈2–3 semanas)

- [ ] `money.cryo`: soma, multiplicação por quantidade, % em pontos‑base,
      arredondamento meio‑para‑cima, **rateio sem perda de centavo**, `R$ 1.234,56`
- [ ] `date.cryo`: `from_iso`, `to_iso`, `add_days`, `add_months`, fim de mês, dia útil
- [ ] `validate.cryo`: CPF, CNPJ, e-mail, CEP, obrigatórios
- [ ] `store.cryo` v2: coleção por arquivo, índice por id e por chave única,
      journal append‑only, recarga a partir do journal, paginação
- [ ] `events.cryo`: barramento síncrono com handlers registrados por nome
- [ ] `router.cryo` + `http.cryo`: `GET /api/estoque/produtos/:id`, JSON de erro padrão
- [ ] `auth.cryo`: usuários, login, sessão com expiração, perfis e permissões
      por rota — **depende de L4** (natives de hash)
- [ ] `audit.cryo`

**Trilha paralela L (linguagem):** abrir issues/PRs para `sha256`/`hmac_sha256`/
`random_bytes` (Go VM + C runtime + testes de paridade) e sincronizar os `main`.

**Pronto quando:** ~100% de cobertura de testes unitários em `money`, `date`, `validate`.

### Fase 2 — Cadastros + UI base (≈2 semanas)

- [ ] Empresa (dados da própria empresa), parceiros (cliente/fornecedor/ambos),
      produtos (SKU, unidade, tipo: matéria‑prima/semiacabado/acabado/serviço),
      unidades de medida e conversões, categorias
- [ ] UI: layout (menu lateral por módulo), listagem com busca e paginação,
      formulário com validação, padrão reaproveitado por todas as telas
- [ ] Primeira geração do executável único com `pyro app build --assets`

**Pronto quando:** cadastrar, editar, buscar e inativar produtos e parceiros pelo navegador.

### Fase 3 — Estoque (≈2 semanas)

- [ ] Depósitos/locais
- [ ] Movimentos (entrada, saída, transferência, ajuste, estorno) — imutáveis
- [ ] Saldo por produto×depósito derivado do ledger (com cache recalculável)
- [ ] Custo médio ponderado
- [ ] Inventário (contagem → ajuste automático)
- [ ] Kardex (extrato por produto)

### Fase 4 — Vendas e Compras (≈3 semanas)

- [ ] Orçamento → Pedido → Faturamento (máquina de estados com `enum` + `match`)
- [ ] Pedido de compra → Recebimento (total ou parcial)
- [ ] Tabela de preços, descontos, condições de pagamento (parcelamento)
- [ ] Eventos: `PedidoFaturado`, `CompraRecebida` → estoque e financeiro

### Fase 5 — Financeiro (≈2–3 semanas)

- [ ] Títulos a receber/pagar (gerados por evento ou manuais), parcelas
- [ ] Baixa total/parcial, juros, multa, desconto
- [ ] Contas (caixa/bancos), transferências, saldo
- [ ] Fluxo de caixa realizado × previsto, plano de contas e centro de custo simples

### Fase 6 — Produção / Engenharia (≈3–4 semanas)

O módulo que dá nome ao projeto.

- [ ] Estrutura de produto (BOM) multinível, com versão/revisão
- [ ] Roteiro de fabricação (operações, centro de trabalho, tempo padrão)
- [ ] Ordem de produção: reserva/consumo de materiais, apontamento, entrada do acabado
- [ ] Custo padrão × real
- [ ] MRP simples: necessidade líquida a partir de pedidos de venda e estoque (job em lote — L7)

### Fase 7 — Relatórios, dashboard e assistente de IA (≈2 semanas)

- [ ] Dashboard: vendas do período, saldo de caixa, rupturas de estoque, OPs atrasadas
- [ ] Exportação CSV
- [ ] Assistente: `agent()` com *tools* somente leitura sobre os módulos
      ("quais clientes estão com título vencido há mais de 30 dias?")

### Fase 8 — Endurecimento e implantação (≈2 semanas)

- [ ] Política de sandbox (`PYRO_POLICY`): só rede local + `data/`
- [ ] Backup/restauração (cópia do `data/` + replay do journal)
- [ ] Assinatura do artefato (HMAC, 11.14) e build reprodutível
- [ ] Guia de implantação (Linux + Windows, atrás de nginx/Caddy)
- [ ] Teste de carga: volume máximo de registros em memória e tempo de resposta

### Fase 9 — Fiscal (a decidir)

NF‑e/NFC‑e/NFS‑e via integração com provedor de emissão (API HTTP) ou
microserviço dedicado. Requer HTTPS cliente e certificados — decidir depois
da Fase 5.

**Total até o MVP (Fases 0–5): ≈ 12–14 semanas. Com produção e relatórios (0–8): ≈ 21–25 semanas.**

---

## 5. Primeira sprint (o que fazemos agora)

1. Criar `toolchain/` com os commits atuais dos branches `dev`
   (Cryo `dev`, Burnout `dev`, pyro `dev` — os únicos que compilam juntos hoje).
2. Esqueleto de `src/` com `app.cryo`, `core/http.cryo`, `core/router.cryo` e rota `/health`.
3. `core/money.cryo` + testes (é a base de tudo e não depende de nenhuma lacuna).
4. `core/date.cryo` + testes.
5. CI rodando bootstrap + testes.
6. Abrir as issues de linguagem: L1 (sincronizar `main`) e L4 (natives de hash).

---

## 6. Decisões em aberto (precisam da sua resposta)

1. **Segmento/foco**: o nome sugere indústria (engenharia/produção). Confirmamos
   que o ERP é para manufatura, e não comércio/serviços?
2. **Uma empresa ou multiempresa (SaaS)?** O plano assume uma empresa por
   instalação, com campo `empresa_id` já reservado para evoluir.
3. **Fiscal**: emitir NF‑e é requisito do MVP ou pode ficar para a Fase 9?
4. **Natives de criptografia**: posso propor as mudanças nos repositórios
   `pyro`/`Burnout` (opção recomendada), ou prefere SHA‑256 em Cryo puro?
5. **Persistência**: JSON + journal no MVP está ok, ou há expectativa de
   volume que exija SQLite desde o início?
6. **Plataforma de implantação**: Windows, Linux ou ambos?

---

## 7. Riscos

| Risco | Prob. | Mitigação |
|---|---|---|
| Bug no compilador/VM bloqueia uma fase | Média | Reduzir a reprodução mínima, corrigir no repo da linguagem, fixar novo commit em `versions.lock` |
| Dados crescem além da RAM | Baixa no MVP | Paginação, arquivamento por exercício, interface `Repo<T>` pronta para SQLite |
| Um servidor single‑thread fica lento | Média | Respostas curtas, jobs fora do loop, medir na Fase 8 |
| Arredondamento financeiro inconsistente | Alta se ignorado | Inteiros + uma só biblioteca `money.cryo` + testes de propriedade |
| Escopo de ERP explode | Alta | MVP fechado nas Fases 0–5; cada fase com critério de pronto |
