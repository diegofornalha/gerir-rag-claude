#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Cliente API
Cliente para interagir com a API LightRAG
"""

import json
import urllib.request
import urllib.parse
import os
import time
import traceback
from typing import Dict, List, Any, Optional, Union

# Importar configurações
from core.settings import SERVER_HOST, SERVER_PORT
from utils.logger import get_core_logger

# Configurar logger
logger = get_core_logger()

class LightRAGClient:
    """Cliente para interagir com o servidor LightRAG"""
    
    def __init__(self, host=None, port=None):
        """
        Inicializa o cliente com o host e porta do servidor
        
        Args:
            host: Host do servidor (default: valor de settings)
            port: Porta do servidor (default: valor de settings)
        """
        self.host = host or SERVER_HOST
        self.port = port or SERVER_PORT
        self.base_url = f"http://{self.host}:{self.port}"
        self.last_error = None
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """
        Faz uma requisição HTTP para o servidor LightRAG
        
        Args:
            endpoint: Endpoint da API (sem barra inicial)
            method: Método HTTP (GET, POST, etc.)
            data: Dados para enviar no corpo da requisição
            
        Retorna:
            Dict: Resposta do servidor ou erro formatado
        """
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
            self.last_error = str(e)
            logger.error(f"Erro de conexão: {str(e)}")
            return {"error": f"Erro de conexão: {str(e)}", "status": "error"}
        except json.JSONDecodeError:
            self.last_error = "Resposta inválida do servidor"
            logger.error("Resposta inválida do servidor")
            return {"error": "Resposta inválida do servidor", "status": "error"}
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erro desconhecido: {str(e)}")
            return {"error": f"Erro desconhecido: {str(e)}", "status": "error"}
    
    def status(self) -> Dict:
        """
        Verifica o status do servidor LightRAG
        
        Retorna:
            Dict: Informações de status
        """
        logger.debug("Verificando status do servidor")
        return self._make_request("status")
    
    def is_online(self) -> bool:
        """
        Verifica se o servidor está online
        
        Retorna:
            bool: True se online, False caso contrário
        """
        try:
            status = self.status()
            return status.get("status") == "online"
        except:
            return False
    
    def query(self, query_text: str, max_results: int = 5, mode: str = "hybrid") -> Dict:
        """
        Realiza uma consulta na base de conhecimento
        
        Args:
            query_text: Texto da consulta
            max_results: Número máximo de resultados
            mode: Modo de busca (hybrid, semantic, keyword)
            
        Retorna:
            Dict: Resultados da consulta
        """
        if not query_text:
            logger.warning("Tentativa de consulta com texto vazio")
            return {"error": "Consulta vazia", "context": [], "response": "Consulta vazia"}
        
        logger.info(f"Consultando: '{query_text}' (modo={mode}, max={max_results})")
        
        data = {
            "query": query_text,
            "max_results": max_results,
            "mode": mode
        }
        
        result = self._make_request("query", "POST", data)
        
        if "error" in result:
            logger.error(f"Erro na consulta: {result['error']}")
        else:
            logger.info(f"Consulta bem-sucedida: {len(result.get('context', []))} resultados")
            
        return result
    
    def insert(self, text: str, summary: Optional[str] = None, source: str = "client", 
               metadata: Optional[Dict] = None) -> Dict:
        """
        Insere um documento na base de conhecimento
        
        Args:
            text: Conteúdo do documento
            summary: Resumo opcional do documento
            source: Fonte do documento
            metadata: Metadados adicionais
            
        Retorna:
            Dict: Resultado da operação
        """
        if not text:
            logger.warning("Tentativa de inserção com texto vazio")
            return {"success": False, "error": "Texto vazio"}
        
        logger.info(f"Inserindo documento: fonte='{source}', tamanho={len(text)}")
        
        data = {
            "text": text,
            "source": source
        }
        
        if summary:
            data["summary"] = summary
            
        if metadata:
            data["metadata"] = metadata
            
        result = self._make_request("insert", "POST", data)
        
        if result.get("success", False):
            logger.info(f"Documento inserido com ID: {result.get('documentId')}")
        else:
            logger.error(f"Erro ao inserir documento: {result.get('error')}")
            
        return result
    
    def delete(self, doc_id: str) -> Dict:
        """
        Remove um documento da base de conhecimento
        
        Args:
            doc_id: ID do documento a ser removido
            
        Retorna:
            Dict: Resultado da operação
        """
        if not doc_id:
            logger.warning("Tentativa de exclusão sem ID")
            return {"success": False, "error": "ID não fornecido"}
        
        logger.info(f"Excluindo documento: ID='{doc_id}'")
        
        data = {"id": doc_id}
        result = self._make_request("delete", "POST", data)
        
        if result.get("success", False):
            logger.info(f"Documento excluído: {doc_id}")
        else:
            logger.error(f"Erro ao excluir documento: {result.get('error')}")
            
        return result
    
    def clear(self, confirm: bool = False) -> Dict:
        """
        Limpa toda a base de conhecimento
        
        Args:
            confirm: Confirmação de segurança
            
        Retorna:
            Dict: Resultado da operação
        """
        if not confirm:
            logger.warning("Tentativa de limpeza sem confirmação")
            return {"success": False, "error": "Confirmação necessária para limpar a base"}
        
        logger.info("Limpando base de conhecimento")
        
        data = {"confirm": True}
        result = self._make_request("clear", "POST", data)
        
        if result.get("success", False):
            logger.info("Base de conhecimento limpa com sucesso")
            if "backup" in result:
                logger.info(f"Backup criado: {result['backup']}")
        else:
            logger.error(f"Erro ao limpar base: {result.get('error')}")
            
        return result

# Função auxiliar para iniciar servidor caso não esteja rodando
def ensure_server_running():
    """
    Garante que o servidor esteja em execução
    
    Retorna:
        bool: True se servidor está rodando, False caso contrário
    """
    client = LightRAGClient()
    if not client.is_online():
        logger.info("Servidor LightRAG não está rodando. Tentando iniciar...")
        try:
            # Encontrar o diretório lightrag
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            start_script = os.path.join(base_dir, "start_flask_lightrag.sh")
            
            if os.path.exists(start_script):
                os.system(f"bash {start_script} > /dev/null 2>&1 &")
                time.sleep(3)  # Aguardar inicialização
                
                if client.is_online():
                    logger.info("Servidor LightRAG iniciado com sucesso!")
                    return True
                else:
                    logger.error("Falha ao iniciar servidor automaticamente.")
            else:
                logger.error(f"Script de inicialização não encontrado: {start_script}")
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor: {str(e)}")
            traceback.print_exc()
        
        return False
    return True