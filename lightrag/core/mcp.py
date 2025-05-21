#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG Model Context Protocol (MCP) Client
Módulo unificado para integrar o LightRAG com o serviço Model Context Protocol (MCP) do Claude
"""

import hashlib
import os
from typing import Dict, List, Any, Optional, Union

# Importar componentes do LightRAG
from core.client import LightRAGClient, ensure_server_running
from utils.logger import get_core_logger

# Configurar logger
logger = get_core_logger()

# Função para Model Context Protocol (MCP) do Claude
def rag_query(query, mode="hybrid", max_results=5):
    """
    Função de consulta para uso via Model Context Protocol (MCP)
    
    Args:
        query: Texto da consulta
        mode: Modo de consulta (hybrid, semantic, keyword)
        max_results: Número máximo de resultados
        
    Retorna:
        Dict: Resultados da consulta
    """
    logger.info(f"Model Context Protocol: rag_query chamado com '{query}'")
    
    # Garantir que o servidor esteja rodando
    if not ensure_server_running():
        error_msg = "Não foi possível garantir que o servidor LightRAG esteja rodando."
        logger.error(error_msg)
        return {"error": error_msg, "context": [], "response": error_msg}
    
    # Realizar consulta
    client = LightRAGClient()
    result = client.query(query, max_results, mode)
    
    if "error" not in result:
        logger.info(f"Model Context Protocol: consulta bem-sucedida com {len(result.get('context', []))} resultados")
    else:
        logger.error(f"Model Context Protocol: erro na consulta - {result.get('error')}")
        
    return result

# Função para Model Context Protocol (MCP) do Claude
def rag_insert_text(text, source="mcp", summary=None, metadata=None):
    """
    Função de inserção para uso via Model Context Protocol (MCP)
    
    Args:
        text: Texto a ser inserido
        source: Identificador da fonte do texto
        summary: Resumo opcional do documento
        metadata: Metadados adicionais
        
    Retorna:
        Dict: Resultado da operação
    """
    logger.info(f"Model Context Protocol: rag_insert_text chamado (fonte={source}, tamanho={len(text)})")
    
    # Garantir que o servidor esteja rodando
    if not ensure_server_running():
        error_msg = "Não foi possível garantir que o servidor LightRAG esteja rodando."
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    # Preparar metadados
    if metadata is None:
        metadata = {}
    
    # Adicionar hash do conteúdo para verificação de duplicidade
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    metadata["content_hash"] = content_hash
    
    # Inserir texto
    client = LightRAGClient()
    result = client.insert(text, summary, source, metadata)
    
    if result.get("success", False):
        logger.info(f"Model Context Protocol: texto inserido com ID {result.get('documentId')}")
    else:
        logger.error(f"Model Context Protocol: erro ao inserir texto - {result.get('error')}")
        
    return result

# Função para Model Context Protocol (MCP) do Claude para inserção de arquivo
def rag_insert_file(file_path, source="file", force=False, max_lines=500):
    """
    Função de inserção de arquivo para uso via Model Context Protocol (MCP)
    
    Args:
        file_path: Caminho do arquivo a ser inserido
        source: Identificador da fonte do arquivo
        force: Forçar inserção mesmo se for detectado como duplicado
        max_lines: Número máximo de linhas a processar do arquivo
        
    Retorna:
        Dict: Resultado da operação
    """
    logger.info(f"Model Context Protocol: rag_insert_file chamado (arquivo={file_path})")
    
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        error_msg = f"Arquivo não encontrado: {file_path}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    # Garantir que o servidor esteja rodando
    if not ensure_server_running():
        error_msg = "Não foi possível garantir que o servidor LightRAG esteja rodando."
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    try:
        # Ler o conteúdo do arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Aplicar limite de linhas se necessário
        if max_lines > 0 and len(lines) > max_lines:
            logger.warning(f"Arquivo excede o limite de {max_lines} linhas. Truncando.")
            lines = lines[:max_lines]
            content = "".join(lines)
            content += f"\n\n[Truncado: arquivo original tinha {len(lines)} linhas]"
        else:
            content = "".join(lines)
        
        # Preparar metadados
        file_name = os.path.basename(file_path)
        metadata = {
            "file_path": file_path,
            "file_name": file_name,
            "original_size": os.path.getsize(file_path),
            "truncated": len(lines) > max_lines if max_lines > 0 else False
        }
        
        # Calcular hash do conteúdo
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        metadata["content_hash"] = content_hash
        
        # Verificar duplicação se force=False
        if not force:
            client = LightRAGClient()
            status = client.status()
            
            # Se o servidor estiver online, verificar por duplicação usando query
            if status.get("status") == "online":
                # Usar o nome do arquivo como consulta para tentar encontrar duplicatas
                query_result = client.query(file_name, max_results=10)
                
                for ctx in query_result.get("context", []):
                    ctx_content = ctx.get("content", "")
                    ctx_hash = hashlib.sha256(ctx_content.encode('utf-8')).hexdigest()
                    
                    # Se encontrarmos um hash correspondente, é uma duplicata
                    if ctx_hash == content_hash:
                        doc_id = ctx.get("document_id", "desconhecido")
                        logger.warning(f"Documento duplicado detectado: {doc_id}")
                        
                        if not force:
                            return {
                                "success": False,
                                "error": f"Documento duplicado detectado (ID: {doc_id}). Use force=True para inserir mesmo assim.",
                                "duplicate_id": doc_id
                            }
        
        # Inserir documento
        summary = f"Arquivo: {file_name}"
        result = rag_insert_text(content, f"{source}:{file_name}", summary, metadata)
        
        if result.get("success", False):
            logger.info(f"Model Context Protocol: arquivo inserido com ID {result.get('documentId')}")
        else:
            logger.error(f"Model Context Protocol: erro ao inserir arquivo - {result.get('error')}")
            
        return result
        
    except Exception as e:
        error_msg = f"Erro ao processar arquivo: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg}

# Função para Model Context Protocol (MCP) do Claude
def rag_status():
    """
    Função de status para uso via Model Context Protocol (MCP)
    
    Retorna:
        Dict: Informações de status
    """
    logger.info("Model Context Protocol: rag_status chamado")
    
    client = LightRAGClient()
    result = client.status()
    
    if result.get("status") == "online":
        logger.info(f"Model Context Protocol: status verificado - {result.get('documents', 0)} documentos")
    else:
        logger.warning(f"Model Context Protocol: servidor offline - {result.get('error', 'erro desconhecido')}")
        
    return result

# Função para Model Context Protocol (MCP) do Claude
def rag_clear(confirm=True):
    """
    Função para limpar base para uso via Model Context Protocol (MCP)
    
    Args:
        confirm: Confirmação explícita
        
    Retorna:
        Dict: Resultado da operação
    """
    logger.info(f"Model Context Protocol: rag_clear chamado (confirm={confirm})")
    
    # Garantir que o servidor esteja rodando
    if not ensure_server_running():
        error_msg = "Não foi possível garantir que o servidor LightRAG esteja rodando."
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    
    if not confirm:
        logger.warning("Model Context Protocol: tentativa de limpeza sem confirmação")
        return {"success": False, "error": "Confirmação necessária para limpar a base"}
    
    client = LightRAGClient()
    result = client.clear(confirm)
    
    if result.get("success", False):
        logger.info("Model Context Protocol: base limpa com sucesso")
        if "backup" in result:
            logger.info(f"Model Context Protocol: backup criado em {result['backup']}")
    else:
        logger.error(f"Model Context Protocol: erro ao limpar base - {result.get('error')}")
        
    return result

# Uso para teste
if __name__ == "__main__":
    # Garantir que o servidor esteja rodando
    if ensure_server_running():
        # Testar funcionalidades
        status = rag_status()
        print(f"Status do servidor: {status}")
        
        # Inserir um documento
        texto = "O LightRAG é um sistema de RAG simplificado para uso com Claude."
        insert_result = rag_insert_text(texto)
        print(f"Inserção: {insert_result}")
        
        # Fazer uma consulta
        query_result = rag_query("O que é LightRAG?")
        print(f"Consulta: {query_result}")
    else:
        print("Não foi possível garantir que o servidor LightRAG esteja rodando.")