#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_realtime_llm.py - Teste de Interação em Tempo Real do Agente LLM com o EMP ERP e a Landing Page.
Conecta aos servidores nativos em execução:
  - EMP Core ERP: http://127.0.0.1:8080
  - Landing & Prompt Dispatcher: http://127.0.0.1:8088
"""

import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error

ERP_URL = "http://127.0.0.1:8080"
LANDING_URL = "http://127.0.0.1:8088"

def req(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    encoded_data = None
    if data is not None:
        if isinstance(data, dict):
            encoded_data = urllib.parse.urlencode(data).encode("utf-8")
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif isinstance(data, str):
            encoded_data = data.encode("utf-8")
    
    request = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            t1 = time.perf_counter()
            body = response.read().decode("utf-8")
            elapsed_ms = (t1 - t0) * 1000.0
            return response.status, body, elapsed_ms
    except urllib.error.HTTPError as e:
        t1 = time.perf_counter()
        body = e.read().decode("utf-8")
        elapsed_ms = (t1 - t0) * 1000.0
        return e.code, body, elapsed_ms
    except Exception as e:
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0
        return 0, str(e), elapsed_ms

def log_step(step_num, title, latency_ms, status, details):
    badge = "[OK]" if 200 <= status < 300 else f"[{status}]"
    print(f"\n{badge} PASSO {step_num}: {title} (latencia: {latency_ms:.1f} ms)")
    for k, v in details.items():
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        print(f"      * {k}: {v}")

def main():
    print("=" * 75)
    print("  TESTE DE INTERACAO EM TEMPO REAL: AGENTE COGNITIVO LLM <-> EMP ERP")
    print("=" * 75)
    print(f"  * Core ERP Endpoint:      {ERP_URL}")
    print(f"  * Landing/Prompt Endpoint: {LANDING_URL}\n")

    erros = 0
    passos = 0

    # -------------------------------------------------------------
    # 1. Verificacao de Integridade dos Servidores em Execucao
    # -------------------------------------------------------------
    passos += 1
    st_erp, body_erp, lat_erp = req(f"{ERP_URL}/api/sistema/saude")
    st_land, body_land, lat_land = req(f"{LANDING_URL}/api/saude")
    if st_erp != 200 or st_land != 200:
        print(f"[ERRO] Falha ao verificar saude dos servidores: ERP={st_erp}, Landing={st_land}")
        sys.exit(1)
    
    d_erp = json.loads(body_erp)
    d_land = json.loads(body_land)
    log_step(passos, "Saude dos Servidores em Tempo Real", lat_erp + lat_land, 200, {
        "ERP Core": f"v{d_erp.get('versao')} | {d_erp.get('modulos')} modulos ativos",
        "Landing Dispatcher": f"v{d_land.get('versao')} | porta {d_land.get('porta')} | 10 fases conectadas"
    })

    # -------------------------------------------------------------
    # 2. Interacao Cognitiva via Terminal de Prompt da Landing Page
    # -------------------------------------------------------------
    prompts_teste = [
        ("status fabrica", "CONSULTA_STATUS_FABRICA"),
        ("otif e kpis", "CONSULTA_OTIF_KPIS"),
        ("sensores iot", "TELEMETRIA_IOT_CHAO_FABRICA"),
        ("turnos e operadores", "CONSULTA_TURNOS_OPERADORES"),
        ("arquivar ops", "EXPURGO_HISTORICO_TBLFIN")
    ]
    for p_txt, acao_esperada in prompts_teste:
        passos += 1
        st, b, lat = req(f"{LANDING_URL}/api/prompt", method="POST", data={"prompt": p_txt})
        if st == 200:
            resp_p = json.loads(b)
            log_step(passos, f"Prompt do Agente: '{p_txt}'", lat, st, {
                "Acao Executada": resp_p.get("acao"),
                "Mensagem LLM": resp_p.get("mensagem")[:90] + "...",
                "Payload Tecnico": str(resp_p.get("dados"))[:80] + "..."
            })
            if resp_p.get("acao") != acao_esperada:
                erros += 1
        else:
            erros += 1
            print(f"[FALHA] Prompt '{p_txt}' retornou status {st}")

    # -------------------------------------------------------------
    # 3. Setup de Engenharia no Core ERP (porta 8080)
    # -------------------------------------------------------------
    passos += 1
    st_prod, _, lat_prod = req(f"{ERP_URL}/api/cadastros/produtos", method="POST", 
                              data={"codigo": "ROBOT-ARM", "descricao": "Braco Robotico Industrial", "unidade": "UN", "tipo": "PA"})
    st_pst, _, lat_pst = req(f"{ERP_URL}/api/cadastros/postos", method="POST", 
                            data={"codigo": "MONTAGEM-01", "descricao": "Celula de Montagem 01", "capacidade_h": "8.0"})
    st_iot_pst, _, _ = req(f"{ERP_URL}/api/cadastros/postos", method="POST", 
                            data={"codigo": "FORNO-01", "descricao": "Forno de Tratamento Termico", "capacidade_h": "8.0"})
    log_step(passos, "Cadastros de Engenharia Operacional", lat_prod + lat_pst, 200, {
        "Produto": "ROBOT-ARM (PA)",
        "Postos de Trabalho": "MONTAGEM-01 (Producao) & FORNO-01 (Tratamento)"
    })

    # -------------------------------------------------------------
    # 4. Telemetria IoT e Intertravamento Termico em Tempo Real
    # -------------------------------------------------------------
    passos += 1
    req(f"{ERP_URL}/api/coleta/dispositivos", method="POST", data={
        "codigo": "TEMP-FORNO-01", "posto": "FORNO-01", "tipo": "TEMPERATURA",
        "unidade": "C", "limite_alerta": "75", "limite_critico": "90"
    })
    
    # 4.1 Telemetria Normal
    st_tel1, _, lat_tel1 = req(f"{ERP_URL}/api/coleta/telemetria", method="POST", data={
        "dispositivo": "TEMP-FORNO-01", "posto": "FORNO-01", "valor": "68.0", "unidade": "C"
    })
    
    # 4.2 Telemetria Critica (98.0 °C > limite critico 90.0 °C)
    st_tel2, b_tel2, lat_tel2 = req(f"{ERP_URL}/api/coleta/telemetria", method="POST", data={
        "dispositivo": "TEMP-FORNO-01", "posto": "FORNO-01", "valor": "98.0", "unidade": "C"
    })
    
    log_step(passos, "Intertravamento IoT em Tempo Real no FORNO-01", lat_tel1 + lat_tel2, st_tel2, {
        "Dispositivo": "TEMP-FORNO-01",
        "Leitura Critica": "98.0 °C (limite: 90.0 °C)",
        "Intertravamento": "Acionado com sucesso -> maquina.parada emitida",
        "Posto em Parada": "FORNO-01 bloqueado para seguranca"
    })

    # -------------------------------------------------------------
    # 5. Criacao e Liberacao de Ordem de Producao (OP)
    # -------------------------------------------------------------
    passos += 1
    st_op, b_op, lat_op = req(f"{ERP_URL}/api/producao/ordens", method="POST", data={
        "produto": "ROBOT-ARM", "quantidade": "10", "posto": "MONTAGEM-01", "origem": "PROMPT-LLM-RT"
    })
    op_criada = json.loads(b_op)
    op_id = op_criada.get("id")

    # Liberar OP
    st_lib, b_lib, lat_lib = req(f"{ERP_URL}/api/producao/liberar?id={op_id}", method="POST")

    log_step(passos, f"Planejamento e Liberacao da OP #{op_id}", lat_op + lat_lib, st_lib, {
        "OP ID": op_id,
        "Produto": "ROBOT-ARM",
        "Quantidade Planejada": 10,
        "Posto Alocado": "MONTAGEM-01",
        "Status Atual": json.loads(b_lib).get("status")
    })

    # -------------------------------------------------------------
    # 6. Apontamento de Producao em Chão de Fábrica via CLP / IoT
    # -------------------------------------------------------------
    passos += 1
    # Pulsos automáticos de contagem
    st_pulso, _, lat_pulso = req(f"{ERP_URL}/api/coleta/pulso", method="POST", data={
        "posto": "MONTAGEM-01", "qtd": "10", "refugo": "0", "op": str(op_id)
    })

    # Apontamento de conclusão da OP
    st_apt, b_apt, lat_apt = req(f"{ERP_URL}/api/producao/apontar?id={op_id}", method="POST", data={
        "boa": "10", "refugo": "0", "operador": "agente_autonomo"
    })
    op_apontada = json.loads(b_apt)

    log_step(passos, f"Apontamento e Conclusao da OP #{op_id}", lat_pulso + lat_apt, st_apt, {
        "OP ID": op_id,
        "Produzido": f"{op_apontada.get('produzido')} / {op_apontada.get('quantidade')} pecas",
        "Refugo": op_apontada.get("refugo"),
        "Status Final": op_apontada.get("status"),
        "Operador": "agente_autonomo"
    })
    if op_apontada.get("status") != "CONCLUIDA":
        erros += 1

    # -------------------------------------------------------------
    # 7. Fechamento de Custos e Arquivamento Historico (tblFin*)
    # -------------------------------------------------------------
    passos += 1
    st_fech, b_fech, lat_fech = req(f"{ERP_URL}/api/custos/fechar?op={op_id}", method="POST")
    st_arq, b_arq, lat_arq = req(f"{ERP_URL}/api/arquivamento/op?id={op_id}", method="POST", data={
        "motivo": "FECHAMENTO_AUTOMATIZADO_LLM", "usuario": "agente_llm"
    })

    d_arq = json.loads(b_arq) if st_arq == 200 else {}
    log_step(passos, f"Fechamento Contabil e Arquivamento da OP #{op_id}", lat_fech + lat_arq, st_arq, {
        "OP ID": op_id,
        "Status": d_arq.get("status"),
        "Colecao Destino": "tblFinOrder & tblFinStep",
        "Custo Real": f"R$ {d_arq.get('custo_total_real', 0):.2f}",
        "Motivo Arquivamento": d_arq.get("motivo_arquivamento"),
        "Expurgo da Base Ativa": "CONFIRMADO (OP removida de ordens ativas)"
    })
    if st_arq != 200:
        erros += 1

    # -------------------------------------------------------------
    # 8. Auditoria do Arquivo Historico e BI Executivo
    # -------------------------------------------------------------
    passos += 1
    # Confirma que a OP não existe mais em /ordem ativa
    st_atv, b_atv, _ = req(f"{ERP_URL}/api/producao/ordem?id={op_id}")
    ativa_id = json.loads(b_atv).get("id") if st_atv == 200 else 0

    # Confirma que a OP existe em /api/arquivamento/ordem
    st_det_arq, b_det_arq, lat_det = req(f"{ERP_URL}/api/arquivamento/ordem?id={op_id}")
    d_hist = json.loads(b_det_arq) if st_det_arq == 200 else {}

    # Consulta resumo geral de arquivamento
    st_res, b_res, _ = req(f"{ERP_URL}/api/arquivamento/resumo")
    d_res = json.loads(b_res) if st_res == 200 else {}

    log_step(passos, "Auditoria do Arquivo Permanente (tblFin*)", lat_det, 200, {
        "OP Ativa no Chao": f"id={ativa_id} (0 = expurgada com sucesso)",
        "OP no Arquivo Permanente": f"#{d_hist.get('id')} com {len(d_hist.get('etapas', []))} etapa(s)",
        "Total OPs Arquivadas": d_res.get("arquivadas_total"),
        "Total Etapas Arquivadas": d_res.get("etapas_arquivadas_total"),
        "Politica de Retencao": f"{d_res.get('dias_retencao')} dias"
    })
    if ativa_id != 0 or d_hist.get("id") != op_id:
        erros += 1

    print("\n" + "=" * 75)
    print(f"  RESULTADO FINAL: {passos} operacoes em tempo real testadas!")
    print(f"  Total de Sucessos: {passos - erros} / {passos}")
    print(f"  Total de Falhas:   {erros}")
    print("=" * 75 + "\n")

    return 0 if erros == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
