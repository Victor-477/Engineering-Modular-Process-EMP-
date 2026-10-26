# tests/test_landing_http.py
# Inicia build/landing.exe e valida todas as rotas e comandos do prompt via HTTP.
import os
import subprocess
import time
import urllib.request
import urllib.parse
import json
import sys

def run_tests():
    # Caminho absoluto: no Windows o CreateProcess não resolve "build/landing.exe"
    # (relativo com barra normal) e o Popen dá FileNotFoundError.
    exe_path = os.path.abspath(os.path.join("build", "landing.exe"))
    print(f"== Iniciando {exe_path} na porta 8088...")
    proc = subprocess.Popen([exe_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Aguarda inicialização
    time.sleep(1.5)

    base_url = "http://127.0.0.1:8088"
    sucessos = 0
    falhas = 0

    def testar_get(url_path, esperado_status=200, check_str=None):
        nonlocal sucessos, falhas
        url = base_url + url_path
        print(f"-> Testando GET {url_path}...", end=" ")
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                status = resp.status
                conteudo = resp.read().decode("utf-8")
                if status == esperado_status and (check_str is None or check_str in conteudo):
                    print(f"OK ({status})")
                    sucessos += 1
                    return conteudo
                else:
                    print(f"FALHA: status={status}, check_str={check_str}")
                    falhas += 1
                    return None
        except Exception as e:
            print(f"ERRO: {e}")
            falhas += 1
            return None

    def testar_prompt(cmd):
        nonlocal sucessos, falhas
        url = base_url + "/api/prompt"
        print(f"-> Testando POST /api/prompt ('{cmd}')...", end=" ")
        try:
            data = urllib.parse.urlencode({"prompt": cmd}).encode("utf-8")
            req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                status = resp.status
                conteudo = resp.read().decode("utf-8")
                parsed = json.loads(conteudo)
                if status == 200 and parsed.get("status") == "ok" and "acao" in parsed and "dados" in parsed:
                    print(f"OK | Acao: {parsed.get('acao')} | Status: {parsed.get('status')}")
                    sucessos += 1
                    return parsed
                else:
                    print(f"FALHA: status={status}, body={conteudo[:100]}")
                    falhas += 1
                    return None
        except Exception as e:
            print(f"ERRO: {e}")
            falhas += 1
            return None

    try:
        # 1. Rota GET /
        testar_get("/", 200, "EMP Industrial ERP")

        # 2. Rota GET /api/saude
        saude_raw = testar_get("/api/saude", 200, "EMP Industrial Landing")
        if saude_raw:
            saude = json.loads(saude_raw)
            print(f"   Dados /api/saude: versao={saude.get('versao')}, fases={saude.get('fases_modulares')}, compilador={saude.get('compilador')}")

        # 3. Pills rápidas
        pills = [
            "status fábrica",
            "otif e kpis",
            "arquivar ops",
            "sensores iot",
            "turnos e operadores",
            "ajuda"
        ]
        for pill in pills:
            testar_prompt(pill)

        # 4. Outros comandos
        testar_prompt("mrp e necessidades")
        testar_prompt("rastreabilidade de lotes")
        testar_prompt("custos e dre")

    finally:
        print("== Encerrando servidor landing.exe...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

    print(f"\n==========================================")
    print(f"Resultado dos Testes: {sucessos} sucessos, {falhas} falhas.")
    print(f"==========================================")
    if falhas > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
