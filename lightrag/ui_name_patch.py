#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Patch para integrar o módulo de nomeação na UI
Este script modifica a interface principal do LightRAG para usar
o novo módulo de nomeação que permite nomear conversas durante a seleção.
"""

import os
import re
import shutil
import sys
from typing import List, Dict, Optional

# Diretório do LightRAG
LIGHTRAG_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(LIGHTRAG_DIR, "ui")
UI_FILE = os.path.join(UI_DIR, "ui.py")
LIGHTRAG_UI_FILE = os.path.join(UI_DIR, "lightrag_ui.py")

# Diretório de backups
BACKUP_DIR = os.path.join(LIGHTRAG_DIR, "backups", "ui_name_patch")

def ensure_backup_dir():
    """Cria o diretório de backups se não existir"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def backup_file(file_path):
    """Faz backup de um arquivo"""
    # Criar diretório de backups
    ensure_backup_dir()
    
    # Nome do arquivo sem caminho
    filename = os.path.basename(file_path)
    backup_path = os.path.join(BACKUP_DIR, filename)
    
    # Fazer backup
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    
    return backup_path

def patch_ui_py():
    """Aplica patch no arquivo ui.py"""
    # Verificar se o arquivo existe
    if not os.path.exists(UI_FILE):
        print(f"Erro: Arquivo ui.py não encontrado em {UI_FILE}")
        return False
    
    # Fazer backup
    backup_file(UI_FILE)
    
    # Ler conteúdo
    with open(UI_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Adicionar importação do módulo de nomeação
    import_pattern = "import streamlit as st\nimport json\nimport os\nimport re\nimport pandas as pd\nimport time"
    import_replacement = """import streamlit as st
import json
import os
import re
import pandas as pd
import time

# Importar módulo de nomeação
from ui.name_selection import select_document_with_naming"""
    
    content = content.replace(import_pattern, import_replacement)
    
    # 2. Substituir a seleção de documentos pelo novo widget
    selectbox_pattern = """            # Visualizar documento completo
            selected_doc_id = st.selectbox("Selecione um documento para visualizar:", 
                                          [""] + [doc.get("id", "") for doc in documents])
            
            if selected_doc_id:
                doc = next((d for d in documents if d.get("id") == selected_doc_id), None)"""
    
    selectbox_replacement = """            # Visualizar documento completo usando widget de seleção com nomeação
            selected_doc = select_document_with_naming(
                documents,
                label="Selecione um documento para visualizar:",
                empty_option=True
            )
            
            if selected_doc:
                doc = selected_doc"""
    
    content = content.replace(selectbox_pattern, selectbox_replacement)
    
    # Salvar arquivo modificado
    with open(UI_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Arquivo ui.py modificado com sucesso")
    return True

def patch_lightrag_ui():
    """Aplica patch no arquivo lightrag_ui.py"""
    # Verificar se o arquivo existe
    if not os.path.exists(LIGHTRAG_UI_FILE):
        print(f"Erro: Arquivo lightrag_ui.py não encontrado em {LIGHTRAG_UI_FILE}")
        return False
    
    # Fazer backup
    backup_file(LIGHTRAG_UI_FILE)
    
    # Ler conteúdo
    with open(LIGHTRAG_UI_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar importação do módulo de nomeação (se existir)
    if "from ui.name_selection import" not in content:
        import_pattern = "# Importar componentes do LightRAG"
        import_replacement = """# Importar componentes do LightRAG
        
# Importar módulo de nomeação (se existir)
try:
    from ui.name_selection import select_document_with_naming
    HAVE_NAME_SELECTION = True
except ImportError:
    HAVE_NAME_SELECTION = False"""
    
        content = content.replace(import_pattern, import_replacement)
    
    # Salvar arquivo modificado
    with open(LIGHTRAG_UI_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Arquivo lightrag_ui.py modificado com sucesso")
    return True

def main():
    """Função principal para aplicar os patches"""
    print("=" * 60)
    print("PATCH PARA INTEGRAR MÓDULO DE NOMEAÇÃO NA UI")
    print("=" * 60)
    print()
    
    # Aplicar patches
    ui_success = patch_ui_py()
    lightrag_ui_success = patch_lightrag_ui()
    
    if ui_success and lightrag_ui_success:
        print("=" * 60)
        print("PATCHES APLICADOS COM SUCESSO!")
        print("=" * 60)
        print()
        print("A interface do LightRAG foi modificada para permitir")
        print("nomear conversas diretamente durante a seleção.")
        print()
        print("Backups dos arquivos originais estão em:")
        print(f"  {BACKUP_DIR}")
        print()
    else:
        print("Falha ao aplicar um ou mais patches.")
    
if __name__ == "__main__":
    main()