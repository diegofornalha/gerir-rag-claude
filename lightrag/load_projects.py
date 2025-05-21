#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para carregar automaticamente arquivos JSONL do diretório projects no LightRAG
Usa a API HTTP para interagir com o servidor LightRAG
"""

import os
import json
import urllib.request
import urllib.parse
import glob
import sys
import datetime
import re

# Configuração
LIGHTRAG_URL = "http://127.0.0.1:5000"
BASE_PROJECTS_DIR = "/Users/agents/.claude/projects"

# Função para encontrar todos os diretórios de projetos automaticamente
def find_project_dirs():
    """Encontra automaticamente todos os diretórios de projetos"""
    project_dirs = []
    
    # Verificar se o diretório base existe
    if not os.path.exists(BASE_PROJECTS_DIR):
        return project_dirs
    
    # Adicionar diretórios específicos que sabemos que existem
    known_dirs = [
        "/Users/agents/.claude/projects/-Users-agents--claude",
        "/Users/agents/.claude/projects/-Users-agents--claude-projects"
    ]
    
    for dir_path in known_dirs:
        if os.path.exists(dir_path):
            project_dirs.append(dir_path)
    
    # Procurar por outros diretórios potenciais
    try:
        # Listar todos os itens no diretório base
        for item in os.listdir(BASE_PROJECTS_DIR):
            full_path = os.path.join(BASE_PROJECTS_DIR, item)
            # Verificar se é um diretório e não está na lista de diretórios conhecidos
            if os.path.isdir(full_path) and full_path not in project_dirs:
                # Verificar se tem arquivos JSONL
                if glob.glob(f"{full_path}/*.jsonl"):
                    project_dirs.append(full_path)
    except Exception as e:
        print(f"Erro ao procurar diretórios de projetos: {e}")
    
    return project_dirs

def check_server():
    """Verifica se o servidor LightRAG está ativo"""
    try:
        with urllib.request.urlopen(f"{LIGHTRAG_URL}/status") as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"✅ LightRAG está rodando. Documentos: {data.get('documents', 0)}")
                return True
            else:
                print("❌ LightRAG respondeu com erro.")
                return False
    except Exception as e:
        print(f"❌ Erro ao conectar ao LightRAG: {e}")
        return False

def get_existing_documents():
    """Recupera os documentos já existentes na base"""
    try:
        # Fazer uma consulta vazia para obter todos os documentos
        data = json.dumps({"query": "*"}).encode('utf-8')
        req = urllib.request.Request(
            f"{LIGHTRAG_URL}/query",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            contexts = result.get('context', [])
            return [ctx.get('document_id') for ctx in contexts]
    except Exception as e:
        print(f"Erro ao recuperar documentos existentes: {e}")
        return []

def insert_document(text, summary, source="file_loader"):
    """Insere um documento no LightRAG"""
    data = {
        "text": text,
        "summary": summary,
        "source": source
    }
    
    try:
        encoded_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            f"{LIGHTRAG_URL}/insert",
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Erro ao inserir documento: {e}")
        return {"success": False, "error": str(e)}

def read_jsonl_summary(file_path):
    """Lê o início do arquivo JSONL para extrair um resumo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Ler a primeira linha para verificar se tem um objeto summary
            first_line = f.readline().strip()
            if first_line.startswith('{'):
                try:
                    data = json.loads(first_line)
                    if 'summary' in data:
                        return f"Arquivo JSONL: {os.path.basename(file_path)} - {data['summary']}"
                except:
                    pass
            
            # Se não encontrou um summary, usar o nome do arquivo como identificação
            return f"Arquivo JSONL: {os.path.basename(file_path)}"
    except Exception as e:
        return f"Arquivo JSONL: {os.path.basename(file_path)} (Erro ao ler: {str(e)})"

def extract_short_id(file_path):
    """Extrai um ID curto do nome do arquivo"""
    # Obter o nome do arquivo sem a extensão
    filename = os.path.basename(file_path).split('.')[0]
    
    # Usar o nome completo se for curto o suficiente
    if len(filename) <= 8:
        return filename
    
    # Caso contrário, extrair apenas o início do UUID
    return filename.split('-')[0] if '-' in filename else filename[:8]

def generate_file_description(file_path):
    """Gera uma descrição útil para o arquivo"""
    filename = os.path.basename(file_path)
    file_id = extract_short_id(file_path)
    
    # Verificar se temos uma descrição específica para este arquivo
    descriptions = {
        "afa4d560": "LightRAG Optimization - Melhorias e Otimização",
        "cb2ac1cc": "MCP Memory - Integração com Grafo de Conhecimento", 
        "b5e69835": "LightRAG Setup - Configuração e Limpeza do Projeto"
    }
    
    if file_id in descriptions:
        return descriptions[file_id]
    
    # Descrição genérica
    return f"Arquivo de histórico de conversação com Claude."

def main():
    """Função principal"""
    print("=== Carregador de Projetos Claude para LightRAG ===")
    
    # Verificar se o servidor está ativo
    if not check_server():
        print("Servidor LightRAG não está disponível. Execute ./start_lightrag.sh primeiro.")
        sys.exit(1)
    
    # Recuperar documentos existentes
    existing_docs = get_existing_documents()
    print(f"Documentos existentes: {len(existing_docs)}")
    
    # Descobrir diretórios de projetos
    project_dirs = find_project_dirs()
    print(f"Encontrados {len(project_dirs)} diretórios de projetos")
    
    # Lista para armazenar todos os arquivos JSONL encontrados
    all_jsonl_files = []
    
    # Verificar cada diretório de projetos
    for projects_dir in project_dirs:
        if os.path.exists(projects_dir):
            # Encontrar arquivos JSONL neste diretório
            jsonl_files = glob.glob(f"{projects_dir}/*.jsonl")
            
            # Procurar também em subdiretórios (um nível abaixo)
            for subdir in glob.glob(f"{projects_dir}/*/"):
                jsonl_files.extend(glob.glob(f"{subdir}/*.jsonl"))
            
            print(f"Diretório: {projects_dir}")
            print(f"  Arquivos JSONL encontrados: {len(jsonl_files)}")
            all_jsonl_files.extend(jsonl_files)
        else:
            print(f"Diretório não encontrado: {projects_dir}")
    
    # Verificar se algum arquivo foi encontrado
    if not all_jsonl_files:
        print("Nenhum arquivo JSONL encontrado em qualquer diretório de projetos.")
        sys.exit(0)
    
    print(f"Total de arquivos JSONL encontrados: {len(all_jsonl_files)}")
    
    # Processar cada arquivo
    new_count = 0
    for file_path in all_jsonl_files:
        file_id = extract_short_id(file_path)
        doc_id = f"doc_{file_id}"
        
        # Verificar se este documento já está indexado
        if doc_id in existing_docs:
            print(f"⏩ Pulando arquivo já indexado: {os.path.basename(file_path)}")
            continue
        
        # Ler informações do arquivo
        content = f"Arquivo JSONL: {os.path.basename(file_path)}"
        description = generate_file_description(file_path)
        
        # Inserir no LightRAG
        print(f"📄 Indexando: {os.path.basename(file_path)}... ", end="")
        result = insert_document(content, description, doc_id)
        
        if result.get("success", False):
            print("✅")
            new_count += 1
        else:
            print(f"❌ ({result.get('error')})")
    
    # Resumo
    print(f"\n=== Resumo da Indexação ===")
    print(f"✅ Arquivos processados: {len(all_jsonl_files)}")
    print(f"✅ Novos documentos adicionados: {new_count}")
    print(f"✅ Documentos ignorados: {len(all_jsonl_files) - new_count}")
    print(f"✅ Total de documentos na base: {len(existing_docs) + new_count}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário.")
        sys.exit(0)