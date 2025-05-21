#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Sistema de nomes baseado em arquivos
Este script implementa um sistema de mapeamento que vincula nomes personalizados
diretamente aos nomes de arquivos .jsonl em vez de IDs que podem mudar.
"""

import os
import re
import json
import glob
from typing import Dict, List, Optional, Tuple

# Arquivo de mapeamento de nomes
CUSTOM_NAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "file_custom_names.json")

# Padrão para extrair o UUID de nomes de arquivos .jsonl
UUID_PATTERN = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'

def extract_uuid_from_filename(filename: str) -> Optional[str]:
    """
    Extrai o UUID de um nome de arquivo .jsonl
    
    Args:
        filename: Nome do arquivo (com ou sem caminho)
        
    Retorna:
        Optional[str]: UUID extraído ou None se não encontrado
    """
    # Extrair apenas o nome do arquivo se um caminho completo for fornecido
    basename = os.path.basename(filename)
    
    # Buscar por padrão UUID no nome do arquivo
    match = re.search(UUID_PATTERN, basename)
    if match:
        return match.group(1)
    
    return None

def get_filename_key(filename: str) -> str:
    """
    Gera uma chave única baseada no nome do arquivo
    
    Args:
        filename: Nome do arquivo .jsonl
        
    Retorna:
        str: Chave única para o arquivo
    """
    uuid = extract_uuid_from_filename(filename)
    if uuid:
        return f"file_{uuid}.jsonl"
    
    # Se não encontrar UUID, usa o nome do arquivo completo
    return os.path.basename(filename)

def register_custom_name(filename: str, custom_name: str) -> bool:
    """
    Registra um nome personalizado para um arquivo .jsonl
    
    Args:
        filename: Nome do arquivo .jsonl (com ou sem caminho)
        custom_name: Nome personalizado a ser registrado
        
    Retorna:
        bool: True se registrado com sucesso, False caso contrário
    """
    try:
        # Gerar chave baseada no nome do arquivo
        file_key = get_filename_key(filename)
        
        # Carregar mapeamento existente
        mappings = {}
        if os.path.exists(CUSTOM_NAMES_FILE):
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
        
        # Fazer backup do arquivo original
        if os.path.exists(CUSTOM_NAMES_FILE):
            import shutil
            backup_file = f"{CUSTOM_NAMES_FILE}.bak"
            shutil.copy2(CUSTOM_NAMES_FILE, backup_file)
        
        # Adicionar novo mapeamento
        mappings[file_key] = custom_name
        
        # Salvar mapeamento atualizado
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        
        print(f"Nome personalizado registrado: {file_key} -> {custom_name}")
        return True
    except Exception as e:
        print(f"Erro ao registrar nome personalizado: {e}")
        return False

def get_custom_name(filename: str) -> Optional[str]:
    """
    Obtém o nome personalizado para um arquivo .jsonl
    
    Args:
        filename: Nome do arquivo .jsonl (com ou sem caminho)
        
    Retorna:
        Optional[str]: Nome personalizado ou None se não encontrado
    """
    try:
        # Gerar chave baseada no nome do arquivo
        file_key = get_filename_key(filename)
        
        # Carregar mapeamento
        if os.path.exists(CUSTOM_NAMES_FILE):
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
                return mappings.get(file_key)
        return None
    except Exception as e:
        print(f"Erro ao obter nome personalizado: {e}")
        return None

def migrate_from_old_mapping() -> bool:
    """
    Migra nomes personalizados do arquivo de mapeamento antigo para o novo
    
    Retorna:
        bool: True se migrado com sucesso, False caso contrário
    """
    try:
        old_mapping_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                     "custom_project_names.json")
        if not os.path.exists(old_mapping_file):
            print("Arquivo de mapeamento antigo não encontrado.")
            return False
        
        # Carregar mapeamento antigo
        with open(old_mapping_file, 'r', encoding='utf-8') as f:
            old_mappings = json.load(f)
        
        # Carregar mapeamento novo (ou criar novo)
        new_mappings = {}
        if os.path.exists(CUSTOM_NAMES_FILE):
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                new_mappings = json.load(f)
        
        # Buscar por todos os arquivos de conversa .jsonl
        project_dirs = [
            "/Users/agents/.claude/projects",
            "/Users/agents/.claude/projects/*"
        ]
        
        found_files = []
        for directory in project_dirs:
            found_files.extend(glob.glob(f"{directory}/**/*.jsonl", recursive=True))
        
        print(f"Encontrados {len(found_files)} arquivos .jsonl para processamento")
        
        # Para cada arquivo .jsonl, verificar se há um nome personalizado no mapeamento antigo
        for file_path in found_files:
            uuid = extract_uuid_from_filename(file_path)
            if not uuid:
                continue
                
            # Verificar o nome personalizado no mapeamento antigo
            custom_name = None
            for old_id, name in old_mappings.items():
                # Se for um ID baseado em UUID (novo formato)
                if old_id.startswith("conv_") and uuid in old_id:
                    custom_name = name
                    break
                    
                # Se o arquivo foi mencionado no nome ou resumo (formato antigo)
                if uuid in name:
                    custom_name = name
                    break
            
            # Se encontrou um nome personalizado, registrar no novo mapeamento
            if custom_name:
                file_key = get_filename_key(file_path)
                # Verificar se não é um nome genérico gerado pelo sistema
                if not custom_name.startswith("Conversa Claude:"):
                    new_mappings[file_key] = custom_name
                    print(f"Migrado: {file_key} -> {custom_name}")
        
        # Salvar novo mapeamento
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_mappings, f, indent=2, ensure_ascii=False)
        
        print(f"Migração concluída. {len(new_mappings)} nomes personalizados registrados.")
        return True
    except Exception as e:
        print(f"Erro durante a migração: {e}")
        return False

def scan_and_update_names() -> bool:
    """
    Escaneia diretórios de projetos e atualiza o mapeamento de nomes
    
    Retorna:
        bool: True se atualizado com sucesso, False caso contrário
    """
    try:
        # Carregar mapeamento atual
        current_mappings = {}
        if os.path.exists(CUSTOM_NAMES_FILE):
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                current_mappings = json.load(f)
        
        # Backup do arquivo original
        if os.path.exists(CUSTOM_NAMES_FILE):
            import shutil
            backup_file = f"{CUSTOM_NAMES_FILE}.bak"
            shutil.copy2(CUSTOM_NAMES_FILE, backup_file)
        
        # Buscar por todos os arquivos de conversa .jsonl
        project_dirs = [
            "/Users/agents/.claude/projects",
            "/Users/agents/.claude/projects/*"
        ]
        
        found_files = []
        for directory in project_dirs:
            found_files.extend(glob.glob(f"{directory}/**/*.jsonl", recursive=True))
        
        print(f"Encontrados {len(found_files)} arquivos .jsonl para processamento")
        
        # Verificar cada arquivo e atualizar se necessário
        for file_path in found_files:
            file_key = get_filename_key(file_path)
            
            # Se ainda não tiver um nome personalizado no mapeamento atual, adicionar um básico
            if file_key not in current_mappings:
                uuid = extract_uuid_from_filename(file_path)
                if uuid:
                    current_mappings[file_key] = f"Conversa Claude: {uuid}"
        
        # Salvar mapeamento atualizado
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_mappings, f, indent=2, ensure_ascii=False)
        
        print(f"Atualização concluída. {len(current_mappings)} nomes registrados.")
        return True
    except Exception as e:
        print(f"Erro durante a atualização: {e}")
        return False

def list_all_custom_names() -> Dict[str, str]:
    """
    Lista todos os nomes personalizados registrados
    
    Retorna:
        Dict[str, str]: Dicionário com arquivo -> nome personalizado
    """
    try:
        if os.path.exists(CUSTOM_NAMES_FILE):
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
                
            print("Nomes personalizados registrados:")
            for file_key, custom_name in mappings.items():
                print(f"{file_key} -> {custom_name}")
                
            return mappings
        else:
            print("Arquivo de mapeamento não encontrado.")
            return {}
    except Exception as e:
        print(f"Erro ao listar nomes personalizados: {e}")
        return {}

# Função para teste e uso em linha de comando
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: file_based_names.py <comando>")
        print("Comandos disponíveis:")
        print("  migrate - Migra nomes do mapeamento antigo para o novo")
        print("  scan - Escaneia diretórios e atualiza mapeamento")
        print("  list - Lista todos os nomes personalizados")
        print("  set <arquivo> <nome> - Define um nome personalizado para um arquivo")
        print("  get <arquivo> - Obtém o nome personalizado de um arquivo")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "migrate":
        migrate_from_old_mapping()
    
    elif command == "scan":
        scan_and_update_names()
    
    elif command == "list":
        list_all_custom_names()
    
    elif command == "set" and len(sys.argv) >= 4:
        filename = sys.argv[2]
        custom_name = sys.argv[3]
        register_custom_name(filename, custom_name)
    
    elif command == "get" and len(sys.argv) >= 3:
        filename = sys.argv[2]
        custom_name = get_custom_name(filename)
        if custom_name:
            print(f"Nome personalizado: {custom_name}")
        else:
            print(f"Nenhum nome personalizado encontrado para {filename}")
    
    else:
        print("Comando inválido ou parâmetros insuficientes.")
        sys.exit(1)