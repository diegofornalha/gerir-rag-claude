#!/usr/bin/env python3
"""
MCP RAG Server com Persistência em Disco
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

# Adicionar path do sistema
sys.path.insert(0, '/opt/homebrew/lib/python3.13/site-packages')

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError as e:
    print(f"Erro ao importar MCP: {e}", file=sys.stderr)
    sys.exit(1)

# Configurações
CACHE_DIR = Path.home() / ".claude" / "mcp-rag-cache"
DOCUMENTS_FILE = CACHE_DIR / "documents.json"

# Criar diretório se não existir
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Criar servidor
server = Server("rag-webfetch")

# Cache de documentos
documents: List[Dict[str, Any]] = []

def load_documents():
    """Carrega documentos do disco"""
    global documents
    if DOCUMENTS_FILE.exists():
        try:
            with open(DOCUMENTS_FILE, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            print(f"Carregados {len(documents)} documentos do cache", file=sys.stderr)
        except Exception as e:
            print(f"Erro ao carregar documentos: {e}", file=sys.stderr)
            documents = []
    else:
        documents = []
        save_documents()

def save_documents():
    """Salva documentos no disco"""
    try:
        with open(DOCUMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        print(f"Salvos {len(documents)} documentos no cache", file=sys.stderr)
    except Exception as e:
        print(f"Erro ao salvar documentos: {e}", file=sys.stderr)

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Lista ferramentas disponíveis"""
    return [
        Tool(
            name="test",
            description="Testa o servidor RAG",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search",
            description="Busca no cache RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
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
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["urls"]
            }
        ),
        Tool(
            name="list",
            description="Lista todos os documentos no cache",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="clear",
            description="Limpa o cache RAG",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Executa ferramentas"""
    global documents
    
    if name == "test":
        return [TextContent(type="text", text=f"✅ RAG funcionando! {len(documents)} docs no cache")]
    
    elif name == "search":
        query = arguments.get("query", "").lower()
        results = []
        
        for doc in documents:
            if query in doc.get("content", "").lower() or query in doc.get("source", "").lower():
                results.append(doc)
        
        if results:
            text = f"Encontrados {len(results)} resultados:\n"
            for doc in results[:5]:  # Limitar a 5 resultados
                text += f"\n📄 {doc['source']}\n"
                text += f"   {doc['content'][:100]}...\n"
        else:
            text = f"Nenhum resultado encontrado para '{query}'"
            
        return [TextContent(type="text", text=text)]
    
    elif name == "add":
        content = arguments.get("content", "")
        source = arguments.get("source", "Unknown")
        metadata = arguments.get("metadata", {})
        
        if content:
            doc = {
                "id": f"{len(documents) + 1}",
                "content": content,
                "source": source,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
            documents.append(doc)
            save_documents()
            return [TextContent(type="text", text=f"✅ Documento adicionado: {source}")]
        else:
            return [TextContent(type="text", text="❌ Conteúdo vazio")]
    
    elif name == "add_batch":
        urls = arguments.get("urls", [])
        if urls:
            # Por enquanto, apenas adicionar as URLs como referências
            added = 0
            for url in urls:
                doc = {
                    "id": f"{len(documents) + 1}",
                    "content": f"URL para indexar: {url}",
                    "source": url,
                    "metadata": {"status": "pending", "type": "url"},
                    "timestamp": datetime.now().isoformat()
                }
                documents.append(doc)
                added += 1
            
            save_documents()
            return [TextContent(type="text", text=f"✅ Adicionadas {added} URLs para indexação")]
        else:
            return [TextContent(type="text", text="❌ Nenhuma URL fornecida")]
    
    elif name == "list":
        if documents:
            text = f"📚 {len(documents)} documentos no cache:\n"
            for doc in documents[:10]:  # Mostrar até 10
                text += f"\n• [{doc['id']}] {doc['source']}"
                text += f"\n  📅 {doc.get('timestamp', 'N/A')}"
        else:
            text = "📭 Cache vazio"
        
        return [TextContent(type="text", text=text)]
    
    elif name == "clear":
        documents = []
        save_documents()
        return [TextContent(type="text", text="🗑️ Cache limpo com sucesso")]
    
    return [TextContent(type="text", text=f"Ferramenta '{name}' não encontrada")]

async def main():
    """Função principal"""
    # Carregar documentos do disco
    load_documents()
    
    # Log para debug
    print(f"MCP RAG Server iniciando com {len(documents)} documentos...", file=sys.stderr)
    print(f"Cache em: {CACHE_DIR}", file=sys.stderr)
    
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