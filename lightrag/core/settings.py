#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Configurações Centralizadas
Este módulo contém todas as configurações centralizadas do sistema LightRAG
"""

import os
import json

# Diretório base da aplicação
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configurações do servidor
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# Configurações de arquivos
DB_FILE = os.path.join(BASE_DIR, 'lightrag_db.json')
MEMORY_SUMMARY_FILE = os.path.join(BASE_DIR, 'lightrag_memory_resumo_v2.md')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Configurações de consulta
MAX_RESULTS = 5
MODES = ["hybrid", "semantic", "keyword"]
DEFAULT_MODE = "hybrid"

# Configurações da aplicação
APP_NAME = "LightRAG"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Sistema simplificado de RAG (Retrieval Augmented Generation)"

# Carregar configurações locais se existirem
LOCAL_SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.local.json')

def load_local_settings():
    """Carrega configurações locais a partir do arquivo settings.local.json"""
    if os.path.exists(LOCAL_SETTINGS_FILE):
        try:
            with open(LOCAL_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                local_settings = json.load(f)
                
                # Atualizar variáveis globais com configurações locais
                globals().update(local_settings)
                
            return True
        except Exception as e:
            print(f"Erro ao carregar configurações locais: {str(e)}")
    
    return False

# Carregar configurações locais automaticamente
load_local_settings()

# Verificar e criar diretórios necessários
def ensure_directories():
    """Garante que os diretórios necessários existam"""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Garantir que o arquivo de banco de dados seja inicializado
    if not os.path.exists(DB_FILE):
        default_db = {
            "documents": [],
            "lastUpdated": None
        }
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_db, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao criar arquivo de banco de dados: {str(e)}")

# Chamar a função para garantir diretórios se este módulo for importado
ensure_directories()