#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Gerador de IDs consistentes
Módulo para gerar IDs consistentes baseados em UUIDs dos arquivos de conversa
"""

import os
import re
import json
from typing import Dict, Optional, Tuple

# Padrão para extrair o UUID de nomes de arquivos .jsonl
UUID_PATTERN = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'

# Arquivo de mapeamento de nomes
CUSTOM_NAMES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "lightrag", "custom_project_names.json")

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

def generate_consistent_id(filename: str) -> Tuple[str, str]:
    """
    Gera um ID consistente baseado no UUID do arquivo .jsonl
    
    Args:
        filename: Nome do arquivo .jsonl
        
    Retorna:
        Tuple[str, str]: ID gerado e o nome descritivo do documento
    """
    uuid = extract_uuid_from_filename(filename)
    
    if not uuid:
        # Fallback para timestamp se não encontrar UUID
        import datetime
        return f"doc_{int(datetime.datetime.now().timestamp() * 1000)}", filename
    
    # Gerar ID com prefixo conv_ para indicar que é uma conversa
    conv_id = f"conv_{uuid}"
    
    # Gerar nome descritivo
    display_name = f"Conversa Claude: {uuid}.jsonl"
    
    return conv_id, display_name

def register_document_name(doc_id: str, display_name: str) -> bool:
    """
    Registra o mapeamento entre ID do documento e seu nome descritivo
    
    Args:
        doc_id: ID do documento
        display_name: Nome descritivo
        
    Retorna:
        bool: True se registrado com sucesso, False caso contrário
    """
    try:
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
        mappings[doc_id] = display_name
        
        # Salvar mapeamento atualizado
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Erro ao registrar nome do documento: {e}")
        return False

def get_document_name(doc_id: str) -> Optional[str]:
    """
    Obtém o nome descritivo de um documento pelo seu ID
    
    Args:
        doc_id: ID do documento
        
    Retorna:
        Optional[str]: Nome descritivo ou None se não encontrado
    """
    try:
        if os.path.exists(CUSTOM_NAMES_FILE):
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
                return mappings.get(doc_id)
        return None
    except Exception as e:
        print(f"Erro ao obter nome do documento: {e}")
        return None

def is_conversation_id(doc_id: str) -> bool:
    """
    Verifica se um ID é do formato de conversa (conv_UUID)
    
    Args:
        doc_id: ID a verificar
        
    Retorna:
        bool: True se for ID de conversa, False caso contrário
    """
    return doc_id.startswith("conv_") and re.search(UUID_PATTERN, doc_id[5:]) is not None

# Função para teste
if __name__ == "__main__":
    test_filename = "8b225707-6263-4081-bc38-df505a930293.jsonl"
    uuid = extract_uuid_from_filename(test_filename)
    print(f"UUID extraído: {uuid}")
    
    doc_id, display_name = generate_consistent_id(test_filename)
    print(f"ID gerado: {doc_id}")
    print(f"Nome descritivo: {display_name}")
    
    success = register_document_name(doc_id, display_name)
    print(f"Registro: {'Sucesso' if success else 'Falha'}")