#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Script de demonstração
Este script demonstra como usar o serviço LightRAG
"""

import json
import urllib.request
import urllib.parse
import sys

# Configuração
HOST = "127.0.0.1"
PORT = 5000
BASE_URL = f"http://{HOST}:{PORT}"

def make_request(endpoint, data=None):
    """Faz uma requisição ao servidor LightRAG"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if data:
            # Requisição POST
            data_json = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_json, headers=headers, method="POST")
        else:
            # Requisição GET
            req = urllib.request.Request(url, headers=headers, method="GET")
            
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            return json.loads(response_data)
            
    except Exception as e:
        print(f"Erro na requisição: {e}")
        return None

def check_status():
    """Verifica o status do servidor"""
    print("\n=== Verificando status do servidor ===")
    response = make_request("status")
    if response:
        print(f"Status: {response['status']}")
        print(f"Documentos disponíveis: {response['documents']}")
        print(f"Última atualização: {response['lastUpdated']}")
        return True
    else:
        print("ERRO: Não foi possível conectar ao servidor LightRAG.")
        print("Certifique-se de que o servidor está rodando com:")
        print("cd ~/.claude/lightrag && ./start_lightrag.sh")
        return False

def insert_document(text):
    """Insere um novo documento na base de conhecimento"""
    print(f"\n=== Inserindo documento ===")
    response = make_request("insert", {"text": text})
    if response and response.get("success"):
        print(f"✓ Documento inserido com sucesso!")
        print(f"ID: {response.get('documentId')}")
        return True
    else:
        error = response.get("error") if response else "Conexão falhou"
        print(f"✗ Falha ao inserir documento: {error}")
        return False

def query_documents(query_text):
    """Consulta documentos na base de conhecimento"""
    print(f"\n=== Consultando: '{query_text}' ===")
    response = make_request("query", {"query": query_text})
    if response:
        contexts = response.get("context", [])
        if contexts:
            print(f"Encontrados {len(contexts)} resultados relevantes:")
            for i, ctx in enumerate(contexts):
                relevance = ctx.get("relevance", 0)
                relevance_str = f"{relevance:.2f}" if relevance else "N/A"
                print(f"\n{i+1}. Relevância: {relevance_str}")
                print(f"Fonte: {ctx.get('source', 'desconhecida')}")
                print(f"Conteúdo: {ctx.get('content', '')}")
        else:
            print("Nenhum resultado encontrado para esta consulta.")
        return True
    else:
        print("✗ Falha ao consultar documentos")
        return False

def demo_mode():
    """Modo de demonstração interativo"""
    if not check_status():
        return
    
    print("\n=== LightRAG Demo ===")
    print("Este é um modo interativo para testar o serviço LightRAG")
    
    while True:
        print("\nOpções:")
        print("1. Inserir documento")
        print("2. Consultar documentos")
        print("3. Verificar status")
        print("0. Sair")
        
        choice = input("\nEscolha uma opção: ")
        
        if choice == "1":
            text = input("Digite o texto para inserir: ")
            if text:
                insert_document(text)
        elif choice == "2":
            query = input("Digite sua consulta: ")
            if query:
                query_documents(query)
        elif choice == "3":
            check_status()
        elif choice == "0":
            print("Encerrando demo...")
            break
        else:
            print("Opção inválida!")

def main():
    """Função principal"""
    args = sys.argv[1:]
    
    # Sem argumentos, entrar no modo interativo
    if not args:
        demo_mode()
        return
    
    # Processar comandos
    command = args[0].lower()
    
    if command == "status":
        check_status()
    elif command == "insert" and len(args) > 1:
        insert_document(" ".join(args[1:]))
    elif command == "query" and len(args) > 1:
        query_documents(" ".join(args[1:]))
    else:
        print("Uso:")
        print(f"{sys.argv[0]} status - Verificar status do servidor")
        print(f"{sys.argv[0]} insert <texto> - Inserir documento")
        print(f"{sys.argv[0]} query <consulta> - Consultar documentos")
        print(f"{sys.argv[0]} - Modo interativo")

if __name__ == "__main__":
    main()