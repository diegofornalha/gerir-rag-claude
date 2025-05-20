#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Sistema simples de RAG (Retrieval Augmented Generation)
Implementação minimalista para uso com Claude via MCP
"""

from flask import Flask, request, jsonify
import json
import os
import datetime
import re

# Configuração
app = Flask(__name__)
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lightrag_db.json')
MAX_RESULTS = 5  # Número máximo de resultados retornados

# Base de conhecimento
knowledge_base = {
    "documents": [],
    "lastUpdated": datetime.datetime.now().isoformat()
}

# Carregar base de conhecimento se existir
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        print(f"Base de conhecimento carregada com {len(knowledge_base['documents'])} documentos")
    except Exception as e:
        print(f"Erro ao carregar base de conhecimento: {str(e)}")

# Salvar base de conhecimento
def save_knowledge_base():
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar base de conhecimento: {str(e)}")
        return False

# Função para calcular relevância entre consulta e documento
def calculate_relevance(query, content):
    query_lower = query.lower()
    content_lower = content.lower()
    
    # Verificar correspondência exata
    if query_lower in content_lower:
        return 0.9  # Alta relevância para correspondência exata
    
    # Verificar palavras individuais
    query_words = set(re.findall(r'\w+', query_lower))
    content_words = set(re.findall(r'\w+', content_lower))
    
    if not query_words:
        return 0
    
    # Calcular interseção de palavras
    common_words = query_words.intersection(content_words)
    if not common_words:
        return 0
    
    # Calcular relevância pela proporção de palavras correspondentes
    return len(common_words) / len(query_words) * 0.8

# Endpoint de status
@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online",
        "documents": len(knowledge_base["documents"]),
        "lastUpdated": knowledge_base["lastUpdated"]
    })

# Endpoint de consulta
@app.route('/query', methods=['POST', 'OPTIONS'])
def query():
    # Lidar com CORS preflight requests
    if request.method == 'OPTIONS':
        return "", 204
    
    # Processar consulta
    try:
        data = request.json
        query_text = data.get('query', '')
        max_results = data.get('max_results', MAX_RESULTS)
        
        print(f"Consulta recebida: {query_text}")
        
        if not query_text:
            return jsonify({
                "success": False,
                "error": "Consulta vazia"
            }), 400
        
        # Resposta padrão
        response = {
            "response": f'Resposta para: "{query_text}"',
            "context": []
        }
        
        # Buscar documentos relevantes
        if knowledge_base["documents"]:
            # Calcular relevância de cada documento
            docs_with_relevance = [
                {"doc": doc, "relevance": calculate_relevance(query_text, doc["content"])}
                for doc in knowledge_base["documents"]
            ]
            
            # Filtrar documentos com alguma relevância
            relevant_docs = [
                item for item in docs_with_relevance 
                if item["relevance"] > 0
            ]
            
            # Ordenar por relevância e limitar resultados
            relevant_docs.sort(key=lambda x: x["relevance"], reverse=True)
            top_docs = relevant_docs[:max_results]
            
            if top_docs:
                # Adicionar contextos encontrados
                response["context"] = [
                    {
                        "content": doc["doc"]["content"],
                        "source": doc["doc"].get("id", "documento"),
                        "relevance": doc["relevance"]
                    } for doc in top_docs
                ]
                
                response["response"] = f'Com base no conhecimento disponível, aqui está a resposta para: "{query_text}"'
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Erro ao processar consulta: {e}")
        return jsonify({"error": str(e)}), 500

# Endpoint de inserção
@app.route('/insert', methods=['POST', 'OPTIONS'])
def insert():
    # Lidar com CORS preflight requests
    if request.method == 'OPTIONS':
        return "", 204
    
    # Processar inserção
    try:
        data = request.json
        text = data.get('text', '')
        source = data.get('source', 'manual')
        
        if not text:
            return jsonify({
                "success": False,
                "error": "Texto para inserção não fornecido"
            }), 400
        
        # Adicionar documento
        doc_id = f"doc_{int(datetime.datetime.now().timestamp() * 1000)}"
        knowledge_base["documents"].append({
            "id": doc_id,
            "content": text,
            "source": source,
            "created": datetime.datetime.now().isoformat()
        })
        
        # Atualizar timestamp
        knowledge_base["lastUpdated"] = datetime.datetime.now().isoformat()
        
        # Salvar base de conhecimento
        if save_knowledge_base():
            print(f"Documento inserido: {text[:50]}...")
            return jsonify({
                "success": True,
                "message": "Documento inserido com sucesso",
                "documentId": doc_id
            })
        else:
            return jsonify({
                "success": False,
                "error": "Erro ao salvar base de conhecimento"
            }), 500
        
    except Exception as e:
        print(f"Erro ao processar inserção: {e}")
        return jsonify({"error": str(e)}), 500

# Endpoint para remover documento específico
@app.route('/delete', methods=['POST', 'OPTIONS'])
def delete_document():
    # Lidar com CORS preflight requests
    if request.method == 'OPTIONS':
        return "", 204
    
    # Processar exclusão
    try:
        data = request.json
        doc_id = data.get('id', '')
        
        if not doc_id:
            return jsonify({
                "success": False,
                "error": "ID do documento não fornecido"
            }), 400
        
        # Verificar se o documento existe
        original_count = len(knowledge_base["documents"])
        documents_filtered = [doc for doc in knowledge_base["documents"] if doc.get("id") != doc_id]
        
        if len(documents_filtered) == original_count:
            return jsonify({
                "success": False,
                "error": f"Documento com ID '{doc_id}' não encontrado"
            }), 404
        
        # Atualizar base de conhecimento
        knowledge_base["documents"] = documents_filtered
        knowledge_base["lastUpdated"] = datetime.datetime.now().isoformat()
        
        # Salvar base de conhecimento
        if save_knowledge_base():
            print(f"Documento removido: {doc_id}")
            return jsonify({
                "success": True,
                "message": f"Documento '{doc_id}' removido com sucesso"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Erro ao salvar base de conhecimento"
            }), 500
        
    except Exception as e:
        print(f"Erro ao processar exclusão: {e}")
        return jsonify({"error": str(e)}), 500

# Endpoint para limpar a base
@app.route('/clear', methods=['POST', 'OPTIONS'])
def clear():
    # Lidar com CORS preflight requests
    if request.method == 'OPTIONS':
        return "", 204
    
    # Processar limpeza
    try:
        data = request.json
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                "success": False,
                "error": "Confirmação necessária para limpar a base de conhecimento"
            }), 400
        
        # Criar backup
        backup_file = f"{DB_FILE}.bak.{int(datetime.datetime.now().timestamp())}"
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as src, open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
        
        # Limpar base
        doc_count = len(knowledge_base["documents"])
        knowledge_base["documents"] = []
        knowledge_base["lastUpdated"] = datetime.datetime.now().isoformat()
        
        # Salvar base vazia
        if save_knowledge_base():
            return jsonify({
                "success": True,
                "message": f"Base de conhecimento limpa. {doc_count} documentos removidos.",
                "backup": backup_file
            })
        else:
            return jsonify({
                "success": False,
                "error": "Erro ao salvar base de conhecimento vazia"
            }), 500
        
    except Exception as e:
        print(f"Erro ao limpar base de conhecimento: {e}")
        return jsonify({"error": str(e)}), 500

# Adicionar cabeçalhos CORS para todas as respostas
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

# Iniciar aplicação se for executado diretamente
if __name__ == '__main__':
    print(f"Servidor LightRAG Flask rodando em http://127.0.0.1:5000")
    print(f"Base de conhecimento: {DB_FILE} ({len(knowledge_base['documents'])} documentos)")
    print("Endpoints disponíveis:")
    print("  - GET  /status - Verifica o status do servidor")
    print("  - POST /query  - Consulta a base de conhecimento")
    print("  - POST /insert - Adiciona conteúdo à base")
    print("  - POST /delete - Remove um documento específico")
    print("  - POST /clear  - Limpa a base de conhecimento")
    app.run(host='127.0.0.1', port=5000)