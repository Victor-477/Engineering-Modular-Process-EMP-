# Histórico de versões

## Não lançado

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
- As capturas em `docs/screenshots/` ainda mostram o visual anterior.

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
