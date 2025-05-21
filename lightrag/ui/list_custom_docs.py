#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ferramenta CLI para listar documentos com nomes personalizados e suas informações
"""

import json
import os
import sys
import argparse
import re
from tabulate import tabulate
from datetime import datetime

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOM_NAMES_FILE = os.path.join(BASE_DIR, "custom_project_names.json")
DOCUMENTS_DB = os.path.join(BASE_DIR, "documents.db")

def load_custom_names():
    """Carrega os nomes personalizados do arquivo JSON"""
    if os.path.exists(CUSTOM_NAMES_FILE):
        try:
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar nomes personalizados: {e}")
    return {}

def format_date(date_str):
    """Formata a data para exibição mais amigável"""
    if not date_str:
        return ""
    
    try:
        # Formato esperado: 2025-05-21T00:49:41.607181
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return date_str

def list_documents(search=None, format="table"):
    """Lista documentos com nomes personalizados"""
    custom_names = load_custom_names()
    
    # Filtrar os nomes personalizados se houver termo de busca
    if search:
        search = search.lower()
        filtered_names = {}
        for doc_id, name in custom_names.items():
            if search in name.lower() or search in doc_id.lower():
                filtered_names[doc_id] = name
        custom_names = filtered_names
    
    # Preparar dados para exibição
    rows = []
    for doc_id, custom_name in custom_names.items():
        rows.append([
            doc_id,
            custom_name
        ])
    
    # Ordenar por nome personalizado
    rows.sort(key=lambda x: x[1].lower())
    
    # Exibir os resultados no formato escolhido
    if format == "json":
        result = []
        for row in rows:
            doc_id, name = row
            result.append({
                "id": doc_id,
                "name": name
            })
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif format == "csv":
        headers = ["ID", "Nome"]
        print(",".join(headers))
        for row in rows:
            # Escapar aspas em campos
            escaped_row = [f'"{field.replace('"', '""')}"' for field in row]
            print(",".join(escaped_row))
    else:  # table (padrão)
        headers = ["ID", "Nome Personalizado"]
            
        if rows:
            print(tabulate(rows, headers=headers, tablefmt="pretty"))
            print(f"\nTotal: {len(rows)} documento(s)")
        else:
            print("Nenhum documento com nome personalizado encontrado.")

def set_document_name(doc_id, custom_name):
    """Define um nome personalizado para um documento"""
    if not doc_id:
        print("ID do documento não fornecido")
        return False
        
    # Carregar nomes existentes
    custom_names = load_custom_names()
    
    # Backup do arquivo antes de modificar
    if os.path.exists(CUSTOM_NAMES_FILE):
        backup_path = f"{CUSTOM_NAMES_FILE}.bak"
        with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dest:
                dest.write(src.read())
    
    # Atualizar ou adicionar o nome personalizado
    custom_names[doc_id] = custom_name
    
    try:
        # Salvar os nomes atualizados
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_names, f, indent=2, ensure_ascii=False)
            
        print(f"Nome personalizado definido: {doc_id} = {custom_name}")
        return True
    except Exception as e:
        print(f"Erro ao salvar nome personalizado: {e}")
        return False

def remove_document_name(doc_id):
    """Remove um nome personalizado"""
    if not doc_id:
        print("ID do documento não fornecido")
        return False
        
    # Carregar nomes existentes
    custom_names = load_custom_names()
    
    # Verificar se o documento existe
    if doc_id not in custom_names:
        print(f"Documento {doc_id} não encontrado")
        return False
    
    # Backup do arquivo antes de modificar
    if os.path.exists(CUSTOM_NAMES_FILE):
        backup_path = f"{CUSTOM_NAMES_FILE}.bak"
        with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dest:
                dest.write(src.read())
    
    # Remover o nome personalizado
    del custom_names[doc_id]
    
    try:
        # Salvar os nomes atualizados
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_names, f, indent=2, ensure_ascii=False)
            
        print(f"Nome personalizado removido: {doc_id}")
        return True
    except Exception as e:
        print(f"Erro ao remover nome personalizado: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Gerenciar nomes personalizados para documentos no LightRAG")
    
    # Criar subcomandos
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")
    
    # Comando list
    list_parser = subparsers.add_parser("list", help="Listar documentos com nomes personalizados")
    list_parser.add_argument("-s", "--search", help="Filtrar por termo de busca")
    list_parser.add_argument("-f", "--format", choices=["table", "json", "csv"], 
                            default="table", help="Formato de saída (padrão: table)")
    
    # Comando set
    set_parser = subparsers.add_parser("set", help="Definir nome personalizado para um documento")
    set_parser.add_argument("doc_id", help="ID do documento")
    set_parser.add_argument("name", help="Nome personalizado")
    
    # Comando delete/remove
    rm_parser = subparsers.add_parser("delete", help="Remover nome personalizado de um documento")
    rm_parser.add_argument("doc_id", help="ID do documento")
    
    # Analisar argumentos
    args = parser.parse_args()
    
    # Executar comando
    if args.command == "list" or not args.command:
        list_documents(
            search=args.search if hasattr(args, 'search') else None, 
            format=args.format if hasattr(args, 'format') else "table"
        )
    elif args.command == "set":
        set_document_name(args.doc_id, args.name)
    elif args.command == "delete":
        remove_document_name(args.doc_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()