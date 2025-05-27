#!/usr/bin/env python3
"""
MCP RAG Server - Integrado com cache/vetores existentes
"""
import asyncio
import json
import sys
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import hashlib

# Adicionar path do sistema
sys.path.insert(0, '/opt/homebrew/lib/python3.13/site-packages')

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    print(f"Erro ao importar: {e}", file=sys.stderr)
    sys.exit(1)

# Configurações
CACHE_DIR = Path.home() / ".claude" / "mcp-rag-cache"
DOCUMENTS_FILE = CACHE_DIR / "documents.json"
INDEX_FILE = CACHE_DIR / "index.pkl"
VECTORS_FILE = CACHE_DIR / "vectors.npy"

# Criar servidor
server = Server("rag-webfetch")

class RAGIndex:
    """Sistema de indexação e busca vetorial integrado"""
    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.documents: List[Dict] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.vectors: Optional[np.ndarray] = None
        self.load()
    
    def load(self):
        """Carrega índice existente do disco"""
        if DOCUMENTS_FILE.exists():
            with open(DOCUMENTS_FILE, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
            print(f"Carregados {len(self.documents)} documentos", file=sys.stderr)
        
        if INDEX_FILE.exists() and VECTORS_FILE.exists():
            try:
                with open(INDEX_FILE, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                self.vectors = np.load(VECTORS_FILE)
                print(f"Índice vetorial carregado", file=sys.stderr)
            except Exception as e:
                print(f"Erro ao carregar vetores: {e}", file=sys.stderr)
    
    def save(self):
        """Salva índice no disco"""
        with open(DOCUMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        if self.vectorizer and self.vectors is not None:
            with open(INDEX_FILE, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            np.save(VECTORS_FILE, self.vectors)
    
    def add_document(self, content: str, source: str, metadata: Dict = None):
        """Adiciona documento ao índice"""
        doc_id = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Evita duplicatas
        for doc in self.documents:
            if doc.get('id') == doc_id:
                return doc_id, False
        
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
        
        return doc_id, True
    
    def _rebuild_index(self):
        """Reconstrói índice vetorial"""
        if not self.documents:
            return
        
        # Extrair textos
        texts = [doc['content'] for doc in self.documents]
        
        # Criar/atualizar vetorizador
        if not self.vectorizer:
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words='english'
            )
            self.vectors = self.vectorizer.fit_transform(texts).toarray()
        else:
            # Recriar vetorizador com todos os documentos
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words='english'
            )
            self.vectors = self.vectorizer.fit_transform(texts).toarray()
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Busca vetorial"""
        if not self.documents or self.vectorizer is None:
            return []
        
        # Vetorizar query
        query_vector = self.vectorizer.transform([query]).toarray()
        
        # Calcular similaridades
        similarities = cosine_similarity(query_vector, self.vectors)[0]
        
        # Ordenar por similaridade
        indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in indices:
            if similarities[idx] > 0.1:  # Threshold mínimo
                doc = self.documents[idx].copy()
                doc['score'] = float(similarities[idx])
                results.append(doc)
        
        return results
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove documento do índice"""
        # Encontrar documento
        doc_index = None
        for i, doc in enumerate(self.documents):
            if doc.get('id') == doc_id:
                doc_index = i
                break
        
        if doc_index is None:
            return False
        
        # Remover documento
        self.documents.pop(doc_index)
        
        # Reconstruir índice se necessário
        if self.documents:
            self._rebuild_index()
        else:
            self.vectorizer = None
            self.vectors = None
        
        self.save()
        return True
    
    def add_batch_urls(self, urls: List[str]) -> Dict[str, int]:
        """Adiciona URLs para indexação futura"""
        added = 0
        skipped = 0
        
        for url in urls:
            # Verificar se já existe
            exists = any(doc.get('source') == url for doc in self.documents)
            
            if not exists:
                doc_id = hashlib.md5(url.encode()).hexdigest()[:8]
                document = {
                    'id': doc_id,
                    'content': f"[PENDING] URL to be indexed: {url}",
                    'source': url,
                    'metadata': {
                        'status': 'pending',
                        'type': 'url',
                        'added_via': 'batch'
                    },
                    'timestamp': datetime.now().isoformat()
                }
                self.documents.append(document)
                added += 1
            else:
                skipped += 1
        
        if added > 0:
            self._rebuild_index()
            self.save()
        
        return {'added': added, 'skipped': skipped}

# Instância global do índice
rag_index = RAGIndex()

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Lista ferramentas disponíveis"""
    return [
        Tool(
            name="test",
            description="Testa o servidor RAG",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="search",
            description="Busca vetorial no cache RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="add",
            description="Adiciona documento ao cache RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "source": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["content", "source"]
            }
        ),
        Tool(
            name="add_batch",
            description="Adiciona múltiplas URLs para indexação",
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["urls"]
            }
        ),
        Tool(
            name="remove",
            description="Remove documento do cache RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "ID do documento a remover"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="list",
            description="Lista documentos no cache",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10}
                }
            }
        ),
        Tool(
            name="stats",
            description="Estatísticas do cache RAG",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="index_session",
            description="Indexa uma sessão Claude (.jsonl)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_path": {"type": "string", "description": "Caminho do arquivo .jsonl"},
                    "chunk_size": {"type": "integer", "default": 1000}
                },
                "required": ["session_path"]
            }
        ),
        Tool(
            name="index_directory",
            description="Indexa todos os arquivos de um diretório",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Caminho do diretório"},
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": [".jsonl", ".json", ".md"]
                    }
                },
                "required": ["directory"]
            }
        ),
        Tool(
            name="monitor_status",
            description="Verifica status do monitor em tempo real",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="monitor_start",
            description="Inicia o monitor em tempo real para indexação automática",
            inputSchema={
                "type": "object",
                "properties": {
                    "interval": {"type": "integer", "default": 5, "description": "Intervalo em segundos"}
                }
            }
        ),
        Tool(
            name="monitor_stop",
            description="Para o monitor em tempo real",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Executa ferramentas"""
    
    if name == "test":
        return [TextContent(
            type="text", 
            text=f"✅ RAG funcionando! {len(rag_index.documents)} docs, "
                 f"vetorização {'ativa' if rag_index.vectorizer else 'inativa'}"
        )]
    
    elif name == "search":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        
        if not query:
            return [TextContent(type="text", text="❌ Query vazia")]
        
        results = rag_index.search(query, top_k)
        
        if results:
            text = f"🔍 Encontrados {len(results)} resultados para '{query}':\n"
            for i, doc in enumerate(results, 1):
                text += f"\n{i}. [{doc['score']:.2f}] {doc['source']}\n"
                text += f"   {doc['content'][:150]}...\n"
        else:
            text = f"Nenhum resultado encontrado para '{query}'"
        
        return [TextContent(type="text", text=text)]
    
    elif name == "add":
        content = arguments.get("content", "")
        source = arguments.get("source", "Unknown")
        metadata = arguments.get("metadata", {})
        
        if not content:
            return [TextContent(type="text", text="❌ Conteúdo vazio")]
        
        doc_id, is_new = rag_index.add_document(content, source, metadata)
        
        if is_new:
            return [TextContent(type="text", text=f"✅ Documento adicionado: {source} (ID: {doc_id})")]
        else:
            return [TextContent(type="text", text=f"⚠️ Documento já existe: {source} (ID: {doc_id})")]
    
    elif name == "add_batch":
        urls = arguments.get("urls", [])
        
        if not urls:
            return [TextContent(type="text", text="❌ Nenhuma URL fornecida")]
        
        result = rag_index.add_batch_urls(urls)
        
        return [TextContent(
            type="text", 
            text=f"✅ Batch processado: {result['added']} adicionadas, {result['skipped']} ignoradas"
        )]
    
    elif name == "remove":
        doc_id = arguments.get("id", "")
        
        if not doc_id:
            return [TextContent(type="text", text="❌ ID do documento não fornecido")]
        
        removed = rag_index.remove_document(doc_id)
        
        if removed:
            return [TextContent(type="text", text=f"✅ Documento removido: {doc_id}")]
        else:
            return [TextContent(type="text", text=f"❌ Documento não encontrado: {doc_id}")]
    
    elif name == "list":
        limit = arguments.get("limit", 10)
        
        if not rag_index.documents:
            return [TextContent(type="text", text="📭 Cache vazio")]
        
        text = f"📚 Total: {len(rag_index.documents)} documentos\n"
        text += f"Mostrando últimos {min(limit, len(rag_index.documents))}:\n"
        
        # Mostrar documentos mais recentes primeiro
        sorted_docs = sorted(rag_index.documents, 
                           key=lambda x: x.get('timestamp', ''), 
                           reverse=True)
        
        for doc in sorted_docs[:limit]:
            status = doc.get('metadata', {}).get('status', 'indexed')
            text += f"\n• [{doc['id']}] {doc['source']}"
            text += f"\n  Status: {status}, Data: {doc.get('timestamp', 'N/A')[:10]}"
        
        return [TextContent(type="text", text=text)]
    
    elif name == "index_session":
        session_path = arguments.get("session_path", "")
        chunk_size = arguments.get("chunk_size", 1000)
        
        if not session_path:
            return [TextContent(type="text", text="❌ Caminho da sessão não fornecido")]
        
        path = Path(session_path)
        if not path.exists():
            return [TextContent(type="text", text=f"❌ Arquivo não encontrado: {session_path}")]
        
        try:
            # Importar o indexador de sessões
            from session_indexer import chunk_session_content
            
            chunks = chunk_session_content(path, chunk_size)
            added_count = 0
            
            for chunk in chunks:
                doc_id, is_new = rag_index.add_document(
                    content=chunk['content'],
                    source=chunk['source'],
                    metadata=chunk['metadata']
                )
                if is_new:
                    added_count += 1
            
            return [TextContent(
                type="text",
                text=f"✅ Sessão indexada: {added_count} chunks adicionados de {path.name}"
            )]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro ao indexar sessão: {str(e)}")]
    
    elif name == "index_directory":
        directory = arguments.get("directory", "")
        file_types = arguments.get("file_types", [".jsonl", ".json", ".md"])
        
        if not directory:
            return [TextContent(type="text", text="❌ Diretório não fornecido")]
        
        dir_path = Path(directory)
        if not dir_path.exists():
            return [TextContent(type="text", text=f"❌ Diretório não encontrado: {directory}")]
        
        indexed_files = 0
        total_chunks = 0
        
        try:
            for file_type in file_types:
                for file_path in dir_path.rglob(f"*{file_type}"):
                    if file_type == ".jsonl":
                        # Indexar sessão Claude
                        from session_indexer import chunk_session_content
                        chunks = chunk_session_content(file_path, 1000)
                        
                        for chunk in chunks:
                            doc_id, is_new = rag_index.add_document(
                                content=chunk['content'],
                                source=chunk['source'],
                                metadata=chunk['metadata']
                            )
                            if is_new:
                                total_chunks += 1
                        
                        indexed_files += 1
                    
                    elif file_type == ".json":
                        # Indexar JSON (TODOs, configs)
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        content = json.dumps(data, indent=2)
                        doc_id, is_new = rag_index.add_document(
                            content=content,
                            source=f"json:{file_path.name}",
                            metadata={
                                'file_type': 'json',
                                'path': str(file_path)
                            }
                        )
                        if is_new:
                            indexed_files += 1
                            total_chunks += 1
            
            return [TextContent(
                type="text",
                text=f"✅ Diretório indexado: {indexed_files} arquivos, {total_chunks} documentos"
            )]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro ao indexar diretório: {str(e)}")]
    
    elif name == "stats":
        total = len(rag_index.documents)
        pending = sum(1 for d in rag_index.documents 
                     if d.get('metadata', {}).get('status') == 'pending')
        indexed = total - pending
        
        text = f"📊 Estatísticas do Cache RAG:\n\n"
        text += f"📄 Total de documentos: {total}\n"
        text += f"✅ Indexados: {indexed}\n"
        text += f"⏳ Pendentes: {pending}\n"
        text += f"🔢 Vetorização: {'Ativa' if rag_index.vectorizer else 'Inativa'}\n"
        text += f"📁 Cache em: {CACHE_DIR}\n"
        
        return [TextContent(type="text", text=text)]
    
    elif name == "monitor_status":
        try:
            from monitor_service import handle_monitor_command
            result = handle_monitor_command("status")
            
            if result["running"]:
                text = f"🟢 Monitor em tempo real ATIVO\n\n"
                text += f"PID: {result.get('pid', 'N/A')}\n"
                text += f"Log: {result.get('log_file', 'N/A')}\n"
                
                recent = result.get('recent_activity', {})
                if recent.get('indexed_files', 0) > 0:
                    text += f"\n📊 Atividade recente:\n"
                    text += f"  Arquivos indexados: {recent['indexed_files']}\n"
                    
                if recent.get('recent_logs'):
                    text += f"\n📋 Últimas mensagens:\n"
                    for log in recent['recent_logs'][-5:]:
                        text += f"  {log.strip()}\n"
            else:
                text = "🔴 Monitor em tempo real PARADO"
                
            return [TextContent(type="text", text=text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro ao verificar monitor: {str(e)}")]
    
    elif name == "monitor_start":
        try:
            from monitor_service import handle_monitor_command
            interval = arguments.get("interval", 5)
            result = handle_monitor_command("start", {"interval": interval})
            
            if result["status"] == "started":
                text = f"✅ Monitor iniciado com sucesso!\n\n"
                text += f"PID: {result['pid']}\n"
                text += f"Intervalo: {result['interval']}s\n"
                text += f"Log: {result['log_file']}\n"
                text += f"\nO monitor está indexando automaticamente:\n"
                text += f"  • Sessões Claude (~/.claude/sessions/)\n"
                text += f"  • TODOs (~/.claude/todos/)\n"
                text += f"  • Projetos (~/.claude/projects/)\n"
                text += f"  • CLAUDE.md\n"
            elif result["status"] == "already_running":
                text = "⚠️ Monitor já está em execução"
            else:
                text = f"❌ Erro ao iniciar monitor: {result.get('message', 'Erro desconhecido')}"
                
            return [TextContent(type="text", text=text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro ao iniciar monitor: {str(e)}")]
    
    elif name == "monitor_stop":
        try:
            from monitor_service import handle_monitor_command
            result = handle_monitor_command("stop")
            
            if result["status"] == "stopped":
                text = "✅ Monitor parado com sucesso"
            elif result["status"] == "not_running":
                text = "⚠️ Monitor não estava em execução"
            else:
                text = f"❌ Erro ao parar monitor: {result.get('message', 'Erro desconhecido')}"
                
            return [TextContent(type="text", text=text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Erro ao parar monitor: {str(e)}")]
    
    return [TextContent(type="text", text=f"❌ Ferramenta '{name}' não encontrada")]

async def main():
    """Função principal"""
    print(f"MCP RAG Server iniciando...", file=sys.stderr)
    print(f"Cache: {CACHE_DIR}", file=sys.stderr)
    print(f"Documentos: {len(rag_index.documents)}", file=sys.stderr)
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        print(f"Erro no servidor: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Erro fatal: {e}", file=sys.stderr)
        sys.exit(1)