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

# Variáveis globais
sync_in_progress = False  # Flag para evitar sincronizações em cascata

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
    """Insere ou atualiza um documento no LightRAG"""
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
        cursor.execute("SELECT doc_id, content_hash FROM documents WHERE file_path = ?", (file_path,))
        path_match = cursor.fetchone()
        
        # Se o arquivo já existe e o hash é o mesmo, não fazer nada (conteúdo não mudou)
        if path_match and path_match[1] == content_hash:
            logger.info(f"Documento já existe e não mudou: {os.path.basename(file_path)} (ID: {path_match[0]})")
            
            # Atualizar timestamp de verificação
            cursor.execute(
                "UPDATE documents SET last_checked = ? WHERE doc_id = ?", 
                (time.time(), path_match[0])
            )
            conn.commit()
            return True
        
        # Verificar se temos um documento com este hash exato mas caminho diferente (duplicata)
        cursor.execute("SELECT doc_id FROM documents WHERE content_hash = ? AND file_path != ?", (content_hash, file_path))
        hash_match = cursor.fetchone()
        
        if hash_match:
            logger.info(f"Documento com hash idêntico já existe: {hash_match[0]} (possível duplicata)")
        
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
            "imported_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
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
        
        # Verificar se precisa atualizar documento existente ou criar um novo
        if path_match:
            # Se o documento já existe mas o conteúdo mudou, atualizamos excluindo o antigo
            # e criando um novo (pois o LightRAG não tem API de atualização direta)
            delete_document(path_match[0])
            cursor.execute("DELETE FROM documents WHERE doc_id = ?", (path_match[0],))
            logger.info(f"Documento atualizado (conteúdo mudou): {path_match[0]}")
        
        # Inserir o novo documento (ou o atualizado)
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
            
            # Salvar ou atualizar no banco de dados
            cursor.execute(
                "INSERT OR REPLACE INTO documents (file_path, doc_id, content_hash, file_size, last_modified, last_checked, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (file_path, doc_id, content_hash, file_size, os.path.getmtime(file_path), time.time(), json.dumps(metadata))
            )
            conn.commit()
            
            if path_match:
                logger.info(f"✅ Documento atualizado com sucesso: {file_name} (ID: {doc_id})")
            else:
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
    """Sincroniza o banco de dados local com o servidor LightRAG - versão otimizada para evitar ciclos"""
    # Definir uma flag global para evitar sincronizações em cascata
    global sync_in_progress
    if 'sync_in_progress' in globals() and sync_in_progress:
        logger.debug("Sincronização já em andamento, pulando ciclo")
        return
    
    sync_in_progress = True
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Obter lista de documentos do servidor
        server_docs = get_existing_documents()
        if not server_docs:
            logger.info("Nenhum documento no servidor para sincronizar")
            conn.close()
            sync_in_progress = False
            return
        
        # Mapear documentos do servidor por ID
        server_doc_ids = {doc.get('document_id', ''): doc for doc in server_docs}
        
        # Verificar status do servidor
        status_data = None
        try:
            with urllib.request.urlopen(f"{LIGHTRAG_URL}/status") as response:
                status_data = json.loads(response.read().decode('utf-8'))
        except:
            pass
        
        # Verificar discrepância grande entre contagem real e reportada
        if status_data and len(server_docs) < status_data.get('documents', 0) * 0.5:
            logger.warning(f"Grande discrepância detectada: {len(server_docs)} documentos encontrados vs {status_data.get('documents', 0)} reportados")
            logger.warning("Isso pode indicar corrupção da base. Considere executar ./resync.sh")
        
        # Buscar documentos do banco de dados local
        cursor.execute("SELECT doc_id, file_path, content_hash FROM documents")
        local_docs = cursor.fetchall()
        local_doc_map = {ld[0]: (ld[1], ld[2]) for ld in local_docs}
        
        # Documentos que estão no servidor mas não no banco local
        orphaned_docs = []
        for doc_id in server_doc_ids:
            if doc_id and doc_id not in local_doc_map:
                orphaned_docs.append(doc_id)
        
        # Limitar número de documentos a excluir por vez para evitar problemas
        max_orphaned_to_delete = 5
        if len(orphaned_docs) > max_orphaned_to_delete:
            logger.warning(f"Muitos documentos órfãos ({len(orphaned_docs)}). Limitando a {max_orphaned_to_delete} por ciclo.")
            orphaned_docs = orphaned_docs[:max_orphaned_to_delete]
        
        # Excluir documentos órfãos do servidor (apenas se não forem documentos válidos)
        deleted_orphans = 0
        for doc_id in orphaned_docs:
            # Verificar se o documento é um arquivo conhecido com outro ID 
            server_doc = server_doc_ids[doc_id]
            server_metadata = server_doc.get('metadata', {})
            server_file_path = server_metadata.get('file_path', '')
            
            # Se for um arquivo conhecido, não remover
            if server_file_path and any(server_file_path == ld[1] for ld in local_docs):
                logger.debug(f"Documento no servidor pertence a um arquivo conhecido: {server_file_path}")
                continue
            
            logger.info(f"Excluindo documento órfão do servidor: {doc_id}")
            if delete_document(doc_id):
                deleted_orphans += 1
        
        # Documentos que estão no banco local mas não existem no servidor
        # Apenas registramos, não removemos para evitar problemas de ciclo
        missing_docs = []
        for doc_id, file_path, _ in local_docs:
            if doc_id and doc_id not in server_doc_ids:
                missing_docs.append((doc_id, file_path))
                logger.debug(f"Documento local não encontrado no servidor: {doc_id} (arquivo: {file_path})")
                # NÃO VAMOS REMOVER para evitar ciclos de inserção/remoção
        
        conn.commit()
        
        if deleted_orphans or missing_docs:
            logger.info(f"Sincronização concluída: {deleted_orphans} excluídos do servidor, {len(missing_docs)} inconsistências detectadas")
            if missing_docs:
                logger.debug("As inconsistências serão corrigidas na próxima verificação de arquivos")
            if deleted_orphans:
                update_sync_timestamp()
    
    except Exception as e:
        logger.error(f"Erro durante sincronização: {e}")
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()
        sync_in_progress = False

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
        cursor.execute("SELECT file_path, content_hash, last_modified FROM documents")
        db_files_info = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        db_files = list(db_files_info.keys())
        
        # Arquivos no sistema que não estão no banco
        new_files = [f for f in existing_files if f not in db_files]
        
        # Arquivos no banco que não existem mais no sistema
        deleted_files = [f for f in db_files if f not in existing_files]
        
        # Verificar arquivos que podem ter sido modificados
        modified_files = []
        for file_path in existing_files:
            if file_path in db_files:
                # Verificar se o arquivo foi modificado desde a última verificação
                current_mtime = os.path.getmtime(file_path)
                db_hash, db_mtime = db_files_info[file_path]
                
                # Se a data de modificação do arquivo for diferente da que está no banco,
                # verificamos o hash para ter certeza que o conteúdo realmente mudou
                if abs(current_mtime - db_mtime) > 1:  # tolerância de 1 segundo para modificações
                    current_hash = calculate_file_hash(file_path)
                    if current_hash != db_hash:
                        modified_files.append(file_path)
        
        # Processar novos arquivos
        for file_path in new_files:
            logger.info(f"Processando novo arquivo: {os.path.basename(file_path)}")
            insert_document(file_path)
        
        # Processar arquivos modificados
        for file_path in modified_files:
            logger.debug(f"Verificando arquivo modificado: {os.path.basename(file_path)}")
            insert_document(file_path)  # Função atualizada vai verificar se realmente mudou
        
        # Processar arquivos excluídos
        for file_path in deleted_files:
            logger.info(f"Processando arquivo removido: {os.path.basename(file_path)}")
            handle_deleted_file(file_path)
        
        if new_files or deleted_files or modified_files:
            logger.info(f"Sincronização de arquivos concluída: {len(new_files)} novos, {len(modified_files)} modificados, {len(deleted_files)} removidos")
            update_sync_timestamp()
        
    except Exception as e:
        logger.error(f"Erro durante sincronização de arquivos: {e}")
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()

class ProjectFileHandler(FileSystemEventHandler):
    """Manipulador de eventos do sistema de arquivos com proteção contra eventos duplicados"""
    
    def __init__(self):
        self.last_events = {}  # Para rastreamento de eventos recentes
        self.debounce_time = 2  # Tempo de debounce em segundos
    
    def _is_duplicate_event(self, event_type, path):
        """Verifica se um evento é duplicado (ocorreu recentemente)"""
        event_key = f"{event_type}:{path}"
        current_time = time.time()
        
        # Se o evento ocorreu recentemente, é um duplicado
        if event_key in self.last_events:
            last_time = self.last_events[event_key]
            if current_time - last_time < self.debounce_time:
                return True
        
        # Registrar o evento atual
        self.last_events[event_key] = current_time
        
        # Limpar eventos antigos
        keys_to_remove = []
        for key, timestamp in self.last_events.items():
            if current_time - timestamp > 60:  # Limpar eventos mais antigos que 60 segundos
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.last_events[key]
            
        return False
    
    def on_created(self, event):
        """Quando um novo arquivo é criado"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            # Verificar se é um evento duplicado
            if self._is_duplicate_event("created", event.src_path):
                logger.debug(f"Ignorando evento duplicado de criação: {event.src_path}")
                return
                
            # Esperar um pouco para garantir que o arquivo está completo
            time.sleep(1.5)
            logger.info(f"Arquivo criado: {event.src_path}")
            insert_document(event.src_path)
    
    def on_modified(self, event):
        """Quando um arquivo é modificado"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            # Verificar se é um evento duplicado
            if self._is_duplicate_event("modified", event.src_path):
                logger.debug(f"Ignorando evento duplicado de modificação: {event.src_path}")
                return
                
            # Esperar um pouco para garantir que o arquivo está completo
            time.sleep(1.5)
            logger.info(f"Arquivo modificado: {event.src_path}")
            insert_document(event.src_path)
    
    def on_deleted(self, event):
        """Quando um arquivo é excluído"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            # Verificar se é um evento duplicado
            if self._is_duplicate_event("deleted", event.src_path):
                logger.debug(f"Ignorando evento duplicado de exclusão: {event.src_path}")
                return
                
            logger.info(f"Arquivo excluído: {event.src_path}")
            handle_deleted_file(event.src_path)

def main():
    """Função principal"""
    global sync_in_progress
    sync_in_progress = False
    
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
    # Criar event handler com proteção contra eventos duplicados
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
        # Iniciar loop principal com intervalo maior para evitar sincronizações frequentes
        while True:
            # Esperar o intervalo definido
            time.sleep(POLL_INTERVAL)
            
            # Limitar frequência de sincronização para evitar ciclos
            if not sync_in_progress:
                # Verificar por atualizações no servidor
                sync_database_with_server()
                # Verificar por atualizações no sistema de arquivos
                sync_files_with_database()
            else:
                logger.debug("Sincronização em andamento, aguardando próximo ciclo")
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuário")
        observer.stop()
    
    observer.join()
    logger.info("Monitor encerrado")

if __name__ == "__main__":
    main()