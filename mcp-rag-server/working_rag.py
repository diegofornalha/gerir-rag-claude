#!/usr/bin/env python3
"""
Working RAG MCP Server
"""

import asyncio
import json
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, '/opt/homebrew/lib/python3.13/site-packages')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult

# Create server instance
server = Server("rag-webfetch")

# Simple in-memory cache
knowledge_base = [
    "Claude Code is an AI-powered coding assistant",
    "MCP (Model Context Protocol) enables tool integration",
    "RAG (Retrieval Augmented Generation) improves AI responses",
    "Python is a popular programming language",
    "WebFetch can retrieve web content"
]

@server.list_tools()
async def list_tools():
    """List available RAG tools"""
    return [
        Tool(
            name="rag_test",
            description="Test if RAG server is working",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Test message"}
                }
            }
        ),
        Tool(
            name="rag_search",
            description="Search the RAG knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="rag_add",
            description="Add knowledge to RAG base",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to add"}
                },
                "required": ["content"]
            }
        )
    ]

@server.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls"""
    name = request.params.name
    arguments = request.params.arguments or {}
    
    if name == "rag_test":
        message = arguments.get("message", "No message provided")
        return CallToolResult(
            content=[TextContent(text=f"✅ RAG Server is working! Your message: {message}")]
        )
    
    elif name == "rag_search":
        query = arguments.get("query", "").lower()
        # Simple keyword search
        results = []
        for item in knowledge_base:
            if query in item.lower():
                results.append(item)
        
        if results:
            response = "Found matches:\n" + "\n".join(f"• {r}" for r in results)
        else:
            response = f"No results found for '{query}'"
        
        return CallToolResult(
            content=[TextContent(text=response)]
        )
    
    elif name == "rag_add":
        content = arguments.get("content", "")
        if content:
            knowledge_base.append(content)
            return CallToolResult(
                content=[TextContent(text=f"✅ Added to knowledge base: {content}")]
            )
        else:
            return CallToolResult(
                content=[TextContent(text="❌ No content provided")],
                isError=True
            )
    
    else:
        return CallToolResult(
            content=[TextContent(text=f"Unknown tool: {name}")],
            isError=True
        )

async def main():
    """Main entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, None)

if __name__ == "__main__":
    asyncio.run(main())