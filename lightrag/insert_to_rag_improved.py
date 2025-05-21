#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Código melhorado para executar rag_insert_file via MCP
# Inclui verificação avançada de documentos duplicados

import json
import argparse
import sys
from claude import MCP

def insert_file_to_lightrag(file_path, force=False, max_lines=100):
    """
    Insere um arquivo no LightRAG usando a implementação melhorada
    
    Parâmetros:
    - file_path: Caminho do arquivo a ser inserido
    - force: Forçar inserção mesmo se for detectado como duplicado
    - max_lines: Número máximo de linhas a processar do arquivo
    """
    try:
        # Conectar ao serviço lightrag
        lightrag_service = MCP.connect_to_service('lightrag')
        
        # Parâmetros para o comando
        params = {
            "file_path": file_path,
            "force": force,
            "max_lines": max_lines
        }
        
        # Executar comando
        resultado = lightrag_service.rag_insert_file(**params)
        
        # Exibir resultado formatado
        print(f"Resultado da operação rag_insert_file:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        # Retornar status da operação
        return resultado.get("success", False)
        
    except Exception as e:
        print(f"Erro ao inserir arquivo: {e}")
        print("Verifique se o servidor LightRAG está em execução na porta 5000")
        print("Para iniciar: python micro_lightrag.py")
        return False

def main():
    parser = argparse.ArgumentParser(description="Insere um arquivo no LightRAG com verificação avançada de duplicação")
    parser.add_argument("file_path", help="Caminho do arquivo a ser inserido")
    parser.add_argument("--force", action="store_true", help="Forçar inserção mesmo se for duplicado")
    parser.add_argument("--max-lines", type=int, default=100, help="Número máximo de linhas a processar (padrão: 100)")
    
    args = parser.parse_args()
    
    success = insert_file_to_lightrag(args.file_path, args.force, args.max_lines)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()