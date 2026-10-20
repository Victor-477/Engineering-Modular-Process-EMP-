# Forja — sistema de design do EMP

> Versão 1.2 (fase 2: pedidos, estoque endereçado, OEE) · implementado em [`src/nucleo/painel.cryo`](../src/nucleo/painel.cryo)
> e [`src/nucleo/terminal.cryo`](../src/nucleo/terminal.cryo) (terminal do operador).
> Os tokens ficam em `painel::tokens_css()` e as duas páginas os usam.

## Conceito

**Metal incandescente sobre papel técnico.** O EMP é um sistema de chão de
fábrica, e o visual vem desse mundo, sem copiar nenhum fornecedor:

- **Papel técnico**: o fundo é um papel quente com uma grade de pontos, como
  uma folha de desenho de engenharia.
- **Console**: a navegação fica num painel grafite que flutua, como o painel
  de comando de uma máquina.
- **Forja**: um laranja incandescente, a cor do metal sendo trabalhado, é a
  única cor de marca. Ela marca o que está ativo, o que está sendo produzido e
  a ação principal de cada tela.
- **Instrumentos**: os dados aparecem como instrumentos de máquina: medidores
  circulares, barras de LED segmentadas e listras de perigo.

Três regras guiam as decisões:

1. **O laranja é escasso.** Se tudo é laranja, nada chama atenção. Ele aparece
   no item ativo do menu, na ação principal da tela e no que está em produção.
2. **O estado se lê de longe.** Um operador olha o painel a dois metros, então
   o estado de cada posto ou ordem se reconhece pela forma e pela cor, sem
   precisar ler o texto.
3. **Nada de cantos vivos.** Superfícies arredondadas (10 a 28 px), números
   grandes e respiro entre os blocos.

---

## Tokens

Todos ficam em `:root`, numa única função (`painel::tokens_css()`) que o
painel e o terminal incluem. O modo escuro redefine os mesmos nomes em
`@media (prefers-color-scheme: dark)`, então nenhum componente precisa saber
em qual tema está.

### Cor

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `--bg` | `#f4f1ec` | `#0f1115` | Fundo da página (papel) |
| `--dot` | `#ddd6ca` | `#1e2129` | Pontos da grade do fundo |
| `--surface` | `#ffffff` | `#171a20` | Cartões |
| `--surface-2` | `#faf8f5` | `#1d2027` | Campos, cartões internos, linha em foco |
| `--ink` | `#1b1d22` | `#eef0f4` | Texto principal |
| `--ink-2` | `#4a4f59` | `#b6bbc5` | Texto secundário |
| `--muted` | `#676c75` | `#8b919c` | Rótulos, metadados |
| `--line` | `#e9e4db` | `#272b34` | Bordas e divisórias |
| `--console` | `#16181d` | `#0a0b0e` | Painel de navegação, avisos |
| `--console-2` | `#23262d` | `#1a1d23` | Hover e blocos dentro do console |
| `--forja` | `#ff5a1f` | = | **Cor de marca**: ativo, ação principal, em produção |
| `--forja-2` | `#ff9a3d` | = | Fim do gradiente da forja |
| `--forja-soft` | `#ffe9de` | `#3a1d12` | Fundo de ícones, anel de foco |
| `--forja-ink` | `#b23a0a` | `#ff8a57` | Laranja **para texto** (links, "ABRIR →", estado "em produção") |
| `--on-forja` | `#16181d` | = | Texto sobre o laranja (botão principal, item ativo) |

**Cores de estado.** Cada uma tem três versões: a cheia, para gráficos
(medidor, LED, pontos); a `-ink`, para **texto**; e a `-soft`, para fundo. Texto
de estado usa sempre a `-ink` sobre a `-soft`.

| Estado | Token | Significa |
|---|---|---|
| Bom | `--ok` `#0f9f6e` · `--ok-ink` `#0b7350` | Operando, concluída, encerrada, módulo ativo |
| Atenção | `--warn` `#e08a00` · `--warn-ink` `#8f5800` (escuro `#f2b448`) | Disponibilidade abaixo de 85%, OEE entre 60% e 85% |
| Crítico | `--bad` `#e5383b` · `--bad-ink` `#b8262a` · `--bad-strong` `#c92a2a` (fundo de botão e contador) | Parado, cancelada, parada aberta, falhou |
| Aguardando | `--info` `#3d6be0` · `--info-ink` `#2a4fb8` | Liberada, esperando para começar |
| Neutro | `--neutral-soft` | Planejada, sem estado |

### Tipografia

| Token | Fonte | Uso |
|---|---|---|
| `--f-display` | Space Grotesk 500–700 | Títulos, números grandes, nomes de posto |
| `--f-body` | Inter 400–600 | Texto corrido, tabelas, formulários |
| `--f-mono` | JetBrains Mono 500–600 | Rótulos em caixa alta, códigos (`OP-007`), horários, contadores |

As fontes vêm do Google Fonts. **Sem internet, o painel continua íntegro**,
porque cada token tem uma fonte do sistema como alternativa (Segoe UI e
Consolas no Windows).

| Papel | Tamanho / peso | Exemplo |
|---|---|---|
| Título da tela | 34 px / 700, `letter-spacing -0.6px` | "Ordens de produção" |
| Número de KPI | 40 px / 700, algarismos tabulares | "86,7%" |
| Título de cartão | 17 px / 600 | "Postos de trabalho" |
| Corpo | 14 px / 400 | — |
| Rótulo mono | 10–11 px / 600, caixa alta, `letter-spacing 1.2–1.6px` | "OPS EM ABERTO" |

### Forma, profundidade e movimento

| Token | Valor | Uso |
|---|---|---|
| `--r-sm` | 10 px | Botões pequenos, chips |
| `--r-md` | 16 px | Cartões de posto, bloco do operador |
| `--r-lg` | 22 px | Cartões |
| `--r-xl` | 28 px | Console, faixa de destaque do início |
| `--sh-1` | sombra curta e difusa | Cartões em repouso |
| `--sh-2` | sombra longa | Console, cartão em hover, avisos |
| `--glow` | brilho laranja | Item ativo do menu, botão principal em hover |
| `--ease` | `cubic-bezier(.2,.8,.2,1)` | Todas as transições (150–350 ms) |

Com `prefers-reduced-motion`, todas as animações e transições são desligadas.

---

## Componentes

### Console (navegação)

Painel grafite flutuante, com 14 px de afastamento das bordas, raio de 28 px e
um brilho laranja no canto inferior.

| Parte | Descrição |
|---|---|
| Marca | Ícone de blocos modulares em gradiente forja + "EMP" + subtítulo mono |
| Grupos | Rótulos mono `OPERAÇÃO` e `SISTEMA` |
| Item | Ícone + nome. **Ativo**: gradiente forja, texto grafite (`--on-forja`), brilho. **Hover**: `--console-2` |
| Contador | Pílula vermelha com o número de pendências (paradas, NCs) |
| Operador | Avatar com iniciais, usuário · perfil e o campo de token |

No celular, o console vira uma **barra flutuante no rodapé**, só com ícone e
nome curto, e rola na horizontal.

### Cabeçalho da tela

Trilha mono (`EMP / ORDENS DE PRODUÇÃO`, com a barra em laranja) → título →
subtítulo. À direita:
- a pílula **AO VIVO** com relógio e um ponto verde pulsando;
- o sino com o total de alertas;
- o botão de atualizar;
- **+ Novo**, que só aparece em telas com formulário e leva o foco ao
  formulário de criação, destacando o cartão.

### Botão

| Variante | Classe | Use para |
|---|---|---|
| Principal | *(padrão)* | A ação principal do cartão. Gradiente forja com **texto grafite**, como uma etiqueta de segurança industrial |
| Secundário | `.sec` | Ações reversíveis ou de menor peso (Cancelar, Ajustar) |
| Confirmação | `.ok` | Ações dentro de linhas de tabela (Apontar, Encerrar). Grafite, para não competir com o laranja |
| Destrutivo | `.bad` | Parar posto. Fundo `--bad-strong`, texto branco |
| Pequeno | `.mini` | Dentro de tabelas (32 px de altura) |
| Redondo | `.redondo` | Ícones do cabeçalho (38 px) |

**Estados**: o hover sobe 1 px e reforça a sombra; o active volta; o foco por
teclado mostra um contorno laranja de 3 px (`:focus-visible`).

### Campo

40 px de altura, raio de 12 px, fundo `--surface-2`. **Foco**: borda forja,
anel `--forja-soft` de 4 px e fundo branco. O rótulo fica acima, em 12 px/600.

### Cartão

`--surface`, borda `--line`, raio de 22 px e `--sh-1`. O título usa
`--f-display`; o contador opcional (`.cont`) é uma pílula mono à direita.

### KPI

| Parte | Descrição |
|---|---|
| Rótulo | Mono, caixa alta |
| Valor | 40 px, Space Grotesk, algarismos tabulares |
| Detalhe | 12 px, `--ink-2` |
| Sinal | Ícone de 30 px no canto: ✓ (bom), ⚠ (alerta), tendência (neutro) |
| Régua | Faixa de 3 px na base, na cor do estado |

Variantes: `bom`, `alerta` (o valor também fica vermelho) e neutro.

### Estado: ícone + cor

**O estado nunca aparece só como cor.** Cada classe de estado tem uma cor
*e* um ícone, sempre juntos, nas etiquetas, nos nós do fluxo de etapas e no
terminal:

| Classe | Ícone | Estados | Cor |
|---|---|---|---|
| `plan` | calendário | planejada | Neutro (`--neutral-soft` / `--ink-2`) |
| `wait` | pausa | liberada, aguardando | Azul (`--info`) |
| `act` | play, **pulsando** | em produção, em execução | Laranja (`--forja`) |
| `ok` | check | concluída, operando, encerrada, ativo | Verde (`--ok`) |
| `bad` | alerta, sobre **listras diagonais** | falha, parado, aberta, falhou | Vermelho (`--bad`) |
| `skip` | avançar | pulada | Neutro |

Exceção: **cancelada** usa a cor `bad` com o ícone ✕ (`ICONE_DE`), porque
cancelar não é uma falha de máquina.

A **etiqueta** (`tag(estado)`) é uma pílula de 26 px com o ícone de 14 px e o
texto em minúsculas. Os ícones ficam em `ICONE_ST` (por classe); o mapa
estado → classe é `ESTADO`.

### Faixa de estado

Cartões e linhas que representam algo com estado (OP, etapa, posto, parada,
NC, tarefa do terminal) ganham uma **borda esquerda** na cor do estado: 4 px
nas linhas de tabela (classe `e-<classe>` no `<tr>`), 5 px nos cartões de
posto e de etapa e de 6 a 8 px no terminal. A cor vem da variável `--eb`,
definida por `.e-plan` … `.e-skip`.

Uma **falha pisca uma vez** (fundo `--bad-soft` por 1,2 s) na primeira vez em
que aparece. A atualização automática não repete a animação, porque
`pisca()` lembra o que já piscou. Com movimento reduzido, não pisca.

### Fluxo de etapas (detalhe da OP)

`/#ordens/N` abre a OP como um **fluxo vertical**: um trilho de 2 px à
esquerda (como a linha do tempo), com um **nó redondo de 36 px** por etapa
que mostra o ícone do estado. Cada etapa é um cartão interno com faixa de
estado:

| Parte | Conteúdo |
|---|---|
| Topo | Número (`.id`), operação, descrição, posto (`.id`) + link `TERMINAL →`, etiqueta |
| Instrução | A frase da etapa, em `--ink-2` |
| Dados | Planejado (início → fim) · Real (início → fim, com **`+N min`** em `--bad-ink` quando atrasa) · Entrada · Boas · refugo · Operador, com rótulos mono em caixa alta |
| Erro | Caixa `--bad-soft` com o motivo do erro ou do pulo |
| Ações | Botões `.mini`: Iniciar, Concluir (`.ok`), Concluir com erro, Reiniciar e Pular (estes dois só para `pcp`/`admin`), e um campo de motivo |

A etapa atual (`etapa_atual`) ganha fundo `--surface` e anel `--forja-soft`.
Acima do fluxo fica o cabeçalho da OP: "← TODAS AS ORDENS", produto,
etiqueta, números (quantidade, boas, refugo, criada) e a barra de LED. No
celular, o trilho e os nós somem e as etapas viram uma pilha de cartões.

### Moldura de lista

Toda lista longa (ordens, saldos, paradas, NCs, produtos, postos, operações,
capacidades) fica numa moldura, `moldura(id, colunas, itens, opções)`:

| Parte | Descrição |
|---|---|
| Barra | Campo **Filtrar…** (texto em qualquer coluna), seletor de estado ou tipo quando faz sentido, a contagem em mono (`6 itens`) e **Exportar CSV** (`.mini.sec`) |
| Aviso | Com filtro ativo: faixa `--info-soft` "**lista filtrada · 2 de 6 · limpar**" |
| Corpo | A tabela; se o filtro não encontra nada, "Nada corresponde ao filtro." |

O filtro vive no navegador e **sobrevive à atualização automática**. O CSV é
gerado no cliente: separador `;`, vírgula decimal e BOM UTF-8 (abre direto no
Excel em português), só com as linhas visíveis.

### Abas internas

Um seletor de pílulas dentro de uma tela (`.abas`), com o item ativo em
grafite (`--console`), porque o laranja continua reservado para a ação
principal. Cada aba tem endereço próprio: `/#cadastros` e
`/#cadastros/roteiros`; o roteiro de um produto, também
(`/#cadastros/roteiros/SUP-02`, aberto pelo nome do produto no detalhe da OP). A aba de um módulo desligado some (`data-mod`).

### Medidor (posto)

Anel com `conic-gradient` de 68 px: o arco é a disponibilidade, com o
percentual no centro. A cor vem do estado: verde a partir de 85%, âmbar abaixo
disso e vermelho quando o posto está parado. O posto **parado** ganha uma
**faixa de perigo amarela e vermelha** no topo e uma caixa com a categoria, o
horário e o motivo.

### Barra de LED (progresso)

12 segmentos com 3 px de espaço entre eles; os acesos são laranja. Com 100%,
todos ficam verdes. O percentual aparece em mono à direita. Ela é usada em vez
de uma barra lisa porque se lê de longe como os indicadores de um painel de
máquina.

### Distribuição

Barra empilhada com 14 px de altura e cantos arredondados, com 3 px de espaço
entre as fatias. Embaixo, uma legenda com chips de cor e a contagem em mono.
Uso atual: ordens por estado e pedidos por estado (`distribuicao(legenda, contagem)`).

### Pedido (`/#pedidos`, `/#pedidos/N`)

Estados de pedido usam as mesmas classes de estado:

| Estado | Classe | Ícone |
|---|---|---|
| aberto | `wait` (azul) | pausa: esperando as OPs |
| em produção | `act` | play pulsando |
| pronto | `ok` | check: pode expedir |
| expedido | `skip` (neutro) | **caminhão** (`ICONE_DE.EXPEDIDO = "envio"`): saiu da fábrica, fica fora do caminho |
| cancelado | `bad` | ✕, como a OP cancelada |

| Parte | Descrição |
|---|---|
| **Sinal de atraso** (`sinalAtraso(p)`) | Pílula `--bad-soft`/`--bad-ink` com ícone de relógio e "atrasado 5 h" (ou "2 d"), ao lado da etiqueta. A linha ganha faixa `e-bad`, a data de entrega fica em `.atraso`, o menu mostra o total de atrasados no contador e o sino soma os atrasados |
| Lista | Moldura com cliente (nome + código), itens resumidos ("SUP-02 × 150, SUP-01 × 300 +1"), entrega prevista, **cobertura** (barra de LED: quanto do pedido o saldo livre já cobre) e OPs (`.id` com link). Digitar "atrasado" no filtro, ou clicar no "N atrasado(s)" do cartão de estados, filtra os atrasados |
| Novo pedido | Cliente, prazo em dias, observação e **linhas de item** (`.item-ped`: produto + quantidade + ✕). "+ Item" acrescenta uma linha; o envio monta `itens="PRODUTO:qtd;..."`. Depois de criar, abre o detalhe |
| Detalhe | Cabeçalho como o da OP (← TODOS OS PEDIDOS, cliente, etiqueta, atraso, números e cobertura); tabela de itens com saldo livre, **falta** em `--bad-ink` e as OPs do item; tabela das OPs ligadas (estado, etapa, progresso); barra de ações (`.ped-acoes`): posto + Gerar OPs, Expedir (principal só quando PRONTO), motivo + Cancelar pedido. O 409 de expedir mostra as faltas no aviso |

As ações só aparecem para `admin`, `pcp` e `comercial`.

### Endereço e posições (`/#estoque/posicoes`)

Cartões de endereço (`.endereco`) em grade: tipo em mono caixa alta (almoxarifado, linha · posto,
expedição, quarentena), código em `--f-display`, descrição, número de produtos e quantidade.
**Não usam cores de estado** (tipo não é estado). Um clique filtra a moldura de posições pelo
endereço (anel `--forja-soft`, `aria-pressed`); outro clique limpa. Saldo negativo aparece em
`--bad-ink` no cartão e com faixa `e-bad` na linha.

O estoque ganhou abas internas (`/#estoque`, `/#estoque/posicoes`, `/#estoque/reposicao`) e o
**detalhe do produto** (`/#estoque/produto/SUP-01`, aberto pelo código em qualquer tabela de
estoque ou de pedido): saldo total, saldo por endereço em barras (`.por-end`), faixa de reposição
e os últimos movimentos.

### Faixa de reposição

Barra de 10 px: a banda `--ok-soft` com contorno `--ok` vai do **mínimo ao máximo**; o traço de
4 px é o **saldo** (grafite; vermelho quando abaixo do mínimo, e então a barra inteira ganha as
listras diagonais de perigo). Escala até 1,25 × máximo. Tem `role="img"` e `aria-label` com os
três números.

As **sugestões** ficam numa tabela com faixa `e-bad`: produzir → **Criar OP** (principal; vira
secundário "Criar outra OP" quando já existe OP aberta do produto, que aparece ao lado com link);
comprar → **Registrar entrada**, que leva à entrada de material com produto, quantidade e endereço
preenchidos. A OP criada leva `origem=REPOSICAO`. O contador da aba e do menu mostra quantos
produtos estão abaixo do mínimo.

### OEE (`/#oee`, `/#oee/24`)

| Parte | Descrição |
|---|---|
| Seletor de janela (`.janela`) | Pílulas mono "8 h" / "24 h", ativo em grafite como as abas; cada uma tem endereço |
| Destaque da linha | O bloco escuro do início, com **anel de OEE** (SVG, 156 px, arco na cor do nível) e a conta escrita: `disponibilidade × desempenho × qualidade = OEE`, cada fator num vidro fosco e o resultado em gradiente forja (texto grafite). Embaixo, a etiqueta de nível e a regra do alerta |
| Nível | ≥ 85% `ok` (check, "na referência"); 60–85% `warn` (alerta, "abaixo de 85%"); < 60% `bad` ("abaixo de 60%", o limite do `indicadores.oee_baixo`). Sempre ícone + texto |
| Cartão de posto (`.oee-posto`) | Medidor circular com o OEE, faixa esquerda na cor do nível, nome, estado atual (`tag`), três barras finas **neutras** (`--ink-2`) para D, desempenho e Q, e os minutos operando/parado/ocioso, boas e refugo em mono |
| Linha do tempo de estados (`.tl`) | Uma faixa SVG de 26 px por posto, da abertura da janela até agora: **operando** `--ok` cheio, **parado** com as listras de perigo (padrão `#p-parado`), **ocioso** `--info` a 40%, sem registro `--surface-2`. Cada trecho tem `<title>` (estado, horário, duração, motivo). Eixo com 5 marcas em mono e legenda em chips |
| OEE por hora | Colunas SVG desenhadas no painel (sem biblioteca), uma série só, em `--forja`, com ponta arredondada de 4 px apoiada na base e 22% de espaço entre colunas; grade recessiva a cada 25%; **meta 85%** tracejada em `--ok`. Passar o mouse (ou tocar) mostra a dica grafite com o horário e os três fatores. "ver em tabela" abre os mesmos números numa tabela. Seletor: linha inteira ou um posto |

O OEE da linha também vira um KPI na visão geral quando o módulo `indicadores` está ativo.

### Linha do tempo (eventos)

Trilho vertical de 2 px com nós em anel laranja. Cada evento mostra o horário
em mono, o tipo em mono 600 e os dados numa linha cortada com reticências.

### Código

`.id`: pílula mono para identificadores (`OP-007`, `P-004`, `NC-002`, códigos
de produto). Os números ganham zeros à esquerda (3 dígitos) para alinhar.

### Destaque do início

Bloco escuro com gradiente grafite→cobre, dois brilhos laranja e a grade de
pontos clara. Ele traz uma frase gerada a partir dos dados ("1 posto parado e
3 ordens em produção agora.") e 3 ou 4 números em vidro fosco.

### Bloco de módulo

Cartão com ícone num quadrado arredondado `--forja-soft`, título, descrição e
"ABRIR →" em mono. **Hover**: sobe 3 px e ganha `--sh-2`.

### Aviso

Pílula grafite centralizada no rodapé, com um ponto verde (sucesso) ou vermelho
(erro). Fica `role="status"` e `aria-live="polite"`.

### Terminal do operador (`/terminal`)

Uma página própria para o tablet ao lado da máquina, inspirada nos
terminais manuais do MES4 e desenhada no visual Forja. Mostra **uma instrução
por vez**, legível a dois metros e operável com luva.

| Parte | Descrição |
|---|---|
| Barra do posto | Console grafite no topo: marca, **posto em 30 px**, etiqueta do estado do posto, selo **"atualizado às HH:MM:SS"** (o ponto verde pulsa a cada atualização; fica vermelho, com "sem conexão · última às …", quando a conexão cai), operador e engrenagem (operador, token, trocar de posto) |
| Seleção de posto | Sem `#POSTO`, mostra uma grade de cartões grandes com o estado de cada posto. O endereço `/terminal#PRENSA-01` vira o favorito do tablet |
| Instrução | Cartão com faixa de estado de 8 px: OP · produto · "etapa 10 · 1 de 3" · etiqueta; **título da operação em 60 px**; a instrução em 26 px; quatro números de 44 px (entrada, boas, refugo, falta) e uma barra de LED de 16 segmentos |
| Ações | Botões de **84 px** de altura, texto de 24 px e ícone: *Iniciar* (laranja, largura total) → *Apontar* (laranja) / *Concluir* (grafite) / *Concluir com erro* (contorno vermelho) / *Reiniciar* (secundário). Numa etapa em falha, só *Reiniciar etapa* |
| Apontar | Campos numéricos de 84 px com botões − e + de 72 px, e um campo por parâmetro medido da operação, que fica verde (**dentro**) ou vermelho (**fora do limite**) enquanto se digita |
| Concluir com erro | Motivos prontos em botões (um toque) e um campo livre |
| Fila | Coluna à direita (embaixo, no tablet em pé) com as tarefas do posto e a faixa de estado de cada uma. Tocar numa tarefa escolhe a instrução que aparece |
| Nenhuma tarefa | Ícone de check de 96 px e "Nenhuma tarefa" em 52 px |
| Posto parado | Faixa de perigo de 12 px sobre um bloco grafite, com a categoria (40 px), o horário e o motivo. **Todas as ações ficam desligadas** |
| Mensagem | Pílula grafite com texto de 20 px no rodapé e um ponto verde, âmbar (aviso) ou vermelho |

Comportamento:

- Atualiza a cada **1 s**; depois de uma mensagem, a próxima atualização
  espera **2 s**.
- Um toque **desliga os botões na hora**, então não existe toque duplo.
- Toda ação manda a `versao` da etapa que está na tela. Um **409 de versão**
  vira o aviso "A tarefa foi alterada por outra pessoa. Recarregando…" e a
  tela recarrega, sem sobrescrever nada.
- A instrução só é redesenhada quando algo muda, então o que o operador está
  digitando não some com a atualização.
- Todo alvo de toque tem **pelo menos 48 px**. A grade passa para uma coluna
  abaixo de 1100 px (tablet em pé) e os números para duas colunas no celular.

---

## Acessibilidade

- **O texto atende ao contraste AA (4,5:1)**, medido nos pares principais:

  | Par | Claro | Escuro |
  |---|---|---|
  | `--ink-2` sobre `--surface` | 8,2 | — |
  | `--muted` sobre `--surface` / `--bg` | 5,3 / 4,7 | 5,5 / 6,0 |
  | `--on-forja` sobre `--forja` / `--forja-2` | 5,7 / 8,4 | = |
  | `--forja-ink` sobre `--forja-soft` | 5,1 | 6,6 |
  | `--ok-ink` sobre `--ok-soft` | 5,1 | 7,7 |
  | `--info-ink` sobre `--info-soft` | 6,1 | 6,8 |
  | `--bad-ink` sobre `--bad-soft` | 5,2 | 6,4 |
  | `--warn-ink` sobre `--warn-soft` | 5,2 | 8,0 |
  | branco sobre `--bad-strong` | 5,5 | = |
  | rótulos do console (`#8a909b`) sobre `--console` | 5,5 | — |

- As cores cheias (`--forja`, `--ok`, `--bad`, `--info`) **não são usadas em
  texto**: ficam só em gráficos, pontos e bordas. Texto branco sobre laranja
  também não, porque dá 3,1:1 e reprova; por isso o botão principal tem
  texto grafite.
- **O estado nunca depende só da cor**: toda etiqueta tem ícone e texto, os
  nós do fluxo têm ícone, o posto parado e a falha têm listras, e os KPIs têm
  ícone de sinal.
- No terminal, todo alvo de toque tem pelo menos 48 px (os botões de ação,
  84 px), e as ações bloqueadas por uma parada dizem por quê.
- Os botões só com ícone têm `aria-label`; o token tem `aria-label`.
- O foco por teclado é sempre visível (`:focus-visible`, laranja de 3 px).
- `prefers-reduced-motion` desliga pulsos, entradas e transições.

## Regras de uso

| ✅ Faça | ❌ Não faça |
|---|---|
| Use os tokens (`var(--ok)`), nunca o hexadecimal direto | Introduzir uma segunda cor de marca |
| Texto colorido com os tokens `-ink` | Texto com `--forja`, `--ok` ou `--bad` (cores de gráfico) |
| Uma só ação principal (laranja) por cartão | Pôr dois botões laranja lado a lado |
| Mostrar identificadores com `.id` | Usar `#7` solto para identificar uma OP |
| Estados com `tag()` (ícone + cor) | Criar etiquetas de estado com cores próprias ou sem ícone |
| Listas longas dentro de `moldura()` | Tabelas grandes sem filtro nem exportação |
| Abrir detalhes no próprio painel (`/#ordens/7`) | Abrir detalhes numa nova aba |
| Rótulos curtos em mono caixa alta | Caixa alta em frases ou parágrafos |
| Números grandes com `--f-display` e algarismos tabulares | Números de KPI na fonte de corpo |

## Como estender

1. Uma tela nova é uma `<section class="secao grid" id="s-NOME">` com cartões.
   Registre o título em `TITULOS`, a função em `telas` e o item em `nav`.
   Para um módulo que pode estar desligado, use `data-mod="id-do-modulo"` (fase 2: `pedidos` esconde Pedidos e Clientes; `indicadores` esconde OEE e o KPI).
2. Um estado novo entra em `ESTADO` (para `plan`, `wait`, `act`, `ok`, `bad`
   ou `skip`) e, se precisar de texto especial, em `ROT`. O terminal tem a
   sua própria cópia de `ESTADO` e `ROT`: mantenha as duas iguais.
3. Uma sub-tela usa o hash com barra (`/#tela/sub`). `sub()` devolve o que
   vem depois da barra, e `mostrar()` ajusta o título e a trilha.
4. Uma cor nova primeiro vira token em `tokens_css()`, em `:root` **e** no
   bloco escuro.
