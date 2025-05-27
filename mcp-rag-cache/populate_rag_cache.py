#!/usr/bin/env python3
"""
Script para popular o cache RAG com documentação útil
"""

urls_to_index = [
    "https://modelcontextprotocol.io",
    "https://orm.drizzle.team/docs",
    "https://github.com/TanStack/db",
    "https://localfirstweb.dev",
    "https://fastify.dev",
    "https://zod.dev",
    "https://electric-sql.com",
    "https://tanstack.com",
    "https://docs.anthropic.com/en/docs/claude-code"
]

print("URLs para indexar no RAG:")
for url in urls_to_index:
    print(f"  - {url}")

print("\nPara indexar essas URLs no RAG, use o WebFetch do Claude:")
print("\nExemplo de comando no Claude:")
print('WebFetch("https://modelcontextprotocol.io", "extrair documentação sobre MCP")')
print("\nOu use a interface visual em http://localhost:5173/rag")

# Criar arquivo de referência para o cache
import json
from pathlib import Path

cache_dir = Path.home() / ".claude" / "mcp-rag-cache"
cache_dir.mkdir(exist_ok=True)

reference_file = cache_dir / "urls_to_index.json"
with open(reference_file, "w") as f:
    json.dump({
        "urls": urls_to_index,
        "description": "Documentação importante para o projeto",
        "timestamp": "2024-01-26"
    }, f, indent=2)

print(f"\n✅ Arquivo de referência criado em: {reference_file}")