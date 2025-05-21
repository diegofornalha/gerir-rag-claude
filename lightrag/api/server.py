#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Servidor API
Implementação da API Flask para o sistema LightRAG
"""

from flask import Flask, request, jsonify
import datetime
from typing import Dict, List, Any, Optional, Union

# Importar módulos do LightRAG
from core.settings import SERVER_HOST, SERVER_PORT, MAX_RESULTS
from core.database import LightRAGDatabase
from core.retrieval import RetrievalEngine
from utils.logger import get_api_logger
from utils.formatters import APIFormatter

# Configurar logging
logger = get_api_logger()

# Inicializar aplicação Flask
app = Flask(__name__)

# Inicializar banco de dados
db = LightRAGDatabase()

# Endpoint de status
@app.route('/status', methods=['GET'])
def status():
    """Retorna o status do servidor e da base de conhecimento"""
    try:
        result = db.get_status()
        logger.info(f"Status verificado: {result['documents']} documentos")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erro ao obter status: {str(e)}")
        return jsonify(APIFormatter.format_error(f"Erro ao obter status: {str(e)}", 500)), 500

# Endpoint de consulta
@app.route('/query', methods=['POST', 'OPTIONS'])
def query():
    """Processa consultas à base de conhecimento"""
    # Lidar com CORS preflight requests
    if request.method == 'OPTIONS':
        return "", 204
    
    # Processar consulta
    try:
        data = request.json
        query_text = data.get('query', '')
        max_results = data.get('max_results', MAX_RESULTS)
        mode = data.get('mode', 'hybrid')
        
        logger.info(f"Consulta recebida: '{query_text}' (modo: {mode}, max: {max_results})")
        
        if not query_text:
            logger.warning("Consulta vazia recebida")
            return jsonify(APIFormatter.format_error("Consulta vazia")), 400
        
        # Obter todos os documentos
        documents = db.get_all_documents()
        
        if documents:
            # Buscar documentos relevantes
            ranked_docs = RetrievalEngine.rank_documents(
                query_text, documents, max_results, mode
            )
            
            # Formatar resultados
            response = RetrievalEngine.format_results(query_text, ranked_docs)
            logger.info(f"Consulta processada: {len(ranked_docs)} resultados encontrados")
        else:
            response = RetrievalEngine.format_results(query_text, [])
            logger.info("Consulta processada: base de conhecimento vazia")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Erro ao processar consulta: {str(e)}", exc_info=True)
        return jsonify(APIFormatter.format_error(str(e), 500)), 500

# Endpoint de inserção
@app.route('/insert', methods=['POST', 'OPTIONS'])
def insert():
    """Insere um novo documento na base de conhecimento"""
    # Lidar com CORS preflight requests
    if request.method == 'OPTIONS':
        return "", 204
    
    # Processar inserção
    try:
        data = request.json
        text = data.get('text', '')
        source = data.get('source', 'manual')
        summary = data.get('summary', 'Documento manual')
        metadata = data.get('metadata', None)
        
        logger.info(f"Inserção recebida: fonte='{source}', tamanho={len(text)}")
        
        if not text:
            logger.warning("Tentativa de inserção com texto vazio")
            return jsonify(APIFormatter.format_error("Texto para inserção não fornecido")), 400
        
        # Inserir documento
        result = db.insert_document(text, source, summary, metadata)
        
        if result.get("success"):
            logger.info(f"Documento inserido: ID={result.get('documentId')}")
            return jsonify(result)
        else:
            logger.error(f"Erro ao inserir documento: {result.get('error')}")
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Erro ao processar inserção: {str(e)}", exc_info=True)
        return jsonify(APIFormatter.format_error(str(e), 500)), 500

# Endpoint para remover documento específico
@app.route('/delete', methods=['POST', 'OPTIONS'])
def delete_document():
    """Remove um documento específico da base de conhecimento"""
    # Lidar com CORS preflight requests
    if request.method == 'OPTIONS':
        return "", 204
    
    # Processar exclusão
    try:
        data = request.json
        doc_id = data.get('id', '')
        
        logger.info(f"Exclusão solicitada: ID='{doc_id}'")
        
        if not doc_id:
            logger.warning("Tentativa de exclusão sem ID")
            return jsonify(APIFormatter.format_error("ID do documento não fornecido")), 400
        
        # Excluir documento
        result = db.delete_document(doc_id)
        
        if result.get("success"):
            logger.info(f"Documento removido: {doc_id}")
            return jsonify(result)
        else:
            status_code = 404 if "não encontrado" in result.get("error", "") else 500
            logger.warning(f"Falha ao remover documento: {result.get('error')}")
            return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Erro ao processar exclusão: {str(e)}", exc_info=True)
        return jsonify(APIFormatter.format_error(str(e), 500)), 500

# Endpoint para limpar a base
@app.route('/clear', methods=['POST', 'OPTIONS'])
def clear():
    """Limpa toda a base de conhecimento"""
    # Lidar com CORS preflight requests
    if request.method == 'OPTIONS':
        return "", 204
    
    # Processar limpeza
    try:
        data = request.json
        confirm = data.get('confirm', False)
        
        logger.info(f"Limpeza solicitada: confirm={confirm}")
        
        if not confirm:
            logger.warning("Tentativa de limpeza sem confirmação")
            return jsonify(APIFormatter.format_error("Confirmação necessária para limpar a base de conhecimento")), 400
        
        # Limpar base
        result = db.clear_database(create_backup=True)
        
        if result.get("success"):
            logger.info(f"Base limpa: {result.get('message')}")
            if "backup" in result:
                logger.info(f"Backup criado: {result['backup']}")
            return jsonify(result)
        else:
            logger.error(f"Falha ao limpar base: {result.get('error')}")
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Erro ao limpar base de conhecimento: {str(e)}", exc_info=True)
        return jsonify(APIFormatter.format_error(str(e), 500)), 500

# Adicionar cabeçalhos CORS para todas as respostas
@app.after_request
def add_cors_headers(response):
    """Adiciona cabeçalhos CORS para permitir acesso de qualquer origem"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

# Iniciar aplicação se for executado diretamente
def run_server(host=None, port=None, debug=False):
    """
    Inicia o servidor Flask
    
    Args:
        host: Host para o servidor (default: valor de settings)
        port: Porta para o servidor (default: valor de settings)
        debug: Modo de debug (default: False)
    """
    server_host = host or SERVER_HOST
    server_port = port or SERVER_PORT
    
    logger.info(f"Iniciando servidor LightRAG em http://{server_host}:{server_port}")
    logger.info(f"Base de conhecimento: {db.db_file} ({len(db.get_all_documents())} documentos)")
    
    app.run(host=server_host, port=server_port, debug=debug)

if __name__ == '__main__':
    run_server(debug=True)