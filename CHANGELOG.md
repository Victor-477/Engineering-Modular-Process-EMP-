# Histórico de versões

## Não lançado

### Novo
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
    últimas só para pcp e admin). A lista de ordens ganhou a coluna
    "Etapa atual" e o código da OP abre o detalhe.
  - **Aba Roteiros em Cadastros** (`/#cadastros/roteiros`, aparece quando o
    módulo `roteiros` está ativo): operações com parâmetros medidos, editor
    do roteiro por produto (incluir, editar, remover etapa) e capacidades
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
