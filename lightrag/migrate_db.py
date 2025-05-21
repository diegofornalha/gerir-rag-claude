#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Script de Migração de Banco de Dados
Este script migra o banco de dados legado para o novo formato,
garantindo compatibilidade com a nova arquitetura.
"""

import json
import os
import sys
import hashlib
import datetime
import shutil
import argparse

# Obter diretório atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'lightrag_db.json')

def create_backup(db_file):
    """Cria um backup do arquivo de banco de dados"""
    backup_file = f"{db_file}.bak.{int(datetime.datetime.now().timestamp())}"
    try:
        shutil.copy2(db_file, backup_file)
        print(f"✓ Backup criado: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"✗ Erro ao criar backup: {str(e)}")
        return None

def load_database(db_file):
    """Carrega o banco de dados do arquivo"""
    if not os.path.exists(db_file):
        print(f"✗ Arquivo não encontrado: {db_file}")
        return None
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Base carregada: {len(data.get('documents', []))} documentos")
        return data
    except Exception as e:
        print(f"✗ Erro ao carregar banco de dados: {str(e)}")
        return None

def save_database(db_file, data):
    """Salva o banco de dados no arquivo"""
    try:
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ Base salva com sucesso")
        return True
    except Exception as e:
        print(f"✗ Erro ao salvar banco de dados: {str(e)}")
        return False

def enrich_document(doc):
    """Enriquece um documento com metadados adicionais"""
    # Verificar se já tem metadados
    if "metadata" not in doc:
        doc["metadata"] = {}
    
    # Adicionar hash de conteúdo se não existir
    if "content_hash" not in doc["metadata"] and "content" in doc:
        content_hash = hashlib.sha256(doc["content"].encode('utf-8')).hexdigest()
        doc["metadata"]["content_hash"] = content_hash
    
    # Adicionar timestamp de criação se não existir
    if "created" not in doc:
        doc["created"] = datetime.datetime.now().isoformat()
    
    # Adicionar resumo se não existir
    if "summary" not in doc and "content" in doc:
        # Criar um resumo básico a partir do conteúdo
        content = doc["content"]
        if len(content) > 50:
            summary = content[:47] + "..."
        else:
            summary = content
        doc["summary"] = summary
    
    return doc

def validate_document(doc):
    """Valida se um documento tem os campos necessários"""
    required_fields = ["id", "content"]
    for field in required_fields:
        if field not in doc:
            return False
    return True

def migrate_database(data):
    """Migra a estrutura do banco de dados para o novo formato"""
    # Verificar se é o formato antigo ou novo
    if "documents" not in data:
        print("✗ Formato de dados desconhecido")
        return None
    
    # Processar cada documento
    migrated_docs = []
    for doc in data["documents"]:
        if validate_document(doc):
            # Enriquecer documento com metadados adicionais
            enriched_doc = enrich_document(doc)
            migrated_docs.append(enriched_doc)
        else:
            print(f"⚠️ Documento inválido ignorado: {doc.get('id', 'sem ID')}")
    
    # Atualizar o banco de dados
    data["documents"] = migrated_docs
    data["lastUpdated"] = datetime.datetime.now().isoformat()
    data["migrated"] = True
    data["migrationDate"] = datetime.datetime.now().isoformat()
    
    return data

def deduplicate_documents(data):
    """Remove documentos duplicados com base no hash de conteúdo"""
    if "documents" not in data:
        return data
    
    unique_docs = {}
    duplicates = []
    
    # Identificar documentos por hash
    for doc in data["documents"]:
        # Obter hash do documento
        content_hash = None
        if "metadata" in doc and "content_hash" in doc["metadata"]:
            content_hash = doc["metadata"]["content_hash"]
        elif "content" in doc:
            content_hash = hashlib.sha256(doc["content"].encode('utf-8')).hexdigest()
        
        if content_hash:
            if content_hash not in unique_docs:
                unique_docs[content_hash] = doc
            else:
                duplicates.append(doc)
    
    # Atualizar lista de documentos
    data["documents"] = list(unique_docs.values())
    
    if duplicates:
        print(f"✓ Removidos {len(duplicates)} documentos duplicados")
    
    return data

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Migrador de banco de dados LightRAG')
    parser.add_argument('--db', help='Caminho para o arquivo de banco de dados')
    parser.add_argument('--deduplicate', action='store_true', help='Remover documentos duplicados')
    args = parser.parse_args()
    
    # Verificar caminho do banco de dados
    db_file = args.db if args.db else DB_FILE
    
    print(f"=== LightRAG - Migração de Banco de Dados ===")
    print(f"Arquivo: {db_file}")
    
    # Criar backup antes de qualquer alteração
    backup_file = create_backup(db_file)
    if not backup_file:
        print("✗ Abortando migração devido a falha no backup")
        sys.exit(1)
    
    # Carregar banco de dados
    data = load_database(db_file)
    if not data:
        print("✗ Abortando migração devido a falha na leitura do banco de dados")
        sys.exit(1)
    
    # Migrar banco de dados
    print("Migrando banco de dados...")
    migrated_data = migrate_database(data)
    if not migrated_data:
        print("✗ Abortando migração devido a falha na migração")
        sys.exit(1)
    
    # Deduplicar documentos se solicitado
    if args.deduplicate:
        print("Removendo documentos duplicados...")
        migrated_data = deduplicate_documents(migrated_data)
    
    # Salvar banco de dados migrado
    if save_database(db_file, migrated_data):
        print(f"✓ Migração concluída com sucesso")
        print(f"  - Documentos: {len(migrated_data.get('documents', []))}")
        print(f"  - Backup: {backup_file}")
    else:
        print("✗ Falha ao salvar banco de dados migrado")
        print(f"  Você pode restaurar a partir do backup: {backup_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()