#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG Server - Módulo Bridge para compatibilidade
Este módulo redireciona para a implementação atual em api/server.py
"""

import sys
import os
import importlib
import warnings

# Aviso sobre módulo de compatibilidade
warnings.warn(
    "core.server é um módulo de compatibilidade. Use api.server diretamente para implementação atual.",
    DeprecationWarning,
    stacklevel=2
)

# Adicionar diretório raiz ao sys.path se necessário
lightrag_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if lightrag_root not in sys.path:
    sys.path.insert(0, lightrag_root)

# Importar módulo api.server
try:
    from api.server import *
    
    # Verificar se as funções/classes essenciais estão disponíveis
    required_attributes = ["app", "create_app", "run_server"]
    for attr in required_attributes:
        if not hasattr(sys.modules[__name__], attr):
            raise ImportError(f"Atributo necessário '{attr}' não encontrado em api.server")
    
except ImportError as e:
    print(f"Erro ao importar api.server: {e}")
    print("Verifique se o módulo api/server.py existe e está configurado corretamente.")
    sys.exit(1)

# Função main para compatibilidade
def main():
    """Função principal para execução direta do servidor"""
    from api.server import run_server
    run_server()

# Execução direta
if __name__ == "__main__":
    main()