#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Migrar para sistema de nomes por UUID
Script para migrar todos os nomes personalizados para o novo sistema baseado em UUID
"""

import os
import json
import re
import glob
from typing import Dict, Any

from uuid_names import extract_uuid, set_name_for_uuid, update_all_names

# Diretório base do LightRAG
LIGHTRAG_DIR = os.path.dirname(os.path.abspath(__file__))

# Arquivos de mapeamento de nomes
CUSTOM_NAMES_FILE = os.path.join(LIGHTRAG_DIR, "custom_project_names.json")
FILE_NAMES_FILE = os.path.join(LIGHTRAG_DIR, "file_custom_names.json")
UUID_NAMES_FILE = os.path.join(LIGHTRAG_DIR, "uuid_names.json")

# Arquivo da base de conhecimento
DB_FILE = os.path.join(LIGHTRAG_DIR, "lightrag_db.json")

def load_knowledge_base() -> Dict[str, Any]:
    """
    Carrega a base de conhecimento
    
    Retorna:
        Dict[str, Any]: Base de conhecimento
    """
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar base de conhecimento: {e}")
    return {"documents": []}

def migrate_from_db() -> bool:
    """
    Migra nomes de documentos a partir da base de conhecimento
    
    Retorna:
        bool: True se migrado com sucesso, False caso contrário
    """
    try:
        # Carregar base de conhecimento
        kb = load_knowledge_base()
        documents = kb.get("documents", [])
        
        print(f"Analisando {len(documents)} documentos na base de conhecimento...")
        
        # Mapear UUIDs a partir do conteúdo e fonte
        for doc in documents:
            doc_id = doc.get("id", "")
            source = doc.get("source", "")
            summary = doc.get("summary", "")
            content = doc.get("content", "")
            
            # Tentar extrair UUID do ID
            uuid = extract_uuid(doc_id)
            
            # Se não encontrar no ID, tentar na fonte
            if not uuid:
                uuid = extract_uuid(source)
            
            # Se ainda não encontrar, tentar no resumo
            if not uuid:
                uuid = extract_uuid(summary)
            
            # Se ainda não encontrar, tentar no conteúdo
            if not uuid and content:
                uuid = extract_uuid(content)
            
            # Se encontrou UUID e tem resumo significativo, usar como nome
            if uuid and summary and not summary.startswith("Conversa Claude:"):
                set_name_for_uuid(uuid, summary)
        
        print("Migração a partir da base de conhecimento concluída.")
        return True
    except Exception as e:
        print(f"Erro durante a migração a partir da base: {e}")
        return False

def migrate_from_old_names() -> bool:
    """
    Migra nomes do arquivo de nomes personalizado antigo
    
    Retorna:
        bool: True se migrado com sucesso, False caso contrário
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(CUSTOM_NAMES_FILE):
            print("Arquivo de nomes personalizado antigo não encontrado.")
            return False
        
        # Carregar nomes
        with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
            old_names = json.load(f)
        
        print(f"Migrando {len(old_names)} nomes do arquivo antigo...")
        
        # Processar cada nome
        for doc_id, name in old_names.items():
            if name.startswith("Conversa Claude:"):
                continue
            
            # Extrair UUID
            uuid = extract_uuid(doc_id)
            if uuid:
                set_name_for_uuid(uuid, name)
        
        print("Migração a partir do arquivo de nomes antigo concluída.")
        return True
    except Exception as e:
        print(f"Erro durante a migração de nomes antigos: {e}")
        return False

def migrate_from_file_names() -> bool:
    """
    Migra nomes do arquivo de nomes baseado em arquivos
    
    Retorna:
        bool: True se migrado com sucesso, False caso contrário
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(FILE_NAMES_FILE):
            print("Arquivo de nomes baseado em arquivos não encontrado.")
            return False
        
        # Carregar nomes
        with open(FILE_NAMES_FILE, 'r', encoding='utf-8') as f:
            file_names = json.load(f)
        
        print(f"Migrando {len(file_names)} nomes do arquivo baseado em arquivos...")
        
        # Processar cada nome
        for file_key, name in file_names.items():
            if name.startswith("Conversa Claude:"):
                continue
            
            # Extrair UUID
            uuid = extract_uuid(file_key)
            if uuid:
                set_name_for_uuid(uuid, name)
        
        print("Migração a partir do arquivo de nomes baseado em arquivos concluída.")
        return True
    except Exception as e:
        print(f"Erro durante a migração de nomes baseados em arquivos: {e}")
        return False

def main() -> None:
    """Função principal para executar todas as migrações"""
    print("=" * 60)
    print("MIGRAÇÃO PARA SISTEMA DE NOMES POR UUID")
    print("=" * 60)
    print()
    
    # Escanear todos os UUIDs para garantir que todos sejam incluídos
    print("Atualizando sistema com todos os UUIDs encontrados...")
    update_all_names()
    print()
    
    # Migrar a partir da base de conhecimento
    print("Migrando nomes a partir da base de conhecimento...")
    migrate_from_db()
    print()
    
    # Migrar a partir do arquivo de nomes antigo
    print("Migrando nomes a partir do arquivo de nomes antigo...")
    migrate_from_old_names()
    print()
    
    # Migrar a partir do arquivo de nomes baseado em arquivos
    print("Migrando nomes a partir do arquivo de nomes baseado em arquivos...")
    migrate_from_file_names()
    print()
    
    print("=" * 60)
    print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    print("Todos os nomes personalizados foram migrados para o novo sistema.")
    print("O arquivo de mapeamento está em:")
    print(f"  {UUID_NAMES_FILE}")
    print()
    print("Para gerenciar nomes, use o comando:")
    print("  python3 uuid_names.py <comando>")
    print()

if __name__ == "__main__":
    main()