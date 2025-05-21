#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitários para carregamento e processamento de documentos
"""

import os
import json
import hashlib
import time
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple, Union

from core.client import LightRAGClient
from utils.logger import get_ui_logger

# Configurar logger
logger = get_ui_logger()

@st.cache_data(ttl=30)
def get_document_hash(doc: Dict[str, Any]) -> str:
    """
    Gera um hash para um documento
    
    Args:
        doc: Documento para gerar hash
    
    Returns:
        str: Hash do documento
    """
    # Criar uma string consistente a partir dos campos mais importantes
    content = doc.get("content", "")
    id = doc.get("id", "")
    source = doc.get("source", "")
    
    # Concatenar e gerar hash
    doc_string = f"{id}:{source}:{content[:100]}"
    return hashlib.md5(doc_string.encode('utf-8')).hexdigest()

@st.cache_data(ttl=30)
def chunk_document(content: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Divide um documento grande em pedaços menores para exibição
    
    Args:
        content: Conteúdo a ser dividido
        chunk_size: Tamanho máximo de cada pedaço
        overlap: Quantidade de sobreposição entre pedaços
    
    Returns:
        List[str]: Lista de pedaços
    """
    if len(content) <= chunk_size:
        return [content]
    
    chunks = []
    start = 0
    
    while start < len(content):
        # Determinar o final do chunk atual
        end = min(start + chunk_size, len(content))
        
        # Se não estamos no final do documento e não estamos no início de uma 
        # nova linha, tentamos encontrar o fim da última linha completa
        if end < len(content) and content[end] != '\n':
            # Procurar pela última quebra de linha dentro do chunk
            last_newline = content.rfind('\n', start, end)
            if last_newline > start:
                end = last_newline + 1
        
        # Adicionar o chunk à lista
        chunks.append(content[start:end])
        
        # Atualizar posição de início para próximo chunk, considerando sobreposição
        start = end - overlap
    
    return chunks

@st.cache_data(ttl=60)
def read_document_batched(doc_id: str, batch_size: int = 3) -> Dict[str, Any]:
    """
    Lê um documento em lotes para otimizar carregamento
    
    Args:
        doc_id: ID do documento
        batch_size: Número de documentos a carregar por lote
    
    Returns:
        Dict: Documento completo ou None se não encontrado
    """
    try:
        client = LightRAGClient()
        result = client.get_document(doc_id)
        
        if result and "document" in result:
            document = result["document"]
            
            # Verificar se o conteúdo é muito grande e precisa ser dividido
            content = document.get("content", "")
            if len(content) > 10000:  # 10KB
                # Dividir em chunks
                chunks = chunk_document(content)
                document["chunks"] = chunks
                document["is_chunked"] = True
            else:
                document["is_chunked"] = False
                
            return document
        else:
            logger.warning(f"Documento não encontrado: {doc_id}")
            return None
    except Exception as e:
        logger.error(f"Erro ao carregar documento {doc_id}: {str(e)}")
        return None

@st.cache_data(ttl=30)
def load_documents_paged(page: int = 1, page_size: int = 10, 
                         source_filter: Optional[str] = None, 
                         date_sort: bool = True) -> Tuple[List[Dict[str, Any]], int]:
    """
    Carrega documentos de forma paginada
    
    Args:
        page: Página atual
        page_size: Tamanho da página
        source_filter: Filtro opcional por fonte
        date_sort: Se deve ordenar por data
    
    Returns:
        Tuple: Lista de documentos e contagem total
    """
    try:
        # Carregar todos os documentos - idealmente a API teria suporte a paginação
        client = LightRAGClient()
        result = client.list_documents()
        
        if result and "documents" in result:
            documents = result["documents"]
            
            # Aplicar filtros
            if source_filter:
                source_filter = source_filter.lower()
                documents = [
                    doc for doc in documents 
                    if source_filter in doc.get("source", "").lower()
                ]
            
            # Ordenar
            if date_sort:
                documents.sort(
                    key=lambda x: x.get("created", ""), 
                    reverse=True
                )
            
            # Calcular totais
            total_docs = len(documents)
            total_pages = (total_docs + page_size - 1) // page_size
            
            # Validar página
            page = max(1, min(page, total_pages)) if total_pages > 0 else 1
            
            # Extrair página
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_docs)
            
            # Extrair página atual
            page_docs = documents[start_idx:end_idx]
            
            # Preparar os documentos para exibição
            for doc in page_docs:
                # Truncar conteúdo para exibição na tabela
                content = doc.get("content", "")
                if len(content) > 100:
                    doc["content_preview"] = content[:97] + "..."
                else:
                    doc["content_preview"] = content
                    
                # Adicionar hash para rastreamento
                doc["hash"] = get_document_hash(doc)
            
            return page_docs, total_docs
        else:
            logger.warning("Nenhum documento encontrado")
            return [], 0
    except Exception as e:
        logger.error(f"Erro ao carregar documentos: {str(e)}")
        return [], 0

def insert_document(content: str, summary: str, source: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Insere um documento na base de conhecimento
    
    Args:
        content: Conteúdo do documento
        summary: Resumo do documento
        source: Fonte do documento
        metadata: Metadados opcionais
    
    Returns:
        Dict: Resultado da operação
    """
    try:
        client = LightRAGClient()
        result = client.insert(content, summary, source, metadata)
        
        # Limpar cache após inserção
        if result.get("success", False):
            logger.info(f"Documento inserido com sucesso: {result.get('documentId')}")
            # Limpar caches relevantes
            st.cache_data.clear()
        else:
            logger.error(f"Erro ao inserir documento: {result.get('error')}")
            
        return result
    except Exception as e:
        logger.error(f"Exceção ao inserir documento: {str(e)}")
        return {"success": False, "error": str(e)}