#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para carregar automaticamente arquivos JSONL do diretório projects no LightRAG
"""

import os
import json
import requests
import glob
import sys
import datetime
import re

# Configuração
LIGHTRAG_URL = "http://127.0.0.1:5000"
PROJECTS_DIR = "/Users/agents/.claude/projects/-Users-agents--claude"
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lightrag_db.json')

def load_knowledge_base():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar base de conhecimento: {e}")
            return {"documents": [], "lastUpdated": datetime.datetime.now().isoformat()}
    return {"documents": [], "lastUpdated": datetime.datetime.now().isoformat()}

def save_knowledge_base(kb):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(kb, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar base de conhecimento: {e}")
        return False

def read_jsonl_summary(file_path):
    """Lê as primeiras linhas do arquivo JSONL para extrair um resumo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Ler as primeiras 5 linhas
            lines = []
            for i, line in enumerate(f):
                if i >= 5:
                    break
                try:
                    data = json.loads(line.strip())
                    # Extrair os primeiros 100 caracteres do texto da mensagem, se existir
                    if 'text' in data and isinstance(data['text'], str):
                        lines.append(data['text'][:100] + ('...' if len(data['text']) > 100 else ''))
                except:
                    continue
            
            if lines:
                return "\n".join(lines)
            return f"Arquivo JSONL: {os.path.basename(file_path)}"
    except Exception as e:
        return f"Arquivo JSONL: {os.path.basename(file_path)} (Erro ao ler: {str(e)})"

def extract_short_id(file_path):
    """Extrai um ID curto do nome do arquivo"""
    # Obter o nome do arquivo sem a extensão
    filename = os.path.basename(file_path).split('.')[0]
    
    # Extrair apenas a primeira parte do UUID (antes do primeiro hífen)
    if '-' in filename:
        short_id = filename.split('-')[0]
    else:
        # Se não tiver hífen, pegar os primeiros 8 caracteres
        short_id = filename[:8]
    
    return short_id

def main():
    # Verificar se o LightRAG está rodando
    try:
        response = requests.get(f"{LIGHTRAG_URL}/status", timeout=2)
        if response.status_code != 200:
            print("❌ LightRAG não está rodando. Inicie-o com ./compact start")
            return
    except Exception as e:
        print(f"❌ Erro ao conectar ao LightRAG: {e}")
        return
    
    # Carregar a base de conhecimento atual
    kb = load_knowledge_base()
    
    # Obter caminhos de arquivos já registrados
    existing_paths = [doc.get("path", "") for doc in kb["documents"]]
    
    # Encontrar todos os arquivos JSONL
    jsonl_files = glob.glob(f"{PROJECTS_DIR}/*.jsonl")
    
    if not jsonl_files:
        print(f"Nenhum arquivo JSONL encontrado em {PROJECTS_DIR}")
        return
    
    new_files = 0
    
    # Adicionar arquivos que ainda não estão na base
    for file_path in jsonl_files:
        if file_path not in existing_paths:
            # Extrair ID curto do nome do arquivo
            short_id = extract_short_id(file_path)
            doc_id = f"doc_{short_id}"
            
            # Ler conteúdo do arquivo para extrair um resumo
            summary = read_jsonl_summary(file_path)
            
            # Adicionar documento à base
            kb["documents"].append({
                "id": doc_id,
                "content": summary,
                "path": file_path,
                "created": datetime.datetime.now().isoformat()
            })
            new_files += 1
            print(f"✅ Adicionado: {file_path} (ID: {doc_id})")
    
    # Atualizar timestamp
    kb["lastUpdated"] = datetime.datetime.now().isoformat()
    
    # Salvar base de conhecimento
    if save_knowledge_base(kb):
        print(f"\n✅ Base de conhecimento atualizada com sucesso.")
        print(f"   Arquivos existentes: {len(existing_paths)}")
        print(f"   Novos arquivos: {new_files}")
        print(f"   Total: {len(kb['documents'])}")
    else:
        print("❌ Erro ao salvar base de conhecimento")

if __name__ == "__main__":
    main()