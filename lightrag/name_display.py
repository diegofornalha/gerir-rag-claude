#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Módulo de exibição de nomes
Este módulo implementa funções para exibir nomes personalizados em vez de IDs ou nomes de arquivo
"""

import os
import re
import json
from file_based_names import get_custom_name, get_filename_key

def get_display_name(document_id: str, source: str = None) -> str:
    """
    Obtém o nome de exibição para um documento
    
    Args:
        document_id: ID do documento no banco de dados
        source: Caminho do arquivo fonte (opcional)
        
    Retorna:
        str: Nome de exibição personalizado ou o ID original se não encontrado
    """
    # Se tiver o caminho do arquivo fonte, usa ele para buscar o nome personalizado
    if source and ".jsonl" in source:
        custom_name = get_custom_name(source)
        if custom_name:
            return custom_name
    
    # Tentar pelo ID, para compatibilidade com o sistema antigo
    try:
        # Arquivo de mapeamento antigo
        old_names_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "custom_project_names.json")
        
        if os.path.exists(old_names_file):
            with open(old_names_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
                if document_id in mappings:
                    return mappings[document_id]
    except Exception:
        pass
    
    # Se não encontrar, retorna o ID original
    return document_id

def resolve_name_from_content(content: str) -> str:
    """
    Tenta extrair o nome personalizado a partir do conteúdo do documento
    
    Args:
        content: Conteúdo do documento
        
    Retorna:
        str: Nome personalizado extraído ou None se não encontrado
    """
    # Padrão para extrair o UUID da sessão
    session_pattern = r'\"sessionId\"\s*:\s*\"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\"'
    match = re.search(session_pattern, content)
    
    if match:
        session_id = match.group(1)
        # Usar o UUID da sessão para buscar o nome personalizado
        filename = f"{session_id}.jsonl"
        custom_name = get_custom_name(filename)
        if custom_name:
            return custom_name
    
    return None

def format_document_list(documents: list) -> list:
    """
    Formata uma lista de documentos substituindo IDs por nomes personalizados
    
    Args:
        documents: Lista de documentos (dicionários)
        
    Retorna:
        list: Lista formatada com nomes personalizados
    """
    formatted_docs = []
    
    for doc in documents:
        # Copiar o documento
        formatted_doc = doc.copy()
        
        # Substituir ID por nome personalizado
        original_id = doc.get("id", "")
        source = doc.get("source", "")
        
        # Tenta obter nome personalizado do arquivo
        display_name = get_display_name(original_id, source)
        
        # Se não encontrar pelo arquivo, tenta pelo conteúdo
        if display_name == original_id and "content" in doc:
            content_name = resolve_name_from_content(doc["content"])
            if content_name:
                display_name = content_name
        
        # Adicionar nome de exibição
        formatted_doc["display_name"] = display_name
        
        formatted_docs.append(formatted_doc)
    
    return formatted_docs

# Função para teste
if __name__ == "__main__":
    # Teste simples
    test_docs = [
        {"id": "doc_1234567890", "source": "test.jsonl", "content": '{"sessionId": "8b225707-6263-4081-bc38-df505a930293"}'},
        {"id": "doc_9876543210", "source": "another.jsonl"}
    ]
    
    formatted = format_document_list(test_docs)
    for doc in formatted:
        print(f"Original ID: {doc['id']}")
        print(f"Display Name: {doc['display_name']}")
        print("---")