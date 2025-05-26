#!/usr/bin/env python3
"""
Servidor MCP RAG Standalone
Funciona independente, sem precisar de backend externo
Persiste dados localmente em JSON e numpy arrays
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

# Desabilitar warnings do sklearn
import warnings
warnings.filterwarnings('ignore')

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, 
    Resource,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsResult,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult
)

# Sistema de logging para arquivo
import logging
log_file = Path.home() / ".claude" / "mcp-rag-cache" / "server.log"
log_file.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.NullHandler()  # Não logar no console
    ]
)
logger = logging.getLogger(__name__)

class StandaloneRAGIndex:
    """Sistema RAG autônomo com persistência local"""
    
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
        try:
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
                
            logger.info(f"Carregados {len(self.documents)} documentos")
        except Exception as e:
            logger.error(f"Erro ao carregar: {e}")
    
    def save(self):
        """Salva dados no disco"""
        try:
            with open(self.docs_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            
            with open(self.webfetch_file, 'w', encoding='utf-8') as f:
                json.dump(self.webfetch_docs, f, ensure_ascii=False, indent=2)
            
            if self.vectorizer and self.vectors is not None:
                with open(self.index_file, 'wb') as f:
                    pickle.dump(self.vectorizer, f)
                np.save(self.vectors_file, self.vectors)
                
            logger.info("Dados salvos com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar: {e}")
    
    def add_document(self, content: str, source: str, metadata: Dict = None) -> str:
        """Adiciona documento e reconstrói índice"""
        doc_id = hashlib.md5(f"{source}{content}".encode()).hexdigest()[:8]
        
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
        
        logger.info(f"Documento adicionado: {doc_id} de {source}")
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
        logger.info(f"Índice reconstruído com {len(texts)} documentos")
    
    def search(self, query: str, mode: str = 'hybrid', limit: int = 5) -> List[Dict]:
        """Busca documentos similares"""
        if not self.documents or self.vectorizer is None:
            return []
        
        try:
            query_vector = self.vectorizer.transform([query]).toarray()
            similarities = cosine_similarity(query_vector, self.vectors)[0]
            
            # Ordenar por similaridade
            indices = np.argsort(similarities)[::-1][:limit]
            
            results = []
            for idx in indices:
                if similarities[idx] > 0.05:  # Threshold mínimo
                    doc = self.documents[idx].copy()
                    doc['score'] = float(similarities[idx])
                    results.append(doc)
            
            logger.info(f"Busca '{query}' retornou {len(results)} resultados")
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []
    
    def add_webfetch_doc(self, url: str, title: str = None, category: str = None) -> str:
        """Registra URL para indexação"""
        doc_id = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Evita duplicatas
        for doc in self.webfetch_docs:
            if doc['url'] == url:
                return doc['id']
        
        webfetch_doc = {
            'id': doc_id,
            'url': url,
            'title': title or url,
            'category': category,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        self.webfetch_docs.append(webfetch_doc)
        self.save()
        
        # Simular conteúdo para demonstração
        demo_content = f"""
        Documentação: {title or url}
        URL: {url}
        Categoria: {category or 'Geral'}
        
        Este é um conteúdo simulado para demonstração do sistema RAG standalone.
        Em uma implementação real, aqui estaria o conteúdo extraído da URL.
        
        O sistema pode indexar e buscar este conteúdo offline.
        """
        
        # Indexar conteúdo simulado
        self.add_document(
            content=demo_content,
            source=f"web:{url}",
            metadata={
                'url': url,
                'title': title,
                'category': category,
                'webfetch_id': doc_id
            }
        )
        
        # Atualizar status
        for doc in self.webfetch_docs:
            if doc['id'] == doc_id:
                doc['status'] = 'indexed'
                break
        
        self.save()
        return doc_id

# Servidor MCP
app = Server("rag-standalone")
rag_index: Optional[StandaloneRAGIndex] = None

@app.list_tools()
async def list_tools() -> List[Tool]:
    """Lista ferramentas disponíveis"""
    return [
        Tool(
            name="rag_search",
            description="Busca informações no índice RAG local",
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
                        "default": "hybrid"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
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
                    "content": {
                        "type": "string",
                        "description": "Conteúdo para indexar"
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
            name="rag_webfetch",
            description="Registra URL para indexação (simulada)",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL para indexar"
                    },
                    "title": {
                        "type": "string",
                        "description": "Título do documento"
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoria do documento"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="rag_stats",
            description="Mostra estatísticas do RAG",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.list_resources()
async def list_resources() -> ListResourcesResult:
    """Lista recursos disponíveis"""
    resources = [
        Resource(
            uri="rag://stats",
            name="Estatísticas do RAG",
            description="Informações sobre o índice",
            mimeType="application/json"
        ),
        Resource(
            uri="rag://webfetch",
            name="URLs Registradas",
            description="Lista de URLs para indexação",
            mimeType="application/json"
        )
    ]
    
    # Adicionar documentos como recursos
    if rag_index:
        for doc in rag_index.documents[:5]:
            resources.append(Resource(
                uri=f"rag://doc/{doc['id']}",
                name=f"{doc['source']}",
                description=doc['content'][:100] + "...",
                mimeType="text/plain"
            ))
    
    return ListResourcesResult(resources=resources)

@app.read_resource()
async def read_resource(request: ReadResourceRequest) -> ReadResourceResult:
    """Lê um recurso"""
    uri = request.uri
    
    if uri == "rag://stats":
        stats = {
            "total_documents": len(rag_index.documents) if rag_index else 0,
            "total_webfetch": len(rag_index.webfetch_docs) if rag_index else 0,
            "cache_dir": str(rag_index.cache_dir) if rag_index else None,
            "index_ready": rag_index.vectorizer is not None if rag_index else False
        }
        return ReadResourceResult(
            contents=[TextContent(
                text=json.dumps(stats, indent=2),
                uri=uri,
                mimeType="application/json"
            )]
        )
    
    elif uri == "rag://webfetch":
        docs = rag_index.webfetch_docs if rag_index else []
        return ReadResourceResult(
            contents=[TextContent(
                text=json.dumps(docs, indent=2),
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

@app.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """Executa ferramentas"""
    name = request.params.name
    args = request.params.arguments
    
    try:
        if name == "rag_search":
            query = args.get("query", "")
            mode = args.get("mode", "hybrid")
            limit = args.get("limit", 5)
            
            if not rag_index:
                return CallToolResult(
                    content=[TextContent(text="❌ Índice RAG não inicializado")]
                )
            
            results = rag_index.search(query, mode, limit)
            
            if not results:
                return CallToolResult(
                    content=[TextContent(text=f"Nenhum resultado encontrado para '{query}'")]
                )
            
            output = f"🔍 Encontrados {len(results)} resultados para '{query}':\n\n"
            for i, result in enumerate(results, 1):
                output += f"{i}. **{result['source']}** (Score: {result['score']:.3f})\n"
                output += f"   {result['content'][:200]}...\n"
                if result.get('metadata', {}).get('url'):
                    output += f"   🔗 {result['metadata']['url']}\n"
                output += "\n"
            
            return CallToolResult(content=[TextContent(text=output)])
        
        elif name == "rag_index":
            content = args.get("content", "")
            source = args.get("source", "manual")
            metadata = args.get("metadata", {})
            
            if not rag_index:
                return CallToolResult(
                    content=[TextContent(text="❌ Índice RAG não inicializado")]
                )
            
            doc_id = rag_index.add_document(content, source, metadata)
            
            return CallToolResult(
                content=[TextContent(text=f"✅ Documento indexado com sucesso!\nID: {doc_id}\nFonte: {source}")]
            )
        
        elif name == "rag_webfetch":
            url = args.get("url", "")
            title = args.get("title")
            category = args.get("category")
            
            if not rag_index:
                return CallToolResult(
                    content=[TextContent(text="❌ Índice RAG não inicializado")]
                )
            
            doc_id = rag_index.add_webfetch_doc(url, title, category)
            
            output = f"✅ URL registrada e indexada!\n\n"
            output += f"🔗 URL: {url}\n"
            output += f"📄 ID: {doc_id}\n"
            output += f"📁 Categoria: {category or 'Geral'}\n"
            output += f"\n💡 Conteúdo simulado foi indexado para demonstração."
            output += f"\n🔍 Você já pode buscar por informações desta URL!"
            
            return CallToolResult(content=[TextContent(text=output)])
        
        elif name == "rag_stats":
            if not rag_index:
                return CallToolResult(
                    content=[TextContent(text="❌ Índice RAG não inicializado")]
                )
            
            output = "📊 **Estatísticas do RAG Standalone**\n\n"
            output += f"📚 Total de documentos: {len(rag_index.documents)}\n"
            output += f"🌐 URLs registradas: {len(rag_index.webfetch_docs)}\n"
            output += f"💾 Cache: {rag_index.cache_dir}\n"
            output += f"🔍 Índice: {'Pronto' if rag_index.vectorizer else 'Não inicializado'}\n"
            
            if rag_index.webfetch_docs:
                output += f"\n📑 **URLs Recentes:**\n"
                for doc in rag_index.webfetch_docs[-5:]:
                    output += f"  • {doc['title']} ({doc['status']})\n"
            
            return CallToolResult(content=[TextContent(text=output)])
        
        else:
            return CallToolResult(
                content=[TextContent(text=f"❌ Ferramenta '{name}' não encontrada")]
            )
            
    except Exception as e:
        logger.error(f"Erro ao executar {name}: {e}")
        return CallToolResult(
            content=[TextContent(text=f"❌ Erro: {str(e)}")]
        )

async def main():
    """Inicializa e roda o servidor"""
    global rag_index
    
    # Configurar cache
    cache_dir = Path.home() / ".claude" / "mcp-rag-cache"
    rag_index = StandaloneRAGIndex(cache_dir)
    
    logger.info("Servidor MCP RAG Standalone iniciando...")
    
    # Rodar servidor
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())