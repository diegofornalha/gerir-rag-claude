#!/usr/bin/env python3
"""
Simple RAG MCP Server
"""

import json
import sys
import asyncio
from pathlib import Path

# MCP imports
sys.path.append(str(Path(__file__).parent.parent))
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    INTERNAL_ERROR
)

class SimpleRAGServer:
    def __init__(self):
        self.server = Server("rag-webfetch")
        self.cache_dir = Path.home() / ".claude" / "mcp-rag-cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Setup handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="rag_test",
                    description="Test RAG connection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "Test message"}
                        },
                        "required": ["message"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            if request.params.name == "rag_test":
                message = request.params.arguments.get("message", "No message")
                return CallToolResult(
                    content=[TextContent(text=f"RAG Server working! Your message: {message}")]
                )
            
            return CallToolResult(
                content=[TextContent(text=f"Unknown tool: {request.params.name}")],
                isError=True
            )
    
    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, None)

if __name__ == "__main__":
    server = SimpleRAGServer()
    asyncio.run(server.run())