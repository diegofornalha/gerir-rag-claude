#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Módulo de exibição de nomes para UI
Este módulo fornece funções para substituir IDs por nomes personalizados
em toda a interface do LightRAG.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, Union

# Tenta importar o sistema novo de nomes baseado em arquivos
try:
    from file_based_names import get_custom_name, get_filename_key
    USING_FILE_BASED = True
except ImportError:
    USING_FILE_BASED = False

# Arquivos de mapeamento de nomes
CUSTOM_NAMES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "custom_project_names.json")
FILE_NAMES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              "file_custom_names.json")

# Padrão para extrair o UUID de nomes de arquivos .jsonl
UUID_PATTERN = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'

def load_custom_names() -> Dict[str, str]:
    """
    Carrega os nomes personalizados de ambos os sistemas (antigo e novo)
    
    Retorna:
        Dict[str, str]: Mapeamento de IDs para nomes personalizados
    """
    mappings = {}
    
    # Carregar mapeamento antigo (IDs para nomes)
    if os.path.exists(CUSTOM_NAMES_FILE):
        try:
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                mappings.update(json.load(f))
        except Exception as e:
            print(f"Erro ao carregar nomes personalizados antigos: {e}")
    
    # Carregar mapeamento novo (arquivos para nomes)
    if os.path.exists(FILE_NAMES_FILE):
        try:
            with open(FILE_NAMES_FILE, 'r', encoding='utf-8') as f:
                file_mappings = json.load(f)
                
                # Converter chaves de arquivo para potenciais IDs
                for file_key, name in file_mappings.items():
                    # Extrair UUID do arquivo
                    match = re.search(UUID_PATTERN, file_key)
                    if match:
                        uuid = match.group(1)
                        # Adicionar mapeamento para potenciais IDs (ambos formatos)
                        mappings[f"doc_{uuid}"] = name
                        mappings[f"conv_{uuid}"] = name
        except Exception as e:
            print(f"Erro ao carregar nomes personalizados baseados em arquivo: {e}")
    
    return mappings

def get_display_name(doc_id: str, source: Optional[str] = None, fallback: Optional[str] = None) -> str:
    """
    Obtém o nome de exibição para um documento
    
    Args:
        doc_id: ID do documento
        source: Fonte do documento (opcional)
        fallback: Nome de fallback (opcional)
        
    Retorna:
        str: Nome personalizado ou o fallback/ID original
    """
    # Carregar mapeamentos de nomes personalizados
    mappings = load_custom_names()
    
    # Tentar pelo ID diretamente
    if doc_id in mappings:
        return mappings[doc_id]
    
    # Se tiver o sistema baseado em arquivo, tentar usar
    if USING_FILE_BASED and source:
        custom_name = get_custom_name(source)
        if custom_name:
            return custom_name
    
    # Tentar extrair UUID do ID
    uuid_match = re.search(UUID_PATTERN, doc_id)
    if uuid_match:
        uuid = uuid_match.group(1)
        
        # Tentar IDs alternativos
        alt_ids = [f"doc_{uuid}", f"conv_{uuid}"]
        for alt_id in alt_ids:
            if alt_id in mappings:
                return mappings[alt_id]
    
    # Retornar fallback ou ID original
    return fallback if fallback else doc_id

def process_document_for_display(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa um documento para exibição, substituindo seu ID por nome personalizado
    
    Args:
        doc: Documento a processar
        
    Retorna:
        Dict[str, Any]: Documento processado
    """
    # Copiar o documento
    processed = doc.copy()
    
    # Adicionar nome personalizado
    doc_id = doc.get("id", "")
    source = doc.get("source", "")
    summary = doc.get("summary", "")
    
    # Tentar obter nome personalizado
    display_name = get_display_name(doc_id, source, fallback=summary)
    
    # Adicionar ao documento processado
    processed["display_name"] = display_name
    
    return processed

def process_documents_for_display(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processa uma lista de documentos para exibição
    
    Args:
        documents: Lista de documentos
        
    Retorna:
        List[Dict[str, Any]]: Lista de documentos processados
    """
    return [process_document_for_display(doc) for doc in documents]

def get_document_options(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cria opções para selectbox a partir de documentos
    
    Args:
        documents: Lista de documentos
        
    Retorna:
        List[Dict[str, Any]]: Lista de opções para selectbox
    """
    options = []
    
    for doc in documents:
        doc_id = doc.get("id", "")
        source = doc.get("source", "")
        summary = doc.get("summary", "")
        
        # Obter nome personalizado
        display_name = get_display_name(doc_id, source, fallback=summary)
        
        # Adicionar opção
        options.append({
            "id": doc_id,
            "label": display_name,
            "original": doc
        })
    
    return options

def get_documents_dataframe(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepara dados para exibição em DataFrame, ocultando IDs e mostrando nomes personalizados
    
    Args:
        documents: Lista de documentos
        
    Retorna:
        List[Dict[str, Any]]: Dados formatados para DataFrame
    """
    processed_data = []
    
    for doc in documents:
        # Obter nome personalizado
        doc_id = doc.get("id", "")
        source = doc.get("source", "")
        summary = doc.get("summary", "")
        display_name = get_display_name(doc_id, source, fallback=summary)
        
        # Truncar conteúdo longo
        content = doc.get("content", "")
        if len(content) > 100:
            content = content[:97] + "..."
        
        # Criar registro para DataFrame
        processed_data.append({
            "Nome": display_name,
            "Resumo": summary or "Arquivo de histórico de conversa",
            "Arquivo": content,
            "Criado": doc.get("created", "").split("T")[0]
        })
    
    return processed_data


# Teste básico
if __name__ == "__main__":
    # Testar carregamento de nomes
    names = load_custom_names()
    print(f"Nomes carregados: {len(names)}")
    
    # Testar obtenção de nome
    test_id = "doc_1234567890"
    test_name = get_display_name(test_id, "test.jsonl")
    print(f"Nome para {test_id}: {test_name}")