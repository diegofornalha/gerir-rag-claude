#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema aprimorado de monitoramento para LightRAG
Gerenciamento de documentos baseado em SQLite e verificação de hash de conteúdo
"""

import os
import sys
import time
import json
import hashlib
import logging
import sqlite3
import urllib.request
import urllib.parse
import glob
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuração
LIGHTRAG_URL = "http://127.0.0.1:5000"
BASE_PROJECTS_DIR = "/Users/agents/.claude/projects"
POLL_INTERVAL = 5.0  # segundos entre verificações
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs/improved_monitor.log")
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents.db")
SYNC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sync_timestamp")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('improved_monitor')

def create_database():
    """Cria o banco de dados SQLite com a estrutura necessária"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Tabela principal para rastrear documentos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            file_path TEXT PRIMARY KEY,
            doc_id TEXT,
            content_hash TEXT,
            file_size INTEGER,
            last_modified INTEGER,
            last_checked INTEGER,
            metadata TEXT
        )
        ''')
        
        # Índices para pesquisa eficiente
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_id ON documents (doc_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_hash ON documents (content_hash)')
        
        conn.commit()
        conn.close()
        logger.info(f"Banco de dados inicializado: {DB_FILE}")
        
    except Exception as e:
        logger.error(f"Erro ao criar banco de dados: {e}")
        sys.exit(1)

def update_sync_timestamp():
    """Atualiza o timestamp de sincronização para notificar o Streamlit"""
    try:
        with open(SYNC_FILE, 'w') as f:
            f.write(str(time.time()))
        logger.debug("Timestamp de sincronização atualizado")
    except Exception as e:
        logger.error(f"Erro ao atualizar timestamp de sincronização: {e}")

def calculate_file_hash(file_path):
    """Calcula o hash SHA-256 do conteúdo do arquivo"""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Ler o arquivo em blocos para não consumir muita memória
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Erro ao calcular hash do arquivo {file_path}: {e}")
        return None

def check_server():
    """Verifica se o servidor LightRAG está ativo"""
    try:
        with urllib.request.urlopen(f"{LIGHTRAG_URL}/status") as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                logger.info(f"✅ LightRAG está rodando. Documentos: {data.get('documents', 0)}")
                return data.get('documents', 0)
            else:
                logger.error("❌ LightRAG respondeu com erro.")
                return None
    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao LightRAG: {e}")
        return None

def get_existing_documents():
    """Recupera todos os documentos existentes no LightRAG"""
    try:
        data = json.dumps({"query": "*", "max_results": 100}).encode('utf-8')
        req = urllib.request.Request(
            f"{LIGHTRAG_URL}/query",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            contexts = result.get('context', [])
            return contexts
    except Exception as e:
        logger.error(f"Erro ao recuperar documentos: {e}")
        return []

def delete_document(doc_id):
    """Exclui um documento do LightRAG pelo seu ID"""
    if not doc_id:
        return False
    
    try:
        # Preparar dados para exclusão
        data = {"id": doc_id}
        encoded_data = json.dumps(data).encode('utf-8')
        
        # Criar e enviar requisição
        req = urllib.request.Request(
            f"{LIGHTRAG_URL}/delete",
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if result.get("success", False):
            logger.info(f"Documento excluído com sucesso: {doc_id}")
            return True
        else:
            logger.error(f"Erro ao excluir documento: {result.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao excluir documento {doc_id}: {e}")
        return False

def insert_document(file_path, content=None):
    """Insere um documento no LightRAG se ele ainda não existir"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return False
        
        # Verificar tamanho do arquivo
        file_size = os.path.getsize(file_path)
        if file_size < 100:  # arquivos muito pequenos são provavelmente inválidos
            logger.warning(f"Arquivo muito pequeno para ser válido: {file_path}")
            return False
        
        # Calcular hash do conteúdo
        content_hash = calculate_file_hash(file_path)
        if not content_hash:
            return False
        
        # Verificar se já temos um documento com este arquivo
        cursor.execute("SELECT doc_id FROM documents WHERE file_path = ?", (file_path,))
        path_match = cursor.fetchone()
        
        if path_match:
            # Excluir o documento antigo do LightRAG e do banco
            delete_document(path_match[0])
            cursor.execute("DELETE FROM documents WHERE doc_id = ?", (path_match[0],))
            logger.info(f"Documento existente removido para atualização: {path_match[0]}")
            
        # Verificar se temos um documento com este hash
        cursor.execute("SELECT doc_id FROM documents WHERE content_hash = ? AND file_path != ?", (content_hash, file_path))
        hash_match = cursor.fetchone()
        
        if hash_match:
            doc_id = hash_match[0]
            logger.info(f"Documento com hash idêntico já existe: {doc_id}")
            
            # Atualizar registro com este arquivo
            cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            logger.info(f"Removido documento duplicado: {doc_id}")
            
            # Continuar para criar um novo
        
        # Ler o conteúdo do arquivo se não foi fornecido
        if not content:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # Gerar resumo do arquivo
        file_name = os.path.basename(file_path)
        summary = f"Conversa Claude: {file_name}"
        
        # Metadados para rastreamento
        metadata = {
            "file_path": file_path,
            "file_name": file_name,
            "content_hash": content_hash,
            "imported_at": datetime.now().isoformat()
        }
        
        # Preparar dados para inserção no LightRAG
        source_id = f"file_{content_hash[:8]}"  # ID baseado no hash, não no nome do arquivo
        data = {
            "text": content,
            "summary": summary,
            "source": source_id,
            "metadata": metadata
        }
        
        # Enviar para o LightRAG
        encoded_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            f"{LIGHTRAG_URL}/insert",
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        if result.get("success", False):
            doc_id = result.get("documentId", "")
            
            # Salvar no banco de dados
            cursor.execute(
                "INSERT INTO documents (file_path, doc_id, content_hash, file_size, last_modified, last_checked, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (file_path, doc_id, content_hash, file_size, os.path.getmtime(file_path), time.time(), json.dumps(metadata))
            )
            conn.commit()
            
            logger.info(f"✅ Documento inserido com sucesso: {file_name} (ID: {doc_id})")
            update_sync_timestamp()
            return True
        else:
            error = result.get("error", "Erro desconhecido")
            logger.error(f"Erro ao inserir documento: {error}")
            return False
    
    except Exception as e:
        logger.error(f"Erro ao processar arquivo {file_path}: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def handle_deleted_file(file_path):
    """Trata um arquivo que foi excluído, removendo-o do LightRAG"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Buscar documento relacionado no banco
        cursor.execute("SELECT doc_id FROM documents WHERE file_path = ?", (file_path,))
        result = cursor.fetchone()
        
        if result:
            doc_id = result[0]
            
            # Excluir do LightRAG
            if delete_document(doc_id):
                # Remover do banco de dados local
                cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
                conn.commit()
                logger.info(f"Documento excluído após remoção do arquivo: {file_path}")
                update_sync_timestamp()
                return True
        else:
            logger.info(f"Arquivo excluído não estava no banco de dados: {file_path}")
        
        return False
    
    except Exception as e:
        logger.error(f"Erro ao processar exclusão do arquivo {file_path}: {e}")
        return False
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def find_project_dirs():
    """Encontra automaticamente todos os diretórios de projetos"""
    project_dirs = []
    
    # Verificar se o diretório base existe
    if not os.path.exists(BASE_PROJECTS_DIR):
        logger.warning(f"Diretório base não encontrado: {BASE_PROJECTS_DIR}")
        return project_dirs
    
    # Procurar por diretórios de projetos
    try:
        # Listar todos os itens no diretório base
        for item in os.listdir(BASE_PROJECTS_DIR):
            full_path = os.path.join(BASE_PROJECTS_DIR, item)
            # Verificar se é um diretório
            if os.path.isdir(full_path):
                # Verificar se tem arquivos JSONL
                if glob.glob(f"{full_path}/*.jsonl"):
                    project_dirs.append(full_path)
    except Exception as e:
        logger.error(f"Erro ao procurar diretórios de projetos: {e}")
    
    return project_dirs

def sync_database_with_server():
    """Sincroniza o banco de dados local com o servidor LightRAG"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Obter lista de documentos do servidor
        server_docs = get_existing_documents()
        if not server_docs:
            logger.info("Nenhum documento no servidor para sincronizar")
            conn.close()
            return
        
        # Mapear documentos do servidor por ID
        server_doc_ids = {doc.get('document_id', ''): doc for doc in server_docs}
        
        # Buscar documentos do banco de dados local
        cursor.execute("SELECT doc_id, file_path FROM documents")
        local_docs = cursor.fetchall()
        
        # Documentos que estão no servidor mas não no banco local
        orphaned_docs = []
        for doc_id in server_doc_ids:
            if doc_id and not any(ld[0] == doc_id for ld in local_docs):
                orphaned_docs.append(doc_id)
        
        # Excluir documentos órfãos do servidor
        for doc_id in orphaned_docs:
            logger.info(f"Excluindo documento órfão do servidor: {doc_id}")
            delete_document(doc_id)
        
        # Documentos que estão no banco local mas não existem no servidor
        missing_docs = []
        for doc_id, file_path in local_docs:
            if doc_id and doc_id not in server_doc_ids:
                missing_docs.append((doc_id, file_path))
        
        # Remover documentos inexistentes do banco local
        for doc_id, file_path in missing_docs:
            cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            logger.info(f"Removido do banco local: {doc_id} (arquivo: {file_path})")
        
        conn.commit()
        
        if orphaned_docs or missing_docs:
            logger.info(f"Sincronização concluída: {len(orphaned_docs)} excluídos do servidor, {len(missing_docs)} removidos do banco local")
            update_sync_timestamp()
    
    except Exception as e:
        logger.error(f"Erro durante sincronização: {e}")
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def sync_files_with_database():
    """Sincroniza os arquivos do sistema com o banco de dados"""
    try:
        # Encontrar todos os arquivos JSONL nos diretórios de projetos
        existing_files = []
        project_dirs = find_project_dirs()
        
        for proj_dir in project_dirs:
            if os.path.exists(proj_dir):
                jsonl_files = glob.glob(f"{proj_dir}/*.jsonl")
                existing_files.extend(jsonl_files)
        
        if not existing_files:
            logger.info("Nenhum arquivo JSONL encontrado para sincronizar")
            return
        
        logger.info(f"Sincronizando {len(existing_files)} arquivos com o banco de dados")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Buscar arquivos registrados no banco
        cursor.execute("SELECT file_path FROM documents")
        db_files = [row[0] for row in cursor.fetchall()]
        
        # Arquivos no sistema que não estão no banco
        new_files = [f for f in existing_files if f not in db_files]
        
        # Arquivos no banco que não existem mais no sistema
        deleted_files = [f for f in db_files if f not in existing_files]
        
        # Processar novos arquivos
        for file_path in new_files:
            logger.info(f"Processando novo arquivo: {os.path.basename(file_path)}")
            insert_document(file_path)
        
        # Processar arquivos excluídos
        for file_path in deleted_files:
            logger.info(f"Processando arquivo removido: {os.path.basename(file_path)}")
            handle_deleted_file(file_path)
        
        if new_files or deleted_files:
            logger.info(f"Sincronização de arquivos concluída: {len(new_files)} novos, {len(deleted_files)} removidos")
            update_sync_timestamp()
        
    except Exception as e:
        logger.error(f"Erro durante sincronização de arquivos: {e}")
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()

class ProjectFileHandler(FileSystemEventHandler):
    """Manipulador de eventos do sistema de arquivos"""
    
    def on_created(self, event):
        """Quando um novo arquivo é criado"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            # Esperar um pouco para garantir que o arquivo está completo
            time.sleep(1)
            logger.info(f"Arquivo criado: {event.src_path}")
            insert_document(event.src_path)
    
    def on_modified(self, event):
        """Quando um arquivo é modificado"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            # Esperar um pouco para garantir que o arquivo está completo
            time.sleep(1)
            logger.info(f"Arquivo modificado: {event.src_path}")
            insert_document(event.src_path)
    
    def on_deleted(self, event):
        """Quando um arquivo é excluído"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            logger.info(f"Arquivo excluído: {event.src_path}")
            handle_deleted_file(event.src_path)

def main():
    """Função principal"""
    logger.info("=== Monitor Aprimorado para LightRAG ===")
    
    # Verificar se o servidor está disponível
    if check_server() is None:
        logger.error("Servidor LightRAG não está disponível. Execute ./start_lightrag.sh primeiro.")
        sys.exit(1)
    
    # Criar banco de dados se não existir
    create_database()
    
    # Criar arquivo de timestamp se não existir
    update_sync_timestamp()
    
    # Primeiro, sincronizar banco com servidor
    sync_database_with_server()
    
    # Depois, sincronizar arquivos com banco
    sync_files_with_database()
    
    # Iniciar monitoramento com watchdog
    project_dirs = find_project_dirs()
    if not project_dirs:
        logger.error("Nenhum diretório de projetos encontrado")
        sys.exit(1)
    
    logger.info(f"Iniciando monitoramento em {len(project_dirs)} diretórios")
    
    observer = Observer()
    event_handler = ProjectFileHandler()
    
    # Adicionar cada diretório para monitoramento
    for proj_dir in project_dirs:
        if os.path.exists(proj_dir):
            observer.schedule(event_handler, proj_dir, recursive=False)
            logger.info(f"Monitorando: {proj_dir}")
    
    # Iniciar observador
    observer.start()
    logger.info(f"Monitoramento ativo. Verificando a cada {POLL_INTERVAL} segundos")
    
    try:
        while True:
            time.sleep(POLL_INTERVAL)
            # Verificar por atualizações no servidor
            sync_database_with_server()
            # Verificar por atualizações no sistema de arquivos
            sync_files_with_database()
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuário")
        observer.stop()
    
    observer.join()
    logger.info("Monitor encerrado")

if __name__ == "__main__":
    main()