#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para remover documentos duplicados da base do LightRAG
"""

import os
import json
import sys
import urllib.request
import urllib.parse
import datetime

# Configuração
LIGHTRAG_URL = "http://127.0.0.1:5000"
LIGHTRAG_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lightrag_db.json')

def get_documents_from_db():
    """Recupera documentos diretamente do arquivo de banco de dados"""
    try:
        if os.path.exists(LIGHTRAG_DB_FILE):
            with open(LIGHTRAG_DB_FILE, 'r', encoding='utf-8') as f:
                db = json.load(f)
                return db.get("documents", [])
        else:
            print(f"Arquivo de banco de dados não encontrado: {LIGHTRAG_DB_FILE}")
            return []
    except Exception as e:
        print(f"Erro ao ler banco de dados: {e}")
        return []

def save_documents_to_db(documents):
    """Salva documentos diretamente no arquivo de banco de dados"""
    try:
        # Criar backup
        if os.path.exists(LIGHTRAG_DB_FILE):
            backup_file = f"{LIGHTRAG_DB_FILE}.bak.{int(datetime.datetime.now().timestamp())}"
            with open(LIGHTRAG_DB_FILE, 'r', encoding='utf-8') as src, open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            print(f"Backup criado: {backup_file}")
        
        # Atualizar banco de dados
        db = {
            "documents": documents,
            "lastUpdated": datetime.datetime.now().isoformat()
        }
        
        with open(LIGHTRAG_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Erro ao salvar banco de dados: {e}")
        return False

def identify_duplicates(documents):
    """Identifica documentos duplicados por arquivo e conteúdo"""
    files_map = {}  # Mapa de nomes de arquivo para documentos
    file_ids = {}   # Mapa de IDs de documentos para nomes de arquivo
    duplicates = []  # Lista de IDs de documentos duplicados
    
    # Primeira passagem: mapear arquivos e IDs
    for doc in documents:
        doc_id = doc.get("id", "")
        content = doc.get("content", "")
        source = doc.get("source", "")
        
        # Extrair nome do arquivo do conteúdo ou source
        file_name = None
        if "Arquivo JSONL:" in content:
            parts = content.split("Arquivo JSONL:", 1)
            if len(parts) > 1:
                file_name = parts[1].strip().split("\n")[0]
        
        if not file_name and source:
            file_name = source
        
        if file_name:
            if file_name in files_map:
                # Arquivo já existe, marcar como duplicado (manter o mais antigo)
                duplicates.append(doc_id)
            else:
                files_map[file_name] = doc
                file_ids[doc_id] = file_name
    
    # Segunda passagem: verificar duplicatas por conteúdo
    unique_contents = {}
    for doc in documents:
        doc_id = doc.get("id", "")
        if doc_id in duplicates:
            continue  # Já marcado como duplicado
        
        content = doc.get("content", "")
        content_hash = hash(content)
        
        if content_hash in unique_contents:
            # Conteúdo já existe, marcar como duplicado
            duplicates.append(doc_id)
        else:
            unique_contents[content_hash] = doc_id
    
    return duplicates

def remove_duplicates():
    """Remove documentos duplicados da base"""
    # Obter documentos
    documents = get_documents_from_db()
    original_count = len(documents)
    
    if not documents:
        print("Nenhum documento encontrado na base.")
        return
    
    print(f"Documentos encontrados: {original_count}")
    
    # Identificar duplicatas
    duplicate_ids = identify_duplicates(documents)
    print(f"Documentos duplicados identificados: {len(duplicate_ids)}")
    
    if not duplicate_ids:
        print("Nenhuma duplicata encontrada.")
        return
    
    # Listar duplicatas
    print("\nDocumentos que serão removidos:")
    for i, doc_id in enumerate(duplicate_ids):
        # Encontrar o documento
        for doc in documents:
            if doc.get("id") == doc_id:
                print(f"{i+1}. ID: {doc_id}")
                print(f"   Source: {doc.get('source', 'desconhecido')}")
                print(f"   Criado: {doc.get('created', 'desconhecido')}")
                print()
                break
    
    # Confirmar remoção
    confirm = input("Confirma a remoção destes documentos? (s/N): ")
    if confirm.lower() not in ['s', 'sim', 'y', 'yes']:
        print("Operação cancelada.")
        return
    
    # Remover duplicatas
    documents_filtered = [doc for doc in documents if doc.get("id") not in duplicate_ids]
    
    # Salvar banco de dados atualizado
    if save_documents_to_db(documents_filtered):
        print(f"\n✅ Documentos duplicados removidos com sucesso!")
        print(f"Documentos antes: {original_count}")
        print(f"Documentos removidos: {len(duplicate_ids)}")
        print(f"Documentos restantes: {len(documents_filtered)}")
    else:
        print("❌ Falha ao salvar banco de dados atualizado.")

def main():
    print("=== Remoção de Documentos Duplicados do LightRAG ===\n")
    
    # Verificar se o servidor está em execução
    try:
        with urllib.request.urlopen(f"{LIGHTRAG_URL}/status") as response:
            if response.getcode() == 200:
                print("⚠️ O servidor LightRAG está em execução.")
                print("Recomenda-se parar o servidor antes de manipular o banco de dados diretamente.")
                confirm = input("Deseja continuar mesmo assim? (s/N): ")
                if confirm.lower() not in ['s', 'sim', 'y', 'yes']:
                    print("Operação cancelada.")
                    return
    except:
        # Se o servidor não estiver rodando, continuar normalmente
        pass
    
    # Executar remoção de duplicatas
    remove_duplicates()

if __name__ == "__main__":
    main()