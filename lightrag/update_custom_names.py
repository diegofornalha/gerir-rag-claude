#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Atualizador de Mapeamentos de Nomes
Script para atualizar o arquivo custom_project_names.json 
com mapeamentos consistentes entre UUIDs e nomes de conversas
"""

import os
import json
import argparse
import glob
from typing import Dict, List, Tuple

# Importar o gerador de IDs consistentes
from fixed_id_generator import extract_uuid_from_filename, generate_consistent_id

# Arquivo de mapeamento de nomes
CUSTOM_NAMES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "lightrag", "custom_project_names.json")

def find_conversation_files(projects_dir: str) -> List[str]:
    """
    Encontra todos os arquivos .jsonl de conversas no diretório de projetos
    
    Args:
        projects_dir: Diretório de projetos
        
    Retorna:
        List[str]: Lista de caminhos de arquivos .jsonl
    """
    # Verificar se o diretório existe
    if not os.path.exists(projects_dir) or not os.path.isdir(projects_dir):
        print(f"Diretório de projetos não encontrado: {projects_dir}")
        return []
    
    # Encontrar arquivos .jsonl recursivamente
    jsonl_files = glob.glob(os.path.join(projects_dir, "**/*.jsonl"), recursive=True)
    
    # Filtrar apenas arquivos que têm UUID no nome
    uuid_files = [f for f in jsonl_files if extract_uuid_from_filename(f)]
    
    return uuid_files

def generate_mappings(files: List[str]) -> Dict[str, str]:
    """
    Gera mapeamentos de IDs para nomes descritivos
    
    Args:
        files: Lista de caminhos de arquivos
        
    Retorna:
        Dict[str, str]: Mapeamento de IDs para nomes
    """
    mappings = {}
    
    for file_path in files:
        doc_id, display_name = generate_consistent_id(file_path)
        mappings[doc_id] = display_name
    
    return mappings

def update_custom_names_file(new_mappings: Dict[str, str], preserve_existing: bool = True) -> Tuple[int, int]:
    """
    Atualiza o arquivo de mapeamentos custom_project_names.json
    
    Args:
        new_mappings: Novos mapeamentos a serem adicionados
        preserve_existing: Se True, preserva mapeamentos existentes
        
    Retorna:
        Tuple[int, int]: (número de mapeamentos adicionados, número total de mapeamentos)
    """
    # Carregar mapeamentos existentes
    existing_mappings = {}
    if os.path.exists(CUSTOM_NAMES_FILE) and preserve_existing:
        try:
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                existing_mappings = json.load(f)
        except json.JSONDecodeError:
            print(f"Erro ao decodificar arquivo JSON existente. Criando novo arquivo.")
    
    # Fazer backup do arquivo original
    if os.path.exists(CUSTOM_NAMES_FILE):
        import shutil
        backup_file = f"{CUSTOM_NAMES_FILE}.bak"
        shutil.copy2(CUSTOM_NAMES_FILE, backup_file)
        print(f"Backup criado em: {backup_file}")
    
    # Contar novos mapeamentos
    new_count = 0
    
    # Mesclar mapeamentos
    for doc_id, display_name in new_mappings.items():
        if doc_id not in existing_mappings:
            existing_mappings[doc_id] = display_name
            new_count += 1
    
    # Salvar mapeamentos atualizados
    with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_mappings, f, indent=2, ensure_ascii=False)
    
    return new_count, len(existing_mappings)

def main():
    parser = argparse.ArgumentParser(description="Atualiza mapeamentos de IDs para nomes descritivos")
    parser.add_argument("--projects-dir", default=os.path.join(os.path.expanduser("~"), ".claude", "projects"),
                        help="Diretório de projetos contendo arquivos .jsonl")
    parser.add_argument("--no-preserve", action="store_true",
                        help="Não preservar mapeamentos existentes")
    args = parser.parse_args()
    
    # Encontrar arquivos de conversa
    print(f"Buscando arquivos de conversa em: {args.projects_dir}")
    conv_files = find_conversation_files(args.projects_dir)
    print(f"Encontrados {len(conv_files)} arquivos de conversa")
    
    # Gerar mapeamentos
    mappings = generate_mappings(conv_files)
    print(f"Gerados {len(mappings)} mapeamentos de IDs")
    
    # Atualizar arquivo de mapeamentos
    new_count, total_count = update_custom_names_file(mappings, preserve_existing=not args.no_preserve)
    print(f"Adicionados {new_count} novos mapeamentos. Total: {total_count}")
    print(f"Arquivo de mapeamentos atualizado: {CUSTOM_NAMES_FILE}")

if __name__ == "__main__":
    main()