#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para limpar nomes personalizados de documentos que não existem mais
"""

import json
import os
import argparse
import sys

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOM_NAMES_FILE = os.path.join(BASE_DIR, "custom_project_names.json")
DOCUMENTS_DB = os.path.join(BASE_DIR, "documents.db")
DB_JSON = os.path.join(BASE_DIR, "lightrag_db.json")

def load_custom_names():
    """Carrega os nomes personalizados do arquivo JSON"""
    if os.path.exists(CUSTOM_NAMES_FILE):
        try:
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar nomes personalizados: {e}")
            return {}
    return {}

def save_custom_names(custom_names):
    """Salva os nomes personalizados no arquivo JSON"""
    try:
        # Criar backup do arquivo antes de modificar
        if os.path.exists(CUSTOM_NAMES_FILE):
            backup_path = f"{CUSTOM_NAMES_FILE}.bak"
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dest:
                    dest.write(src.read())
        
        # Salvar os nomes atualizados
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_names, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar nomes personalizados: {e}")
        return False

def load_document_ids():
    """Carrega os IDs dos documentos existentes no banco de dados"""
    if os.path.exists(DB_JSON):
        try:
            with open(DB_JSON, 'r', encoding='utf-8') as f:
                db = json.load(f)
                documents = db.get("documents", [])
                return [doc.get("id") for doc in documents if "id" in doc]
        except Exception as e:
            print(f"Erro ao carregar banco de dados: {e}")
    return []

def clean_custom_names(dry_run=False):
    """Remove nomes personalizados para documentos que não existem mais"""
    custom_names = load_custom_names()
    
    if not custom_names:
        print("Nenhum nome personalizado encontrado.")
        return
    
    # Backup antes de qualquer modificação
    old_count = len(custom_names)
    print(f"Total de nomes personalizados encontrados: {old_count}")
    
    # Carregar IDs dos documentos existentes
    existing_ids = load_document_ids()
    print(f"Total de documentos no banco de dados: {len(existing_ids)}")
    
    # Identificar nomes a serem removidos
    to_remove = []
    for doc_id in custom_names:
        if doc_id not in existing_ids:
            to_remove.append(doc_id)
    
    if not to_remove:
        print("Nenhum nome personalizado para remover. Todos os documentos existem.")
        return
    
    # Exibir o que será removido
    print(f"\nDocumentos a serem removidos ({len(to_remove)}):")
    for doc_id in to_remove:
        print(f"  {doc_id}: {custom_names[doc_id]}")
    
    # Se for apenas simulação, parar aqui
    if dry_run:
        print("\nModo de simulação. Nenhuma alteração foi feita.")
        return
    
    # Confirmação do usuário
    confirm = input("\nDeseja realmente remover estes nomes personalizados? (s/N): ")
    if confirm.lower() != 's':
        print("Operação cancelada pelo usuário.")
        return
    
    # Remover os nomes
    for doc_id in to_remove:
        del custom_names[doc_id]
    
    # Salvar alterações
    if save_custom_names(custom_names):
        print(f"\nNomes personalizados removidos com sucesso: {len(to_remove)}")
        print(f"Total de nomes personalizados restantes: {len(custom_names)}")
    else:
        print("\nErro ao salvar alterações!")

def main():
    parser = argparse.ArgumentParser(description="Limpa nomes personalizados de documentos que não existem mais")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simula a operação, sem fazer alterações")
    
    args = parser.parse_args()
    clean_custom_names(args.dry_run)

if __name__ == "__main__":
    main()