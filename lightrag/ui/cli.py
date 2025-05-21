#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG CLI - Interface de linha de comando
Implementa a interface para acesso via terminal ao LightRAG
"""

import argparse
import sys
import time
import os
from typing import Dict, List, Any, Optional

# Importar componentes LightRAG
from core.client import LightRAGClient, ensure_server_running
from utils.formatters import CLIFormatter, Colors
from utils.logger import get_cli_logger

# Configurar logger
logger = get_cli_logger()

class LightRAGCLI:
    """Interface de linha de comando para o LightRAG"""
    
    def __init__(self):
        """Inicializa a CLI"""
        self.client = LightRAGClient()
        self.formatter = CLIFormatter()
    
    def parse_args(self):
        """
        Analisa os argumentos da linha de comando
        
        Retorna:
            argparse.Namespace: Argumentos parseados
        """
        parser = argparse.ArgumentParser(
            description="Interface de linha de comando para o LightRAG",
            add_help=False  # Desabilita ajuda automática para usar nossa própria formatação
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
        
        # Comando HELP
        help_parser = subparsers.add_parser("help", help="Exibe ajuda detalhada")
        
        # Comando STATUS
        status_parser = subparsers.add_parser("status", help="Verificar status do servidor")
        
        # Comando QUERY
        query_parser = subparsers.add_parser("query", help="Consultar a base de conhecimento")
        query_parser.add_argument("text", help="Texto da consulta")
        query_parser.add_argument("--max", type=int, default=5, help="Número máximo de resultados")
        query_parser.add_argument("--mode", choices=["hybrid", "semantic", "keyword"], 
                                default="hybrid", help="Modo de busca")
        query_parser.add_argument("--verbose", "-v", action="store_true", 
                                help="Exibir resultados detalhados")
        
        # Comando INSERT
        insert_parser = subparsers.add_parser("insert", help="Inserir documento na base de conhecimento")
        
        # Grupo mutuamente exclusivo: texto ou arquivo
        insert_group = insert_parser.add_mutually_exclusive_group(required=True)
        insert_group.add_argument("text", nargs="?", help="Texto do documento")
        insert_group.add_argument("--file", "-f", help="Arquivo contendo o texto do documento")
        
        insert_parser.add_argument("--summary", "-s", help="Resumo do documento")
        insert_parser.add_argument("--source", default="cli", help="Fonte do documento")
        insert_parser.add_argument("--tags", help="Tags separadas por vírgula")
        
        # Comando DELETE
        delete_parser = subparsers.add_parser("delete", help="Remover documento da base de conhecimento")
        delete_parser.add_argument("id", help="ID do documento a ser removido")
        
        # Comando CLEAR
        clear_parser = subparsers.add_parser("clear", help="Limpar toda a base de conhecimento")
        clear_parser.add_argument("--confirm", action="store_true", help="Confirmar limpeza da base")
        
        # Parâmetros globais (para todos os comandos)
        parser.add_argument("--host", default="127.0.0.1", help="Host do servidor LightRAG")
        parser.add_argument("--port", type=int, default=5000, help="Porta do servidor LightRAG")
        
        # Processar argumentos
        args = parser.parse_args()
        
        # Se nenhum comando foi especificado ou ajuda foi solicitada, mostrar banner e ajuda
        if not args.command or args.command == "help":
            print(self.formatter.print_banner())
            print(self.formatter.print_help())
            sys.exit(0)
        
        # Atualizar configuração do cliente se host/porta foram especificados
        if args.host != "127.0.0.1" or args.port != 5000:
            self.client = LightRAGClient(host=args.host, port=args.port)
        
        return args
    
    def execute_command(self, args):
        """
        Executa o comando especificado pelos argumentos
        
        Args:
            args: Argumentos parseados da linha de comando
        """
        # Verificar se o servidor está online (exceto para comando status)
        if args.command != "status" and not self.client.is_online():
            print(f"{Colors.RED}Erro: Servidor LightRAG não está acessível em {self.client.host}:{self.client.port}{Colors.ENDC}")
            print(f"{Colors.YELLOW}Certifique-se de que o servidor está rodando com: ./start_lightrag.sh{Colors.ENDC}")
            sys.exit(1)
        
        # Executar o comando apropriado
        if args.command == "status":
            result = self.client.status()
            print(self.formatter.format_status(result))
            
        elif args.command == "query":
            start_time = time.time()
            result = self.client.query(args.text, args.max, args.mode)
            elapsed = time.time() - start_time
            print(self.formatter.format_query_result(result, args.verbose))
            print(f"{Colors.BLUE}Consulta executada em {elapsed:.2f} segundos{Colors.ENDC}")
            
        elif args.command == "insert":
            # Obter texto do documento
            if args.file:
                try:
                    with open(args.file, 'r', encoding='utf-8') as f:
                        text = f.read()
                except Exception as e:
                    print(f"{Colors.RED}Erro ao ler arquivo: {str(e)}{Colors.ENDC}")
                    sys.exit(1)
            else:
                text = args.text
            
            # Processar metadados
            metadata = None
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(",")]
                metadata = {"tags": tags}
                
            # Inserir documento
            result = self.client.insert(text, args.summary, args.source, metadata)
            print(self.formatter.format_insert_result(result))
            
        elif args.command == "delete":
            result = self.client.delete(args.id)
            print(self.formatter.format_delete_result(result))
            
        elif args.command == "clear":
            if not args.confirm:
                confirm = input(f"{Colors.YELLOW}ATENÇÃO: Isso irá remover TODOS os documentos. Confirma? (s/N): {Colors.ENDC}")
                if confirm.lower() not in ["s", "sim", "y", "yes"]:
                    print(f"{Colors.BLUE}Operação cancelada pelo usuário.{Colors.ENDC}")
                    sys.exit(0)
            
            result = self.client.clear(True)
            print(self.formatter.format_clear_result(result))
    
    def run(self):
        """Executa a CLI"""
        try:
            args = self.parse_args()
            logger.info(f"Executando comando: {args.command}")
            self.execute_command(args)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Operação interrompida pelo usuário.{Colors.ENDC}")
            logger.info("Operação interrompida pelo usuário")
            sys.exit(0)
        except Exception as e:
            print(f"{Colors.RED}Erro inesperado: {str(e)}{Colors.ENDC}")
            logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
            sys.exit(1)

def main():
    """Função principal para iniciar a CLI"""
    cli = LightRAGCLI()
    cli.run()

# Se for executado diretamente
if __name__ == "__main__":
    main()