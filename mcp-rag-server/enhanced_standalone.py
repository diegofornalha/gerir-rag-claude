#!/usr/bin/env python3
"""
Servidor MCP RAG Standalone Enhanced
Integra com Puppeteer MCP quando disponível para captura real
"""
import asyncio
import json
import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# Desabilitar warnings
import warnings
warnings.filterwarnings('ignore')

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent

# Configuração
app = Server("rag-standalone")

class EnhancedRAGIndex:
    """Sistema RAG com suporte a captura via Puppeteer"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        
        # Arquivos
        self.docs_file = cache_dir / "documents.json"
        self.index_file = cache_dir / "index.pkl"
        self.vectors_file = cache_dir / "vectors.npy"
        self.webfetch_file = cache_dir / "webfetch_docs.json"
        
        # Estado
        self.documents: List[Dict] = []
        self.webfetch_docs: List[Dict] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.vectors: Optional[np.ndarray] = None
        
        self.load()
    
    def load(self):
        """Carrega dados do disco"""
        if self.docs_file.exists():
            with open(self.docs_file, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
        
        if self.webfetch_file.exists():
            with open(self.webfetch_file, 'r', encoding='utf-8') as f:
                self.webfetch_docs = json.load(f)
        
        if self.index_file.exists() and self.vectors_file.exists():
            with open(self.index_file, 'rb') as f:
                self.vectorizer = pickle.load(f)
            self.vectors = np.load(self.vectors_file)
    
    def save(self):
        """Salva dados no disco"""
        with open(self.docs_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        with open(self.webfetch_file, 'w', encoding='utf-8') as f:
            json.dump(self.webfetch_docs, f, ensure_ascii=False, indent=2)
        
        if self.vectorizer and self.vectors is not None:
            with open(self.index_file, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            np.save(self.vectors_file, self.vectors)
    
    def add_document(self, content: str, source: str, metadata: Dict = None) -> str:
        """Adiciona documento e reconstrói índice"""
        doc_id = hashlib.md5(f"{source}{content[:100]}".encode()).hexdigest()[:8]
        
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
        
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
        
        self.vectors = self.vectorizer.fit_transform(texts).toarray()
    
    def search(self, query: str, mode: str = 'hybrid', limit: int = 5) -> List[Dict]:
        """Busca documentos similares"""
        if not self.documents or self.vectorizer is None:
            return []
        
        try:
            query_vector = self.vectorizer.transform([query]).toarray()
            similarities = cosine_similarity(query_vector, self.vectors)[0]
            
            indices = np.argsort(similarities)[::-1][:limit]
            
            results = []
            for idx in indices:
                if similarities[idx] > 0.05:
                    doc = self.documents[idx].copy()
                    doc['score'] = float(similarities[idx])
                    results.append(doc)
            
            return results
        except:
            return []
    
    def add_webfetch_doc(self, url: str, title: str = None, category: str = None, 
                        captured_content: str = None, screenshot_path: str = None) -> str:
        """Registra URL capturada"""
        doc_id = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Atualizar ou criar
        webfetch_doc = None
        for doc in self.webfetch_docs:
            if doc['url'] == url:
                webfetch_doc = doc
                break
        
        if not webfetch_doc:
            webfetch_doc = {
                'id': doc_id,
                'url': url,
                'title': title or url,
                'category': category,
                'status': 'indexed',
                'created_at': datetime.now().isoformat()
            }
            self.webfetch_docs.append(webfetch_doc)
        
        # Atualizar com nova captura
        webfetch_doc['last_captured'] = datetime.now().isoformat()
        webfetch_doc['status'] = 'indexed'
        if screenshot_path:
            webfetch_doc['screenshot'] = screenshot_path
        
        # Indexar conteúdo se fornecido
        if captured_content:
            self.add_document(
                content=captured_content,
                source=f"web:{url}",
                metadata={
                    'url': url,
                    'title': title,
                    'category': category,
                    'webfetch_id': doc_id,
                    'screenshot': screenshot_path
                }
            )
        
        self.save()
        return doc_id

# Instância global
rag_index: Optional[EnhancedRAGIndex] = None

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="rag_search",
            description="Busca informações no índice RAG local",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto para buscar"},
                    "mode": {"type": "string", "enum": ["naive", "local", "global", "hybrid"], "default": "hybrid"},
                    "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="rag_index",
            description="Indexa um texto no RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Conteúdo para indexar"},
                    "source": {"type": "string", "description": "Fonte ou nome do documento"},
                    "metadata": {"type": "object", "description": "Metadados adicionais"}
                },
                "required": ["content", "source"]
            }
        ),
        Tool(
            name="rag_webfetch_capture",
            description="Captura e indexa URL usando Puppeteer (recomendado)",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL para capturar"},
                    "title": {"type": "string", "description": "Título do documento"},
                    "category": {"type": "string", "description": "Categoria"},
                    "use_puppeteer": {"type": "boolean", "default": True, "description": "Usar Puppeteer MCP se disponível"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="rag_stats",
            description="Mostra estatísticas do RAG",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="rag_list_docs",
            description="Lista documentos indexados",
            inputSchema={
                "type": "object", 
                "properties": {
                    "source_filter": {"type": "string", "description": "Filtrar por fonte (ex: 'web:')"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "rag_search":
        query = arguments.get("query", "")
        mode = arguments.get("mode", "hybrid")
        limit = arguments.get("limit", 5)
        
        results = rag_index.search(query, mode, limit)
        
        if not results:
            return [TextContent(text=f"Nenhum resultado para '{query}'")]
        
        output = f"🔍 **{len(results)} resultados para '{query}':**\n\n"
        for i, result in enumerate(results, 1):
            output += f"**{i}. {result['source']}** (Score: {result['score']:.3f})\n"
            output += f"{result['content'][:200]}...\n"
            if result.get('metadata', {}).get('url'):
                output += f"🔗 {result['metadata']['url']}\n"
            output += "\n"
        
        return [TextContent(text=output)]
    
    elif name == "rag_index":
        content = arguments.get("content", "")
        source = arguments.get("source", "manual")
        metadata = arguments.get("metadata", {})
        
        doc_id = rag_index.add_document(content, source, metadata)
        
        return [TextContent(text=f"✅ Indexado!\nID: {doc_id}\nFonte: {source}")]
    
    elif name == "rag_webfetch_capture":
        url = arguments.get("url", "")
        title = arguments.get("title")
        category = arguments.get("category")
        use_puppeteer = arguments.get("use_puppeteer", True)
        
        output = f"📥 **Capturando: {url}**\n\n"
        
        if use_puppeteer:
            output += "💡 **Dica**: Para capturar com Puppeteer, use:\n"
            output += f"1. `puppeteer_navigate` para navegar até {url}\n"
            output += f"2. `puppeteer_screenshot` para capturar tela\n"
            output += f"3. `puppeteer_evaluate` para extrair conteúdo\n"
            output += f"4. Use `rag_index` para indexar o conteúdo extraído\n\n"
            output += "Isso evita erros 308 e captura conteúdo dinâmico!"
        
        # Registrar URL
        doc_id = rag_index.add_webfetch_doc(url, title, category)
        output += f"\n✅ URL registrada! ID: {doc_id}"
        
        return [TextContent(text=output)]
    
    elif name == "rag_stats":
        output = "📊 **Estatísticas do RAG**\n\n"
        output += f"📚 Documentos: {len(rag_index.documents)}\n"
        output += f"🌐 URLs: {len(rag_index.webfetch_docs)}\n"
        output += f"💾 Cache: {rag_index.cache_dir}\n"
        output += f"🔍 Índice: {'Pronto' if rag_index.vectorizer else 'Vazio'}\n"
        
        # URLs recentes
        if rag_index.webfetch_docs:
            output += f"\n📑 **URLs Recentes:**\n"
            for doc in rag_index.webfetch_docs[-5:]:
                output += f"• {doc['title']} ({doc['status']})\n"
        
        return [TextContent(text=output)]
    
    elif name == "rag_list_docs":
        source_filter = arguments.get("source_filter", "")
        
        docs = rag_index.documents
        if source_filter:
            docs = [d for d in docs if source_filter in d['source']]
        
        output = f"📄 **{len(docs)} documentos**"
        if source_filter:
            output += f" (filtro: {source_filter})"
        output += "\n\n"
        
        for doc in docs[-10:]:  # Últimos 10
            output += f"• **{doc['source']}** ({doc['id']})\n"
            output += f"  {doc['content'][:100]}...\n"
            if doc.get('metadata', {}).get('url'):
                output += f"  🔗 {doc['metadata']['url']}\n"
            output += "\n"
        
        return [TextContent(text=output)]
    
    return [TextContent(text=f"❌ Ferramenta '{name}' não encontrada")]

async def main():
    global rag_index
    
    cache_dir = Path.home() / ".claude" / "mcp-rag-cache"
    rag_index = EnhancedRAGIndex(cache_dir)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())