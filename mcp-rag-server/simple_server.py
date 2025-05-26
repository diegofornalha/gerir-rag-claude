#!/usr/bin/env python3
"""
Servidor MCP-RAG simplificado para testes
"""
import asyncio
import json
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Criar servidor
app = Server("rag-webfetch")

@app.list_tools()
async def list_tools():
    return [
        {
            "name": "rag_test",
            "description": "Teste simples do RAG",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Mensagem de teste"
                    }
                },
                "required": ["message"]
            }
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "rag_test":
        return {
            "type": "text",
            "text": f"RAG funcionando! Mensagem: {arguments.get('message', 'sem mensagem')}"
        }
    return {"type": "error", "error": f"Ferramenta {name} não encontrada"}

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())