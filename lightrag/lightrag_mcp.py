#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG MCP Client
Módulo para integrar o LightRAG com o serviço MCP do Claude
"""

import json
import urllib.request
import urllib.parse
import time
import os
import traceback

class LightRAGClient:
    """Cliente Python para o servidor LightRAG"""
    
    def __init__(self, host="127.0.0.1", port=5000):
        self.base_url = f"http://{host}:{port}"
        self.last_error = None
    
    def check_server(self):
        """Verifica se o servidor está online"""
        try:
            result = self._make_request("status")
            return result is not None and result.get("status") == "online"
        except Exception:
            return False
    
    def _make_request(self, endpoint, data=None):
        """Faz uma requisição ao servidor LightRAG"""
        url = f"{self.base_url}/{endpoint}"
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
            self.last_error = str(e)
            return None
    
    def rag_query(self, query, mode="hybrid", max_results=5):
        """
        Consulta a base de conhecimento do LightRAG
        
        Parâmetros:
        - query: texto da consulta
        - mode: modo de consulta (padrão: "hybrid")
        - max_results: número máximo de resultados (padrão: 5)
        
        Retorna:
        - Dicionário com a resposta e contextos encontrados
        """
        if not query:
            return {"error": "Consulta vazia", "context": [], "response": "Consulta vazia"}
        
        data = {
            "query": query,
            "mode": mode,
            "max_results": max_results
        }
        
        result = self._make_request("query", data)
        
        if not result:
            return {
                "error": f"Falha na consulta: {self.last_error}",
                "context": [],
                "response": f"Erro ao conectar ao servidor LightRAG: {self.last_error}"
            }
        
        return result
    
    def rag_insert_text(self, text, source="mcp"):
        """
        Insere texto na base de conhecimento
        
        Parâmetros:
        - text: texto a ser inserido
        - source: identificador da fonte do texto
        
        Retorna:
        - Dicionário com status da operação
        """
        if not text:
            return {"success": False, "error": "Texto vazio"}
        
        data = {
            "text": text,
            "source": source
        }
        
        result = self._make_request("insert", data)
        
        if not result:
            return {"success": False, "error": f"Falha na inserção: {self.last_error}"}
        
        return result
    
    def clear_database(self, confirm=True):
        """
        Limpa toda a base de conhecimento (use com cuidado!)
        
        Parâmetros:
        - confirm: confirmação explícita (padrão: True)
        
        Retorna:
        - Dicionário com status da operação
        """
        data = {"confirm": confirm}
        result = self._make_request("clear", data)
        
        if not result:
            return {"success": False, "error": f"Falha ao limpar: {self.last_error}"}
        
        return result
    
    def get_status(self):
        """
        Obtém status do servidor e da base de conhecimento
        
        Retorna:
        - Dicionário com informações de status
        """
        result = self._make_request("status")
        
        if not result:
            return {"status": "offline", "error": self.last_error}
        
        return result

# Função para MCP do Claude
def rag_query(query, mode="hybrid", max_results=5):
    """Função de consulta para uso via MCP"""
    client = LightRAGClient()
    return client.rag_query(query, mode, max_results)

# Função para MCP do Claude
def rag_insert_text(text, source="mcp"):
    """Função de inserção para uso via MCP"""
    client = LightRAGClient()
    return client.rag_insert_text(text, source)

# Função para MCP do Claude
def rag_status():
    """Função de status para uso via MCP"""
    client = LightRAGClient()
    return client.get_status()

# Função para MCP do Claude
def rag_clear(confirm=True):
    """Função para limpar base para uso via MCP"""
    client = LightRAGClient()
    return client.clear_database(confirm)

# Função auxiliar para iniciar servidor caso não esteja rodando
def ensure_server_running():
    """Garante que o servidor esteja em execução"""
    client = LightRAGClient()
    if not client.check_server():
        print("Servidor LightRAG não está rodando. Tentando iniciar...")
        try:
            # Encontrar o diretório lightrag
            lightrag_dir = os.path.join(os.path.expanduser("~"), ".claude", "lightrag")
            start_script = os.path.join(lightrag_dir, "start_lightrag.sh")
            
            if os.path.exists(start_script):
                os.system(f"bash {start_script} > /dev/null 2>&1 &")
                time.sleep(3)  # Aguardar inicialização
                
                if client.check_server():
                    print("Servidor LightRAG iniciado com sucesso!")
                    return True
                else:
                    print("Falha ao iniciar servidor automaticamente.")
            else:
                print(f"Script de inicialização não encontrado: {start_script}")
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")
            traceback.print_exc()
        
        return False
    return True

# Uso para teste
if __name__ == "__main__":
    # Garantir que o servidor esteja rodando
    if ensure_server_running():
        # Testar funcionalidades
        status = rag_status()
        print(f"Status do servidor: {status}")
        
        # Inserir um documento
        texto = "O LightRAG é um sistema de RAG simplificado para uso com Claude."
        insert_result = rag_insert_text(texto)
        print(f"Inserção: {insert_result}")
        
        # Fazer uma consulta
        query_result = rag_query("O que é LightRAG?")
        print(f"Consulta: {query_result}")
    else:
        print("Não foi possível garantir que o servidor LightRAG esteja rodando.")