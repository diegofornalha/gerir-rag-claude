#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Sistema de Nomes por UUID
Sistema simples e direto que gerencia nomes personalizados usando apenas UUIDs.
"""

import os
import re
import json
import glob
from typing import Dict, List, Optional, Any

# Arquivo para armazenar nomes personalizados
UUID_NAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                             "uuid_names.json")

# Arquivo de mapeamento antigo
OLD_NAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            "custom_project_names.json")

# Padrão para extrair o UUID de nomes de arquivos ou IDs
UUID_PATTERN = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'

def extract_uuid(text: str) -> Optional[str]:
    """
    Extrai o UUID de qualquer texto (caminho de arquivo, ID, etc.)
    
    Args:
        text: Texto contendo um UUID
        
    Retorna:
        Optional[str]: UUID extraído ou None se não encontrado
    """
    match = re.search(UUID_PATTERN, text)
    return match.group(1) if match else None

def load_uuid_names() -> Dict[str, str]:
    """
    Carrega o mapeamento de UUIDs para nomes personalizados
    
    Retorna:
        Dict[str, str]: Mapeamento UUID -> nome personalizado
    """
    if os.path.exists(UUID_NAMES_FILE):
        try:
            with open(UUID_NAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar nomes de UUID: {e}")
    return {}

def save_uuid_names(uuid_names: Dict[str, str]) -> bool:
    """
    Salva o mapeamento de UUIDs para nomes personalizados
    
    Args:
        uuid_names: Mapeamento UUID -> nome personalizado
        
    Retorna:
        bool: True se salvo com sucesso, False caso contrário
    """
    try:
        # Criar backup se o arquivo existir
        if os.path.exists(UUID_NAMES_FILE):
            import shutil
            backup_file = f"{UUID_NAMES_FILE}.bak"
            shutil.copy2(UUID_NAMES_FILE, backup_file)
        
        # Salvar mapeamento
        with open(UUID_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(uuid_names, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Erro ao salvar nomes de UUID: {e}")
        return False

def set_name_for_uuid(uuid_or_filename: str, name: str) -> bool:
    """
    Define um nome personalizado para um UUID
    
    Args:
        uuid_or_filename: UUID ou nome de arquivo contendo UUID
        name: Nome personalizado
        
    Retorna:
        bool: True se definido com sucesso, False caso contrário
    """
    # Extrair UUID
    uuid = extract_uuid(uuid_or_filename)
    if not uuid:
        print(f"Erro: Não foi possível extrair UUID de '{uuid_or_filename}'")
        return False
    
    # Carregar mapeamento atual
    uuid_names = load_uuid_names()
    
    # Definir nome
    uuid_names[uuid] = name
    
    # Salvar mapeamento atualizado
    success = save_uuid_names(uuid_names)
    if success:
        print(f"Nome personalizado definido: UUID={uuid}, Nome='{name}'")
    
    return success

def get_name_for_uuid(uuid_or_filename: str, default_name: Optional[str] = None) -> Optional[str]:
    """
    Obtém o nome personalizado para um UUID
    
    Args:
        uuid_or_filename: UUID ou nome de arquivo contendo UUID
        default_name: Nome padrão para retornar se não encontrar um nome personalizado
        
    Retorna:
        Optional[str]: Nome personalizado ou default_name se não encontrado
    """
    # Extrair UUID
    uuid = extract_uuid(uuid_or_filename)
    if not uuid:
        return default_name
    
    # Carregar mapeamento
    uuid_names = load_uuid_names()
    
    # Retornar nome ou padrão
    return uuid_names.get(uuid, default_name)

def migrate_from_old_names() -> bool:
    """
    Migra nomes do formato antigo (ID -> nome) para o novo formato (UUID -> nome)
    
    Retorna:
        bool: True se migrado com sucesso, False caso contrário
    """
    try:
        # Verificar se o arquivo antigo existe
        if not os.path.exists(OLD_NAMES_FILE):
            print("Arquivo de nomes antigo não encontrado.")
            return False
        
        # Carregar mapeamento antigo
        with open(OLD_NAMES_FILE, 'r', encoding='utf-8') as f:
            old_names = json.load(f)
        
        # Carregar mapeamento novo (ou criar vazio)
        uuid_names = load_uuid_names()
        
        # Processar cada entrada antiga
        migrations = 0
        for old_id, name in old_names.items():
            # Ignorar nomes genéricos
            if "Conversa Claude:" in name:
                continue
                
            # Extrair UUID do ID
            uuid = extract_uuid(old_id)
            if uuid:
                # Adicionar ao novo mapeamento
                uuid_names[uuid] = name
                migrations += 1
                print(f"Migrado: UUID={uuid}, Nome='{name}'")
        
        # Salvar mapeamento atualizado
        success = save_uuid_names(uuid_names)
        if success:
            print(f"Migração concluída. {migrations} nomes migrados.")
        
        return success
    except Exception as e:
        print(f"Erro durante a migração: {e}")
        return False

def scan_for_uuids() -> Dict[str, str]:
    """
    Escaneia todos os arquivos de conversa para extrair seus UUIDs
    
    Retorna:
        Dict[str, str]: Mapeamento UUID -> nome de arquivo
    """
    try:
        # Locais para buscar arquivos de conversa
        project_dirs = [
            "/Users/agents/.claude/projects",
            "/Users/agents/.claude/projects/*"
        ]
        
        found_uuids = {}
        
        # Buscar todos os arquivos .jsonl
        for directory in project_dirs:
            for file_path in glob.glob(f"{directory}/**/*.jsonl", recursive=True):
                # Extrair UUID do nome do arquivo
                uuid = extract_uuid(file_path)
                if uuid:
                    found_uuids[uuid] = os.path.basename(file_path)
        
        return found_uuids
    except Exception as e:
        print(f"Erro ao escanear UUIDs: {e}")
        return {}

def update_all_names() -> bool:
    """
    Atualiza o sistema de nomes com todos os UUIDs encontrados
    
    Retorna:
        bool: True se atualizado com sucesso, False caso contrário
    """
    try:
        # Escanear UUIDs
        found_uuids = scan_for_uuids()
        print(f"Encontrados {len(found_uuids)} arquivos com UUID.")
        
        # Carregar mapeamento atual
        uuid_names = load_uuid_names()
        
        # Adicionar UUIDs não mapeados com nome padrão
        for uuid, filename in found_uuids.items():
            if uuid not in uuid_names:
                uuid_names[uuid] = f"Conversa: {filename}"
        
        # Salvar mapeamento atualizado
        success = save_uuid_names(uuid_names)
        if success:
            print(f"Atualização concluída. {len(uuid_names)} UUIDs mapeados.")
        
        return success
    except Exception as e:
        print(f"Erro durante a atualização: {e}")
        return False

def list_all_names() -> Dict[str, str]:
    """
    Lista todos os nomes personalizados
    
    Retorna:
        Dict[str, str]: Mapeamento UUID -> nome personalizado
    """
    uuid_names = load_uuid_names()
    
    print(f"Total de {len(uuid_names)} nomes personalizados:")
    for uuid, name in uuid_names.items():
        # Só mostrar se não for nome genérico
        if not name.startswith("Conversa:"):
            print(f"UUID: {uuid} -> Nome: '{name}'")
    
    return uuid_names

def get_display_name(doc_id_or_filename: str) -> str:
    """
    Obtém um nome de exibição para um documento ou arquivo,
    usando o sistema de nomes por UUID
    
    Args:
        doc_id_or_filename: ID do documento ou caminho do arquivo
        
    Retorna:
        str: Nome personalizado ou nome genérico se não encontrado
    """
    # Extrair UUID
    uuid = extract_uuid(doc_id_or_filename)
    if not uuid:
        # Se não conseguir extrair UUID, retornar o texto original
        return os.path.basename(doc_id_or_filename)
    
    # Carregar nomes
    uuid_names = load_uuid_names()
    
    # Verificar se tem nome personalizado
    if uuid in uuid_names:
        return uuid_names[uuid]
    
    # Retornar nome genérico baseado no UUID
    filename = os.path.basename(doc_id_or_filename)
    return f"Conversa: {filename}"


# Função principal para uso em linha de comando
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: uuid_names.py <comando>")
        print("Comandos disponíveis:")
        print("  migrate - Migra nomes do formato antigo para o novo")
        print("  update - Atualiza o sistema com todos os UUIDs encontrados")
        print("  list - Lista todos os nomes personalizados")
        print("  set <uuid-ou-arquivo> <nome> - Define um nome personalizado")
        print("  get <uuid-ou-arquivo> - Obtém o nome personalizado")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "migrate":
        migrate_from_old_names()
    
    elif command == "update":
        update_all_names()
    
    elif command == "list":
        list_all_names()
    
    elif command == "set" and len(sys.argv) >= 4:
        uuid_or_file = sys.argv[2]
        name = sys.argv[3]
        set_name_for_uuid(uuid_or_file, name)
    
    elif command == "get" and len(sys.argv) >= 3:
        uuid_or_file = sys.argv[2]
        name = get_name_for_uuid(uuid_or_file)
        if name:
            print(f"Nome personalizado: {name}")
        else:
            print(f"Nenhum nome personalizado encontrado para {uuid_or_file}")
    
    else:
        print("Comando inválido ou parâmetros insuficientes.")
        sys.exit(1)