#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para inserir arquivos no LightRAG com verificação avançada de duplicação
"""

import os
import json
import hashlib
import urllib.request
import urllib.parse
import re
from extract_jsonl import extract_jsonl_content

# Configuração
LIGHTRAG_URL = "http://127.0.0.1:5000"

def calculate_file_hash(file_path):
    """
    Calcula o hash SHA-256 do conteúdo do arquivo
    Retorna um identificador único baseado no conteúdo
    """
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return file_hash
    except Exception as e:
        print(f"Erro ao calcular hash do arquivo: {e}")
        return None

def extract_file_id(file_path):
    """
    Extrai um ID do caminho do arquivo
    Mais confiável que simplesmente usar o nome do arquivo
    """
    # Extrair o nome do arquivo sem a extensão
    filename = os.path.basename(file_path).split('.')[0]
    
    # Se tiver um UUID, usar o início dele
    if re.match(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', filename):
        return filename.split('-')[0]
    
    # Se for curto o suficiente, usar completo
    if len(filename) <= 10:
        return filename
    
    # Caso contrário, usar os primeiros 8 caracteres
    return filename[:8]

def get_documents_metadata():
    """
    Recupera metadados de todos os documentos existentes na base
    Retorna um dicionário com IDs, hashes e conteúdo para comparação
    """
    try:
        # Fazer uma consulta especial para obter metadados
        data = json.dumps({"query": "*", "include_metadata": True}).encode('utf-8')
        req = urllib.request.Request(
            f"{LIGHTRAG_URL}/query",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            contexts = result.get('context', [])
            
            metadata = {}
            for ctx in contexts:
                doc_id = ctx.get('document_id')
                if doc_id:
                    metadata[doc_id] = {
                        'content': ctx.get('content', ''),
                        'source': ctx.get('source', ''),
                        'content_hash': ctx.get('content_hash', '')
                    }
            
            return metadata
    except Exception as e:
        print(f"Erro ao recuperar metadados dos documentos: {e}")
        return {}

def check_content_similarity(content1, content2, threshold=0.8):
    """
    Verifica a similaridade entre dois textos
    Retorna True se a similaridade for maior que o threshold
    """
    # Simplificar os textos para comparação
    def normalize_text(text):
        if not text:
            return ""
        # Remover espaços extras e converter para minúsculas
        return re.sub(r'\s+', ' ', text.lower()).strip()
    
    norm1 = normalize_text(content1)
    norm2 = normalize_text(content2)
    
    if not norm1 or not norm2:
        return False
    
    # Verificar se um é substring do outro
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # Verificar sobreposição de palavras
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return False
    
    # Calcular coeficiente de Jaccard
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    similarity = intersection / union if union > 0 else 0
    return similarity >= threshold

def is_duplicate_file(file_path, existing_docs):
    """
    Verifica se um arquivo já está inserido na base de conhecimento
    Usa múltiplos métodos de verificação de duplicação
    """
    # 1. Verificar por ID direto
    file_id = extract_file_id(file_path)
    doc_id = f"doc_{file_id}"
    
    if doc_id in existing_docs:
        print(f"⚠️ Documento com ID {doc_id} já existe na base")
        return True
    
    # 2. Verificar por hash do arquivo
    file_hash = calculate_file_hash(file_path)
    
    if file_hash:
        for existing_id, metadata in existing_docs.items():
            if metadata.get('content_hash') == file_hash:
                print(f"⚠️ Arquivo com mesmo hash já existe na base (ID: {existing_id})")
                return True
    
    # 3. Verificar por conteúdo similar
    text, _, _ = extract_jsonl_content(file_path)
    
    if text:
        for existing_id, metadata in existing_docs.items():
            existing_content = metadata.get('content', '')
            if check_content_similarity(text, existing_content):
                print(f"⚠️ Arquivo com conteúdo similar já existe na base (ID: {existing_id})")
                return True
    
    # Nenhuma duplicação encontrada
    return False

def insert_document(text, summary, source="file_loader", content_hash=None):
    """
    Insere um documento no LightRAG com metadata adicional
    """
    data = {
        "text": text,
        "summary": summary,
        "source": source,
        "metadata": {
            "content_hash": content_hash
        }
    }
    
    try:
        encoded_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            f"{LIGHTRAG_URL}/insert",
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Erro ao inserir documento: {e}")
        return {"success": False, "error": str(e)}

def rag_insert_file(file_path, force=False, max_lines=100):
    """
    Função principal para inserir um arquivo no LightRAG
    Com verificação avançada de duplicação
    
    Parâmetros:
    - file_path: caminho do arquivo a ser inserido
    - force: forçar inserção mesmo se for detectado como duplicado
    - max_lines: número máximo de linhas a processar do arquivo
    
    Retorna:
    - Dicionário com status da operação e metadados
    """
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"Arquivo não encontrado: {file_path}"
        }
    
    # Obter metadados dos documentos existentes
    existing_docs = get_documents_metadata()
    print(f"Verificando duplicação entre {len(existing_docs)} documentos existentes...")
    
    # Verificar duplicação
    is_duplicate = is_duplicate_file(file_path, existing_docs)
    
    if is_duplicate and not force:
        return {
            "success": False,
            "error": "Arquivo duplicado detectado",
            "message": "Use o parâmetro force=True para forçar a inserção"
        }
    
    # Extrair conteúdo do arquivo
    text, summary, source_id = extract_jsonl_content(file_path, max_lines)
    
    if not text:
        return {
            "success": False,
            "error": "Falha ao extrair conteúdo do arquivo"
        }
    
    # Calcular hash do conteúdo
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    # Inserir no LightRAG
    print(f"Inserindo arquivo {os.path.basename(file_path)} (tamanho: {len(text)} caracteres)...")
    result = insert_document(text, summary, source_id, content_hash)
    
    if result.get("success", False):
        return {
            "success": True,
            "message": "Arquivo inserido com sucesso",
            "document_id": result.get("documentId"),
            "is_duplicate": is_duplicate,
            "content_hash": content_hash
        }
    else:
        return {
            "success": False,
            "error": result.get("error", "Erro desconhecido ao inserir documento")
        }

# Uso para teste
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python improved_rag_insert_file.py <arquivo.jsonl> [--force]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    force = "--force" in sys.argv
    
    result = rag_insert_file(file_path, force)
    print(json.dumps(result, indent=2, ensure_ascii=False))