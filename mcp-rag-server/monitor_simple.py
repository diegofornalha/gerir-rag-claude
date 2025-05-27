#!/usr/bin/env python3
"""
Monitor simplificado para indexação em tempo real
Usa diretamente o cache local do RAG
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
import logging
import sys
import os

# Adicionar o diretório ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_rag import RAGIndex

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleRAGHandler(FileSystemEventHandler):
    """Handler simplificado para monitorar e indexar arquivos"""
    
    def __init__(self):
        self.rag_index = RAGIndex()
        self.pending_files: Set[str] = set()
        self.watched_extensions = {'.jsonl', '.json', '.md', '.txt'}
        
    def on_modified(self, event):
        if not event.is_directory and self._should_index(event.src_path):
            logger.info(f"Arquivo modificado: {event.src_path}")
            self.pending_files.add(event.src_path)
            self.process_file(event.src_path)
            
    def on_created(self, event):
        if not event.is_directory and self._should_index(event.src_path):
            logger.info(f"Arquivo criado: {event.src_path}")
            self.pending_files.add(event.src_path)
            self.process_file(event.src_path)
            
    def _should_index(self, file_path: str) -> bool:
        """Verifica se o arquivo deve ser indexado"""
        path = Path(file_path)
        
        # Verificar extensão
        if path.suffix not in self.watched_extensions:
            return False
            
        # Verificar se é arquivo Claude relevante
        path_str = str(path)
        relevant_patterns = [
            '/sessions/', '/todos/', '/projects/', 
            'CLAUDE.md', '/mcp-rag-cache/'
        ]
        
        return any(pattern in path_str for pattern in relevant_patterns)
        
    def process_file(self, file_path: str):
        """Processa um arquivo para indexação"""
        try:
            path = Path(file_path)
            
            # Ignorar arquivos do próprio cache
            if 'mcp-rag-cache' in str(path):
                return
                
            # Determinar tipo e processar
            if '/sessions/' in str(path) and path.suffix == '.jsonl':
                self._index_session_file(path)
            elif '/todos/' in str(path) and path.suffix == '.json':
                self._index_todo_file(path)
            elif path.name == 'CLAUDE.md':
                self._index_claude_md(path)
            else:
                self._index_generic_file(path)
                
        except Exception as e:
            logger.error(f"Erro ao processar {file_path}: {e}")
            
    def _index_session_file(self, path: Path):
        """Indexa arquivo de sessão Claude"""
        logger.info(f"Indexando sessão: {path.name}")
        
        try:
            # Usar chunking para sessões grandes
            from session_indexer import chunk_session_content
            
            chunks = chunk_session_content(path, chunk_size=1000)
            added = 0
            
            for chunk in chunks:
                doc_id, is_new = self.rag_index.add_document(
                    content=chunk['content'],
                    source=chunk['source'],
                    metadata=chunk['metadata']
                )
                if is_new:
                    added += 1
                    
            logger.info(f"✅ Sessão indexada: {added} chunks de {path.name}")
            
        except Exception as e:
            # Fallback para indexação simples
            try:
                content = path.read_text(encoding='utf-8')
                # Limitar tamanho
                if len(content) > 50000:
                    content = content[:50000] + "\n... (truncado)"
                    
                doc_id, is_new = self.rag_index.add_document(
                    content=content,
                    source=f"session:{path.stem}",
                    metadata={
                        "type": "session",
                        "file_path": str(path),
                        "project_id": path.stem
                    }
                )
                
                if is_new:
                    logger.info(f"✅ Sessão indexada (simples): {path.name}")
                    
            except Exception as e2:
                logger.error(f"Erro ao indexar sessão {path}: {e2}")
                
    def _index_todo_file(self, path: Path):
        """Indexa arquivo de TODOs"""
        logger.info(f"Indexando TODOs: {path.name}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                todos = json.load(f)
                
            # Formatar conteúdo
            lines = [f"# TODOs - {path.stem}\n"]
            
            for todo in todos:
                status = todo.get('status', 'pending')
                priority = todo.get('priority', 'medium')
                content = todo.get('content', '')
                
                icon = {
                    'completed': '✅',
                    'in_progress': '🔄',
                    'pending': '⏳'
                }.get(status, '❓')
                
                lines.append(f"{icon} [{priority}] {content}")
                
            content = "\n".join(lines)
            
            doc_id, is_new = self.rag_index.add_document(
                content=content,
                source=f"todos:{path.stem}",
                metadata={
                    "type": "todos",
                    "file_path": str(path),
                    "project_id": path.stem,
                    "todo_count": len(todos)
                }
            )
            
            if is_new:
                logger.info(f"✅ TODOs indexados: {path.name} ({len(todos)} itens)")
                
        except Exception as e:
            logger.error(f"Erro ao indexar TODOs {path}: {e}")
            
    def _index_claude_md(self, path: Path):
        """Indexa arquivo CLAUDE.md"""
        logger.info(f"Indexando CLAUDE.md")
        
        try:
            content = path.read_text(encoding='utf-8')
            
            doc_id, is_new = self.rag_index.add_document(
                content=content,
                source="CLAUDE.md",
                metadata={
                    "type": "configuration",
                    "file_path": str(path),
                    "importance": "high"
                }
            )
            
            if is_new:
                logger.info("✅ CLAUDE.md indexado")
            else:
                logger.info("⚠️ CLAUDE.md atualizado")
                
        except Exception as e:
            logger.error(f"Erro ao indexar CLAUDE.md: {e}")
            
    def _index_generic_file(self, path: Path):
        """Indexa arquivo genérico"""
        logger.info(f"Indexando arquivo: {path.name}")
        
        try:
            content = path.read_text(encoding='utf-8')
            
            # Limitar tamanho
            if len(content) > 10000:
                content = content[:10000] + "\n... (truncado)"
                
            doc_id, is_new = self.rag_index.add_document(
                content=content,
                source=f"file:{path.name}",
                metadata={
                    "type": "document",
                    "file_path": str(path),
                    "extension": path.suffix
                }
            )
            
            if is_new:
                logger.info(f"✅ Arquivo indexado: {path.name}")
                
        except Exception as e:
            logger.error(f"Erro ao indexar arquivo {path}: {e}")


def main():
    """Função principal"""
    # Diretórios para monitorar
    base_path = Path.home() / ".claude"
    watch_dirs = [
        base_path / "sessions",
        base_path / "todos",
        base_path / "projects",
        base_path  # Para CLAUDE.md
    ]
    
    # Criar handler e observer
    handler = SimpleRAGHandler()
    observer = Observer()
    
    # Adicionar diretórios ao observer
    for watch_dir in watch_dirs:
        if watch_dir.exists():
            observer.schedule(
                handler,
                str(watch_dir),
                recursive=True
            )
            logger.info(f"📁 Monitorando: {watch_dir}")
            
    # Iniciar monitoramento
    observer.start()
    logger.info("🚀 Monitor RAG em tempo real iniciado!")
    logger.info(f"📊 Cache atual: {len(handler.rag_index.documents)} documentos")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("🛑 Monitor encerrado")
        
    observer.join()


if __name__ == "__main__":
    main()