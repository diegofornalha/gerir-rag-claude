#!/usr/bin/env python3
"""
Marag Hybrid Agent - Integração A2A + MCP
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Simulação das bibliotecas A2A e MCP
class A2AServer:
    """Servidor A2A para comunicação com outros agentes"""
    
    def __init__(self, name: str, skills: List[str]):
        self.name = name
        self.skills = skills
        self.is_running = False
    
    async def start(self, host: str = "localhost", port: int = 10031):
        """Inicia o servidor A2A"""
        self.is_running = True
        print(f"🚀 Servidor A2A '{self.name}' iniciado em {host}:{port}")
        print(f"📊 Skills disponíveis: {', '.join(self.skills)}")
    
    async def stop(self):
        """Para o servidor A2A"""
        self.is_running = False
        print("✅ Servidor A2A parado")
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Processa mensagem A2A"""
        role = message.get("role", "user")
        parts = message.get("parts", [])
        
        print(f"📨 Mensagem A2A recebida de {role}")
        
        # Extrai texto da mensagem
        text_content = ""
        for part in parts:
            if part.get("kind") == "text":
                text_content += part.get("text", "")
        
        return {
            "messageId": f"response_{int(time.time() * 1000)}",
            "role": "agent",
            "parts": [
                {
                    "kind": "text",
                    "text": f"Processei sua mensagem: {text_content}"
                }
            ]
        }


class MCPClient:
    """Cliente MCP para acesso a ferramentas"""
    
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = config_path
        self.sessions = {}
        self.is_connected = False
    
    async def create_all_sessions(self):
        """Cria sessões com todos os servidores MCP"""
        self.is_connected = True
        print("🔧 Conectado aos servidores MCP")
        
        # Simula conexão com servidores
        self.sessions = {
            "rag": RAGSession(),
            "database": DatabaseSession(),
            "filesystem": FilesystemSession()
        }
    
    async def close_all_sessions(self):
        """Fecha todas as sessões MCP"""
        self.sessions.clear()
        self.is_connected = False
        print("✅ Sessões MCP fechadas")
    
    def get_session(self, name: str):
        """Obtém uma sessão específica"""
        return self.sessions.get(name)


class RAGSession:
    """Sessão MCP para RAG"""
    
    async def save_document(self, title: str, content: str, source: str = "marag_a2a"):
        """Salva documento no RAG"""
        rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
        
        documents = []
        if rag_cache_path.exists():
            with open(rag_cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                documents = data.get('documents', [])
        
        new_doc = {
            "id": f"doc_marag_a2a_{int(time.time() * 1000)}",
            "title": title,
            "content": content,
            "type": "contact_extraction",
            "source": source,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "metadata": {
                "extracted_by": "marag_a2a",
                "method": "hybrid_agent"
            }
        }
        
        documents.append(new_doc)
        
        rag_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(rag_cache_path, 'w', encoding='utf-8') as f:
            json.dump({'documents': documents}, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "document_id": new_doc["id"]}
    
    async def search_documents(self, query: str, limit: int = 5):
        """Busca documentos no RAG"""
        rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
        
        if not rag_cache_path.exists():
            return {"results": [], "total": 0}
        
        with open(rag_cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            documents = data.get('documents', [])
        
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
        
        return {"results": results[:limit], "total": len(results)}


class DatabaseSession:
    """Sessão MCP para banco de dados"""
    
    async def query(self, sql: str):
        """Executa query SQL"""
        print(f"🗄️  Executando query: {sql}")
        # Simula resultado
        return {
            "success": True,
            "data": [
                {"id": 1, "name": "João Silva", "email": "joao@exemplo.com"},
                {"id": 2, "name": "Maria Santos", "email": "maria@exemplo.com"}
            ]
        }


class FilesystemSession:
    """Sessão MCP para sistema de arquivos"""
    
    async def write_file(self, path: str, content: str):
        """Escreve arquivo"""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"success": True, "path": str(file_path)}
    
    async def read_file(self, path: str):
        """Lê arquivo"""
        file_path = Path(path)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content}
        else:
            return {"success": False, "error": "Arquivo não encontrado"}


@dataclass
class A2AMessage:
    """Estrutura de mensagem A2A"""
    role: str
    parts: List[Dict[str, Any]]
    messageId: str
    contextId: Optional[str] = None


@dataclass
class A2AResponse:
    """Estrutura de resposta A2A"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MaragHybridAgent:
    """Agente híbrido Marag que integra A2A e MCP"""
    
    def __init__(self):
        # A2A Server para comunicação com outros agentes
        self.a2a_server = A2AServer(
            name="marag",
            skills=["contact_extraction", "data_analysis", "rag_operations"]
        )
        
        # MCP Client para acesso a ferramentas
        self.mcp_client = MCPClient("mcp_config.json")
        
        # Estado do agente
        self.is_running = False
    
    async def start(self):
        """Inicia o agente híbrido"""
        print("🚀 Iniciando Marag Hybrid Agent...")
        
        # Inicia servidor A2A
        await self.a2a_server.start(host="localhost", port=10031)
        
        # Conecta MCP
        await self.mcp_client.create_all_sessions()
        
        self.is_running = True
        print("✅ Marag Hybrid Agent iniciado com sucesso!")
        print("📊 Capacidades:")
        print("  - A2A: Comunicação com outros agentes")
        print("  - MCP: Acesso a RAG, Database, Filesystem")
    
    async def stop(self):
        """Para o agente híbrido"""
        print("🛑 Parando Marag Hybrid Agent...")
        
        # Para servidor A2A
        await self.a2a_server.stop()
        
        # Fecha sessões MCP
        await self.mcp_client.close_all_sessions()
        
        self.is_running = False
        print("✅ Marag Hybrid Agent parado")
    
    async def handle_a2a_request(self, request: A2AMessage) -> A2AResponse:
        """Processa requisição A2A usando MCP internamente"""
        
        try:
            # Extrai texto da mensagem
            text_content = ""
            for part in request.parts:
                if part.get("kind") == "text":
                    text_content += part.get("text", "")
            
            print(f"📨 Processando requisição A2A: {text_content[:50]}...")
            
            # Determina ação baseada no conteúdo
            if "extrair" in text_content.lower() or "contato" in text_content.lower():
                return await self._handle_contact_extraction(text_content)
            
            elif "buscar" in text_content.lower() or "procurar" in text_content.lower():
                return await self._handle_rag_search(text_content)
            
            elif "salvar" in text_content.lower() or "guardar" in text_content.lower():
                return await self._handle_save_operation(text_content)
            
            else:
                return A2AResponse(
                    success=True,
                    data={"message": f"Processei sua mensagem: {text_content}"}
                )
        
        except Exception as e:
            return A2AResponse(
                success=False,
                error=f"Erro ao processar requisição: {str(e)}"
            )
    
    async def _handle_contact_extraction(self, text: str) -> A2AResponse:
        """Processa extração de contato via MCP"""
        print("🔍 Extraindo contato...")
        
        # Simula extração de contato
        import re
        
        # Extrair email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        email = email_match.group() if email_match else ""
        
        # Extrair nome
        name_match = re.search(r'meu nome é (\w+)', text, re.IGNORECASE)
        name = name_match.group(1) if name_match else "Nome não encontrado"
        
        # Salvar no RAG via MCP
        rag_session = self.mcp_client.get_session("rag")
        result = await rag_session.save_document(
            title=f"Contato - {name}",
            content=f"Nome: {name}\nEmail: {email}\nTexto original: {text}",
            source="marag_a2a_extraction"
        )
        
        return A2AResponse(
            success=True,
            data={
                "extracted_contact": {
                    "name": name,
                    "email": email
                },
                "saved_to_rag": result
            }
        )
    
    async def _handle_rag_search(self, text: str) -> A2AResponse:
        """Processa busca no RAG via MCP"""
        print("🔍 Buscando no RAG...")
        
        # Extrai query da mensagem
        query = text.replace("buscar", "").replace("procurar", "").strip()
        
        rag_session = self.mcp_client.get_session("rag")
        result = await rag_session.search_documents(query, limit=5)
        
        return A2AResponse(
            success=True,
            data={
                "search_results": result["results"],
                "total_found": result["total"],
                "query": query
            }
        )
    
    async def _handle_save_operation(self, text: str) -> A2AResponse:
        """Processa operação de salvamento via MCP"""
        print("💾 Salvando dados...")
        
        # Simula salvamento em arquivo
        fs_session = self.mcp_client.get_session("filesystem")
        
        # Gera nome de arquivo baseado no timestamp
        filename = f"marag_data_{int(time.time())}.txt"
        
        result = await fs_session.write_file(
            path=f"/tmp/{filename}",
            content=f"Dados salvos em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n{text}"
        )
        
        return A2AResponse(
            success=True,
            data={
                "saved_file": result,
                "message": f"Dados salvos em {filename}"
            }
        )
    
    async def run_demo(self):
        """Executa demonstração do agente híbrido"""
        print("\n🎯 Demonstração Marag Hybrid Agent")
        print("=" * 50)
        
        # Simula mensagens A2A
        demo_messages = [
            A2AMessage(
                role="user",
                parts=[{"kind": "text", "text": "Extraia o contato: Meu nome é João Silva, email: joao@exemplo.com"}],
                messageId="demo_1"
            ),
            A2AMessage(
                role="user",
                parts=[{"kind": "text", "text": "Busque informações sobre João Silva"}],
                messageId="demo_2"
            ),
            A2AMessage(
                role="user",
                parts=[{"kind": "text", "text": "Salve estes dados importantes para análise"}],
                messageId="demo_3"
            )
        ]
        
        for i, message in enumerate(demo_messages, 1):
            print(f"\n📝 Demo {i}: {message.parts[0]['text']}")
            response = await self.handle_a2a_request(message)
            
            if response.success:
                print(f"✅ Resposta: {response.data}")
            else:
                print(f"❌ Erro: {response.error}")
        
        print("\n🎉 Demonstração concluída!")


async def main():
    """Função principal"""
    agent = MaragHybridAgent()
    
    try:
        # Inicia o agente
        await agent.start()
        
        # Executa demonstração
        await agent.run_demo()
        
        # Mantém rodando por um tempo
        print("\n⏳ Agente rodando por 30 segundos...")
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
    
    finally:
        # Para o agente
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main()) 