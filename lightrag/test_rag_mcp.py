#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de integração do LightRAG com MCP
Este script testa a funcionalidade básica do LightRAG através do MCP
"""

import json
import urllib.request
import urllib.parse
import sys
import os

# Adicionar alguns documentos de teste
def add_test_documents():
    print("Adicionando documentos de teste...")
    
    documents = [
        {
            "text": "O LightRAG é um sistema leve de RAG (Retrieval Augmented Generation) desenvolvido para uso com Claude. Permite armazenar informações em uma base de conhecimento local e recuperá-las conforme necessário usando algoritmos de relevância.",
            "summary": "Descrição do LightRAG"
        },
        {
            "text": "O arquivo afa4d560-57d5-4a29-8598-586978109939.jsonl contém o histórico de conversação da sessão atual com Claude, incluindo mensagens sobre a configuração e uso do LightRAG.",
            "summary": "Descrição do arquivo afa4d560"
        },
        {
            "text": "O arquivo cb2ac1cc-c8c4-40e0-9098-321118163357.jsonl contém o histórico de uma sessão anterior de conversação com Claude, onde foram discutidos tópicos relacionados ao status dos serviços MCP.",
            "summary": "Descrição do arquivo cb2ac1cc"
        },
        {
            "text": "O arquivo b5e69835-8aa3-4238-809e-b43cf4058e94.jsonl contém histórico relacionado à remoção do diretório .git e limpeza do projeto LightRAG para torná-lo mais funcional e enxuto.",
            "summary": "Descrição do arquivo b5e69835"
        }
    ]
    
    for doc in documents:
        try:
            data = json.dumps({
                "text": doc["text"],
                "source": "test_script",
                "summary": doc["summary"]
            }).encode('utf-8')
            
            req = urllib.request.Request(
                "http://127.0.0.1:5000/insert",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("success"):
                    print(f"✓ Documento '{doc['summary']}' adicionado com ID: {result.get('documentId')}")
                else:
                    print(f"✗ Falha ao adicionar documento: {result.get('error')}")
        except Exception as e:
            print(f"✗ Erro ao adicionar documento: {str(e)}")

# Testar consultas ao LightRAG
def test_queries():
    print("\nTestando consultas ao LightRAG...")
    
    queries = [
        "O que é o LightRAG?",
        "Informações sobre o arquivo afa4d560",
        "Qual o conteúdo do arquivo cb2ac1cc?",
        "O que tem no arquivo b5e69835?",
        "Como funciona o sistema RAG?"
    ]
    
    for query in queries:
        try:
            data = json.dumps({"query": query}).encode('utf-8')
            
            req = urllib.request.Request(
                "http://127.0.0.1:5000/query",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                print(f"\n=== Consulta: '{query}' ===")
                print(f"Resposta: {result.get('response')}")
                
                contexts = result.get('context', [])
                if contexts:
                    print(f"\nContextos encontrados ({len(contexts)}):")
                    for i, ctx in enumerate(contexts):
                        relevance = ctx.get('relevance', 0)
                        source = ctx.get('source', 'desconhecido')
                        content = ctx.get('content', '')
                        
                        print(f"{i+1}. [{source}] (Relevância: {relevance:.2f})")
                        print(f"   {content[:150]}...")
                else:
                    print("Nenhum contexto encontrado.")
                
        except Exception as e:
            print(f"✗ Erro ao consultar '{query}': {str(e)}")

# Simulação do MCP para testes
def simulate_mcp_client():
    print("\nSimulando cliente MCP...")
    
    class MCPClient:
        def rag_query(self, query, **kwargs):
            data = {"query": query}
            data.update(kwargs)
            
            try:
                encoded_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(
                    "http://127.0.0.1:5000/query",
                    data=encoded_data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                
                with urllib.request.urlopen(req) as response:
                    return json.loads(response.read().decode('utf-8'))
            except Exception as e:
                return {"error": str(e), "context": [], "response": f"Erro: {str(e)}"}
        
        def rag_insert_text(self, text, **kwargs):
            data = {"text": text}
            data.update(kwargs)
            
            try:
                encoded_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(
                    "http://127.0.0.1:5000/insert",
                    data=encoded_data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                
                with urllib.request.urlopen(req) as response:
                    return json.loads(response.read().decode('utf-8'))
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    # Criar cliente MCP simulado
    mcp_client = MCPClient()
    
    # Testar consulta via MCP
    print("\nConsultando via MCP: 'O que é o arquivo afa4d560?'")
    result = mcp_client.rag_query("O que é o arquivo afa4d560?")
    
    print(f"Resposta MCP: {result.get('response')}")
    contexts = result.get('context', [])
    
    if contexts:
        print(f"\nContextos MCP ({len(contexts)}):")
        for i, ctx in enumerate(contexts):
            print(f"{i+1}. [{ctx.get('source', 'desconhecido')}] (Relevância: {ctx.get('relevance', 0):.2f})")
            print(f"   {ctx.get('content', '')[:150]}...")
    else:
        print("Nenhum contexto MCP encontrado.")
    
    print("\nTeste MCP concluído!")

# Função principal
def main():
    print("=== Teste de Integração LightRAG com MCP ===")
    
    # Verificar se o servidor está rodando
    try:
        with urllib.request.urlopen("http://127.0.0.1:5000/status") as response:
            status = json.loads(response.read().decode('utf-8'))
            print(f"Servidor LightRAG: {status.get('status', 'erro')}")
            print(f"Documentos: {status.get('documents', 0)}")
    except:
        print("ERRO: Servidor LightRAG não está rodando. Inicie-o com ./start_lightrag.sh")
        sys.exit(1)
    
    # Limpar a base de dados
    try:
        data = json.dumps({"confirm": True}).encode('utf-8')
        req = urllib.request.Request(
            "http://127.0.0.1:5000/clear",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get("success"):
                print("Base de conhecimento limpa com sucesso")
            else:
                print(f"Falha ao limpar base: {result.get('error')}")
    except Exception as e:
        print(f"Erro ao limpar base: {str(e)}")
    
    # Executar testes
    add_test_documents()
    test_queries()
    simulate_mcp_client()
    
    print("\n=== Teste concluído com sucesso! ===")

if __name__ == "__main__":
    main()