#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para consultar o LightRAG sobre a documentação do Claude Code.
Este script permite fazer perguntas sobre a documentação que foi previamente 
carregada com o script rag_claude_docs.py.
"""

import json
import argparse
from claude import MCP  # Model Context Protocol

def format_response(response_data):
    """Formata a resposta do LightRAG para exibição."""
    if not response_data:
        return "Sem resposta do servidor."
    
    # Extrai a resposta principal
    response = response_data.get('response', 'Sem resposta gerada.')
    
    # Formata os trechos de contexto usados
    contexts = response_data.get('context', [])
    context_text = ""
    
    if contexts:
        context_text = "\n\n--- Fontes utilizadas ---\n"
        for i, ctx in enumerate(contexts, 1):
            content = ctx.get('content', 'Conteúdo não disponível')
            source = ctx.get('source', 'Fonte desconhecida')
            context_text += f"\n{i}. {source}\n   {content[:150]}...\n"
    
    return f"{response}\n{context_text}"

def main():
    # Configurar argumentos de linha de comando
    parser = argparse.ArgumentParser(description='Consultar LightRAG sobre documentação do Claude Code')
    parser.add_argument('query', nargs='?', default=None, help='A pergunta a ser feita')
    parser.add_argument('--mode', choices=['naive', 'local', 'global', 'hybrid'], default='hybrid',
                      help='Modo de consulta: naive, local, global ou hybrid (padrão)')
    parser.add_argument('--context-only', action='store_true', help='Retornar apenas o contexto sem resposta gerada')
    args = parser.parse_args()
    
    # Se nenhuma consulta for fornecida, solicitar interativamente
    query = args.query
    if not query:
        query = input("Digite sua pergunta sobre o Claude Code: ")
    
    try:
        # Conectar ao serviço LightRAG
        print(f"Conectando ao serviço LightRAG...")
        lightrag_service = MCP.connect_to_service('lightrag')
        
        # Definir parâmetros da consulta
        query_params = {
            "query": query,
            "mode": args.mode,
            "onlyNeedContext": args.context_only
        }
        
        print(f"Consultando LightRAG no modo '{args.mode}'...\n")
        
        # Executar a consulta
        result = lightrag_service.rag_query(**query_params)
        
        # Exibir o resultado formatado
        print("\n--- Resposta ---\n")
        print(format_response(result))
        
        # Exibir resultado bruto em modo de depuração (opcional)
        # print("\n--- Resultado bruto ---\n")
        # print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Erro ao consultar LightRAG: {e}")
        print("\nVerifique se:")
        print("1. O serviço LightRAG Model Context Protocol (MCP) está em execução")
        print("2. A documentação foi previamente carregada com rag_claude_docs.py")
        print("3. O servidor LightRAG está configurado corretamente na porta 8020")

if __name__ == "__main__":
    main()