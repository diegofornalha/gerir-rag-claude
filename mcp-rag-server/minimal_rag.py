#!/usr/bin/env python3
"""
Minimal RAG MCP Server
"""

import json
import sys
import os

# Add MCP to path
sys.path.insert(0, '/opt/homebrew/lib/python3.13/site-packages')

try:
    from mcp import run_stdio_server
    from mcp.types import Tool, TextContent
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)

async def list_tools():
    """List available tools"""
    return [
        Tool(
            name="rag_test",
            description="Test RAG server",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Test message"}
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="rag_search",
            description="Search in RAG index",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
    ]

async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    if name == "rag_test":
        message = arguments.get("message", "No message")
        return [TextContent(text=f"RAG Server OK! Message: {message}")]
    
    elif name == "rag_search":
        query = arguments.get("query", "")
        # Simple mock search
        results = [
            f"Result 1 for '{query}': Claude Code documentation",
            f"Result 2 for '{query}': MCP integration guide"
        ]
        return [TextContent(text="\n".join(results))]
    
    else:
        return [TextContent(text=f"Unknown tool: {name}")]

def main():
    """Main entry point"""
    server_config = {
        "name": "rag-webfetch",
        "version": "0.1.0"
    }
    
    run_stdio_server(
        server_config,
        list_tools_handler=list_tools,
        call_tool_handler=call_tool
    )

if __name__ == "__main__":
    main()