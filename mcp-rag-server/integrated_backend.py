#!/usr/bin/env python3
"""
MCP Server que se integra com o backend TypeScript existente
"""
import asyncio
import json
import requests
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuração - ajuste a porta do seu backend
BACKEND_URL = "http://localhost:3333"

app = Server("rag-backend")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_rag",
            description="Busca documentações no sistema RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto para buscar"},
                    "mode": {"type": "string", "enum": ["naive", "local", "global", "hybrid"], "default": "hybrid"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="add_doc_url", 
            description="Adiciona URL para indexação",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL da documentação"},
                    "category": {"type": "string", "description": "Categoria (MCP, Claude, etc)"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="list_docs",
            description="Lista documentações indexadas",
            inputSchema={
                "type": "object", 
                "properties": {
                    "status": {"type": "string", "enum": ["all", "indexed", "pending", "failed"]}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "search_rag":
            # Buscar via API do backend
            response = requests.post(
                f"{BACKEND_URL}/api/webfetch/search",
                json={"query": arguments.get("query"), "mode": arguments.get("mode", "hybrid")},
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return [TextContent(type="text", text="Nenhum resultado encontrado")]
                
                text = f"Encontrados {len(results)} resultados:\n\n"
                for i, r in enumerate(results[:5], 1):
                    doc = r.get("doc", {})
                    text += f"{i}. {doc.get('title', doc.get('url', 'Sem título'))}\n"
                    text += f"   Score: {r.get('score', 0):.3f}\n\n"
                
                return [TextContent(type="text", text=text)]
            else:
                return [TextContent(type="text", text=f"Erro: {response.status_code}")]
                
        elif name == "add_doc_url":
            response = requests.post(
                f"{BACKEND_URL}/api/webfetch",
                json={
                    "url": arguments.get("url"),
                    "category": arguments.get("category", "Geral")
                },
                timeout=30
            )
            
            if response.ok:
                doc = response.json()
                return [TextContent(
                    type="text", 
                    text=f"✅ URL adicionada!\nID: {doc.get('id')}\nStatus: {doc.get('status')}"
                )]
            else:
                return [TextContent(type="text", text=f"Erro ao adicionar: {response.status_code}")]
                
        elif name == "list_docs":
            params = {}
            status = arguments.get("status", "all")
            if status != "all":
                params["status"] = status
                
            response = requests.get(
                f"{BACKEND_URL}/api/webfetch",
                params=params,
                timeout=30
            )
            
            if response.ok:
                docs = response.json()
                if not docs:
                    return [TextContent(type="text", text="Nenhuma documentação encontrada")]
                
                text = f"📚 {len(docs)} documentações:\n\n"
                for doc in docs[:10]:
                    text += f"• {doc.get('title', doc.get('url'))}\n"
                    text += f"  Status: {doc.get('status')} | "
                    text += f"Categoria: {doc.get('category', 'N/A')}\n\n"
                
                return [TextContent(type="text", text=text)]
            else:
                return [TextContent(type="text", text=f"Erro: {response.status_code}")]
                
    except requests.ConnectionError:
        return [TextContent(type="text", text=f"❌ Backend não está rodando em {BACKEND_URL}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Erro: {str(e)}")]
    
    return [TextContent(type="text", text=f"Ferramenta '{name}' não encontrada")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())