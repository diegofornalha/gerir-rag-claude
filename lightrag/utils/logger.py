#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Sistema de Logging
Este módulo implementa o sistema de logging centralizado
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import datetime
from typing import Optional

# Importar configurações
from core.settings import LOG_DIR

# Garantir que o diretório de logs exista
os.makedirs(LOG_DIR, exist_ok=True)

class Logger:
    """
    Sistema de logging centralizado para o LightRAG
    
    Gerencia logs para diferentes componentes do sistema, com suporte a 
    rotação de arquivos e níveis de log configuráveis.
    """
    
    # Cache de loggers já criados
    _loggers = {}
    
    @staticmethod
    def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
        """
        Obtém um logger configurado com o nome especificado
        
        Args:
            name: Nome do logger (usado para identificar o componente)
            level: Nível de logging (default: INFO)
            
        Retorna:
            logging.Logger: Logger configurado
        """
        # Verificar se já existe no cache
        if name in Logger._loggers:
            return Logger._loggers[name]
        
        # Criar novo logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Configurar formato da mensagem
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Configurar handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        
        # Adicionar handler de console
        logger.addHandler(console_handler)
        
        # Configurar handler para arquivo
        log_file = os.path.join(LOG_DIR, f"{name}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        
        # Adicionar handler de arquivo
        logger.addHandler(file_handler)
        
        # Armazenar no cache
        Logger._loggers[name] = logger
        
        return logger
    
    @staticmethod
    def configure_level(name: str, level: int) -> None:
        """
        Configura o nível de log para um logger específico
        
        Args:
            name: Nome do logger existente
            level: Novo nível de log (ex: logging.DEBUG)
        """
        if name in Logger._loggers:
            logger = Logger._loggers[name]
            logger.setLevel(level)
            
            # Atualizar nível de todos os handlers
            for handler in logger.handlers:
                handler.setLevel(level)

# Loggers pré-configurados para uso comum
def get_api_logger() -> logging.Logger:
    """Obtém o logger para a API Flask"""
    return Logger.get_logger("lightrag_api")

def get_core_logger() -> logging.Logger:
    """Obtém o logger para o núcleo do sistema"""
    return Logger.get_logger("lightrag_core")

def get_cli_logger() -> logging.Logger:
    """Obtém o logger para a interface de linha de comando"""
    return Logger.get_logger("lightrag_cli")

def get_ui_logger() -> logging.Logger:
    """Obtém o logger para a interface web"""
    return Logger.get_logger("lightrag_ui")