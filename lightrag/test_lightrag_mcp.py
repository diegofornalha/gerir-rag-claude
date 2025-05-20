#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de integração do LightRAG com MCP
"""

import sys
import json

# Tentar importar MCP do Claude
try:
    from claude import MCP
    has_claude_mcp = True
except ImportError:
    has_claude_mcp = False
    print("Aviso: Módulo claude.MCP não encontrado. Usando simulação.")

# Implementação alternativa para testes locais (quando claude.MCP não está disponível)
class LightRAGClient:
    def __init__(self, host="127.0.0.1", port=5000):
        import urllib.request
        import urllib.parse
        self.base_url = f"http://{host}:{port}"
        self.urllib = urllib
    
    def status(self):
        url = f"{self.base_url}/status"
        try:
            with self.urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"error": str(e), "status": "offline"}
    
    def query(self, query_text, **kwargs):
        url = f"{self.base_url}/query"
        data = {"query": query_text}
        data.update(kwargs)
        
        headers = {"Content-Type": "application/json"}
        req = self.urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method="POST"
        )
        
        try:
            with self.urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"error": str(e), "context": []}

# Função principal
def main():
    print("\n=== Teste de Integração LightRAG com MCP ===\n")
    
    # Conectar ao serviço LightRAG
    if has_claude_mcp:
        print("Usando MCP do Claude para conectar ao LightRAG...")
        lightrag = MCP.connect_to_service('lightrag')
    else:
        print("Usando implementação alternativa para testes locais...")
        lightrag = LightRAGClient()
    
    # Verificar status
    print("\n1. Verificando status do serviço LightRAG...")
    if has_claude_mcp:
        status = lightrag.rag_status()
    else:
        status = lightrag.status()
    
    print(f"Status: {json.dumps(status, indent=2)}")
    
    # Consultar documentos
    print("\n2. Consultando documentos com RAG...")
    queries = [
        "O que é o arquivo afa4d560?",
        "Quais arquivos JSONL estão disponíveis?",
        "O que está no arquivo cb2ac1cc?",
        "Existe o arquivo b5e69835?",
    ]
    
    for query in queries:
        print(f"\nConsulta: \"{query}\"")
        if has_claude_mcp:
            result = lightrag.rag_query(query=query)
        else:
            result = lightrag.query(query)
        
        # Exibir resultados de forma formatada
        print(f"Resposta: {result.get('response', 'Sem resposta')}")
        
        # Exibir contextos ordenados por relevância
        contexts = result.get('context', [])
        if contexts:
            print(f"\nContextos encontrados ({len(contexts)}):")
            for i, ctx in enumerate(contexts):
                relevance = ctx.get('relevance', 0)
                print(f"{i+1}. Relevância: {relevance:.2f}")
                print(f"   Documento: {ctx.get('source', 'desconhecido')}")
                print(f"   Conteúdo: {ctx.get('content', '')[:200]}")
                print()
        else:
            print("Nenhum contexto relevante encontrado.")
    
    print("\n=== Teste concluído ===")

if __name__ == "__main__":
    main()