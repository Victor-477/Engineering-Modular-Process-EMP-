# Histórico de versões

## Não lançado

### Alterado
- **Novo visual do painel web** (`src/nucleo/painel.cryo`), na linha das
  interfaces industriais da Festo: barra superior branca com a marca EMP em
  azul (`#0091dc`), menu lateral claro com indicador azul no item ativo, cantos
  retos, cartões com cabeçalho separado, indicadores com faixa de status à
  esquerda, etiquetas de status com ponto colorido e botões retangulares. Só
  CSS e estrutura mudaram: rotas, IDs e o JavaScript do painel continuam os
  mesmos.
- Tabelas largas rolam dentro do cartão no celular, em vez de alargar a página.
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
