# Requisitos da linguagem Cryo/Pyro para o ERP EMP

> Versão 0.1 — 16/10/2026. Levantamento feito sobre os branches `dev` de
> `Victor-477/Cryo`, `Victor-477/Burnout` e `Victor-477/pyro`, lendo o código
> **e executando programas de teste** na VM Pyro (Go) neste ambiente.

## Contexto que define os requisitos

| Decisão | Consequência para a linguagem |
|---|---|
| ERP **industrial** | Cálculos de quantidade/custo com precisão, jobs longos (MRP), muitos relatórios |
| **SaaS** multiempresa | Servidor concorrente, isolamento de falhas entre clientes, segurança forte |
| **NF-e no MVP** | XML + assinatura digital (XML-DSig), certificado A1 (.pfx), HTTPS com certificado de cliente (mTLS), SOAP, gzip/base64 |
| **SQLite** | Acesso a biblioteca C externa — hoje o backend `pyro` **não aceita** blocos estrangeiros |
| **Windows primeiro** (Linux também) | Caminhos Unicode, serviço do Windows, build com MinGW/MSVC ligando bibliotecas C |

## Legenda

- **Prioridade**: **P0** = bloqueia o início do ERP · **P1** = necessário para o MVP (Fases 0–5 + NF-e) · **P2** = necessário para escalar/produção madura
- **Evidência**: ✅ verificado executando · 📖 verificado no código/documentação · 💭 necessidade do domínio (não existe na linguagem)
- **Engines**: hoje cada native precisa existir no **Go VM**, no **C runtime** (C VM + AOT) e, pela regra de paridade, também em C++/C#. Ver **A2**.

---

## A. Fundação: extensão nativa e engine de produção

Tudo o que vem depois (SQLite, criptografia, TLS, XML, compressão) é muito mais
barato se existir **um jeito de ligar bibliotecas C ao programa Pyro**. Sem isso,
cada função precisa ser escrita à mão em 2 a 4 engines.

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| A1 | **FFI / natives externas** — declarar em Cryo uma função implementada em C e ligá-la no build | 📖 Blocos estrangeiros dão erro no backend `pyro` (`estrangeiros.md`: "`asm`/`pyro`: error"). A API de embedding em C (`pyro_vm_register_native`, `pyro_vm_eval`, `pyro_vm_call`) é **simulada** — `eval` e `call` só retornam `null` | Sintaxe tipo `extern "sqlite3" fn sqlite3_open(string path) -> int;` ou um módulo de natives registráveis (`native lib "emp_sqlite" { fn db_open(string) -> int; }`), com tabela de natives carregada do lado C do runtime/AOT. Valores opacos (handles) como novo tipo de valor | **P0** |
| A2 | **Definir a engine de produção** | 📖 Paridade exigida em Go VM, C VM, AOT, C++ VM e C# VM | Recomendo: **C runtime + AOT = engine de produção** (gera `.exe` nativo, liga bibliotecas C, ideal para Windows). Go VM fica como engine de desenvolvimento/referência; natives "de sistema" (SQLite, crypto, XML) podem existir só na engine de produção | **P0** (decisão) |
| A3 | **Ligar bibliotecas C no build** (`pyro app build`) | 📖 O build chama o compilador C, mas não há opção para incluir `.c`/`.a`/`.lib` extras | Opções `--link`, `--cflags`, `--csrc` ou seção `[native]` no `cryo.toml` (ex.: `sources = ["vendor/sqlite3.c"]`). Funcionar com **MinGW e MSVC** | **P0** |
| A4 | **Limite de 256 natives** | 📖 `OP_NATIVE` usa `u8` para o id; 69 já estão em uso | Ampliar para `u16` (nova versão do formato `.pyro`) ou natives com namespace resolvidas por nome | P1 |
| A5 | **Sincronizar `main`** dos 3 repositórios | ✅ `main` do Burnout chama `semantic.check(ast, source, path)`, `main` do Cryo só tem `check(program)` → `TypeError`. Só `dev` compila | Merge de `dev` em `main` + tag de versão comum (ex.: `v1.5.0`) nos três | **P0** |

---

## B. Banco de dados (SQLite)

Depende de A1/A3 (compilar `sqlite3.c` amalgamation junto). Em SaaS, a
recomendação é **um arquivo SQLite por cliente (tenant)** + um banco de controle.

| ID | Recurso | Proposta de API | Prio |
|---|---|---|---|
| B1 | Abrir/fechar conexão, várias ao mesmo tempo | `db_open(string path) -> Db` · `db_close(Db)` | P0 |
| B2 | **Prepared statements com parâmetros** (única forma aceitável — evita SQL injection) | `db_exec(Db, string sql, any[] params) -> int` (linhas afetadas) | P0 |
| B3 | Consultas retornando linhas | `db_query(Db, string sql, any[] params) -> map<string,any>[]` e, idealmente, tipado: `db_query(...) as Produto[]` com validação de tipos (ver J3) | P0 |
| B4 | Transações | `db_begin`, `db_commit`, `db_rollback` (ou `db_tx(Db, fn() -> bool)`) | P0 |
| B5 | Metadados | `db_last_id(Db)`, `db_changes(Db)` | P1 |
| B6 | Configuração | `db_busy_timeout`, `PRAGMA journal_mode=WAL`, `foreign_keys=ON` (via `db_exec`) | P1 |
| B7 | `NULL` ↔ opcionais `T?`, BLOB ↔ `bytes` (ver E1) | — | P1 |
| B8 | Backup online | `db_backup(Db, string destino)` (API `sqlite3_backup_*`) | P2 |
| B9 | Iteração preguiçosa de resultados grandes | `for (Row r in db_rows(...))` usando o protocolo `iter()` (11.5) | P2 |

---

## C. Números e dinheiro

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| C1 | **Detecção de overflow em `int`** | ✅ `9223372036854775807 + 1` imprime `-9223372036854775808` sem erro | Overflow gera erro capturável (modo seguro) ou funções `checked_add/sub/mul -> int?` | **P0** |
| C2 | **Tipo `decimal`** (ponto fixo) | ✅ Só `int` e `number` (double): `0.1 + 0.2` = `0.30000000000000004` | Tipo `decimal` com escala (ex.: 18 dígitos inteiros, até 10 casas) e operações + − × ÷ com modo de arredondamento. Paliativo: `int` em centavos/milésimos (biblioteca do EMP) — por isso P1 e não P0 | P1 |
| C3 | Arredondamento com modo e casas | 📖 Só `round(x)`, `floor`, `ceil` | `round_to(x, casas, modo)` com `HALF_UP`, `HALF_EVEN`, `DOWN`, `UP`; `div_round(a, b, modo)` para inteiros | P1 |
| C4 | **Conversão de texto que não derruba o processo** | ✅ `to_int("abc")` **aborta o programa** e **não é capturável** por `try/catch` | `parse_int(s) -> int?` / `parse_number(s) -> number?` (ou erro capturável) | **P0** |
| C5 | Formatação pt-BR | ✅ `${1234567.891:,.2f}` → `1,234,567.89` (padrão americano) | `format_number(v, casas, sep_decimal, sep_milhar)` ou especificador de locale (`${v:L.2f}` → `1.234.567,89`) | P1 |
| C6 | Parse pt-BR | 💭 `"1.234,56"` | `parse_decimal(s, sep_decimal, sep_milhar)` | P1 |
| C7 | Semântica de `/` e `%` com negativos documentada e igual em todas as engines | ✅ No Go VM `-7 / 2` = `-3` e `-7 % 2` = `-1` (truncamento) — falta garantir o mesmo nas outras engines | Documentar + teste de paridade | P2 |

---

## D. Texto e Unicode

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| D1 | **Strings conscientes de UTF-8** | ✅ `len("Ação Ônibus")` = **14** (bytes, são 11 caracteres); `"Ação Ônibus"[0..2]` = `A�` (**corta caractere ao meio**); `pad_start` conta bytes | `len`, fatias, `substr`, `pad_*`, `chars`, `reverse_str` contando **caracteres** (code points); `byte_len` separado. Limites de campos da NF-e são em caracteres | **P0** |
| D2 | Remover acentos / normalizar | 💭 Busca de clientes/produtos, campos da NF-e | `strip_accents(s)`, `normalize(s, "NFC"/"NFD")` | P1 |
| D3 | **Construção eficiente de strings** | ✅ 20.000 concatenações `acc = acc + "x"` = 65 ms — custo **quadrático** (XML de NF-e, CSV, HTML e JSON grandes) | Otimizar `s = s + x` no lugar quando a referência é única (refcount 1) **ou** `StringBuilder` (`sb_new`, `sb_append`, `sb_to_string`) | P1 |
| D4 | Expressões regulares | 💭 Validação de campos, parsing | `regex_match`, `regex_find_all`, `regex_replace` (RE2/PCRE2 via A1) | P1 |
| D5 | Comparação/ordenação com regras do português | 💭 Listagens ordenadas por nome | `compare_locale(a, b, "pt-BR")` | P2 |

---

## E. Binário e codificações

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| E1 | **Tipo `bytes`** | 📖 Só `write_bytes(path, int[])` (um `int` de 8 bytes por byte); sem `read_bytes` | Tipo `bytes` imutável com fatias, `len`, `read_bytes(path)`, `write_bytes(path, bytes)`, conversão `to_bytes(string)`/`utf8_decode(bytes)` | P1 |
| E2 | Base64 / Base64URL | 💭 Certificado, assinatura NF-e, JWT, anexos | `base64_encode/decode`, `base64url_encode/decode` | P1 |
| E3 | Hex | 💭 Hashes, chave de acesso | `hex_encode/decode` | P1 |
| E4 | gzip/deflate | 💭 Distribuição DF-e (SEFAZ devolve XML em gzip+base64), compressão HTTP | `gzip(bytes)`, `gunzip(bytes)`, `deflate/inflate` (zlib/miniz via A1) | P1 |
| E5 | ZIP | 💭 Exportar lote de XMLs ao contador, gerar `.xlsx` | `zip_create`, `zip_add`, `zip_read` | P2 |

---

## F. Criptografia e segurança

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| F1 | Hashes | 📖 Nenhum native de hash (HMAC-SHA256 existe só **dentro do compilador** para assinar `.pyro`) | `sha1` (**a NF-e assina com RSA-SHA1**), `sha256`, `sha512` → `bytes` | **P0** |
| F2 | HMAC | 💭 Tokens de sessão/JWT, webhooks | `hmac_sha256(key, msg)` | **P0** |
| F3 | **Aleatório criptográfico** | 📖 `random`/`random_int` são PRNG com semente fixa (`prngState = 0x853c49e6748fea9b`) — **previsível** | `random_bytes(n) -> bytes` (CSPRNG do SO: `BCryptGenRandom` no Windows, `getrandom` no Linux) | **P0** |
| F4 | Hash de senha | 💭 Login dos usuários | `password_hash(s)` / `password_verify(s, hash)` (Argon2id ou bcrypt; PBKDF2 aceitável) | **P0** |
| F5 | Comparação em tempo constante | 💭 Verificar tokens | `constant_time_eq(a, b)` | P1 |
| F6 | UUID | 💭 IDs públicos em SaaS | `uuid_v4()`, `uuid_v7()` | P1 |
| F7 | Criptografia simétrica | 💭 Guardar certificados A1 e segredos de cada cliente cifrados (LGPD) | `aes_gcm_encrypt(key, nonce, data, aad)` / `decrypt` | P1 |
| F8 | **Assinatura RSA** | 💭 XML-DSig da NF-e | `rsa_sign(private_key, data, "SHA1"\|"SHA256")`, `rsa_verify` | P1 (NF-e) |
| F9 | **Certificado A1 (.pfx / PKCS#12)** | 💭 Todo emissor de NF-e usa | `pkcs12_load(bytes, senha) -> {key, cert, chain}`; ler validade, titular, CNPJ do certificado; exportar cert em base64 (vai no XML) | P1 (NF-e) |
| F10 | Proteção de chave mestra no Windows | 💭 Não deixar a chave de cifragem em texto no disco | `dpapi_protect/unprotect` (Windows) / keyring (Linux) | P2 |

Sugestão de biblioteca via A1: **mbedTLS** (cobre F1–F9 e H2, compila em MinGW e MSVC) ou **BearSSL**; Argon2 da implementação de referência.

---

## G. XML (NF-e)

| ID | Recurso | Proposta | Prio |
|---|---|---|---|
| G1 | Gerar XML com escape correto | `xml_escape(s)` + builder (`xml_el(nome, attrs, filhos)`) — pode ser biblioteca Cryo se D3 existir | P1 |
| G2 | **Ler XML** (retorno da SEFAZ, **importar XML de NF-e de fornecedor** na entrada de compras) | Parser para árvore (`xml_parse(s) -> XmlNode`) com consulta por caminho (`xml_find(node, "NFe/infNFe/det")`) e namespaces | P1 |
| G3 | **Canonicalização C14N** | `xml_c14n(node)` (C14N 1.0, exigido pela assinatura da NF-e) | P1 (NF-e) |
| G4 | Assinatura XML-DSig *enveloped* | Biblioteca Cryo sobre F1 + F8 + G3 (`xmldsig_sign(xml, ref_id, key, cert)`) | P1 (NF-e) |
| G5 | Validação contra XSD | `xml_validate(xml, xsd_path)` — evita rejeições da SEFAZ; pode ficar para depois (a SEFAZ valida) | P2 |

---

## H. Cliente HTTP (SEFAZ, bancos, integrações)

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| H1 | **Requisição completa** | 📖 `http_get(url)` e `http_post(url, body)` apenas: sem cabeçalhos, `Content-Type` fixo `application/json`, sem status, sem timeout, **qualquer erro vira `""`** | `http_request({method, url, headers, body, timeout_ms}) -> Response {status, headers, body}` com erro tratável (`Result`/opcional). PUT/PATCH/DELETE | P1 |
| H2 | **HTTPS com certificado de cliente (mTLS)** | 💭 A SEFAZ exige o certificado A1 na conexão TLS | `tls: {client_cert, client_key, ca_bundle}` no `http_request` (cadeia ICP-Brasil) | P1 (NF-e) |
| H3 | SOAP 1.2 | Só um caso de H1 (`application/soap+xml`) + G1/G2 | — | P1 (NF-e) |
| H4 | Proxy corporativo | 💭 Clientes industriais costumam ter proxy | Respeitar `HTTPS_PROXY` / parâmetro `proxy` | P2 |

---

## I. Servidor HTTP (SaaS)

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| I1 | **Cabeçalhos de resposta** | ✅ `http_respond(status, content_type, body)` só escreve `Content-Type`, `Content-Length` e `Connection: close` | `http_respond(status, headers: map<string,string>, body)` — `Set-Cookie`, `Location`, `Cache-Control`, `Content-Disposition` (download de XML/PDF), CORS, cabeçalhos de segurança | **P0** |
| I2 | Corpo binário na resposta | 💭 PDF da DANFE, XML, anexos | Aceitar `bytes` (E1) no corpo | P1 |
| I3 | Escolher interface de escuta | 📖 `http_listen(port)` escuta em **todas** as interfaces (`":"+port`) | `http_listen(host, port)` — ex.: só `127.0.0.1` atrás do nginx/IIS | P1 |
| I4 | **Atender requisições em paralelo** | 📖 Uma requisição por vez; `spawn`/`await` é cooperativo e sem I/O assíncrono | Opção 1: `http_accept` assíncrono integrado ao escalonador (IOCP no Windows, epoll no Linux). Opção 2: pool de *workers*, cada um com sua VM isolada. Paliativo: vários processos atrás do proxy + SQLite WAL | P1 |
| I5 | Limites e streaming | 📖 Corpo lido inteiro em buffer fixo; sem *chunked* | Limite de corpo configurável, upload grande (XML/.pfx), resposta em *chunks* para exportações | P1 |
| I6 | Keep-alive | ✅ Sempre `Connection: close` | Suporte a keep-alive | P2 |
| I7 | multipart/form-data | 💭 Upload de arquivos | `http_parse_multipart(req) -> Part[]` (depende de E1) | P1 |
| I8 | WebSocket ou SSE | 💭 Painel de chão de fábrica em tempo real | `http_upgrade_ws` ou resposta SSE | P2 |
| I9 | TLS no próprio servidor | 💭 | Opcional — proxy reverso resolve | P2 |

---

## J. Robustez do runtime (essencial para SaaS)

Em SaaS, **um erro numa requisição de um cliente não pode derrubar o servidor de todos.**

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| J1 | **Erros de runtime capturáveis** | ✅ Índice fora do limite, divisão por zero e `to_int` inválido **encerram o processo**; `try/catch` não os captura (testado: `try { xs[5] } catch` → processo morre) | Esses erros viram exceções capturáveis no Pyro (como já acontece no backend Go via `recover`), ou uma barreira por requisição: `recover(fn) -> Result` | **P0** |
| J2 | **Exceções tipadas** | 📖 `throw("msg")` / `catch (string e)` — só texto | `throw` de qualquer valor (struct/enum de erro), `catch (ErroNegocio e)`, código + mensagem + campo | P1 |
| J3 | **`json_decode` tipado que valida** | ✅ `json_decode("{\"qty\":\"nao-e-int\"}") as Item` aceita e `it.qty` vira `"nao-e-int"` num campo `int` | Decode validado: `json_decode_as<T>(s) -> Result<T, ErroValidacao[]>` com campos obrigatórios/opcionais e erro por campo. O mesmo mecanismo serve para `db_query as T[]` (B3) | **P0** |
| J4 | Limites por requisição | 💭 Evitar que um cliente trave os outros (laço infinito, consulta enorme) | Orçamento de instruções/tempo (`with_budget(ms, fn)`) e limite de memória | P2 |
| J5 | Vazamento de memória em processo longo | 📖 Contagem de referências — ciclos (closures e mapas que se referenciam) podem vazar | Teste de longa duração + detector de ciclos/coleta de ciclos | P2 |

---

## K. Data e hora

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| K1 | **Tipos de data/hora** | 📖 Só `now_ms()` e `monotonic_ms()` | `Date` (dia civil) e `DateTime` (instante) com `date_from_iso`, `to_iso`, `add_days`, `add_months`, `diff_days`, `day_of_week`, fim de mês | P1 |
| K2 | **Fuso horário** | 💭 A NF-e exige `dhEmi` com deslocamento (`2026-10-16T10:00:00-03:00`); SaaS atende vários estados | `to_zone(dt, "America/Sao_Paulo")`, `format_datetime(dt, padrão, zona)`; base de fusos embutida (o Windows não tem tzdata IANA) | P1 |
| K3 | Formatação pt-BR | 💭 `16/10/2026` | `format_date(d, "dd/MM/yyyy")`, `parse_date(s, padrão)` | P1 |

(Feriados e dias úteis: biblioteca do EMP, não da linguagem.)

---

## L. Processos, jobs e concorrência

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| L1 | **Executar processo com segurança** | 📖 `exec(cmd)` passa uma string para `cmd /C`/`sh -c` (risco de injeção), retorna só stdout, **sem código de saída**, sem stderr, sem timeout | `process_run(prog, args[], {cwd, env, timeout_ms, stdin}) -> {code, stdout, stderr}` sem shell | P1 |
| L2 | Tarefas agendadas / em segundo plano | 💭 MRP, consulta de lote da NF-e, envio de e-mails, backups | Timer (`every(ms, fn)`, `after(ms, fn)`) integrado ao loop + *workers* reais (threads com VM isolada ou processos filhos) | P1 |
| L3 | Paralelismo de CPU | 📖 "There is no CPU parallelism" no Pyro | Workers isolados (mensagens, sem memória compartilhada) | P2 |

---

## M. Sistema operacional (Windows primeiro)

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| M1 | **Caminhos com acento no Windows** | 📖 O C runtime abre arquivos com `fopen` (6 usos, nenhum `_wfopen`/`MultiByteToWideChar`) — `C:\Usuários\...` ou `Produção\` falham | Converter UTF-8 → UTF-16 e usar as APIs `W` no Windows (arquivos, diretórios, env, processos) | **P0** |
| M2 | Console UTF-8 no Windows | 💭 Logs com acento saem corrompidos | `SetConsoleOutputCP(CP_UTF8)` na inicialização | P1 |
| M3 | Arquivos e caminhos | 📖 Sem `read_bytes`, `append_file`, `rename`, remover diretório, data de modificação, diretório temporário | `path_join`, `path_dir`, `path_ext`, `temp_dir`, `app_data_dir`, `append_file`, `rename`, `remove_dir`, `file_mtime`, `copy_file` | P1 |
| M4 | **Logs** | 📖 Só `print` (stdout) | `log_info/warn/error` com níveis, saída em stderr/arquivo com rotação; JSON estruturado | P1 |
| M5 | Encerramento limpo | 💭 Fechar o SQLite e terminar requisições ao parar o serviço | `on_shutdown(fn)` (Ctrl+C, SIGTERM, parada do serviço) | P1 |
| M6 | **Serviço do Windows** | 💭 Instalação em servidor do cliente / on-premises | Executável que se registra no SCM (`emp.exe --install-service`), responde a start/stop | P2 |
| M7 | Instância única / trava de arquivo | 💭 Evitar dois servidores no mesmo banco | `file_lock(path) -> bool` | P2 |

---

## N. Documentos e comunicação

| ID | Recurso | Proposta | Prio |
|---|---|---|---|
| N1 | **PDF** (DANFE, pedido, ordem de produção) | Biblioteca Cryo de PDF (depende de E1 + E4) ou native (libharu/PDFio via A1) | P1 |
| N2 | Código de barras e QR Code | Code128 (DANFE) e QR (NFC-e, etiquetas de produção) — viável em Cryo puro | P1 |
| N3 | E-mail (SMTP com TLS) | `smtp_send({host, port, user, pass, from, to, subject, body, attachments})`, ou envio via API HTTP de provedor (H1) | P1 |
| N4 | Planilhas `.xlsx` | Biblioteca Cryo sobre E5 (ZIP) + G1 | P2 |

---

## O. Linguagem — ergonomia para um sistema grande

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| O1 | **Reflexão de campos em tempo de compilação** | 📖 Existe `schema_of(T)` (JSON Schema) | `fields_of(T)` com nome/tipo/opcional para gerar SQL, validação e formulários sem repetir código | P1 |
| O2 | Atributos/anotações em campos | 💭 Tags da NF-e (`cProd`, `xProd`), nomes de colunas | `struct Item { @xml("cProd") string codigo; @db("preco_centavos") int preco; }` | P2 |
| O3 | Enum ↔ texto | 💭 Gravar status no banco/JSON | `to_string(Status.APROVADO)` e `Status.parse("APROVADO") -> Status?` garantidos em todas as engines | P1 |
| O4 | Valores padrão em structs | 💭 Entidades com muitos campos opcionais | `struct Pedido { int desconto = 0; }` e `Pedido{..base, status: X}` | P2 |
| O5 | Despacho dinâmico (`dyn Trait`) | 📖 Traits só com despacho estático | Objetos de trait, ou continuar com structs de funções (já funciona) | P2 |
| O6 | Constantes públicas de módulo | 💭 Alíquotas, códigos fiscais | `pub const` exportável entre módulos (confirmar em todas as engines) | P1 |

---

## P. Ferramentas e qualidade

| ID | Recurso | Situação atual | Proposta | Prio |
|---|---|---|---|---|
| P1 | **Análise de taint para SQL e afins** | 📖 Auditor cobre exec, path, SSRF, segredos | Novos *sinks*: `tainted-sql` (SQL montado por concatenação), injeção de XML, de cabeçalho HTTP e de log | P1 |
| P2 | Sandbox para os novos natives | 📖 Capacidades `fs.read`, `fs.write`, `net`, `exec`, `env` | Capacidades `db`, `crypto.key`, e `net` com **lista de hosts permitidos** (ex.: só endpoints da SEFAZ) | P1 |
| P3 | Testes | 📖 `test fn` + `cryoc test` | `before_each/after_each`, *fixtures*, *mock* de `http_request` e relógio (`now`) controlável | P1 |
| P4 | Pacotes | 📖 Só dependências por caminho local, sem registro | Dependências por git + commit fixo no `cryo.lock` (para separar `emp-core`, `emp-nfe`) | P2 |
| P5 | CI do toolchain no Windows | 📖 CI planejado só em Ubuntu (roadmap 14.1) | Matriz Windows (MinGW + MSVC) e Linux | P1 |

---

## Ordem de implementação recomendada

**Onda 0 — destrava o projeto (P0)**
1. A5 sincronizar `main` e versionar
2. A2 decidir a engine de produção (recomendo C runtime + AOT)
3. A1 + A3 FFI e ligação de bibliotecas C (Windows MinGW/MSVC)
4. J1 erros de runtime capturáveis · C4 `parse_int`/`parse_number` seguros · C1 overflow
5. D1 strings UTF-8 · M1 caminhos Unicode no Windows
6. J3 decode tipado com validação
7. I1 cabeçalhos na resposta HTTP
8. B1–B4 SQLite (via A1) · F1–F4 hash, HMAC, CSPRNG, hash de senha

**Onda 1 — MVP do ERP (P1 gerais)**
C2/C3/C5/C6 decimal e formatação · D2/D3/D4 · E1–E4 · F5–F7 · H1 · I2/I3/I4/I5/I7 · J2 · K1–K3 · L1/L2 · M2–M5 · N2/N3 · O1/O3/O6 · P1/P2/P3/P5 · A4

**Onda 2 — NF-e**
F8/F9 RSA e PKCS#12 · G1–G4 XML, C14N e XML-DSig · H2/H3 mTLS e SOAP · N1 PDF (DANFE)

**Onda 3 — produção madura (P2)**
Restante: B8/B9, C7, D5, E5, F10, G5, H4, I6/I8/I9, J4/J5, L3, M6/M7, N4, O2/O4/O5, P4

---

## O que fica de fora da linguagem (vira biblioteca do EMP)

Regras fiscais (ICMS, IPI, PIS/COFINS, CFOP, NCM), validação de CPF/CNPJ,
feriados e dias úteis, cálculo de MRP, layout da DANFE, montagem do XML da NF-e
e comunicação com cada webservice da SEFAZ. Essas partes serão escritas em Cryo
sobre os recursos acima.

---

## Apêndice — testes executados

Executados com `python3 burnout/cryoc.py <arquivo> --backend pyro --run`
(branches `dev`, VM em Go).

```cryo
print(len("Ação Ônibus"));            // 14  (são 11 caracteres)
print("Ação Ônibus"[0..2]);           // A�  (corta o "ç" ao meio)
int big = 9223372036854775807;
print(big + 1);                        // -9223372036854775808  (sem erro)
print(0.1 + 0.2);                      // 0.30000000000000004
print("${1234567.891:,.2f}");          // 1,234,567.89
try { print(to_int("abc")); } catch (string e) { print("pegou"); }
                                       // processo encerrado: "to_int: 'abc' is not a valid integer"
int[] xs = [1, 2];
try { print(xs[5]); } catch (string e) { print("pegou"); }
                                       // processo encerrado: IndexError — o catch não roda
int z = to_int("0");
try { print(10 / z); } catch (string e) { print("pegou"); }
                                       // processo encerrado: DivByZero
struct Item { string sku; int qty; }
Item it = json_decode("{\"sku\":\"A\",\"qty\":\"nao-e-int\"}") as Item;
print(it.qty);                         // nao-e-int  (aceito num campo int)
string acc = "";
for (int i in 0..20000) { acc = acc + "x"; }   // 65 ms — custo quadrático
```
