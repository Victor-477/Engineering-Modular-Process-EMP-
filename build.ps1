# build.ps1 - testa e compila o EMP e os plugins para executaveis Windows nativos.
#
#   powershell -ExecutionPolicy Bypass -File build.ps1
#
# Rota: .cryo -> bytecode .pyro -> C (AOT) -> gcc (MinGW) -> .exe
# O .exe nao precisa de Python, Go nem da VM para rodar.
#
# CRYO_HOME aponta para o checkout do toolchain (pastas Burnout/, Cryo/, Pyro/).
# Padrao: a pasta acima deste repositorio.

$ErrorActionPreference = "Stop"
$emp = $PSScriptRoot
$cryo = $env:CRYO_HOME
if (-not $cryo) { $cryo = Split-Path -Parent $emp }
if (-not (Test-Path "$cryo\Burnout\cryoc.py")) {
    throw "toolchain Cryo nao encontrado em '$cryo' - defina CRYO_HOME"
}
$cryoc = "$cryo\Burnout\cryoc.py"
$pyro  = "$cryo\Burnout\pyro.py"
Set-Location $emp

# O gcc do MinGW falha em silencio se uma DLL anterior no PATH o encobrir.
$env:PATH = "C:\MinGW\bin;C:\Windows\system32;C:\Windows;" + $env:PATH

New-Item -ItemType Directory -Force "$emp\build" | Out-Null

Write-Host "== testes do nucleo (VM Pyro)"
python $cryoc tests/test_nucleo.cryo --backend pyro --run -o build/testes.pyro
if ($LASTEXITCODE -ne 0) { throw "testes do nucleo falharam" }

Write-Host "== testes de eventos (cryoc test)"
python $cryoc test tests/test_eventos.cryo --backend pyro
if ($LASTEXITCODE -ne 0) { throw "testes de eventos falharam" }

Write-Host "== nucleo -> build\emp.exe"
python $pyro build src/main.cryo -o build/emp.exe
if ($LASTEXITCODE -ne 0) { throw "build do nucleo falhou" }

Get-ChildItem "$emp\plugins_src" -Directory | ForEach-Object {
    $nome = $_.Name
    Write-Host "== plugin $nome -> build\$nome.exe"
    python $pyro build "plugins_src/$nome/$nome.cryo" -o "build/$nome.exe"
    if ($LASTEXITCODE -ne 0) { throw "build do plugin $nome falhou" }
}

Remove-Item -Force -ErrorAction SilentlyContinue "$emp\build\testes.pyro"
Get-ChildItem "$emp\build\*.exe" | Select-Object Name, Length
