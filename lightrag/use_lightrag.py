#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use LightRAG - Interface simples para usar o LightRAG
"""

import argparse
import sys

# Importar implementação do LightRAG na nova arquitetura
from core.client import LightRAGClient, ensure_server_running

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
            print(f"   {content[:150]}{'...' if len(content) > 150 else ''}")
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
    # Garantir que o servidor está rodando
    if not ensure_server_running():
        print("✗ Não foi possível garantir que o servidor LightRAG esteja rodando.")
        sys.exit(1)
    
    # Configurar argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Interface para o LightRAG")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Comando STATUS
    status_parser = subparsers.add_parser("status", help="Verificar status do servidor")
    
    # Comando QUERY
    query_parser = subparsers.add_parser("query", help="Consultar a base de conhecimento")
    query_parser.add_argument("text", help="Texto da consulta")
    query_parser.add_argument("--max", type=int, default=5, help="Número máximo de resultados")
    query_parser.add_argument("--mode", choices=["hybrid", "semantic", "keyword"], 
                              default="hybrid", help="Modo de busca")
    
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
    
    # Comando DEMO
    demo_parser = subparsers.add_parser("demo", help="Executa uma demonstração interativa")
    
    # Analisar argumentos
    args = parser.parse_args()
    
    # Criar cliente
    client = LightRAGClient()
    
    # Executar comando
    if args.command == "status":
        status = client.status()
        print_status(status)
    
    elif args.command == "query":
        result = client.query(args.text, args.max, args.mode)
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
    
    elif args.command == "demo":
        run_demo(client)
    
    else:
        parser.print_help()

def run_demo(client):
    """Executa uma demonstração interativa do LightRAG"""
    print("\n=== Demonstração do LightRAG ===")
    
    # Verificar status
    print("\n1. Verificando status do servidor...")
    status = client.status()
    print_status(status)
    
    # Consultar algo existente
    print("\n2. Realizando consulta de exemplo...")
    result = client.query("O que é LightRAG?", 2)
    print_query_result(result)
    
    # Inserir novo documento
    print("\n3. Inserindo documento de exemplo...")
    insert_text = (
        "LightRAG é um sistema modular de RAG (Retrieval Augmented Generation) "
        "que permite armazenar e recuperar conhecimento para uso com Claude."
    )
    insert_result = client.insert(
        insert_text,
        summary="Descrição do LightRAG",
        source="demo"
    )
    print_insert_result(insert_result)
    
    # Consulta novamente
    print("\n4. Consultando novamente...")
    result = client.query("O que é LightRAG?", 2)
    print_query_result(result)
    
    # Mostrar documentos na base
    print("\n5. Estado atual da base de conhecimento:")
    status = client.status()
    print_status(status)
    
    print("\nDemonstração concluída!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário.")
        sys.exit(0)