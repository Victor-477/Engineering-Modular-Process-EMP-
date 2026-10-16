# Forja — sistema de design do EMP

> Versão 1.0 · implementado em [`src/nucleo/painel.cryo`](../src/nucleo/painel.cryo)

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

Todos ficam em `:root`. O modo escuro redefine os mesmos nomes em
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
| Atenção | `--warn` `#e08a00` | Disponibilidade abaixo de 85% |
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

### Etiqueta de estado

Pílula de 26 px com um ponto na cor do texto, em minúsculas.

| Classe | Estados | Visual |
|---|---|---|
| `st-ok` | operando, concluída, encerrada, ativo | Verde |
| `st-wait` | liberada | Azul |
| `st-act` | em produção | Laranja, **ponto pulsando** |
| `st-bad` | parado, cancelada, aberta, falhou | Vermelho sobre **listras diagonais** |
| *(neutro)* | planejada | Cinza |

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
Uso atual: ordens por estado.

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
  | branco sobre `--bad-strong` | 5,5 | = |
  | rótulos do console (`#8a909b`) sobre `--console` | 5,5 | — |

- As cores cheias (`--forja`, `--ok`, `--bad`, `--info`) **não são usadas em
  texto**: ficam só em gráficos, pontos e bordas. Texto branco sobre laranja
  também não, porque dá 3,1:1 e reprova; por isso o botão principal tem
  texto grafite.
- **O estado nunca depende só da cor**: toda etiqueta tem texto, o posto
  parado tem listras, e os KPIs têm ícone de sinal.
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
| Estados com `tag()` | Criar etiquetas de estado com cores próprias |
| Rótulos curtos em mono caixa alta | Caixa alta em frases ou parágrafos |
| Números grandes com `--f-display` e algarismos tabulares | Números de KPI na fonte de corpo |

## Como estender

1. Uma tela nova é uma `<section class="secao grid" id="s-NOME">` com cartões.
   Registre o título em `TITULOS`, a função em `telas` e o item em `nav`.
   Para um módulo que pode estar desligado, use `data-mod="id-do-modulo"`.
2. Um estado novo entra em `ESTADO` (para `st-ok`, `st-wait`, `st-act` ou
   `st-bad`) e, se precisar de texto especial, em `ROT`.
3. Uma cor nova primeiro vira token em `:root` **e** no bloco escuro.
