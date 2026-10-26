# Fase 10 — Arquivamento Histórico e Fechamento de Produção (`tblFin*`)

Documentação técnica do módulo de arquivamento histórico e fechamento contábil de ordens finalizadas do EMP (Engineering Modular Process), implementado em [`src/modulos/arquivamento/arquivamento.cryo`](file:///c:/Users/senai/Desktop/Projetos/Pyro_Cryo/Engineering-Modular-Process-EMP-/src/modulos/arquivamento/arquivamento.cryo).

---

## 1. Contexto e Motivação Industrial

Em sistemas MES e ERPs de chão de fábrica (como Siemens MES4, FactoryViews e SAP PP), a tabela ativa de ordens de produção acumula milhares de registros ao longo do tempo. Esse acúmulo contínuo degrada a velocidade de:
- Algoritmos de cálculo de capacidade finita e sequenciamento (APS);
- Explosão de necessidades líquidas de materiais (MRP);
- Filas de trabalho nos terminais touch de operadores de postos;
- Respostas a requisições de status em tempo real.

A **Fase 10** introduz a separação estrita entre as **tabelas operacionais ativas** (`ordens.json`, `etapas.json`) e as **tabelas de histórico permanente** (`ordens_arquivadas.json`, `etapas_arquivadas.json`), seguindo o padrão clássico `tblFinOrder` e `tblFinStep`.

```
                  ┌─────────────────────────────────────────┐
                  │          CHÃO DE FÁBRICA ATIVO          │
                  │  ordens.json  │  etapas.json            │
                  │  (alta velocidade, OPs em andamento)    │
                  └────────────────────┬────────────────────┘
                                       │
                      POST /api/arquivamento/op?id=N
                      POST /api/arquivamento/lote?dias=N
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       ARQUIVO HISTÓRICO IMUTÁVEL        │
                  │  tblFinOrder  │  tblFinStep             │
                  │  (auditoria, relatórios, governança)    │
                  └────────────────────┬────────────────────┘
                                       │
                     POST /api/arquivamento/desarquivar?id=N
                                       │ (reversão controlada)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │      RESTAURAÇÃO PARA BASE ATIVA        │
                  └─────────────────────────────────────────┘
```

---

## 2. Princípios de Projeto e Regras de Negócio

1. **Imutabilidade e Integridade**:
   - Uma ordem de produção só pode ser arquivada se estiver em estado terminal: `CONCLUIDA` ou `CANCELADA`.
   - Tentativas de arquivar ordens `PLANEJADA`, `LIBERADA` ou `EM_PRODUCAO` são sumariamente rejeitadas com HTTP 409 (Conflito).
2. **Reversibilidade Total (Desarquivamento)**:
   - Em caso de auditoria regulatória, fiscal ou revisão técnica, uma OP pode ser desarquivada por perfis autorizados (`admin` e `pcp`) através de `POST /api/arquivamento/desarquivar?id=N`.
   - A ordem e todas as suas etapas (`tblFinStep`) retornam à base ativa sem qualquer perda de dados históricos (apontamentos, operadores, medições).
3. **Monotonicidade de Identificadores (Garantia anti-colisão)**:
   - A inicialização do módulo de produção calcula o próximo ID como:
     $$\text{proximo\_id} = \max(\max(\text{ordens\_ativas}), \max(\text{ordens\_arquivadas})) + 1$$
   - Isso garante que a criação de novas OPs nunca reutilize o ID de uma OP que já foi para o histórico, mesmo após reinicializações do servidor `emp.exe`.
4. **Desacoplamento por Eventos**:
   - Ao arquivar uma OP individual: publica `arquivamento.op_arquivada` com `id`, `produto`, `quantidade`, `custo_total_real`.
   - Ao arquivar em lote: publica `arquivamento.lote_concluido` com `quantidade`, `dias_retencao`.
   - Ao restaurar uma OP: publica `arquivamento.op_desarquivada`.

---

## 3. Endpoints da API (`/api/arquivamento`)

| Método | Rota | Perfis Permitidos | Descrição |
|---|---|---|---|
| `GET` | `/api/arquivamento/ordens` | Todos | Lista as ordens arquivadas (`tblFinOrder`) com filtros opcionais por produto, período ou status |
| `GET` | `/api/arquivamento/ordem?id=N` | Todos | Detalhe completo da ordem arquivada, incluindo suas etapas congeladas (`tblFinStep`) |
| `GET` | `/api/arquivamento/resumo` | Todos | Resumo quantitativo: total ativas, total arquivadas, etapas arquivadas e retenção configurada |
| `GET` | `/api/arquivamento/config` | Todos | Retorna a política de retenção em dias (padrão: 30 dias) |
| `POST` | `/api/arquivamento/config` | `admin`, `pcp` | Atualiza a política de retenção temporal (`dias_retencao=N`) |
| `POST` | `/api/arquivamento/op?id=N` | `admin`, `pcp` | Arquiva uma ordem individual concluída ou cancelada, transferindo-a da base ativa para a histórica |
| `POST` | `/api/arquivamento/lote?dias=N`| `admin`, `pcp` | Executa o arquivamento em massa de ordens concluídas há mais de $N$ dias |
| `POST` | `/api/arquivamento/desarquivar?id=N` | `admin`, `pcp` | Restaura a ordem e suas etapas do arquivo histórico para as coleções ativas do ERP |

---

## 4. Estrutura de Dados Persistida

Os dados do módulo são mantidos em `dados/arquivamento/`:

### 4.1 `dados/arquivamento/ordens_arquivadas.json` (`tblFinOrder`)
```json
{
  "1": {
    "id": 1,
    "produto": "SUP-01",
    "quantidade": 100,
    "status": "CONCLUIDA",
    "posto": "MONTAGEM-01",
    "criada_em": "2026-10-26T10:00:00Z",
    "concluida_em": "2026-10-26T14:15:00Z",
    "arquivado_em": "2026-10-26T14:22:00Z",
    "usuario": "admin",
    "custo_total_real": 1250.00,
    "lead_time_min": 255.0
  }
}
```

### 4.2 `dados/arquivamento/etapas_arquivadas.json` (`tblFinStep`)
```json
{
  "1-10": {
    "op": 1,
    "numero": 10,
    "operacao": "ESTAMPAR",
    "posto": "PRENSA-01",
    "status": "CONCLUIDA",
    "entrada": 100,
    "boas": 98,
    "refugo": 2,
    "operador": "joao",
    "medicoes": "espessura=2.01"
  }
}
```

---

## 5. Interface no Painel Web (`painel.cryo`)

A aba **Histórico & Arquivo** no painel do EMP oferece:
- **Big Numbers de Governança**:
  - Total de OPs Ativas no chão de fábrica;
  - Total de OPs Arquivadas em `tblFinOrder`;
  - Total de Etapas Arquivadas em `tblFinStep`;
  - Dias de Retenção Atuais.
- **Painel de Ações Rápidas**:
  - Formulário para arquivamento individual por ID da OP;
  - Botão de arquivamento em lote com base no período de retenção;
  - Configuração do parâmetro de retenção em dias.
- **Tabela Histórica de OPs Arquivadas**:
  - Listagem com produto, quantidade, status terminal, data de arquivamento e usuário responsável;
  - Ação **Ver Etapas**: modal com o fluxo completo das etapas (`tblFinStep`);
  - Ação **Desarquivar**: restauração instantânea com feedback visual.
- **Integração na Aba de Produção**:
  - Badge no menu lateral (`qt-arq`) indicando OPs concluídas no chão prontas para arquivamento;
  - Botão de atalho "Arquivar" diretamente na linha da OP concluída ou cancelada.

---

## 6. Cobertura de Testes Automatizados

O arquivo [`tests/test_arquivamento.cryo`](file:///c:/Users/senai/Desktop/Projetos/Pyro_Cryo/Engineering-Modular-Process-EMP-/tests/test_arquivamento.cryo) valida:
1. Rejeição de arquivamento de OP em andamento (`EM_PRODUCAO` ou `LIBERADA` → 409).
2. Arquivamento bem-sucedido de OP `CONCLUIDA` e migração das etapas (`tblFinStep`).
3. Bloqueio de duplicidade ou IDs inexistentes.
4. Desarquivamento e restauração íntegra para a base ativa.
5. Arquivamento em lote respeitando a janela temporal de retenção.

Todos os 5 testes rodam via `cryoc test` e integram o pipeline contínuo do `build.ps1` (101 testes totais com 100% de aprovação).
