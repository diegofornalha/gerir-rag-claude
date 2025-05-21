#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Patch para aplicativo principal (app.py)
Este script garante que o arquivo app.py use a implementação correta da UI
"""

import os
import shutil
import sys

# Diretório do LightRAG
LIGHTRAG_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(LIGHTRAG_DIR, "ui")
APP_FILE = os.path.join(UI_DIR, "app.py")

# Diretório de backups
BACKUP_DIR = os.path.join(LIGHTRAG_DIR, "backups", "app_patch")

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

def patch_app_py():
    """Atualiza o arquivo app.py"""
    # Verificar se o arquivo existe
    if not os.path.exists(APP_FILE):
        print(f"Erro: Arquivo app.py não encontrado em {APP_FILE}")
        return False
    
    # Fazer backup
    backup_file(APP_FILE)
    
    # Conteúdo atualizado do app.py
    new_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - App Principal
Ponto de entrada para a interface do LightRAG
"""

import sys
import os

# Adicionar diretórios aos caminhos de importação
current_dir = os.path.dirname(os.path.abspath(__file__))
lightrag_root = os.path.dirname(current_dir)

# Adicionar tanto o diretório atual quanto o diretório raiz ao PYTHONPATH
sys.path.insert(0, current_dir)  # Para importar módulos locais
sys.path.insert(0, lightrag_root)  # Para importar componentes principais do LightRAG

# Verificar se o módulo name_selection existe e está acessível
try:
    from name_selection import select_document_with_naming
    print("✅ Módulo de nomeação encontrado e acessível")
except ImportError:
    print("⚠️ Módulo de nomeação não encontrado. A interface usará o comportamento padrão.")

# Importar a classe principal da UI
try:
    from ui import LightRAGUI
    print("✅ Usando implementação consolidada da UI")
except ImportError:
    # Fallback para módulo original
    try:
        from lightrag_ui import LightRAGUI
        print("⚠️ Usando implementação original da UI")
    except ImportError:
        print("❌ Não foi possível importar a interface do LightRAG")
        sys.exit(1)

def main():
    """Função principal para iniciar a UI Streamlit"""
    ui = LightRAGUI()
    ui.run()

if __name__ == "__main__":
    main()
"""
    
    # Salvar arquivo modificado
    with open(APP_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Arquivo app.py modificado com sucesso")
    return True

def main():
    """Função principal para aplicar o patch"""
    print("=" * 60)
    print("PATCH DO APLICATIVO PRINCIPAL (app.py)")
    print("=" * 60)
    print()
    
    # Aplicar patch
    success = patch_app_py()
    
    if success:
        print("=" * 60)
        print("PATCH APLICADO COM SUCESSO!")
        print("=" * 60)
        print()
        print("O aplicativo principal agora está configurado para usar")
        print("o módulo de nomeação e a implementação consolidada da UI.")
        print()
        print("Backup do arquivo original está em:")
        print(f"  {BACKUP_DIR}")
        print()
    else:
        print("Falha ao aplicar o patch. Verifique os erros acima.")
    
if __name__ == "__main__":
    main()