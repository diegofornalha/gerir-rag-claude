#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para consultar projetos no LightRAG
Este script permite fazer perguntas sobre os projetos carregados no LightRAG
"""

import json
import argparse
import urllib.request
import urllib.parse
import sys
import os

def query_lightrag(query_text, max_results=5):
    """Faz uma consulta ao servidor LightRAG"""
    base_url = "http://127.0.0.1:5000"
    
    data = {
        "query": query_text,
        "max_results": max_results
    }
    
    try:
        encoded_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/query",
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Erro ao consultar LightRAG: {e}")
        return {"error": str(e), "context": [], "response": f"Erro: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="Consulta projetos no LightRAG")
    parser.add_argument("query", help="A pergunta a ser consultada")
    parser.add_argument("--max", type=int, default=5, help="Número máximo de resultados")
    args = parser.parse_args()
    
    # Fazer a consulta
    print(f"Consultando: '{args.query}'...")
    result = query_lightrag(args.query, args.max)
    
    # Exibir resultados
    print("\n=== Resposta ===")
    print(result.get("response", "Sem resposta"))
    
    # Exibir contextos
    contexts = result.get("context", [])
    if contexts:
        print(f"\n=== Contextos encontrados ({len(contexts)}) ===")
        for i, ctx in enumerate(contexts):
            print(f"\n--- Contexto {i+1} ---")
            print(f"Fonte: {ctx.get('source', 'desconhecido')}")
            print(f"Relevância: {ctx.get('relevance', 0):.2f}")
            print(f"Documento ID: {ctx.get('document_id', 'desconhecido')}")
            print("\nConteúdo:")
            print(ctx.get("content", ""))
            print("-" * 50)
    else:
        print("\nNenhum contexto relevante encontrado.")

if __name__ == "__main__":
    main()