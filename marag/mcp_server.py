#!/usr/bin/env python3
"""
Servidor MCP para Marag - Conecta ao A2A Gateway
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Adicionar o diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from pydantic import BaseModel, EmailStr, Field
    
    class ContactInfo(BaseModel):
        name: str = ""
        email: str = ""
        phone: str = ""
        organization: str = ""
        role: str = ""
        
    # Simular ExtractorAgent
    class ExtractorAgent:
        def __init__(self, instructions, result_type):
            self.instructions = instructions
            self.result_type = result_type
            
except ImportError:
    # Fallback se não conseguir importar
    class ContactInfo:
        def __init__(self):
            self.name = ""
            self.email = ""
            self.phone = ""
            self.organization = ""
            self.role = ""
    
    class ExtractorAgent:
        def __init__(self, instructions, result_type):
            self.instructions = instructions
            self.result_type = result_type


class MaragMCPServer:
    """Servidor MCP para Marag Agent"""
    
    def __init__(self):
        self.initialized = False
        self.tools = {
            "extract_contact": {
                "name": "extract_contact",
                "description": "Extrai informações de contato estruturadas do texto",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Texto contendo informações de contato"
                        }
                    },
                    "required": ["text"]
                }
            },
            "save_to_rag": {
                "name": "save_to_rag",
                "description": "Salva informações extraídas no RAG",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Título do documento"
                        },
                        "content": {
                            "type": "string",
                            "description": "Conteúdo a ser salvo"
                        },
                        "source": {
                            "type": "string",
                            "description": "Fonte dos dados"
                        }
                    },
                    "required": ["title", "content"]
                }
            },
            "search_rag": {
                "name": "search_rag",
                "description": "Busca informações no RAG",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query de busca"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Limite de resultados"
                        }
                    },
                    "required": ["query"]
                }
            },
            "get_rag_stats": {
                "name": "get_rag_stats",
                "description": "Obtém estatísticas do RAG",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
        
        # Inicializar agente
        try:
            self.agent = ExtractorAgent(
                instructions="Extraia informações de contato do texto fornecido de forma estruturada.",
                result_type=ContactInfo
            )
        except Exception as e:
            print(f"⚠️  Erro ao inicializar agente: {e}", file=sys.stderr)
            self.agent = None
    
    def initialize(self) -> Dict[str, Any]:
        """Inicializa o servidor MCP"""
        self.initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "marag-mcp-server",
                "version": "1.0.0"
            }
        }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Lista as ferramentas disponíveis"""
        return list(self.tools.values())
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executa uma ferramenta"""
        
        if name == "extract_contact":
            return self._extract_contact(arguments)
        elif name == "save_to_rag":
            return self._save_to_rag(arguments)
        elif name == "search_rag":
            return self._search_rag(arguments)
        elif name == "get_rag_stats":
            return self._get_rag_stats(arguments)
        else:
            raise ValueError(f"Ferramenta desconhecida: {name}")
    
    def _extract_contact(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai informações de contato"""
        try:
            text = arguments.get("text", "")
            
            if not self.agent:
                return {
                    "error": "Agente não inicializado",
                    "extracted_data": None
                }
            
            # Simular extração (em produção, usar o agente real)
            import re
            
            # Extrair email
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            email = email_match.group() if email_match else ""
            
            # Extrair nome (simples)
            name_match = re.search(r'meu nome é (\w+)', text, re.IGNORECASE)
            name = name_match.group(1) if name_match else "Nome não encontrado"
            
            # Extrair telefone
            phone_match = re.search(r'\(?\d{2,3}\)?\s*\d{4,5}-?\d{4}', text)
            phone = phone_match.group() if phone_match else ""
            
            extracted_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "organization": "",
                "role": ""
            }
            
            return {
                "extracted_data": extracted_data,
                "summary": f"Extraído contato de {name} ({email})"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "extracted_data": None
            }
    
    def _save_to_rag(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Salva informações no RAG"""
        try:
            title = arguments.get("title", "")
            content = arguments.get("content", "")
            source = arguments.get("source", "marag_mcp")
            
            # Salvar no cache RAG
            rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
            
            documents = []
            if rag_cache_path.exists():
                with open(rag_cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    documents = data.get('documents', [])
            
            new_doc = {
                "id": f"doc_marag_mcp_{int(time.time() * 1000)}",
                "title": title,
                "content": content,
                "type": "contact_extraction",
                "source": source,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "metadata": {
                    "extracted_by": "marag_mcp",
                    "method": "mcp_server"
                }
            }
            
            documents.append(new_doc)
            
            rag_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(rag_cache_path, 'w', encoding='utf-8') as f:
                json.dump({'documents': documents}, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "document_id": new_doc["id"],
                "message": f"Documento salvo: {title}"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def _search_rag(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Busca no RAG"""
        try:
            query = arguments.get("query", "")
            limit = arguments.get("limit", 5)
            
            rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
            
            if not rag_cache_path.exists():
                return {
                    "results": [],
                    "total": 0
                }
            
            with open(rag_cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                documents = data.get('documents', [])
            
            # Busca simples por texto
            results = []
            query_lower = query.lower()
            
            for doc in documents:
                content = f"{doc.get('title', '')} {doc.get('content', '')}".lower()
                if query_lower in content:
                    results.append({
                        "id": doc.get("id"),
                        "title": doc.get("title"),
                        "content": doc.get("content")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content"),
                        "source": doc.get("source"),
                        "created_at": doc.get("created_at")
                    })
            
            return {
                "results": results[:limit],
                "total": len(results),
                "query": query
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "results": []
            }
    
    def _get_rag_stats(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Obtém estatísticas do RAG"""
        try:
            rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
            
            if not rag_cache_path.exists():
                return {
                    "total_documents": 0,
                    "marag_documents": 0,
                    "cache_size": 0
                }
            
            with open(rag_cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                documents = data.get('documents', [])
            
            marag_docs = [doc for doc in documents if doc.get('source', '').startswith('marag')]
            
            return {
                "total_documents": len(documents),
                "marag_documents": len(marag_docs),
                "cache_size": rag_cache_path.stat().st_size if rag_cache_path.exists() else 0
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Processa uma requisição MCP"""
        
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                result = self.initialize()
            elif method == "tools/list":
                result = {"tools": self.list_tools()}
            elif method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments", {})
                result = self.call_tool(name, arguments)
            else:
                result = {"error": f"Método não suportado: {method}"}
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }


def main():
    """Função principal do servidor MCP"""
    
    server = MaragMCPServer()
    
    print("🚀 Servidor MCP Marag iniciado", file=sys.stderr)
    print("📊 Ferramentas disponíveis:", file=sys.stderr)
    for tool in server.list_tools():
        print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)
    print(file=sys.stderr)
    
    # Loop principal
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {e}"
                }
            }))
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {e}"
                }
            }))


if __name__ == "__main__":
    main() 