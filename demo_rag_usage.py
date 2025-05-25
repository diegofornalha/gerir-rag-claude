#!/usr/bin/env python3
"""
Demonstração de uso do LightRAG
Este script mostra como usar o LightRAG para indexar e buscar informações
"""

import requests
import json

# Configuração
RAG_URL = "http://localhost:8020"

def inserir_texto(texto):
    """Insere texto na base do RAG"""
    response = requests.post(f"{RAG_URL}/insert", json={
        "text": texto,
        "source": "demo",
        "summary": "Texto de demonstração"
    })
    return response.json()

def inserir_arquivo(caminho):
    """Insere arquivo na base do RAG"""
    with open(caminho, 'r') as f:
        conteudo = f.read()
    
    return inserir_texto(conteudo)

def buscar(query, modo="hybrid"):
    """Busca informações na base"""
    response = requests.post(f"{RAG_URL}/query", json={
        "query": query,
        "mode": modo,
        "max_results": 5
    })
    return response.json()

# Exemplos de uso
if __name__ == "__main__":
    print("=== Demonstração LightRAG ===\n")
    
    # 1. Inserir conhecimento sobre Claude Sessions
    print("1. Inserindo conhecimento...")
    conhecimento = """
    O sistema Claude Sessions permite visualizar todas as conversas e tarefas do Claude.
    Cada sessão é identificada por um UUID único que conecta:
    - Arquivo JSONL com a conversa completa
    - Arquivo JSON com as tarefas (todos)
    - Metadados como timestamp e status
    
    A integração funciona através de:
    1. File watcher que monitora mudanças
    2. API REST que serve os dados
    3. Dashboard React que visualiza em tempo real
    """
    
    # resultado = inserir_texto(conhecimento)
    # print(f"Inserido: {resultado}")
    
    # 2. Buscar informações
    print("\n2. Buscando informações...")
    queries = [
        "como funciona claude sessions",
        "visualizar tarefas em tempo real",
        "UUID único sessão"
    ]
    
    for q in queries:
        print(f"\nBusca: '{q}'")
        # resultado = buscar(q)
        # print(f"Resultados: {len(resultado.get('results', []))}")
        print("(Simulação - serviço não está rodando)")
    
    # 3. Inserir arquivo de documentação
    print("\n3. Inserindo arquivo...")
    # resultado = inserir_arquivo("/Users/agents/.claude/CLAUDE.md")
    # print(f"Arquivo inserido: {resultado}")
    
    print("\n=== Fim da demonstração ===")
    print("\nPara usar de verdade, inicie o serviço:")
    print("cd /Users/agents/.claude/lightrag && python3 api/server.py")