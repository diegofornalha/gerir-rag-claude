#!/usr/bin/env python3
"""Minimal MCP Server for testing"""

import sys
import json

# Simple echo server that implements MCP protocol
while True:
    try:
        line = sys.stdin.readline()
        if not line:
            break
        
        request = json.loads(line)
        
        # Handle initialize
        if request.get("method") == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "rag-webfetch",
                        "version": "0.1.0"
                    }
                }
            }
            print(json.dumps(response))
            sys.stdout.flush()
        
        # Handle list_tools
        elif request.get("method") == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "tools": [
                        {
                            "name": "test",
                            "description": "Test tool",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            }
            print(json.dumps(response))
            sys.stdout.flush()
            
        # Handle tool calls
        elif request.get("method") == "tools/call":
            response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Test response"
                        }
                    ]
                }
            }
            print(json.dumps(response))
            sys.stdout.flush()
            
    except Exception as e:
        # Log error to stderr
        sys.stderr.write(f"Error: {e}\n")
        sys.stderr.flush()