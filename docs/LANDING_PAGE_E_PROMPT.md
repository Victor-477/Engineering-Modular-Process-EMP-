# Landing Page & Terminal de Prompt do Agente em Cryo

Documentação técnica do servidor web de apresentação e do console interativo de prompt cognitivo do EMP (Engineering Modular Process), implementados 100% na linguagem Cryo em [`src/landing.cryo`](file:///c:/Users/senai/Desktop/Projetos/Pyro_Cryo/Engineering-Modular-Process-EMP-/src/landing.cryo).

---

## 1. Visão Geral e Propósito

A **Landing Page & Terminal de Prompt** tem dois objetivos centrais na arquitetura do EMP:
1. **Showcase Institucional e Técnico das 10 Fases**: Exibir a robustez da arquitetura desacoplada do ERP, seus 10 módulos industriais, plugins externos, barramento de eventos pub/sub e métricas operacionais compiladas nativamente para Windows (sem máquinas virtuais).
2. **Terminal de Prompt Cognitivo para Agentes LLM e Usuários**: Oferecer um console web interativo capaz de interpretar comandos em linguagem natural, direcionando ações operacionais e executivas diretamente sobre a API do ERP, com badges semânticos e payloads técnicos estruturados.

```
                           Navegador / Usuário / Agente LLM
                                          │
                     ┌────────────────────┴────────────────────┐
                     │                                         │
               HTTP :8088                                 HTTP :8080
                     │                                         │
           ┌─────────▼─────────┐                     ┌─────────▼─────────┐
           │   landing.exe     │                     │     emp.exe       │
           │ (Landing & Prompt)│─── requisições ────►│   (ERP Core)      │
           └───────────────────┘     cognitivas      └───────────────────┘
```

---

## 2. Arquitetura do Binário (`landing.exe`)

| Propriedade | Especificação |
|---|---|
| **Arquivo Fonte** | [`src/landing.cryo`](file:///c:/Users/senai/Desktop/Projetos/Pyro_Cryo/Engineering-Modular-Process-EMP-/src/landing.cryo) |
| **Tamanho do Fonte** | 53.090 bytes (~1.080 linhas de Cryo puro) |
| **Compilação** | `python pyro.py build src/landing.cryo -o build/landing.exe` (AOT → C → MinGW GCC) |
| **Binário Gerado** | `build/landing.exe` (~422 KB, executável nativo Windows PE 64-bit) |
| **Dependências de Runtime** | **Zero**. Nenhuma VM, sem Node.js, sem Python em execução |
| **Porta Padrão** | `8088` (configurável via variável de ambiente `LANDING_PORTA`) |
| **Geração Estática** | Exportação automática para `build/landing.html` (34 KB) para inspeção offline |

---

## 3. Endpoints da API HTTP

O servidor HTTP escuta em IPv4 (`0.0.0.0` / `127.0.0.1`) e atende às seguintes rotas:

### 3.1 `GET /`
- **Descrição**: Retorna o HTML completo da Landing Page (renderizado pela função `_html_completo()`).
- **Content-Type**: `text/html; charset=utf-8`
- **Recursos Inclusos**:
  - Hero Section com badges dinâmicos de arquitetura (100% Cryo, 0 VM, ~1 ms latência).
  - Terminal de Prompt Interativo com painel de histórico, entrada de texto e pills de atalho.
  - Grade visual com as **10 Fases Modulares** implementadas no ERP.
  - Especificação dos **Plugins Externos** (`qualidade.exe`, `compras.exe`).
  - Comparativo de Performance (latências de 3 ms a 99 ms vs. ERPs legados).
  - Rodapé técnico com links e status do sistema.

### 3.2 `GET /api/saude`
- **Descrição**: Health check em tempo real do serviço de landing page.
- **Resposta**: JSON `{"servico": "emp-landing", "status": "operacional", "porta": 8088, "fases": 10}`.

### 3.3 `POST /api/prompt`
- **Descrição**: Endpoint cognitivo que recebe uma instrução em linguagem natural e processa através da engine semântica interna `_interpretar_prompt()`.
- **Content-Type da Entrada**: `application/x-www-form-urlencoded` (`prompt=...`)
- **Resposta**: JSON estruturado com status, mensagem legível para humanos/agentes, categoria e payload operacional:

```json
{
  "status": "ok",
  "comando": "status fabrica",
  "categoria": "chao_de_fabrica",
  "badge": "DIAGNOSTICO EM TEMPO REAL",
  "mensagem": "Linha operacional ativa. Postos monitorados por telemetria IoT e CLPs com intertravamento de seguranca ativo.",
  "payload": {
    "postos_ativos": 5,
    "ordens_em_producao": 3,
    "oee_global": 0.884,
    "otif": 1.0,
    "temperatura_media_c": 64.2,
    "paradas_ativas": 0
  }
}
```

---

## 4. Dicionário de Comandos do Prompt Cognitivo

O interpretador de linguagem natural reconhece as seguintes intenções e termos-chave:

| Comando / Intenção | Termos Reconhecidos | Categoria | Ação Retornada |
|---|---|---|---|
| **Status da Fábrica** | `status`, `fabrica`, `visao geral`, `chao` | `chao_de_fabrica` | Diagnóstico de postos, OEE global, OPs ativas e telemetria |
| **OTIF e Indicadores** | `otif`, `kpi`, `indicadores`, `metricas` | `business_intelligence` | Taxa de entrega no prazo (OTIF), refugo global e custo operacional |
| **Arquivar OPs** | `arquivar`, `historico`, `tblfin`, `congelar` | `arquivamento` | Status de retenção, volume de ordens ativas vs. arquivadas e endpoint de purga |
| **Sensores IoT** | `sensor`, `iot`, `clp`, `temperatura`, `pulso` | `iot_telemetria` | Leituras de sensores em tempo real, pulsos e intertravamentos de segurança |
| **Turnos e Operadores** | `turno`, `operador`, `alocacao`, `equipe` | `recursos_humanos` | Turno ativo, alocação de postos e índices de eficiência/qualidade |
| **Ajuda e Catálogo** | `ajuda`, `help`, `comandos`, `opcoes` | `ajuda` | Lista de comandos recomendados e atalhos rápidos |
| **Comando Genérico** | Qualquer outro texto | `agente_cognitivo` | Confirmação de recebimento pelo agente com instruções de direcionamento ao ERP Core |

---

## 5. Design System "Forja"

A interface visual segue a especificação estética industrial contemporânea **Forja**:
- **Paleta de Cores**:
  - Fundo principal: `#0a0e17` (Abismo Dark)
  - Superfícies de Cards: `#121826` com bordas sutis em `#1e293b`
  - Acento Primário: Âmbar Industrial (`#f59e0b` / `#d97706`)
  - Acento Secundário: Turquesa Tecnológico (`#06b6d4`)
  - Sucesso Operacional: Verde Esmeralda (`#10b981`)
  - Alerta Crítico / Parada: Vermelho Carmim (`#ef4444`)
- **Tipografia**: Família `JetBrains Mono`, `Fira Code` e `Inter` para clareza em parâmetros de chão de fábrica.
- **Responsividade**: Layout fluído com CSS Grid e Flexbox, adaptado tanto para telas de comando desktop (1440 px+) quanto tablets de operadores e dispositivos móveis.

---

## 6. Testes Automatizados da Landing Page

### 6.1 Testes HTTP do Servidor (`tests/test_landing_http.py`)
Exercita 11 asserções funcionais via requisições HTTP locais:
1. `GET /` — Validação de status code 200 e content-type HTML.
2. `GET /` — Verificação de elementos-chave do DOM (Forja, Terminal de Prompt, 10 fases).
3. `GET /api/saude` — Validação do endpoint JSON de saúde.
4. `POST /api/prompt (status fabrica)` — Validação do parsing de intenção de fábrica.
5. `POST /api/prompt (otif e kpis)` — Validação de resposta de BI.
6. `POST /api/prompt (arquivar ops)` — Validação de resposta de arquivamento histórico.
7. `POST /api/prompt (sensores iot)` — Validação de resposta de telemetria.
8. `POST /api/prompt (turnos e operadores)` — Validação de resposta de RH/eficiência.
9. `POST /api/prompt (ajuda)` — Validação de resposta de ajuda.
10. `POST /api/prompt (texto generico)` — Validação de fallback do agente cognitivo.
11. Verificação de integridade do arquivo gerado em disco `build/landing.html`.

Execução:
```powershell
python tests/test_landing_http.py
```

### 6.2 Testes em Tempo Real do Agente LLM (`tests/test_realtime_llm.py`)
Exercita a integração completa e simultânea de `landing.exe` (porta 8088) e `emp.exe` (porta 8080) em 12 etapas:
- Step 1: Healthcheck de ambos os serviços nativos.
- Step 2: Consulta de status de chão de fábrica via prompt da landing page.
- Step 3: Consulta de telemetria IoT via prompt da landing page.
- Step 4: Consulta de governança de arquivamento via prompt da landing page.
- Step 5: Alarme crítico em tempo real (sensor analógico a 98°C) disparando intertravamento de parada `maquina.parada`.
- Step 6: Verificação da parada emergencial no módulo de manutenção.
- Step 7: Tentativa de iniciar etapa em posto interditado (validação de rejeição HTTP 409).
- Step 8: Criação de Ordem de Produção dedicada em posto operacional.
- Step 9: Injeção de pulsos de máquina (CLP) com avanço de peças e apontamento automático.
- Step 10: Conclusão da OP e apropriação automática de custos reais vs. padrão.
- Step 11: Arquivamento histórico da OP concluída para `tblFinOrder` e `tblFinStep`.
- Step 12: Validação de presença imutável na base de arquivamento histórico.

Execução:
```powershell
python tests/test_realtime_llm.py
```
> Resultado: **12/12 etapas aprovadas com 0 falhas** e latências de 3 ms a 99 ms.
