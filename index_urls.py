#!/usr/bin/env python3
"""
Script para indexar URLs importantes no RAG
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
for i, url in enumerate(urls_to_index, 1):
    print(f"{i}. {url}")

print("\nPara indexar usando o servidor MCP RAG:")
print('mcp__rag-webfetch__add_batch(urls=', urls_to_index, ')')

print("\nOu use WebFetch individualmente para cada URL")
print("Exemplo: WebFetch('https://zod.dev', 'extrair documentação principal')")