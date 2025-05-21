#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Funções de processamento de dados para o LightRAG
Utilitários para carregar, processar e gerenciar dados da base de conhecimento
"""

import json
import os
import re
import hashlib
import streamlit as st
from typing import Dict, List, Any, Optional, Union

# Importar componentes do LightRAG
from core.client import LightRAGClient, ensure_server_running
from core.settings import DB_FILE, MEMORY_SUMMARY_FILE
from utils.logger import get_ui_logger

# Configurar logger
logger = get_ui_logger()

@st.cache_data(ttl=5)
def check_server():
    """
    Verifica o status do servidor LightRAG
    
    Returns:
        Dict: Status do servidor
    """
    try:
        client = LightRAGClient()
        result = client.status()
        logger.debug(f"Status do servidor verificado: {result}")
        return result
    except Exception as e:
        logger.error(f"Erro ao verificar status do servidor: {str(e)}")
        return {"status": "offline", "error": str(e)}

@st.cache_data(ttl=10)
def load_knowledge_base():
    """
    Carrega a base de conhecimento diretamente do arquivo
    
    Returns:
        Dict: Conteúdo da base de conhecimento
    """
    logger.debug("Carregando base de conhecimento do arquivo")
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar base de conhecimento: {str(e)}")
            st.error(f"Erro ao carregar base de conhecimento: {str(e)}")
    return {"documents": [], "lastUpdated": ""}

@st.cache_data(ttl=60)
def load_memory_summary():
    """
    Carrega o arquivo de resumo da integração com Memory e Model Context Protocol (MCP)
    
    Returns:
        str: Conteúdo do arquivo de resumo
    """
    logger.debug("Carregando resumo da integração com Memory e Model Context Protocol (MCP)")
    if os.path.exists(MEMORY_SUMMARY_FILE):
        try:
            with open(MEMORY_SUMMARY_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erro ao carregar resumo da integração: {str(e)}")
            return f"Erro ao carregar resumo da integração Memory: {str(e)}"
    return "Resumo da integração com Memory e Model Context Protocol (MCP) não encontrado."

def extract_entities(text):
    """
    Extrai entidades mencionadas em um texto (menções a Memory e Model Context Protocol (MCP))
    
    Args:
        text: Texto para análise
        
    Returns:
        list: Lista de entidades encontradas
    """
    logger.debug("Extraindo entidades do texto")
    # Expressão regular para encontrar entidades em formato JSON
    entity_pattern = r'"name"\s*:\s*"([^"]+)"'
    relation_patterns = [
        r'"from"\s*:\s*"([^"]+)"',
        r'"to"\s*:\s*"([^"]+)"'
    ]
    
    entities = set()
    
    # Encontrar entidades diretas
    for match in re.finditer(entity_pattern, text):
        entities.add(match.group(1))
    
    # Encontrar entidades em relações
    for pattern in relation_patterns:
        for match in re.finditer(pattern, text):
            entities.add(match.group(1))
    
    return list(entities)

def delete_document(doc_id):
    """
    Remove um documento da base de conhecimento
    
    Args:
        doc_id: ID do documento a ser removido
        
    Returns:
        bool: True se sucesso, False se falha
    """
    logger.info(f"Solicitada exclusão do documento: {doc_id}")
    try:
        client = LightRAGClient()
        result = client.delete(doc_id)
        if result.get("success"):
            logger.info(f"Documento {doc_id} excluído com sucesso!")
            st.success(f"Documento {doc_id} excluído com sucesso!")
            st.cache_data.clear()  # Limpar cache para atualizar a lista
            return True
        else:
            error_msg = result.get("error", "Erro desconhecido")
            logger.error(f"Erro na exclusão: {error_msg}")
            st.error(error_msg)
    except Exception as e:
        logger.error(f"Erro ao conectar ao servidor: {str(e)}")
        st.error(f"Erro ao conectar ao servidor: {str(e)}")
    return False