#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Formatadores
Módulo contendo formatadores de saída para diferentes interfaces
"""

from typing import Dict, List, Any, Optional, Union
import textwrap

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

class CLIFormatter:
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

class APIFormatter:
    """Formatador para respostas da API"""
    
    @staticmethod
    def format_error(message: str, status_code: int = 400) -> Dict:
        """
        Formata uma mensagem de erro para a API
        
        Args:
            message: Mensagem de erro
            status_code: Código de status HTTP
            
        Retorna:
            Dict: Resposta formatada
        """
        return {
            "success": False,
            "error": message,
            "status_code": status_code
        }
    
    @staticmethod
    def format_success(message: str, data: Optional[Dict] = None) -> Dict:
        """
        Formata uma mensagem de sucesso para a API
        
        Args:
            message: Mensagem de sucesso
            data: Dados adicionais para incluir na resposta
            
        Retorna:
            Dict: Resposta formatada
        """
        response = {
            "success": True,
            "message": message
        }
        
        if data:
            response.update(data)
            
        return response
    
    @staticmethod
    def format_query_response(query: str, contexts: List[Dict]) -> Dict:
        """
        Formata uma resposta de consulta para a API
        
        Args:
            query: Texto da consulta
            contexts: Lista de contextos relevantes
            
        Retorna:
            Dict: Resposta formatada
        """
        if contexts:
            response_message = f'Com base no conhecimento disponível, aqui está a resposta para: "{query}"'
        else:
            response_message = f'Resposta para: "{query}"'
            
        return {
            "response": response_message,
            "context": contexts
        }