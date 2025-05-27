#!/usr/bin/env python3
"""
Monitor em tempo real para indexação automática de arquivos Claude
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
import aiohttp
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClaudeFileHandler(FileSystemEventHandler):
    """Handler para monitorar mudanças em arquivos Claude"""
    
    def __init__(self, mcp_command: str = "mcp__rag-webfetch__"):
        self.mcp_command = mcp_command
        self.pending_files: Set[str] = set()
        self.loop = asyncio.new_event_loop()
        self.watched_extensions = {'.jsonl', '.json', '.md', '.txt'}
        
    def on_modified(self, event: FileModifiedEvent):
        if not event.is_directory and self._should_index(event.src_path):
            logger.info(f"Arquivo modificado: {event.src_path}")
            self.pending_files.add(event.src_path)
            
    def on_created(self, event: FileCreatedEvent):
        if not event.is_directory and self._should_index(event.src_path):
            logger.info(f"Arquivo criado: {event.src_path}")
            self.pending_files.add(event.src_path)
            
    def _should_index(self, file_path: str) -> bool:
        """Verifica se o arquivo deve ser indexado"""
        path = Path(file_path)
        
        # Verificar extensão
        if path.suffix not in self.watched_extensions:
            return False
            
        # Verificar se é arquivo Claude relevante
        path_str = str(path)
        if any(pattern in path_str for pattern in [
            '/sessions/', '/todos/', '/projects/', 'CLAUDE.md'
        ]):
            return True
            
        return False
        
    async def process_pending_files(self):
        """Processa arquivos pendentes para indexação"""
        if not self.pending_files:
            return
            
        files_to_process = list(self.pending_files)
        self.pending_files.clear()
        
        for file_path in files_to_process:
            try:
                await self._index_file(file_path)
            except Exception as e:
                logger.error(f"Erro ao indexar {file_path}: {e}")
                
    async def _index_file(self, file_path: str):
        """Indexa um arquivo específico"""
        path = Path(file_path)
        
        # Determinar tipo de arquivo
        if '/sessions/' in str(path) and path.suffix == '.jsonl':
            await self._index_session_file(path)
        elif '/todos/' in str(path) and path.suffix == '.json':
            await self._index_todo_file(path)
        elif path.name == 'CLAUDE.md':
            await self._index_claude_md(path)
        else:
            await self._index_generic_file(path)
            
    async def _index_session_file(self, path: Path):
        """Indexa arquivo de sessão Claude"""
        logger.info(f"Indexando sessão: {path}")
        
        try:
            # Usar o MCP para indexar via ferramenta index_session
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "index_session",
                        "arguments": {
                            "session_path": str(path),
                            "chunk_size": 1000
                        }
                    },
                    "id": 1
                }
                
                async with session.post(
                    f"{self.indexer_url}/mcp",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    logger.info(f"Sessão indexada: {result}")
                    
        except Exception as e:
            logger.error(f"Erro ao indexar sessão {path}: {e}")
            
    async def _index_todo_file(self, path: Path):
        """Indexa arquivo de TODOs"""
        logger.info(f"Indexando TODOs: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                todos = json.load(f)
                
            # Preparar documento para indexação
            content = self._format_todos_content(todos)
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "add",
                        "arguments": {
                            "content": content,
                            "source": f"todos:{path.stem}",
                            "metadata": {
                                "type": "todos",
                                "file_path": str(path),
                                "project_id": path.stem
                            }
                        }
                    },
                    "id": 1
                }
                
                async with session.post(
                    f"{self.indexer_url}/mcp",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    logger.info(f"TODOs indexados: {result}")
                    
        except Exception as e:
            logger.error(f"Erro ao indexar TODOs {path}: {e}")
            
    async def _index_claude_md(self, path: Path):
        """Indexa arquivo CLAUDE.md"""
        logger.info(f"Indexando CLAUDE.md: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "add",
                        "arguments": {
                            "content": content,
                            "source": "CLAUDE.md",
                            "metadata": {
                                "type": "configuration",
                                "file_path": str(path),
                                "importance": "high"
                            }
                        }
                    },
                    "id": 1
                }
                
                async with session.post(
                    f"{self.indexer_url}/mcp",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    logger.info(f"CLAUDE.md indexado: {result}")
                    
        except Exception as e:
            logger.error(f"Erro ao indexar CLAUDE.md {path}: {e}")
            
    async def _index_generic_file(self, path: Path):
        """Indexa arquivo genérico"""
        logger.info(f"Indexando arquivo: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Limitar tamanho do conteúdo
            if len(content) > 10000:
                content = content[:10000] + "\n... (truncado)"
                
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "add",
                        "arguments": {
                            "content": content,
                            "source": f"file:{path.name}",
                            "metadata": {
                                "type": "document",
                                "file_path": str(path),
                                "extension": path.suffix
                            }
                        }
                    },
                    "id": 1
                }
                
                async with session.post(
                    f"{self.indexer_url}/mcp",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    logger.info(f"Arquivo indexado: {result}")
                    
        except Exception as e:
            logger.error(f"Erro ao indexar arquivo {path}: {e}")
            
    def _format_todos_content(self, todos: List[Dict]) -> str:
        """Formata TODOs para indexação"""
        lines = ["# TODOs do Projeto\n"]
        
        for todo in todos:
            status = todo.get('status', 'pending')
            priority = todo.get('priority', 'medium')
            content = todo.get('content', '')
            
            lines.append(f"- [{status}] [{priority}] {content}")
            
        return "\n".join(lines)


class RealtimeIndexer:
    """Indexador em tempo real para arquivos Claude"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.path.expanduser("~/.claude"))
        self.observer = Observer()
        self.handler = ClaudeFileHandler()
        
    def start(self):
        """Inicia o monitoramento"""
        # Diretórios para monitorar
        watch_dirs = [
            self.base_path / "sessions",
            self.base_path / "todos",
            self.base_path / "projects",
            self.base_path  # Para CLAUDE.md
        ]
        
        for watch_dir in watch_dirs:
            if watch_dir.exists():
                self.observer.schedule(
                    self.handler,
                    str(watch_dir),
                    recursive=True
                )
                logger.info(f"Monitorando: {watch_dir}")
                
        self.observer.start()
        logger.info("Monitor em tempo real iniciado")
        
    async def run(self):
        """Loop principal do monitor"""
        try:
            while True:
                # Processar arquivos pendentes a cada 5 segundos
                await self.handler.process_pending_files()
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        """Para o monitoramento"""
        self.observer.stop()
        self.observer.join()
        logger.info("Monitor em tempo real parado")


async def main():
    """Função principal"""
    indexer = RealtimeIndexer()
    indexer.start()
    
    try:
        await indexer.run()
    except KeyboardInterrupt:
        logger.info("Encerrando monitor...")
        indexer.stop()


if __name__ == "__main__":
    asyncio.run(main())