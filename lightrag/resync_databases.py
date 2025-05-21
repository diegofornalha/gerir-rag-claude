#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para resincronizar bancos de dados LightRAG e SQLite
Este script força uma limpeza completa e reconstrução da sincronização
"""

import os
import sys
import json
import urllib.request
import sqlite3
import time
import glob
import subprocess
from datetime import datetime

# Configuração
LIGHTRAG_URL = "http://127.0.0.1:5000"
BASE_PROJECTS_DIR = "/Users/agents/.claude/projects"
LOG_FILE = "/Users/agents/.claude/lightrag/logs/resync.log"
DB_FILE = "/Users/agents/.claude/lightrag/documents.db"
LIGHTRAG_DB = "/Users/agents/.claude/lightrag/lightrag_db.json"
SYNC_FILE = "/Users/agents/.claude/lightrag/.sync_timestamp"

def log(message):
    """Registra mensagem no console e no arquivo de log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} - {message}"
    print(log_line)
    
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_line + "\n")

def stop_services():
    """Para todos os serviços relacionados"""
    log("Parando serviços em execução...")
    
    # Parar monitor aprimorado
    try:
        subprocess.run("pkill -f 'python.*improved_monitor.py'", shell=True)
        log("Monitor aprimorado interrompido")
    except Exception as e:
        log(f"Erro ao parar monitor: {e}")
    
    time.sleep(2)

def find_jsonl_files():
    """Encontra todos os arquivos JSONL nos diretórios de projetos"""
    log("Procurando arquivos JSONL...")
    
    all_files = []
    for root, _, _ in os.walk(BASE_PROJECTS_DIR):
        jsonl_files = glob.glob(os.path.join(root, "*.jsonl"))
        all_files.extend(jsonl_files)
    
    log(f"Encontrados {len(all_files)} arquivos JSONL")
    return all_files

def clear_databases():
    """Limpa todos os bancos de dados"""
    log("Limpando bancos de dados...")
    
    # Limpar banco de dados SQLite
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            log(f"Banco de dados SQLite removido: {DB_FILE}")
        except Exception as e:
            log(f"Erro ao remover SQLite: {e}")
    
    # Limpar LightRAG via API
    try:
        data = {"confirm": True}
        encoded_data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(
            f"{LIGHTRAG_URL}/clear",
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        if result.get("success", False):
            log(f"LightRAG limpo: {result.get('message', '')}")
        else:
            log(f"Erro ao limpar LightRAG: {result.get('error', 'Erro desconhecido')}")
    except Exception as e:
        log(f"Erro ao limpar LightRAG: {e}")
    
    # Criar banco LightRAG limpo
    try:
        with open(LIGHTRAG_DB, 'w') as f:
            json.dump({"documents": [], "lastUpdated": datetime.now().isoformat()}, f)
        log(f"Banco de dados LightRAG limpo recriado: {LIGHTRAG_DB}")
    except Exception as e:
        log(f"Erro ao criar banco limpo: {e}")
    
    # Atualizar timestamp
    try:
        with open(SYNC_FILE, 'w') as f:
            f.write(str(time.time()))
        log("Timestamp de sincronização atualizado")
    except Exception as e:
        log(f"Erro ao atualizar timestamp: {e}")

def restart_services():
    """Reinicia todos os serviços"""
    log("Reiniciando serviços...")
    
    try:
        # Iniciar monitor aprimorado
        lightrag_dir = os.path.dirname(DB_FILE)
        subprocess.Popen(
            f"cd {lightrag_dir} && ./start_improved_monitor.sh",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        log("Monitor aprimorado reiniciado")
        
        # Aguardar inicialização
        time.sleep(5)
        
        # Iniciar interface web
        subprocess.Popen(
            f"cd {lightrag_dir} && ./start_ui.sh",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        log("Interface web reiniciada")
        
    except Exception as e:
        log(f"Erro ao reiniciar serviços: {e}")

def verify_sync():
    """Verifica se a sincronização está correta"""
    log("Verificando sincronização...")
    
    time.sleep(10)  # Aguardar indexação
    
    try:
        # Verificar documentos no LightRAG
        with urllib.request.urlopen(f"{LIGHTRAG_URL}/status") as response:
            result = json.loads(response.read().decode('utf-8'))
            lightrag_count = result.get('documents', 0)
        
        # Verificar documentos no SQLite
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        sqlite_count = cursor.fetchone()[0]
        conn.close()
        
        # Verificar arquivos JSONL
        jsonl_files = find_jsonl_files()
        
        log(f"Relatório de sincronização:")
        log(f"- Arquivos JSONL: {len(jsonl_files)}")
        log(f"- Documentos SQLite: {sqlite_count}")
        log(f"- Documentos LightRAG: {lightrag_count}")
        
        if len(jsonl_files) == sqlite_count and sqlite_count <= lightrag_count:
            log("✅ Sincronização concluída com sucesso!")
            return True
        else:
            log("⚠️ Sincronização concluída com discrepâncias!")
            return False
    
    except Exception as e:
        log(f"Erro ao verificar sincronização: {e}")
        return False

def main():
    """Função principal"""
    log("=== INÍCIO DA RESINCRONIZAÇÃO ===")
    
    # Parar serviços
    stop_services()
    
    # Encontrar arquivos JSONL (para referência)
    jsonl_files = find_jsonl_files()
    
    # Limpar bancos de dados
    clear_databases()
    
    # Reiniciar serviços
    restart_services()
    
    # Verificar sincronização
    success = verify_sync()
    
    log(f"=== RESINCRONIZAÇÃO {'CONCLUÍDA' if success else 'FALHOU'} ===")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())