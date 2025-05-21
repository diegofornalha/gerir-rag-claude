#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Atualização de nomes personalizados
Este script atualiza o mapeamento de nomes personalizados para arquivos de conversa
"""

import os
import json
import sys
import glob
import re
from file_based_names import register_custom_name, migrate_from_old_mapping, scan_and_update_names

# Diretório onde os projetos são armazenados
PROJECTS_DIR = "/Users/agents/.claude/projects"

# Arquivo de mapeamento de nomes antigo
OLD_NAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           "custom_project_names.json")

# Arquivo de mapeamento de nomes novo
NEW_NAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           "file_custom_names.json")

def main():
    """Função principal do script de atualização de nomes"""
    
    print("=== Atualização de Nomes Personalizados ===")
    
    # Verificar se o mapeamento antigo existe
    if os.path.exists(OLD_NAMES_FILE):
        print("\nMapeamento antigo encontrado. Migrando nomes...")
        migrate_from_old_mapping()
    else:
        print("\nMapeamento antigo não encontrado. Ignorando migração.")
    
    # Escanear e atualizar mapeamentos
    print("\nEscaneando diretórios de conversas...")
    scan_and_update_names()
    
    # Exibir resultados
    print("\nMapeamento atual de nomes personalizados:")
    if os.path.exists(NEW_NAMES_FILE):
        with open(NEW_NAMES_FILE, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
            
        print(f"Total de {len(mappings)} nomes personalizados registrados:")
        for file_key, custom_name in mappings.items():
            if not custom_name.startswith("Conversa Claude:"):
                print(f" - {file_key}: {custom_name}")

    print("\nAtualização concluída com sucesso!")
    print("Use o comando 'python3 file_based_names.py set <arquivo> <nome>' para definir novos nomes personalizados.")

if __name__ == "__main__":
    main()