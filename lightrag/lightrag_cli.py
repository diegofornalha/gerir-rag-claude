#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG CLI - Interface completa de linha de comando para o LightRAG
Esta ferramenta fornece acesso completo às funcionalidades do LightRAG via terminal
"""

import json
import urllib.request
import urllib.parse
import sys
import os
import argparse
import datetime
import time
import re
import textwrap
from typing import Dict, List, Any, Optional, Union

# Cores ANSI para formatação do terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class LightRAGClient:
    """Cliente para interagir com o servidor LightRAG"""
    
    def __init__(self, host="127.0.0.1", port=5000):
        """Inicializa o cliente com o host e porta do servidor"""
        self.base_url = f"http://{host}:{port}"
        self.host = host
        self.port = port
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Faz uma requisição HTTP para o servidor LightRAG"""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if data and method in ["POST", "PUT"]:
                encoded_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(
                    url, 
                    data=encoded_data,
                    headers=headers,
                    method=method
                )
            else:
                req = urllib.request.Request(url, headers=headers, method=method)
                
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            return {"error": f"Erro de conexão: {str(e)}", "status": "error"}
        except json.JSONDecodeError:
            return {"error": "Resposta inválida do servidor", "status": "error"}
        except Exception as e:
            return {"error": f"Erro desconhecido: {str(e)}", "status": "error"}
    
    def status(self) -> Dict:
        """Verifica o status do servidor LightRAG"""
        return self._make_request("status")
    
    def query(self, query_text: str, max_results: int = 5, mode: str = "hybrid") -> Dict:
        """
        Realiza uma consulta na base de conhecimento
        
        Parâmetros:
        - query_text: Texto da consulta
        - max_results: Número máximo de resultados
        - mode: Modo de busca (hybrid, semantic, keyword)
        
        Retorna:
        - Dict com os resultados da consulta
        """
        data = {
            "query": query_text,
            "max_results": max_results,
            "mode": mode
        }
        return self._make_request("query", "POST", data)
    
    def insert(self, text: str, summary: Optional[str] = None, source: str = "cli", 
               tags: Optional[List[str]] = None) -> Dict:
        """
        Insere um documento na base de conhecimento
        
        Parâmetros:
        - text: Conteúdo do documento
        - summary: Resumo opcional do documento
        - source: Fonte do documento
        - tags: Lista de tags para categorização
        
        Retorna:
        - Dict com o resultado da operação
        """
        data = {
            "text": text,
            "source": source
        }
        
        if summary:
            data["summary"] = summary
            
        if tags:
            data["tags"] = tags
            
        return self._make_request("insert", "POST", data)
    
    def delete(self, doc_id: str) -> Dict:
        """
        Remove um documento da base de conhecimento
        
        Parâmetros:
        - doc_id: ID do documento a ser removido
        
        Retorna:
        - Dict com o resultado da operação
        """
        data = {"id": doc_id}
        return self._make_request("delete", "POST", data)
    
    def clear(self, confirm: bool = False) -> Dict:
        """
        Limpa toda a base de conhecimento
        
        Parâmetros:
        - confirm: Confirmação de segurança
        
        Retorna:
        - Dict com o resultado da operação
        """
        if not confirm:
            return {"error": "Confirmação necessária para limpar a base", "status": "error"}
        
        data = {"confirm": True}
        return self._make_request("clear", "POST", data)
    
    def is_online(self) -> bool:
        """Verifica se o servidor está online"""
        try:
            status = self.status()
            return status.get("status") == "online"
        except:
            return False

class LightRAGFormatter:
    """Formatador para saídas do LightRAG no terminal"""
    
    @staticmethod
    def format_status(status: Dict) -> str:
        """Formata informações de status do servidor"""
        if "error" in status:
            return f"{Colors.RED}Erro: {status['error']}{Colors.ENDC}"
        
        if status.get("status") == "online":
            output = [
                f"{Colors.GREEN}=== Servidor LightRAG ===",
                f"✓ Status: {Colors.BOLD}ONLINE{Colors.ENDC}{Colors.GREEN}",
                f"✓ Documentos: {status.get('documents', 0)}",
                f"✓ Última atualização: {status.get('lastUpdated', 'N/A')}{Colors.ENDC}"
            ]
        else:
            output = [
                f"{Colors.RED}=== Servidor LightRAG ===",
                f"✗ Status: {Colors.BOLD}OFFLINE{Colors.ENDC}{Colors.RED}",
                f"✗ Erro: {status.get('error', 'Desconhecido')}{Colors.ENDC}"
            ]
        
        return "\n".join(output)
    
    @staticmethod
    def format_query_result(result: Dict, verbose: bool = False) -> str:
        """Formata os resultados de uma consulta"""
        if "error" in result:
            return f"{Colors.RED}Erro: {result['error']}{Colors.ENDC}"
        
        # Cabeçalho da resposta
        output = [f"{Colors.BLUE}=== Resultado da Consulta ==={Colors.ENDC}"]
        output.append(f"{Colors.BOLD}{result.get('response', 'Sem resposta')}{Colors.ENDC}")
        
        # Processar contextos
        contexts = result.get('context', [])
        if contexts:
            output.append(f"\n{Colors.CYAN}Contextos encontrados ({len(contexts)}):{Colors.ENDC}")
            
            for i, ctx in enumerate(contexts):
                relevance = ctx.get('relevance', 0) * 100  # Converter para porcentagem
                source = ctx.get('source', 'desconhecido')
                doc_id = ctx.get('document_id', 'doc_unknown')
                content = ctx.get('content', '')
                
                # Determinar cor com base na relevância
                if relevance >= 70:
                    rel_color = Colors.GREEN
                elif relevance >= 40:
                    rel_color = Colors.YELLOW
                else:
                    rel_color = Colors.RED
                
                # Formatar cabeçalho do contexto
                output.append(f"{Colors.BOLD}{i+1}. [{source}]{Colors.ENDC} " +
                             f"({rel_color}Relevância: {relevance:.0f}%{Colors.ENDC})")
                
                # Formatar conteúdo
                if verbose:
                    # Exibir conteúdo completo em modo verbose
                    wrapped_content = textwrap.fill(content, width=100, 
                                                   initial_indent="   ", subsequent_indent="   ")
                    output.append(f"{wrapped_content}")
                else:
                    # Exibir conteúdo resumido
                    preview = content[:150] + ("..." if len(content) > 150 else "")
                    wrapped_preview = textwrap.fill(preview, width=100, 
                                                  initial_indent="   ", subsequent_indent="   ")
                    output.append(f"{wrapped_preview}")
                
                output.append("")  # Linha em branco entre contextos
        else:
            output.append(f"\n{Colors.YELLOW}Nenhum contexto relevante encontrado.{Colors.ENDC}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_insert_result(result: Dict) -> str:
        """Formata o resultado de uma inserção"""
        if result.get("success", False):
            output = [
                f"{Colors.GREEN}=== Documento Inserido ===",
                f"✓ Documento inserido com sucesso!",
                f"✓ ID: {result.get('documentId', 'desconhecido')}{Colors.ENDC}"
            ]
        else:
            output = [
                f"{Colors.RED}=== Erro ao Inserir Documento ===",
                f"✗ {result.get('error', 'Erro desconhecido')}{Colors.ENDC}"
            ]
        
        return "\n".join(output)
    
    @staticmethod
    def format_delete_result(result: Dict) -> str:
        """Formata o resultado de uma exclusão"""
        if result.get("success", False):
            output = [
                f"{Colors.GREEN}=== Documento Removido ===",
                f"✓ {result.get('message', 'Documento removido com sucesso')}{Colors.ENDC}"
            ]
        else:
            output = [
                f"{Colors.RED}=== Erro ao Remover Documento ===",
                f"✗ {result.get('error', 'Erro desconhecido')}{Colors.ENDC}"
            ]
        
        return "\n".join(output)
    
    @staticmethod
    def format_clear_result(result: Dict) -> str:
        """Formata o resultado de uma limpeza da base"""
        if result.get("success", False):
            output = [
                f"{Colors.GREEN}=== Base de Conhecimento Limpa ===",
                f"✓ {result.get('message', 'Base de conhecimento limpa com sucesso')}"
            ]
            if "backup" in result:
                output.append(f"✓ Backup criado em: {result['backup']}{Colors.ENDC}")
            else:
                output.append(f"{Colors.ENDC}")
        else:
            output = [
                f"{Colors.RED}=== Erro ao Limpar Base de Conhecimento ===",
                f"✗ {result.get('error', 'Erro desconhecido')}{Colors.ENDC}"
            ]
        
        return "\n".join(output)
    
    @staticmethod
    def print_banner() -> str:
        """Retorna o banner do LightRAG CLI"""
        banner = f"""
{Colors.CYAN}╭───────────────────────────────────────────────╮
│  {Colors.BOLD}LightRAG CLI{Colors.ENDC}{Colors.CYAN} - Retrieval Augmented Generation  │
│  Versão 1.0.0                                 │
╰───────────────────────────────────────────────╯{Colors.ENDC}
"""
        return banner
    
    @staticmethod
    def print_help() -> str:
        """Exibe informações de ajuda"""
        help_text = f"""
{Colors.CYAN}=== Comandos Disponíveis ==={Colors.ENDC}

{Colors.BOLD}status{Colors.ENDC}
  Verifica o status do servidor LightRAG
  {Colors.YELLOW}Exemplo: lightrag_cli.py status{Colors.ENDC}

{Colors.BOLD}query{Colors.ENDC} <texto da consulta>
  Consulta a base de conhecimento
  Opções:
    --max <num>   Número máximo de resultados (padrão: 5)
    --mode <modo> Modo de busca: hybrid, semantic, keyword (padrão: hybrid)
    --verbose     Exibe o conteúdo completo dos resultados
  {Colors.YELLOW}Exemplo: lightrag_cli.py query "O que é LightRAG?" --max 3{Colors.ENDC}

{Colors.BOLD}insert{Colors.ENDC} <texto>
  Insere um documento na base de conhecimento
  Opções:
    --summary <resumo>    Resumo do documento
    --source <origem>     Origem do documento (padrão: cli)
    --tags <tag1,tag2>    Tags para categorização
    --file <arquivo>      Ler conteúdo de um arquivo
  {Colors.YELLOW}Exemplo: lightrag_cli.py insert "LightRAG é um sistema de RAG" --summary "Descrição"{Colors.ENDC}

{Colors.BOLD}delete{Colors.ENDC} <id_documento>
  Remove um documento da base de conhecimento
  {Colors.YELLOW}Exemplo: lightrag_cli.py delete doc_1234567890{Colors.ENDC}

{Colors.BOLD}clear{Colors.ENDC}
  Limpa toda a base de conhecimento (requer confirmação)
  {Colors.YELLOW}Exemplo: lightrag_cli.py clear --confirm{Colors.ENDC}
"""
        return help_text

class LightRAGCLI:
    """Interface de linha de comando para o LightRAG"""
    
    def __init__(self):
        """Inicializa a CLI"""
        self.client = LightRAGClient()
        self.formatter = LightRAGFormatter()
    
    def parse_args(self):
        """Analisa os argumentos da linha de comando"""
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
        """Executa o comando especificado pelos argumentos"""
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
            
            # Processar tags
            tags = None
            if args.tags:
                tags = [tag.strip() for tag in args.tags.split(",")]
                
            # Inserir documento
            result = self.client.insert(text, args.summary, args.source, tags)
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
            self.execute_command(args)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Operação interrompida pelo usuário.{Colors.ENDC}")
            sys.exit(0)
        except Exception as e:
            print(f"{Colors.RED}Erro inesperado: {str(e)}{Colors.ENDC}")
            sys.exit(1)

if __name__ == "__main__":
    cli = LightRAGCLI()
    cli.run()