#!/usr/bin/env python3
"""
Monitor com polling para indexação em tempo real
Sem dependências externas
"""

import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List
import hashlib
import logging

# Adicionar o diretório ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_rag import RAGIndex

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileMonitor:
    """Monitor de arquivos usando polling"""
    
    def __init__(self, poll_interval: float = 5.0):
        self.rag_index = RAGIndex()
        self.poll_interval = poll_interval
        self.file_hashes: Dict[str, str] = {}
        self.watched_extensions = {'.jsonl', '.json', '.md', '.txt'}
        self.base_path = Path.home() / ".claude"
        
    def get_file_hash(self, file_path: Path) -> str:
        """Calcula hash do arquivo"""
        try:
            content = file_path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except:
            return ""
            
    def scan_directory(self, directory: Path) -> List[Path]:
        """Escaneia diretório recursivamente"""
        files = []
        try:
            for item in directory.rglob("*"):
                if item.is_file() and item.suffix in self.watched_extensions:
                    # Ignorar arquivos do cache
                    if 'mcp-rag-cache' not in str(item):
                        files.append(item)
        except:
            pass
        return files
        
    def check_for_changes(self):
        """Verifica mudanças nos arquivos"""
        # Diretórios para monitorar
        watch_dirs = [
            self.base_path / "sessions",
            self.base_path / "todos",
            self.base_path / "projects",
            self.base_path  # Para CLAUDE.md
        ]
        
        all_files = []
        for watch_dir in watch_dirs:
            if watch_dir.exists():
                all_files.extend(self.scan_directory(watch_dir))
                
        # Verificar mudanças
        for file_path in all_files:
            current_hash = self.get_file_hash(file_path)
            
            if current_hash:
                str_path = str(file_path)
                
                # Arquivo novo ou modificado
                if str_path not in self.file_hashes or self.file_hashes[str_path] != current_hash:
                    self.file_hashes[str_path] = current_hash
                    self.process_file(file_path)
                    
    def process_file(self, file_path: Path):
        """Processa arquivo para indexação"""
        try:
            logger.info(f"📄 Processando: {file_path.name}")
            
            # Determinar tipo e processar
            if '/sessions/' in str(file_path) and file_path.suffix == '.jsonl':
                self._index_session_file(file_path)
            elif '/todos/' in str(file_path) and file_path.suffix == '.json':
                self._index_todo_file(file_path)
            elif file_path.name == 'CLAUDE.md':
                self._index_claude_md(file_path)
            else:
                self._index_generic_file(file_path)
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar {file_path}: {e}")
            
    def _index_session_file(self, path: Path):
        """Indexa arquivo de sessão"""
        try:
            # Tentar usar chunking
            try:
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
                        
                if added > 0:
                    logger.info(f"✅ Sessão indexada: {added} chunks de {path.name}")
                    
            except ImportError:
                # Fallback simples
                content = path.read_text(encoding='utf-8')[:50000]
                doc_id, is_new = self.rag_index.add_document(
                    content=content,
                    source=f"session:{path.stem}",
                    metadata={"type": "session", "file": path.name}
                )
                if is_new:
                    logger.info(f"✅ Sessão indexada: {path.name}")
                    
        except Exception as e:
            logger.error(f"Erro na sessão {path}: {e}")
            
    def _index_todo_file(self, path: Path):
        """Indexa arquivo de TODOs"""
        try:
            with open(path, 'r') as f:
                todos = json.load(f)
                
            lines = [f"# TODOs - {path.stem}\n"]
            stats = {'completed': 0, 'in_progress': 0, 'pending': 0}
            
            for todo in todos:
                status = todo.get('status', 'pending')
                stats[status] = stats.get(status, 0) + 1
                priority = todo.get('priority', 'medium')
                content = todo.get('content', '')
                
                icon = {
                    'completed': '✅',
                    'in_progress': '🔄', 
                    'pending': '⏳'
                }.get(status, '❓')
                
                lines.append(f"{icon} [{priority}] {content}")
                
            # Adicionar estatísticas
            lines.insert(1, f"\n📊 Total: {len(todos)} | ✅ {stats['completed']} | 🔄 {stats['in_progress']} | ⏳ {stats['pending']}\n")
            
            content = "\n".join(lines)
            
            doc_id, is_new = self.rag_index.add_document(
                content=content,
                source=f"todos:{path.stem}",
                metadata={
                    "type": "todos",
                    "file": path.name,
                    "stats": stats
                }
            )
            
            if is_new:
                logger.info(f"✅ TODOs indexados: {path.name} ({len(todos)} itens)")
                
        except Exception as e:
            logger.error(f"Erro nos TODOs {path}: {e}")
            
    def _index_claude_md(self, path: Path):
        """Indexa CLAUDE.md"""
        try:
            content = path.read_text(encoding='utf-8')
            
            doc_id, is_new = self.rag_index.add_document(
                content=content,
                source="CLAUDE.md",
                metadata={
                    "type": "configuration",
                    "importance": "high"
                }
            )
            
            if is_new:
                logger.info("✅ CLAUDE.md indexado")
            else:
                logger.info("⚠️ CLAUDE.md atualizado")
                
        except Exception as e:
            logger.error(f"Erro no CLAUDE.md: {e}")
            
    def _index_generic_file(self, path: Path):
        """Indexa arquivo genérico"""
        try:
            content = path.read_text(encoding='utf-8')[:10000]
            
            doc_id, is_new = self.rag_index.add_document(
                content=content,
                source=f"file:{path.name}",
                metadata={
                    "type": "document",
                    "extension": path.suffix
                }
            )
            
            if is_new:
                logger.info(f"✅ Arquivo indexado: {path.name}")
                
        except Exception as e:
            logger.error(f"Erro no arquivo {path}: {e}")
            
    def run(self):
        """Loop principal do monitor"""
        logger.info("🚀 Monitor RAG iniciado (modo polling)")
        logger.info(f"📊 Cache inicial: {len(self.rag_index.documents)} documentos")
        logger.info(f"⏱️ Intervalo de verificação: {self.poll_interval}s")
        
        try:
            while True:
                self.check_for_changes()
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitor encerrado")
            logger.info(f"📊 Cache final: {len(self.rag_index.documents)} documentos")


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor RAG com polling")
    parser.add_argument(
        "--interval", 
        type=float, 
        default=5.0,
        help="Intervalo de polling em segundos (padrão: 5.0)"
    )
    
    args = parser.parse_args()
    
    monitor = FileMonitor(poll_interval=args.interval)
    monitor.run()


if __name__ == "__main__":
    main()