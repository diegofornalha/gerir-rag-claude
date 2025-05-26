#!/usr/bin/env python3
"""
MCP RAG Server - Versão funcional mínima
"""
import asyncio
import json
import sys
from typing import Any

# Adicionar path do sistema
sys.path.insert(0, '/opt/homebrew/lib/python3.13/site-packages')

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError as e:
    print(f"Erro ao importar MCP: {e}", file=sys.stderr)
    sys.exit(1)

# Criar servidor
server = Server("rag-webfetch")

# Cache simples
cache = ["Claude Code é uma ferramenta de IA", "MCP permite integração com ferramentas"]

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
            description="Adiciona conteúdo ao cache RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "source": {"type": "string"}
                },
                "required": ["content", "source"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Executa ferramentas"""
    if name == "test":
        return [TextContent(type="text", text=f"✅ RAG funcionando! {len(cache)} docs no cache")]
    
    elif name == "search":
        query = arguments.get("query", "").lower()
        results = [doc for doc in cache if query in doc.lower()]
        
        if results:
            text = f"Encontrados {len(results)} resultados:\n" + "\n".join(f"- {r}" for r in results)
        else:
            text = "Nenhum resultado encontrado"
            
        return [TextContent(type="text", text=text)]
    
    elif name == "add":
        content = arguments.get("content", "")
        source = arguments.get("source", "Unknown")
        
        if content:
            # Adicionar ao cache com formato
            doc = f"[{source}] {content}"
            cache.append(doc)
            return [TextContent(type="text", text=f"✅ Adicionado ao cache: {doc[:100]}...")]
        else:
            return [TextContent(type="text", text="❌ Conteúdo vazio")]
    
    return [TextContent(type="text", text=f"Ferramenta '{name}' não encontrada")]

async def main():
    """Função principal"""
    # Log para debug
    print("MCP RAG Server iniciando...", file=sys.stderr)
    
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