
import sys
import os

# Adicionar diretórios aos caminhos de importação
current_dir = os.path.dirname(os.path.abspath(__file__))
lightrag_root = os.path.dirname(current_dir)

# Adicionar tanto o diretório atual quanto o diretório raiz ao PYTHONPATH
sys.path.insert(0, current_dir)  # Para importar módulos locais
sys.path.insert(0, lightrag_root)  # Para importar componentes principais do LightRAG

# Importar diretamente do módulo lightrag_ui.py (no mesmo diretório)
from lightrag_ui import LightRAGUI

def main():
    """Função principal para iniciar a UI Streamlit"""
    ui = LightRAGUI()
    ui.run()

if __name__ == "__main__":
    main()