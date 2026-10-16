# EMP

ERP modular para linha de produção, escrito somente em Cryo e compilado para um
executável nativo do Windows. Escopo, arquitetura e lacunas da linguagem:
**[ESCOPO.md](ESCOPO.md)**.

## Compilar

O toolchain Cryo é procurado na pasta acima deste repositório (ou em `CRYO_HOME`).

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Gera `build\emp.exe` e `build\qualidade.exe` (plugin).

Durante o desenvolvimento, sem gerar o `.exe`:

```bash
python ../Burnout/cryoc.py src/main.cryo --backend pyro -o build/emp.pyro --run
```

## Rodar

```powershell
$env:ERP_TOKENS="tk-ana:ana:admin,tk-joao:joao:operador,tk-rui:rui:almoxarife"
.\qualidade.exe          # opcional: plugin, porta 8091
.\emp.exe              # http://localhost:8080
```

| Variável | Padrão | |
|---|---|---|
| `ERP_PORTA` | `8080` | porta HTTP |
| `ERP_DADOS` | `dados` | diretório de dados |
| `ERP_PLUGINS` | `plugins` | manifestos `*.plugin` |
| `ERP_TOKENS` | vazio | `token:usuario:perfil,...` — vazio = modo dev sem autenticação |
| `PYRO_HTTP_TIMEOUT_MS` | `10000` | prazo para uma requisição chegar inteira (use ~2000 na rede local) |
| `PYRO_HTTP_CLIENT_TIMEOUT_MS` | `15000` | prazo de cada chamada a um plugin |
| `QUALIDADE_PORTA` / `QUALIDADE_LIMITE` | `8091` / `5` | plugin de qualidade |

## API (corpos em form-urlencoded)

```bash
T="Authorization: Bearer tk-ana"
curl -H "$T" -X POST localhost:8080/api/cadastros/produtos -d "codigo=aco&tipo=MP&unidade=KG"
curl -H "$T" -X POST localhost:8080/api/cadastros/produtos -d "codigo=sup01&tipo=PA"
curl -H "$T" -X POST localhost:8080/api/cadastros/estrutura -d "produto=sup01&componente=aco&quantidade=1,5"
curl -H "Authorization: Bearer tk-rui" -X POST localhost:8080/api/estoque/entrada -d "produto=aco&quantidade=100"
curl -H "$T" -X POST localhost:8080/api/producao/ordens -d "produto=sup01&quantidade=50&posto=PRENSA1"
curl -H "$T" -X POST "localhost:8080/api/producao/liberar?id=1"
curl -H "Authorization: Bearer tk-joao" -X POST "localhost:8080/api/producao/apontar?id=1" -d "boa=30&refugo=2"
curl -H "$T" localhost:8080/api/estoque/saldos
curl -H "$T" localhost:8080/api/producao/indicadores
curl -H "$T" localhost:8080/api/qualidade/ncs
curl -H "$T" localhost:8080/api/sistema/modulos
```

| Prefixo | Rotas |
|---|---|
| `/api/sistema` | `GET /saude`, `GET /modulos` |
| `/api/cadastros` | `GET/POST /produtos`, `GET/POST /estrutura`, `GET/POST /postos` |
| `/api/producao` | `GET/POST /ordens`, `GET /ordem?id=`, `POST /liberar?id=`, `POST /apontar?id=`, `POST /cancelar?id=`, `GET /indicadores` |
| `/api/estoque` | `GET /saldos[?produto=]`, `GET /movimentos`, `POST /entrada`, `POST /ajuste` |
| `/api/qualidade` (plugin) | `GET/POST /ncs` |

## Testes

```bash
python ../Burnout/cryoc.py tests/test_nucleo.cryo --backend pyro --run
python ../Burnout/cryoc.py test tests/test_eventos.cryo --backend pyro
```
