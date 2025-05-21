#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para monitorar automaticamente novos arquivos JSONL de projetos Claude
e indexá-los no LightRAG em tempo real.
"""

import os
import sys
import time
import json
import logging
import hashlib
import urllib.request
import urllib.parse
import glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuração
LIGHTRAG_URL = "http://127.0.0.1:5000"
BASE_PROJECTS_DIR = "/Users/agents/.claude/projects"
POLL_INTERVAL = 5.0  # segundos entre verificações
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs/monitor_projects.log")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('monitor_projects')

# Importar funções dos scripts existentes
try:
    from improved_rag_insert_file import rag_insert_file
    from extract_jsonl import extract_jsonl_content
    from load_projects import find_project_dirs, check_server, get_existing_documents
except ImportError as e:
    logger.error(f"Erro ao importar módulos necessários: {e}")
    sys.exit(1)

# Cache de arquivos já processados
processed_files = set()

def load_processed_files_cache():
    """Carrega o cache de arquivos já processados de um arquivo"""
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".processed_files_cache.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            logger.warning(f"Erro ao carregar cache de arquivos: {e}")
    return set()

def save_processed_files_cache(files_set):
    """Salva o cache de arquivos já processados em um arquivo"""
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".processed_files_cache.json")
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(list(files_set), f)
    except Exception as e:
        logger.warning(f"Erro ao salvar cache de arquivos: {e}")

def get_document_id_for_file(file_path):
    """Obtém o ID do documento no LightRAG a partir do caminho do arquivo"""
    try:
        # Obter documentos existentes
        documents = get_existing_documents()
        if not documents:
            return None
        
        # Calcular hash do nome do arquivo para comparação
        filename = os.path.basename(file_path)
        
        # Procurar por referência ao arquivo nas metadatas ou source
        for doc in documents:
            source = doc.get("source", "")
            metadata = doc.get("metadata", {})
            
            # Verificar source
            if filename in source:
                return doc.get("id")
            
            # Verificar em metadata.file_path ou metadata.file_name
            if isinstance(metadata, dict):
                file_path_meta = metadata.get("file_path", "")
                file_name_meta = metadata.get("file_name", "")
                
                if filename in file_path_meta or filename in file_name_meta:
                    return doc.get("id")
        
        return None
    except Exception as e:
        logger.error(f"Erro ao tentar encontrar documento: {e}")
        return None

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

def process_file(file_path):
    """Processa um arquivo JSONL e o adiciona ao LightRAG"""
    try:
        # Verificar se já foi processado
        if file_path in processed_files:
            logger.debug(f"Arquivo já processado: {file_path}")
            return False

        # Verificar se o servidor está ativo
        if not check_server():
            logger.error("Servidor LightRAG não está disponível")
            return False
        
        # Verificar se o arquivo parece ser um JSONL válido
        if not os.path.exists(file_path) or not file_path.endswith('.jsonl'):
            logger.debug(f"Arquivo inválido ou não encontrado: {file_path}")
            return False

        # Verificar tamanho mínimo do arquivo
        if os.path.getsize(file_path) < 100:  # arquivos menores que 100 bytes são provavelmente inválidos
            logger.debug(f"Arquivo muito pequeno para ser válido: {file_path}")
            return False

        # Inserir no LightRAG
        logger.info(f"Processando novo arquivo: {os.path.basename(file_path)}")
        result = rag_insert_file(file_path, force=False)

        if result.get("success", False):
            logger.info(f"✅ Arquivo indexado com sucesso: {os.path.basename(file_path)}")
            processed_files.add(file_path)
            save_processed_files_cache(processed_files)
            return True
        else:
            error = result.get("error", "Erro desconhecido")
            if "duplicado" in error:
                # Arquivo duplicado não é um erro crítico
                logger.info(f"Arquivo duplicado detectado: {os.path.basename(file_path)}")
                processed_files.add(file_path)
                save_processed_files_cache(processed_files)
                return True
            else:
                logger.error(f"Erro ao indexar arquivo: {error}")
                return False

    except Exception as e:
        logger.error(f"Erro ao processar arquivo {file_path}: {e}")
        return False

def handle_deleted_file(file_path):
    """Trata um arquivo que foi excluído, removendo-o do LightRAG"""
    try:
        logger.info(f"Detectada exclusão do arquivo: {os.path.basename(file_path)}")
        
        # Verificar se o servidor está ativo
        if not check_server():
            logger.error("Servidor LightRAG não está disponível")
            return False
        
        # Encontrar o documento correspondente ao arquivo
        doc_id = get_document_id_for_file(file_path)
        if not doc_id:
            logger.info(f"Nenhum documento encontrado para o arquivo: {os.path.basename(file_path)}")
            
            # Remover do cache de processados de qualquer forma
            if file_path in processed_files:
                processed_files.remove(file_path)
                save_processed_files_cache(processed_files)
                logger.info(f"Arquivo removido do cache: {os.path.basename(file_path)}")
            
            return False
        
        # Excluir o documento
        if delete_document(doc_id):
            # Atualizar cache
            if file_path in processed_files:
                processed_files.remove(file_path)
                save_processed_files_cache(processed_files)
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Erro ao processar exclusão do arquivo {file_path}: {e}")
        return False
    
class ProjectFileHandler(FileSystemEventHandler):
    """Manipulador de eventos do sistema de arquivos"""
    
    def on_created(self, event):
        """Quando um novo arquivo é criado"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            # Esperar um pouco para garantir que o arquivo está completo
            time.sleep(1)  
            process_file(event.src_path)
    
    def on_modified(self, event):
        """Quando um arquivo é modificado"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            # Remover do cache se estiver lá
            if event.src_path in processed_files:
                processed_files.remove(event.src_path)
                save_processed_files_cache(processed_files)
            # Esperar um pouco para garantir que o arquivo está completo
            time.sleep(1)
            process_file(event.src_path)
    
    def on_deleted(self, event):
        """Quando um arquivo é excluído"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            handle_deleted_file(event.src_path)

def check_deleted_files():
    """Verifica arquivos que foram excluídos desde a última execução"""
    # Verificar arquivos que estão no cache mas não existem mais
    deleted_files = set()
    for file_path in processed_files:
        if not os.path.exists(file_path):
            logger.info(f"Detectado arquivo excluído entre execuções: {os.path.basename(file_path)}")
            deleted_files.add(file_path)
            handle_deleted_file(file_path)
    
    # Remover arquivos excluídos do cache
    for file_path in deleted_files:
        if file_path in processed_files:
            processed_files.remove(file_path)
    
    # Salvar cache atualizado
    if deleted_files:
        save_processed_files_cache(processed_files)
        logger.info(f"Cache atualizado: {len(deleted_files)} arquivos excluídos removidos")
        
def sync_database_with_files():
    """Sincroniza a base de dados com os arquivos existentes, removendo documentos órfãos"""
    try:
        logger.info("Sincronizando base de dados com arquivos existentes...")
        
        # Passo 1: Coletar todos os arquivos JSONL que existem atualmente
        existing_files = []
        
        # Encontrar diretórios de projetos
        project_dirs = find_project_dirs()
        
        for proj_dir in project_dirs:
            if os.path.exists(proj_dir):
                # Encontrar arquivos JSONL
                jsonl_files = glob.glob(f"{proj_dir}/*.jsonl")
                existing_files.extend(jsonl_files)
        
        # Extrair nomes base dos arquivos existentes
        existing_filenames = set(os.path.basename(f) for f in existing_files)
        
        # Passo 2: Obter todos os documentos atuais do LightRAG
        try:
            # Fazer uma consulta vazia para obter todos os documentos
            data = json.dumps({"query": "*"}).encode('utf-8')
            req = urllib.request.Request(
                f"{LIGHTRAG_URL}/query",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                contexts = result.get('context', [])
                
                if not contexts:
                    logger.info("Nenhum documento existente na base")
                    return
                
                documents = contexts
        except Exception as e:
            logger.error(f"Erro ao recuperar documentos: {e}")
            return
        
        # Passo 3: Identificar documentos órfãos (que não têm arquivo correspondente)
        orphaned_docs = []
        for doc in documents:
            doc_id = doc.get('document_id', "")
            source = doc.get('source', "")
            metadata = doc.get('metadata', {})
            
            # Verificar se o documento tem referência a um arquivo que não existe mais
            has_file_reference = False
            referenced_file = None
            
            # Verificar source
            for filename in existing_filenames:
                if filename in source:
                    has_file_reference = True
                    referenced_file = filename
                    break
            
            # Verificar metadata
            if not has_file_reference and isinstance(metadata, dict):
                file_path = metadata.get("file_path", "")
                file_name = metadata.get("file_name", "")
                
                for filename in existing_filenames:
                    if filename in file_path or filename in file_name:
                        has_file_reference = True
                        referenced_file = filename
                        break
            
            # Se não encontrou referência a um arquivo existente, é órfão
            if not has_file_reference:
                orphaned_docs.append((doc_id, source))
        
        # Passo 4: Excluir documentos órfãos
        if orphaned_docs:
            logger.info(f"Encontrados {len(orphaned_docs)} documentos órfãos para excluir")
            
            for doc_id, source in orphaned_docs:
                logger.info(f"Excluindo documento órfão: {doc_id} (fonte: {source})")
                delete_document(doc_id)
                
            logger.info(f"Sincronização concluída: {len(orphaned_docs)} documentos órfãos removidos")
        else:
            logger.info("Nenhum documento órfão encontrado. Base sincronizada.")
            
    except Exception as e:
        logger.error(f"Erro durante sincronização da base: {e}")
        return False

def scan_existing_files():
    """Digitaliza e processa arquivos existentes"""
    logger.info("Verificando arquivos existentes...")
    
    # Encontrar diretórios de projetos
    project_dirs = find_project_dirs()
    logger.info(f"Encontrados {len(project_dirs)} diretórios de projetos")
    
    for proj_dir in project_dirs:
        if os.path.exists(proj_dir):
            # Encontrar arquivos JSONL
            jsonl_files = glob.glob(f"{proj_dir}/*.jsonl")
            logger.info(f"Diretório {proj_dir}: {len(jsonl_files)} arquivos JSONL")
            
            # Processar cada arquivo
            for file_path in jsonl_files:
                process_file(file_path)

def main():
    """Função principal"""
    logger.info("=== Monitor de Projetos Claude para LightRAG ===")
    
    # Verificar se o servidor está ativo
    if not check_server():
        logger.error("Servidor LightRAG não está disponível. Execute ./start_lightrag.sh primeiro.")
        sys.exit(1)
    
    # Carregar cache de arquivos processados
    global processed_files
    processed_files = load_processed_files_cache()
    logger.info(f"Cache de arquivos: {len(processed_files)} arquivos já processados")
    
    # Sincronizar base de dados (remover documentos órfãos)
    sync_database_with_files()
    
    # Verificar arquivos excluídos entre execuções
    check_deleted_files()
    
    # Primeiro, processar arquivos existentes
    scan_existing_files()
    
    # Descobrir diretórios de projetos para monitorar
    project_dirs = find_project_dirs()
    if not project_dirs:
        logger.error("Nenhum diretório de projetos encontrado")
        sys.exit(1)
    
    # Iniciar monitoramento com watchdog
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
        sync_interval = 0
        while True:
            time.sleep(POLL_INTERVAL)
            # Verificar periodicamente por exclusões não capturadas
            check_deleted_files()
            
            # A cada 60 segundos, sincronizar completamente a base
            sync_interval += 1
            if sync_interval >= 12:  # 12 x 5 segundos = 60 segundos
                sync_database_with_files()
                sync_interval = 0
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuário")
        observer.stop()
    
    observer.join()
    logger.info("Monitor encerrado")

if __name__ == "__main__":
    main()