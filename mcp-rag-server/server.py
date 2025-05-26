#!/usr/bin/env python3
"""
MCP-RAG Server - Servidor MCP customizado para RAG
Integra com Claude Sessions e oferece busca vetorial real
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import hashlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# Import WebFetch integration
from webfetch_integration import WebFetchRAGIntegration

# MCP imports
sys.path.append(str(Path(__file__).parent.parent))
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, 
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
    INTERNAL_ERROR
)

class RAGIndex:
    """Sistema de indexação e busca vetorial"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        
        # Arquivos de persistência
        self.docs_file = cache_dir / "documents.json"
        self.index_file = cache_dir / "index.pkl"
        self.vectors_file = cache_dir / "vectors.npy"
        
        # Carregar ou inicializar
        self.documents: List[Dict] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.vectors: Optional[np.ndarray] = None
        
        self.load()
    
    def load(self):
        """Carrega índice do disco"""
        if self.docs_file.exists():
            with open(self.docs_file, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
        
        if self.index_file.exists() and self.vectors_file.exists():
            with open(self.index_file, 'rb') as f:
                self.vectorizer = pickle.load(f)
            self.vectors = np.load(self.vectors_file)
    
    def save(self):
        """Salva índice no disco"""
        with open(self.docs_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        if self.vectorizer and self.vectors is not None:
            with open(self.index_file, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            np.save(self.vectors_file, self.vectors)
    
    def add_document(self, content: str, source: str, metadata: Dict = None):
        """Adiciona documento ao índice"""
        doc_id = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Evita duplicatas
        for doc in self.documents:
            if doc['id'] == doc_id:
                return doc_id
        
        document = {
            'id': doc_id,
            'content': content,
            'source': source,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.documents.append(document)
        self._rebuild_index()
        self.save()
        
        return doc_id
    
    def _rebuild_index(self):
        """Reconstrói índice vetorial"""
        if not self.documents:
            return
        
        texts = [doc['content'] for doc in self.documents]
        
        # Criar vetorizador TF-IDF
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        self.vectors = self.vectorizer.fit_transform(texts).toarray()
    
    def search(self, query: str, mode: str = 'hybrid', limit: int = 5) -> List[Dict]:
        """Busca documentos relevantes"""
        if not self.documents or self.vectorizer is None:
            return []
        
        # Vetorizar query
        query_vector = self.vectorizer.transform([query]).toarray()
        
        # Calcular similaridade
        similarities = cosine_similarity(query_vector, self.vectors)[0]
        
        # Ordenar por relevância
        indices = np.argsort(similarities)[::-1][:limit]
        
        results = []
        for idx in indices:
            if similarities[idx] > 0.1:  # Threshold mínimo
                doc = self.documents[idx].copy()
                doc['score'] = float(similarities[idx])
                results.append(doc)
        
        return results

class ClaudeSessionsIntegration:
    """Integração com Claude Sessions"""
    
    def __init__(self, claude_base: Path):
        self.claude_base = claude_base
        self.todos_dir = claude_base / "todos"
        self.projects_dir = claude_base / "projects"
    
    def get_all_sessions(self) -> List[Dict]:
        """Lista todas as sessões"""
        sessions = []
        
        if not self.todos_dir.exists():
            return sessions
        
        for todo_file in self.todos_dir.glob("*.json"):
            try:
                session_id = todo_file.stem
                with open(todo_file, 'r', encoding='utf-8') as f:
                    todos = json.load(f)
                
                sessions.append({
                    'session_id': session_id,
                    'todos': todos,
                    'todo_count': len(todos),
                    'file': str(todo_file)
                })
            except Exception as e:
                print(f"Erro ao ler {todo_file}: {e}")
        
        return sessions
    
    def get_session_content(self, session_id: str) -> str:
        """Extrai conteúdo textual de uma sessão"""
        content_parts = [f"Sessão Claude: {session_id}\n"]
        
        # Ler todos
        todo_file = self.todos_dir / f"{session_id}.json"
        if todo_file.exists():
            with open(todo_file, 'r', encoding='utf-8') as f:
                todos = json.load(f)
            
            if todos:
                content_parts.append("\nTAREFAS:")
                for i, todo in enumerate(todos, 1):
                    status = todo.get('status', 'pending')
                    content = todo.get('content', '')
                    priority = todo.get('priority', 'medium')
                    content_parts.append(f"{i}. [{status}] {content} (Prioridade: {priority})")
        
        # Buscar conversa
        for project_dir in self.projects_dir.glob("*"):
            conv_file = project_dir / f"{session_id}.jsonl"
            if conv_file.exists():
                content_parts.append("\n\nCONVERSA:")
                with open(conv_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:20]  # Primeiras 20 linhas
                
                for line in lines:
                    try:
                        entry = json.loads(line)
                        if entry.get('type') == 'user' and 'message' in entry:
                            msg = entry['message'].get('content', '')[:200]
                            content_parts.append(f"User: {msg}...")
                    except:
                        pass
                break
        
        return "\n".join(content_parts)

# Instância global do servidor
app = Server("mcp-rag-server")
rag_index: Optional[RAGIndex] = None
claude_integration: Optional[ClaudeSessionsIntegration] = None
web_integration: Optional[WebFetchRAGIntegration] = None

@app.list_resources()
async def list_resources() -> ListResourcesResult:
    """Lista recursos disponíveis"""
    resources = [
        Resource(
            uri="rag://stats",
            name="Estatísticas do RAG",
            description="Mostra estatísticas do índice RAG",
            mimeType="application/json"
        ),
        Resource(
            uri="rag://sessions",
            name="Claude Sessions",
            description="Lista todas as sessões do Claude",
            mimeType="application/json"
        )
    ]
    
    # Adicionar documentos indexados como recursos
    if rag_index:
        for doc in rag_index.documents[:10]:  # Limitar a 10
            resources.append(Resource(
                uri=f"rag://doc/{doc['id']}",
                name=f"Documento {doc['source']}",
                description=doc['content'][:100] + "...",
                mimeType="text/plain"
            ))
    
    return ListResourcesResult(resources=resources)

@app.read_resource()
async def read_resource(request: ReadResourceRequest) -> ReadResourceResult:
    """Lê um recurso específico"""
    uri = request.uri
    
    if uri == "rag://stats":
        stats = {
            "total_documents": len(rag_index.documents) if rag_index else 0,
            "index_size": len(rag_index.vectors) if rag_index and rag_index.vectors is not None else 0,
            "cache_dir": str(rag_index.cache_dir) if rag_index else None
        }
        return ReadResourceResult(
            contents=[TextContent(
                text=json.dumps(stats, indent=2),
                uri=uri,
                mimeType="application/json"
            )]
        )
    
    elif uri == "rag://sessions":
        sessions = claude_integration.get_all_sessions() if claude_integration else []
        return ReadResourceResult(
            contents=[TextContent(
                text=json.dumps(sessions, indent=2),
                uri=uri,
                mimeType="application/json"
            )]
        )
    
    elif uri.startswith("rag://doc/"):
        doc_id = uri.replace("rag://doc/", "")
        if rag_index:
            for doc in rag_index.documents:
                if doc['id'] == doc_id:
                    return ReadResourceResult(
                        contents=[TextContent(
                            text=doc['content'],
                            uri=uri,
                            mimeType="text/plain"
                        )]
                    )
    
    raise ValueError(f"Recurso não encontrado: {uri}")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """Lista ferramentas disponíveis"""
    return [
        Tool(
            name="rag_search",
            description="Busca informações no índice RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto para buscar"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["naive", "local", "global", "hybrid"],
                        "default": "hybrid",
                        "description": "Modo de busca"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "Número máximo de resultados"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="rag_index",
            description="Indexa um documento no RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Conteúdo do documento"
                    },
                    "source": {
                        "type": "string",
                        "description": "Fonte ou nome do documento"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Metadados adicionais"
                    }
                },
                "required": ["content", "source"]
            }
        ),
        Tool(
            name="rag_index_session",
            description="Indexa uma sessão do Claude",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "ID da sessão para indexar"
                    }
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="rag_index_all_sessions",
            description="Indexa todas as sessões do Claude",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="rag_webfetch",
            description="Busca e indexa documentação web no RAG local",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL da documentação para indexar"
                    },
                    "max_depth": {
                        "type": "integer",
                        "default": 1,
                        "description": "Profundidade máxima para indexar subpáginas (0-3)"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="rag_create_knowledge_base",
            description="Cria knowledge base a partir de múltiplas URLs",
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de URLs para criar knowledge base"
                    }
                },
                "required": ["urls"]
            }
        )
    ]

@app.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """Executa uma ferramenta"""
    tool_name = request.params.name
    args = request.params.arguments
    
    try:
        if tool_name == "rag_search":
            query = args.get("query", "")
            mode = args.get("mode", "hybrid")
            limit = args.get("limit", 5)
            
            if not rag_index:
                return CallToolResult(
                    content=[TextContent(text="Índice RAG não inicializado")],
                    isError=True
                )
            
            results = rag_index.search(query, mode, limit)
            
            if not results:
                return CallToolResult(
                    content=[TextContent(text="Nenhum resultado encontrado")]
                )
            
            # Formatar resultados
            output = f"Encontrados {len(results)} resultados para '{query}':\n\n"
            for i, result in enumerate(results, 1):
                output += f"{i}. {result['source']} (Score: {result['score']:.2f})\n"
                output += f"   {result['content'][:200]}...\n\n"
            
            return CallToolResult(
                content=[TextContent(text=output)]
            )
        
        elif tool_name == "rag_index":
            content = args.get("content", "")
            source = args.get("source", "manual")
            metadata = args.get("metadata", {})
            
            if not rag_index:
                return CallToolResult(
                    content=[TextContent(text="Índice RAG não inicializado")],
                    isError=True
                )
            
            doc_id = rag_index.add_document(content, source, metadata)
            
            return CallToolResult(
                content=[TextContent(text=f"Documento indexado com sucesso. ID: {doc_id}")]
            )
        
        elif tool_name == "rag_index_session":
            session_id = args.get("session_id", "")
            
            if not claude_integration or not rag_index:
                return CallToolResult(
                    content=[TextContent(text="Integração não inicializada")],
                    isError=True
                )
            
            content = claude_integration.get_session_content(session_id)
            if content:
                doc_id = rag_index.add_document(
                    content, 
                    f"claude_session_{session_id}",
                    {"session_id": session_id}
                )
                return CallToolResult(
                    content=[TextContent(text=f"Sessão {session_id} indexada. ID: {doc_id}")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(text=f"Sessão {session_id} não encontrada")],
                    isError=True
                )
        
        elif tool_name == "rag_index_all_sessions":
            if not claude_integration or not rag_index:
                return CallToolResult(
                    content=[TextContent(text="Integração não inicializada")],
                    isError=True
                )
            
            sessions = claude_integration.get_all_sessions()
            indexed = 0
            
            for session in sessions:
                try:
                    content = claude_integration.get_session_content(session['session_id'])
                    if content:
                        rag_index.add_document(
                            content,
                            f"claude_session_{session['session_id']}",
                            {"session_id": session['session_id']}
                        )
                        indexed += 1
                except Exception as e:
                    print(f"Erro ao indexar {session['session_id']}: {e}")
            
            return CallToolResult(
                content=[TextContent(text=f"Indexadas {indexed} de {len(sessions)} sessões")]
            )
        
        elif tool_name == "rag_webfetch":
            url = args.get("url", "")
            max_depth = args.get("max_depth", 1)
            
            if not web_integration or not rag_index:
                return CallToolResult(
                    content=[TextContent(text="Integração WebFetch não inicializada")],
                    isError=True
                )
            
            result = await web_integration.fetch_and_index_url(url, max_depth=max_depth)
            
            # Formatar resultado
            if result["status"] == "indexed":
                output = f"✅ Documentação indexada com sucesso!\n\n"
                output += f"URL: {result['url']}\n"
                output += f"Título: {result.get('title', 'N/A')}\n"
                output += f"ID do documento: {result['doc_id']}\n"
                output += f"Seções encontradas: {result.get('sections', 0)}\n"
                
                if result.get('subpages'):
                    output += f"\nSubpáginas indexadas: {len(result['subpages'])}"
            else:
                output = f"❌ Falha ao indexar: {result.get('error', result['status'])}"
            
            return CallToolResult(
                content=[TextContent(text=output)]
            )
        
        elif tool_name == "rag_create_knowledge_base":
            urls = args.get("urls", [])
            
            if not web_integration or not rag_index:
                return CallToolResult(
                    content=[TextContent(text="Integração WebFetch não inicializada")],
                    isError=True
                )
            
            results = await web_integration.create_knowledge_base(urls)
            
            output = f"📚 Knowledge Base criado!\n\n"
            output += f"Total de URLs: {results['total_urls']}\n"
            output += f"✅ Indexadas: {results['indexed']}\n"
            output += f"❌ Falhas: {results['failed']}\n\n"
            
            # Mostrar detalhes resumidos
            for detail in results['details'][:5]:  # Primeiros 5
                status_icon = "✅" if detail['status'] == "indexed" else "❌"
                output += f"{status_icon} {detail['url']}\n"
            
            if len(results['details']) > 5:
                output += f"... e mais {len(results['details']) - 5} URLs"
            
            return CallToolResult(
                content=[TextContent(text=output)]
            )
        
        else:
            return CallToolResult(
                content=[TextContent(text=f"Ferramenta desconhecida: {tool_name}")],
                isError=True
            )
    
    except Exception as e:
        return CallToolResult(
            content=[TextContent(text=f"Erro: {str(e)}")],
            isError=True
        )

async def main():
    """Função principal"""
    global rag_index, claude_integration, web_integration
    
    # Configurar caminhos
    claude_base = Path.home() / ".claude"
    cache_dir = claude_base / "mcp-rag-cache"
    
    # Inicializar componentes
    rag_index = RAGIndex(cache_dir)
    claude_integration = ClaudeSessionsIntegration(claude_base)
    web_integration = WebFetchRAGIntegration(rag_index)
    
    # Não imprimir nada no stderr para não confundir o MCP
    
    # Iniciar servidor
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())