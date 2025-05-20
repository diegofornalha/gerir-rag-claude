#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use LightRAG - Interface simples para usar o LightRAG
"""

import json
import urllib.request
import urllib.parse
import sys
import os
import argparse

class LightRAGClient:
    def __init__(self, host="127.0.0.1", port=5000):
        self.base_url = f"http://{host}:{port}"
    
    def status(self):
        """Verificar status do servidor"""
        try:
            with urllib.request.urlopen(f"{self.base_url}/status") as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    def query(self, query_text, max_results=5):
        """Consultar a base de conhecimento"""
        data = {
            "query": query_text,
            "max_results": max_results
        }
        
        try:
            encoded_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/query",
                data=encoded_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"error": str(e), "context": [], "response": f"Erro: {str(e)}"}
    
    def insert(self, text, summary=None, source="command_line"):
        """Inserir documento na base de conhecimento"""
        data = {
            "text": text,
            "source": source
        }
        
        if summary:
            data["summary"] = summary
        
        try:
            encoded_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/insert",
                data=encoded_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete(self, doc_id):
        """Remover documento da base de conhecimento"""
        data = {"id": doc_id}
        
        try:
            encoded_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/delete",
                data=encoded_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear(self, confirm=True):
        """Limpar toda a base de conhecimento"""
        data = {"confirm": confirm}
        
        try:
            encoded_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/clear",
                data=encoded_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"success": False, "error": str(e)}

# Funções de utilidade para exibir resultados no terminal
def print_status(status):
    """Exibe o status do servidor de forma formatada"""
    print("\n=== Status do Servidor LightRAG ===")
    if status.get("status") == "online":
        print(f"✓ Servidor: ONLINE")
        print(f"✓ Documentos disponíveis: {status.get('documents', 0)}")
        print(f"✓ Última atualização: {status.get('lastUpdated', 'desconhecido')}")
    else:
        print(f"✗ Servidor: OFFLINE")
        if "error" in status:
            print(f"✗ Erro: {status['error']}")

def print_query_result(result):
    """Exibe o resultado de uma consulta de forma formatada"""
    print("\n=== Resultado da Consulta ===")
    print(f"{result.get('response', 'Sem resposta')}")
    
    contexts = result.get('context', [])
    if contexts:
        print(f"\nContextos encontrados ({len(contexts)}):")
        for i, ctx in enumerate(contexts):
            relevance = ctx.get('relevance', 0)
            source = ctx.get('source', 'desconhecido')
            content = ctx.get('content', '')
            
            print(f"{i+1}. [{source}] (Relevância: {relevance:.2f})")
            print(f"   {content}")
            print()
    else:
        print("\nNenhum contexto relevante encontrado.")

def print_insert_result(result):
    """Exibe o resultado de uma inserção de forma formatada"""
    if result.get("success", False):
        print(f"✓ Documento inserido com sucesso!")
        print(f"✓ ID: {result.get('documentId', 'desconhecido')}")
    else:
        print(f"✗ Falha ao inserir documento: {result.get('error', 'Erro desconhecido')}")

def print_delete_result(result):
    """Exibe o resultado de uma exclusão de forma formatada"""
    if result.get("success", False):
        print(f"✓ {result.get('message', 'Documento removido com sucesso')}")
    else:
        print(f"✗ Falha ao remover documento: {result.get('error', 'Erro desconhecido')}")

def print_clear_result(result):
    """Exibe o resultado de uma limpeza de forma formatada"""
    if result.get("success", False):
        print(f"✓ {result.get('message', 'Base de conhecimento limpa com sucesso')}")
        if "backup" in result:
            print(f"✓ Backup criado em: {result['backup']}")
    else:
        print(f"✗ Falha ao limpar base de conhecimento: {result.get('error', 'Erro desconhecido')}")

def main():
    # Configurar argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Interface para o LightRAG")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Comando STATUS
    status_parser = subparsers.add_parser("status", help="Verificar status do servidor")
    
    # Comando QUERY
    query_parser = subparsers.add_parser("query", help="Consultar a base de conhecimento")
    query_parser.add_argument("text", help="Texto da consulta")
    query_parser.add_argument("--max", type=int, default=5, help="Número máximo de resultados")
    
    # Comando INSERT
    insert_parser = subparsers.add_parser("insert", help="Inserir documento na base de conhecimento")
    insert_parser.add_argument("text", help="Texto do documento")
    insert_parser.add_argument("--summary", help="Resumo do documento")
    insert_parser.add_argument("--source", default="command_line", help="Fonte do documento")
    
    # Comando DELETE
    delete_parser = subparsers.add_parser("delete", help="Remover documento da base de conhecimento")
    delete_parser.add_argument("id", help="ID do documento a ser removido")
    
    # Comando CLEAR
    clear_parser = subparsers.add_parser("clear", help="Limpar toda a base de conhecimento")
    clear_parser.add_argument("--no-confirm", action="store_true", help="Não pedir confirmação")
    
    # Analisar argumentos
    args = parser.parse_args()
    
    # Criar cliente
    client = LightRAGClient()
    
    # Executar comando
    if args.command == "status":
        status = client.status()
        print_status(status)
    
    elif args.command == "query":
        result = client.query(args.text, args.max)
        print_query_result(result)
    
    elif args.command == "insert":
        result = client.insert(args.text, args.summary, args.source)
        print_insert_result(result)
    
    elif args.command == "delete":
        result = client.delete(args.id)
        print_delete_result(result)
    
    elif args.command == "clear":
        if args.no_confirm:
            result = client.clear(True)
            print_clear_result(result)
        else:
            confirm = input("ATENÇÃO: Isso irá remover TODOS os documentos. Confirma? (s/N): ")
            if confirm.lower() in ["s", "sim", "y", "yes"]:
                result = client.clear(True)
                print_clear_result(result)
            else:
                print("Operação cancelada pelo usuário.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário.")
        sys.exit(0)