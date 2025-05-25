#!/usr/bin/env python3
"""
Sincronização automática do .claude com Google Drive
Monitora mudanças e sincroniza em tempo real
"""

import os
import shutil
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import json

# Configurações
SOURCE_DIR = "/Users/agents/.claude"
DEST_DIR = "/Users/agents/Library/CloudStorage/GoogleDrive-diegodg3web@gmail.com/Meu Drive/.claude_backup"

# Itens para sincronizar
SYNC_ITEMS = [
    "projects",
    "todos", 
    "lightrag",
    "CLAUDE.md",
    "custom_project_names.json"
]

# Padrões para ignorar
IGNORE_PATTERNS = [
    "*.log",
    "*.pid",
    "node_modules",
    "__pycache__",
    ".DS_Store",
    "*.pyc",
    "*.lock"
]

class SyncHandler(FileSystemEventHandler):
    """Handler para eventos de mudança no sistema de arquivos"""
    
    def __init__(self):
        self.last_sync = {}
        
    def should_ignore(self, path):
        """Verifica se o arquivo deve ser ignorado"""
        for pattern in IGNORE_PATTERNS:
            if pattern.replace("*", "") in path:
                return True
        return False
    
    def sync_file(self, src_path):
        """Sincroniza um arquivo específico"""
        if self.should_ignore(src_path):
            return
            
        # Calcular caminho relativo
        rel_path = os.path.relpath(src_path, SOURCE_DIR)
        
        # Verificar se está em uma pasta que queremos sincronizar
        for item in SYNC_ITEMS:
            if rel_path.startswith(item):
                dest_path = os.path.join(DEST_DIR, rel_path)
                
                # Criar diretório se necessário
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)
                
                # Copiar arquivo
                try:
                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dest_path)
                        print(f"✅ Sincronizado: {rel_path}")
                except Exception as e:
                    print(f"❌ Erro ao sincronizar {rel_path}: {e}")
                    
    def on_modified(self, event):
        if not event.is_directory:
            self.sync_file(event.src_path)
            
    def on_created(self, event):
        if not event.is_directory:
            self.sync_file(event.src_path)
            
    def on_deleted(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            rel_path = os.path.relpath(event.src_path, SOURCE_DIR)
            dest_path = os.path.join(DEST_DIR, rel_path)
            
            try:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                    print(f"🗑️  Removido: {rel_path}")
            except Exception as e:
                print(f"❌ Erro ao remover {rel_path}: {e}")

def initial_sync():
    """Faz a sincronização inicial completa"""
    print("🔄 Iniciando sincronização completa...")
    
    # Criar diretório de destino
    os.makedirs(DEST_DIR, exist_ok=True)
    
    # Sincronizar cada item
    for item in SYNC_ITEMS:
        src = os.path.join(SOURCE_DIR, item)
        if os.path.exists(src):
            dest = os.path.join(DEST_DIR, item)
            
            try:
                if os.path.isfile(src):
                    shutil.copy2(src, dest)
                else:
                    # Usar rsync para diretórios
                    cmd = [
                        "rsync", "-av", "--delete",
                        "--exclude=*.log",
                        "--exclude=*.pid",
                        "--exclude=node_modules/",
                        "--exclude=__pycache__/",
                        "--exclude=.DS_Store",
                        src + "/", dest + "/"
                    ]
                    subprocess.run(cmd, check=True)
                
                print(f"✅ {item} sincronizado")
            except Exception as e:
                print(f"❌ Erro ao sincronizar {item}: {e}")
    
    # Criar arquivo de timestamp
    with open(os.path.join(DEST_DIR, "last_sync.txt"), "w") as f:
        f.write(f"Última sincronização: {datetime.now()}\n")
    
    print("✅ Sincronização inicial concluída!")

def main():
    """Função principal"""
    print("🚀 Iniciando sincronização automática .claude -> Google Drive")
    print(f"📁 Origem: {SOURCE_DIR}")
    print(f"☁️  Destino: {DEST_DIR}")
    print("")
    
    # Sincronização inicial
    initial_sync()
    
    # Configurar observador
    event_handler = SyncHandler()
    observer = Observer()
    observer.schedule(event_handler, SOURCE_DIR, recursive=True)
    
    # Iniciar monitoramento
    observer.start()
    print("\n👀 Monitorando mudanças...")
    print("   Pressione Ctrl+C para parar")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Sincronização parada")
    
    observer.join()

if __name__ == "__main__":
    main()