#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG UI - Interface web Streamlit
Ponto de entrada para a aplicação Streamlit
"""

import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Agora importar da UI
from ui.streamlit_ui import LightRAGUI

def main():
    """Função principal para iniciar a UI Streamlit"""
    ui = LightRAGUI()
    ui.run()

if __name__ == "__main__":
    main()