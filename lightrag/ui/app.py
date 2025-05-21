#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG UI - Interface web Streamlit
Ponto de entrada para a aplicação Streamlit
"""

import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH (diretório pai da pasta ui)
lightrag_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, lightrag_root)

# Importar diretamente do módulo streamlit_ui (no mesmo diretório)
from streamlit_ui import LightRAGUI

def main():
    """Função principal para iniciar a UI Streamlit"""
    ui = LightRAGUI()
    ui.run()

if __name__ == "__main__":
    main()