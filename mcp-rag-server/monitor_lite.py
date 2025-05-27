#!/usr/bin/env python3
"""
Monitor leve para indexação em tempo real
Funciona diretamente com o cache JSON sem numpy/sklearn
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List
import hashlib
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiteRAGMonitor:
    """Monitor leve que trabalha diretamente com o cache JSON"""
    
    def __init__(self, poll_interval: float = 5.0):
        self.poll_interval = poll_interval
        self.file_hashes: Dict[str, str] = {}
        self.watched_extensions = {'.jsonl', '.json', '.md', '.txt'}
        self.base_path = Path.home() / ".claude"
        self.cache_dir = self.base_path / "mcp-rag-cache"
        self.cache_file = self.cache_dir / "documents.json"
        
        # Criar diretório se não existir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Carregar cache existente
        self.documents = self._load_cache()
        
    def _load_cache(self) -> List[Dict]:
        """Carrega documentos do cache"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
        
    def _save_cache(self):
        """Salva documentos no cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
            
    def _generate_id(self, content: str) -> str:
        """Gera ID único para documento"""
        return hashlib.md5(content.encode()).hexdigest()[:8]
        
    def get_file_hash(self, file_path: Path) -> str:
        """Calcula hash do arquivo"""
        try:
            stat = file_path.stat()
            # Usar tamanho + mtime para detectar mudanças
            return f"{stat.st_size}_{stat.st_mtime}"
        except:
            return ""
            
    def add_document(self, content: str, source: str, metadata: dict = None) -> bool:
        """Adiciona documento ao cache"""
        doc_id = self._generate_id(content)
        
        # Verificar se já existe
        for doc in self.documents:
            if doc.get('id') == doc_id:
                return False
                
        # Criar novo documento
        document = {
            'id': doc_id,
            'content': content,
            'source': source,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.documents.append(document)
        self._save_cache()
        return True
        
    def scan_directory(self, directory: Path) -> List[Path]:
        """Escaneia diretório recursivamente"""
        files = []
        try:
            for item in directory.rglob("*"):
                if item.is_file() and item.suffix in self.watched_extensions:
                    path_str = str(item)
                    # Ignorar diretórios indesejados
                    skip_patterns = [
                        'mcp-rag-cache',
                        'node_modules',
                        '.pnpm',
                        '__pycache__',
                        '.git',
                        'dist',
                        'build'
                    ]
                    if not any(pattern in path_str for pattern in skip_patterns):
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
                # Verificar se é realmente um arquivo de TODOs
                if file_path.parent.name == 'todos':
                    self._index_todo_file(file_path)
                else:
                    self._index_generic_file(file_path)
            elif file_path.name == 'CLAUDE.md':
                self._index_claude_md(file_path)
            else:
                self._index_generic_file(file_path)
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar {file_path}: {e}")
            
    def _index_session_file(self, path: Path):
        """Indexa arquivo de sessão (simplificado)"""
        try:
            # Ler primeiras linhas para ter uma amostra
            lines = []
            with open(path, 'r') as f:
                for i, line in enumerate(f):
                    if i >= 100:  # Limitar a 100 linhas
                        break
                    lines.append(line)
                    
            content = ''.join(lines)
            
            # Extrair informações básicas
            user_messages = content.count('"role":"user"')
            assistant_messages = content.count('"role":"assistant"')
            
            summary = f"# Sessão Claude: {path.stem}\n\n"
            summary += f"📊 Estatísticas:\n"
            summary += f"- Mensagens do usuário: {user_messages}\n"
            summary += f"- Mensagens do assistente: {assistant_messages}\n"
            summary += f"- Total de interações: {user_messages + assistant_messages}\n\n"
            summary += f"## Amostra do conteúdo:\n{content[:2000]}..."
            
            added = self.add_document(
                content=summary,
                source=f"session:{path.stem}",
                metadata={
                    "type": "session",
                    "file": path.name,
                    "user_messages": user_messages,
                    "assistant_messages": assistant_messages
                }
            )
            
            if added:
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
            
            added = self.add_document(
                content=content,
                source=f"todos:{path.stem}",
                metadata={
                    "type": "todos",
                    "file": path.name,
                    "total": len(todos),
                    **stats
                }
            )
            
            if added:
                logger.info(f"✅ TODOs indexados: {path.name} ({len(todos)} itens)")
                
        except Exception as e:
            logger.error(f"Erro nos TODOs {path}: {e}")
            
    def _index_claude_md(self, path: Path):
        """Indexa CLAUDE.md"""
        try:
            content = path.read_text(encoding='utf-8')
            
            added = self.add_document(
                content=content,
                source="CLAUDE.md",
                metadata={
                    "type": "configuration",
                    "importance": "high"
                }
            )
            
            if added:
                logger.info("✅ CLAUDE.md indexado")
            else:
                logger.info("⚠️ CLAUDE.md já está no cache")
                
        except Exception as e:
            logger.error(f"Erro no CLAUDE.md: {e}")
            
    def _index_generic_file(self, path: Path):
        """Indexa arquivo genérico"""
        try:
            content = path.read_text(encoding='utf-8')
            
            # Limitar tamanho
            if len(content) > 10000:
                content = content[:10000] + "\n... (truncado)"
                
            added = self.add_document(
                content=content,
                source=f"file:{path.name}",
                metadata={
                    "type": "document",
                    "extension": path.suffix,
                    "size": len(content)
                }
            )
            
            if added:
                logger.info(f"✅ Arquivo indexado: {path.name}")
                
        except Exception as e:
            logger.error(f"Erro no arquivo {path}: {e}")
            
    def run(self):
        """Loop principal do monitor"""
        logger.info("🚀 Monitor RAG Lite iniciado")
        logger.info(f"📊 Cache inicial: {len(self.documents)} documentos")
        logger.info(f"📁 Cache em: {self.cache_file}")
        logger.info(f"⏱️ Intervalo: {self.poll_interval}s")
        logger.info("=" * 50)
        
        try:
            while True:
                self.check_for_changes()
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 50)
            logger.info("🛑 Monitor encerrado")
            logger.info(f"📊 Cache final: {len(self.documents)} documentos")


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor RAG Lite")
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Intervalo de verificação em segundos (padrão: 5.0)"
    )
    
    args = parser.parse_args()
    
    monitor = LiteRAGMonitor(poll_interval=args.interval)
    monitor.run()


if __name__ == "__main__":
    main()