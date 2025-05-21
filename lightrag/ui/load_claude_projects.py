#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para carregar e monitorar novos projetos Claude para exibição no Streamlit
"""

import os
import glob
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuração
BASE_PROJECTS_DIR = "/Users/agents/.claude/projects"
PROJECTS_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui_projects_cache.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs/ui_projects.log")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('streamlit_projects')

def find_project_dirs():
    """Encontra automaticamente todos os diretórios de projetos"""
    project_dirs = []
    
    # Verificar se o diretório base existe
    if not os.path.exists(BASE_PROJECTS_DIR):
        logger.warning(f"Diretório base não encontrado: {BASE_PROJECTS_DIR}")
        return project_dirs
    
    # Adicionar diretórios específicos que sabemos que existem
    known_dirs = [
        "/Users/agents/.claude/projects/-Users-agents--claude",
        "/Users/agents/.claude/projects/-Users-agents--claude-lightrag",
        "/Users/agents/.claude/projects/-Users-agents--claude-projects"
    ]
    
    for dir_path in known_dirs:
        if os.path.exists(dir_path):
            project_dirs.append(dir_path)
    
    # Procurar por outros diretórios potenciais
    try:
        # Listar todos os itens no diretório base
        for item in os.listdir(BASE_PROJECTS_DIR):
            full_path = os.path.join(BASE_PROJECTS_DIR, item)
            # Verificar se é um diretório e não está na lista de diretórios conhecidos
            if os.path.isdir(full_path) and full_path not in project_dirs:
                # Verificar se tem arquivos JSONL
                if glob.glob(f"{full_path}/*.jsonl"):
                    project_dirs.append(full_path)
    except Exception as e:
        logger.error(f"Erro ao procurar diretórios de projetos: {e}")
    
    return project_dirs

def calculate_file_hash(file_path):
    """Calcula o hash SHA-256 do conteúdo do arquivo"""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return file_hash
    except Exception as e:
        logger.error(f"Erro ao calcular hash do arquivo {file_path}: {e}")
        return None

def extract_short_id(file_path):
    """Extrai um ID curto do nome do arquivo"""
    # Obter o nome do arquivo sem a extensão
    filename = os.path.basename(file_path).split('.')[0]
    
    # Usar o nome completo se for curto o suficiente
    if len(filename) <= 8:
        return filename
    
    # Caso contrário, extrair apenas o início do UUID
    return filename.split('-')[0] if '-' in filename else filename[:8]

def extract_conversation_info(file_path):
    """Extrai informações básicas da conversa a partir do arquivo JSONL"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Tentar ler algumas linhas para extrair metadados
            lines = []
            for _ in range(10):  # Limitar a 10 linhas para performance
                line = f.readline().strip()
                if not line:
                    break
                lines.append(line)
            
            # Se não houver linhas, retornar info básica
            if not lines:
                return {
                    "id": extract_short_id(file_path),
                    "file_path": file_path,
                    "title": os.path.basename(file_path),
                    "first_message": "",
                    "message_count": 0,
                    "last_updated": "",
                    "file_size": os.path.getsize(file_path)
                }
            
            # Analisar a primeira linha para obter timestamp da conversa
            first_msg = {}
            try:
                first_msg = json.loads(lines[0])
            except json.JSONDecodeError:
                pass
            
            # Extrair conteúdo da primeira mensagem do usuário
            first_user_message = ""
            for line in lines:
                try:
                    msg_obj = json.loads(line)
                    if (msg_obj.get("type") == "user" or 
                        (isinstance(msg_obj.get("message"), dict) and 
                         msg_obj.get("message", {}).get("role") == "user")):
                        
                        # Extrair content como string ou lista
                        content = msg_obj.get("message", {}).get("content", "")
                        if isinstance(content, list):
                            # Concatenar elementos de texto
                            text_parts = []
                            for item in content:
                                if isinstance(item, dict) and "text" in item:
                                    text_parts.append(item["text"])
                                elif isinstance(item, str):
                                    text_parts.append(item)
                            first_user_message = " ".join(text_parts)
                        elif isinstance(content, str):
                            first_user_message = content
                        
                        if first_user_message:
                            break
                except:
                    continue
            
            # Truncar mensagem se for muito longa
            if len(first_user_message) > 100:
                first_user_message = first_user_message[:97] + "..."
            
            # Usar base do caminho como título se a mensagem não for informativa
            parent_dir = os.path.basename(os.path.dirname(file_path))
            if not first_user_message or first_user_message.lower() in ("hi", "hello", "oi", "olá"):
                title = parent_dir
            else:
                title = first_user_message
            
            # Extrair timestamp como string ISO
            timestamp = first_msg.get("timestamp", "")
            if timestamp and timestamp.endswith("Z"):
                # Simplificar para só a data
                try:
                    date_part = timestamp.split("T")[0]
                except:
                    date_part = timestamp
            else:
                date_part = ""
            
            return {
                "id": extract_short_id(file_path),
                "file_path": file_path,
                "title": title,
                "first_message": first_user_message,
                "message_count": 0,  # Poderíamos contar linhas, mas seria custoso
                "last_updated": date_part,
                "file_size": os.path.getsize(file_path)
            }
            
    except Exception as e:
        logger.error(f"Erro ao extrair informações do arquivo {file_path}: {e}")
        return {
            "id": extract_short_id(file_path),
            "file_path": file_path,
            "title": os.path.basename(file_path),
            "first_message": f"Erro ao ler arquivo: {str(e)}",
            "message_count": 0,
            "last_updated": "",
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }

def scan_projects():
    """Escaneia todos os projetos Claude disponíveis"""
    # Cache de projetos conhecido
    known_projects = {}
    if os.path.exists(PROJECTS_CACHE_FILE):
        try:
            with open(PROJECTS_CACHE_FILE, 'r', encoding='utf-8') as f:
                known_projects = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar cache de projetos: {e}")
    
    # Descobrir diretórios de projetos
    project_dirs = find_project_dirs()
    logger.info(f"Encontrados {len(project_dirs)} diretórios de projetos")
    
    # Lista para armazenar todos os arquivos JSONL encontrados
    all_jsonl_files = []
    
    # Verificar cada diretório de projetos
    for projects_dir in project_dirs:
        if os.path.exists(projects_dir):
            # Encontrar arquivos JSONL neste diretório
            jsonl_files = glob.glob(f"{projects_dir}/*.jsonl")
            logger.info(f"Diretório {projects_dir}: {len(jsonl_files)} arquivos JSONL")
            all_jsonl_files.extend(jsonl_files)
    
    # Processar cada arquivo
    projects_info = {}
    unchanged_count = 0
    new_count = 0
    removed_count = 0
    
    # Primeiro, verificar por arquivos removidos
    for file_id, info in known_projects.items():
        file_path = info.get("file_path", "")
        if not file_path or not os.path.exists(file_path):
            logger.info(f"Arquivo removido detectado: {file_path} (ID: {file_id})")
            removed_count += 1
            # Não adicionar ao projects_info (será excluído)
        else:
            # Manter temporariamente, será atualizado ou confirmado abaixo
            projects_info[file_id] = info
    
    # Agora processar arquivos existentes
    for file_path in all_jsonl_files:
        file_id = extract_short_id(file_path)
        
        # Verificar se temos informações em cache e se o arquivo não mudou
        if file_id in projects_info:
            cached_info = projects_info[file_id]
            if os.path.exists(file_path) and os.path.getsize(file_path) == cached_info.get("file_size", 0):
                # Arquivo não mudou, manter informações do cache
                unchanged_count += 1
                continue
        
        # Arquivo novo ou modificado, extrair informações
        info = extract_conversation_info(file_path)
        projects_info[file_id] = info
        new_count += 1
    
    # Atualizar cache
    try:
        with open(PROJECTS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects_info, f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar cache de projetos: {e}")
    
    logger.info(f"Projetos processados: {len(projects_info)} (Novos/Modificados: {new_count}, Removidos: {removed_count}, Mantidos: {unchanged_count})")
    return projects_info

class ProjectsFileHandler(FileSystemEventHandler):
    """Manipulador de eventos do sistema de arquivos para projetos"""
    
    def on_created(self, event):
        """Quando um novo arquivo é criado"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            logger.info(f"Novo arquivo detectado: {event.src_path}")
            # Esperar um pouco para garantir que o arquivo esteja completo
            time.sleep(1)
            # Disparar uma nova varredura
            scan_projects()
    
    def on_modified(self, event):
        """Quando um arquivo é modificado"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            logger.info(f"Arquivo modificado: {event.src_path}")
            # Esperar um pouco para garantir que o arquivo esteja completo
            time.sleep(1)
            # Disparar uma nova varredura
            scan_projects()
    
    def on_deleted(self, event):
        """Quando um arquivo é excluído"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            logger.info(f"Arquivo excluído detectado: {event.src_path}")
            # Disparar uma nova varredura
            scan_projects()

def start_monitoring():
    """Inicia o monitoramento de arquivos de projetos"""
    # Primeiro, fazer uma varredura inicial
    scan_projects()
    
    # Configurar observador
    observer = Observer()
    event_handler = ProjectsFileHandler()
    
    # Descobrir diretórios para monitorar
    project_dirs = find_project_dirs()
    
    # Adicionar cada diretório para monitoramento
    for proj_dir in project_dirs:
        if os.path.exists(proj_dir):
            observer.schedule(event_handler, proj_dir, recursive=False)
            logger.info(f"Monitorando: {proj_dir}")
    
    # Iniciar observador
    observer.start()
    logger.info("Monitoramento de projetos iniciado")
    
    return observer

def get_projects():
    """Função para obter projetos atual (usada pelo Streamlit)"""
    # Vamos usar o cache se existir
    if os.path.exists(PROJECTS_CACHE_FILE):
        try:
            with open(PROJECTS_CACHE_FILE, 'r', encoding='utf-8') as f:
                projects = json.load(f)
            # Ordenar por data de atualização se disponível
            sorted_projects = sorted(
                projects.values(), 
                key=lambda x: x.get("last_updated", ""), 
                reverse=True
            )
            return sorted_projects
        except Exception as e:
            logger.error(f"Erro ao carregar projetos do cache: {e}")
    
    # Se não existe cache ou deu erro, fazer varredura
    projects = scan_projects()
    sorted_projects = sorted(
        projects.values(), 
        key=lambda x: x.get("last_updated", ""), 
        reverse=True
    )
    return sorted_projects

# Uso para teste
if __name__ == "__main__":
    # Testar varredura
    print("Escaneando projetos...")
    projects = scan_projects()
    print(f"Encontrados {len(projects)} projetos")
    
    # Testar monitoramento
    print("Iniciando monitoramento...")
    observer = start_monitoring()
    
    try:
        print("Pressione Ctrl+C para interromper")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()