#\!/usr/bin/env python3
"""
Sistema de Indexação em Tempo Real para RAG
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime

class RealtimeIndexer:
    """Indexador em tempo real simplificado"""
    
    def __init__(self):
        self.watch_dirs = [
            Path.home() / ".claude" / "projects",
            Path.home() / ".claude" / "todos"
        ]
        self.last_check = {}
    
    async def monitor_changes(self):
        """Monitora mudanças nos diretórios"""
        print("🚀 Monitoramento em tempo real iniciado...")
        
        while True:
            for watch_dir in self.watch_dirs:
                if watch_dir.exists():
                    await self.check_directory(watch_dir)
            
            await asyncio.sleep(5)  # Verificar a cada 5 segundos
    
    async def check_directory(self, directory: Path):
        """Verifica mudanças em um diretório"""
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.jsonl', '.json', '.md']:
                mtime = file_path.stat().st_mtime
                
                if file_path not in self.last_check or self.last_check[file_path] < mtime:
                    print(f"  📄 Mudança detectada: {file_path.name}")
                    await self.index_file(file_path)
                    self.last_check[file_path] = mtime
    
    async def index_file(self, file_path: Path):
        """Indexa arquivo modificado"""
        print(f"    → Indexando {file_path.suffix} arquivo...")
        # Aqui conectaria com o servidor MCP

if __name__ == "__main__":
    indexer = RealtimeIndexer()
    asyncio.run(indexer.monitor_changes())
EOF < /dev/null