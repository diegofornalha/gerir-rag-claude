#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Aplicação API
Ponto de entrada para a API Flask do LightRAG
"""

import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.server import run_server

if __name__ == '__main__':
    # Iniciar o servidor Flask
    run_server(debug=True)