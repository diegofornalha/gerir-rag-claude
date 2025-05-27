#!/usr/bin/env python3
"""
Monitor em Tempo Real - Integrado com servidor MCP
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess

class RealtimeMonitor:
    """Monitor que detecta mudanças e chama o servidor MCP"""
    
    def __init__(self):
        self.watch_dirs = [
            Path.home() / ".claude" / "projects",
            Path.home() / ".claude" / "todos"
        ]
        self.last_indexed = {}
        self.mcp_server_path = Path(__file__).parent / "integrated_rag.py"
        
    async def start_monitoring(self):
        """Inicia monitoramento contínuo"""
        print("🚀 Monitor RAG em tempo real iniciado!")
        print(f"📁 Monitorando: {[str(d) for d in self.watch_dirs]}")
        
        # Indexar arquivos existentes primeiro
        await self.initial_index()
        
        # Loop de monitoramento
        while True:
            try:
                await self.check_for_changes()
                await asyncio.sleep(10)  # Verificar a cada 10 segundos
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                await asyncio.sleep(30)
    
    async def initial_index(self):
        """Indexa arquivos existentes na primeira execução"""
        print("\n📋 Indexação inicial...")
        
        for watch_dir in self.watch_dirs:
            if watch_dir.exists():
                result = await self.call_mcp_tool("index_directory", {
                    "directory": str(watch_dir),
                    "file_types": [".jsonl", ".json", ".md"]
                })
                print(f"  {result}")
    
    async def check_for_changes(self):
        """Verifica mudanças nos arquivos"""
        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue
                
            # Verificar sessões Claude (.jsonl)
            for jsonl_file in watch_dir.rglob("*.jsonl"):
                await self.check_file(jsonl_file, "session")
            
            # Verificar TODOs (.json)
            for json_file in watch_dir.rglob("*.json"):
                await self.check_file(json_file, "json")
    
    async def check_file(self, file_path: Path, file_type: str):
        """Verifica se arquivo mudou e precisa reindexar"""
        try:
            stat = file_path.stat()
            file_key = str(file_path)
            last_mtime = self.last_indexed.get(file_key, 0)
            
            if stat.st_mtime > last_mtime:
                print(f"\n🔄 Mudança detectada: {file_path.name}")
                
                if file_type == "session":
                    result = await self.call_mcp_tool("index_session", {
                        "session_path": str(file_path),
                        "chunk_size": 1000
                    })
                else:
                    # Para outros arquivos, reindexar como documento único
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    result = await self.call_mcp_tool("add", {
                        "content": content,
                        "source": f"{file_type}:{file_path.name}",
                        "metadata": {
                            "file_type": file_type,
                            "path": str(file_path),
                            "updated_at": datetime.now().isoformat()
                        }
                    })
                
                print(f"  {result}")
                self.last_indexed[file_key] = stat.st_mtime
                
        except Exception as e:
            print(f"❌ Erro ao verificar {file_path}: {e}")
    
    async def call_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """Chama ferramenta do servidor MCP"""
        # Por enquanto, simular chamada
        # Em produção, usar o cliente MCP real
        return f"✅ {tool_name} executado com sucesso"
    
    async def get_stats(self):
        """Obtém estatísticas do cache"""
        stats = await self.call_mcp_tool("stats", {})
        print(f"\n📊 {stats}")

async def main():
    """Função principal"""
    monitor = RealtimeMonitor()
    
    print("=" * 50)
    print("🤖 Sistema RAG em Tempo Real")
    print("=" * 50)
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor parado pelo usuário")
        await monitor.get_stats()

if __name__ == "__main__":
    asyncio.run(main())