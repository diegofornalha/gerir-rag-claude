#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Patch do módulo de banco de dados
Este script modifica o arquivo core/database.py para usar o sistema de nomes por UUID
"""

import os
import re
import shutil
import sys
from typing import List, Dict, Optional

# Diretório do LightRAG
LIGHTRAG_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(LIGHTRAG_DIR, "core")
DATABASE_FILE = os.path.join(CORE_DIR, "database.py")

# Diretório de backups
BACKUP_DIR = os.path.join(LIGHTRAG_DIR, "backups", "database_patch")

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

def get_import_section():
    """Retorna a seção de código para importar o módulo de nomes por UUID"""
    return """
# Importar o sistema de nomes por UUID
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from uuid_names import extract_uuid, set_name_for_uuid, get_name_for_uuid
    USING_UUID_NAMES = True
except ImportError:
    USING_UUID_NAMES = False
    print("Aviso: Sistema de nomes por UUID não encontrado. Os nomes personalizados não serão persistentes.")
"""

def apply_patches(content):
    """Aplica as modificações ao conteúdo do arquivo database.py"""
    modified_content = content
    
    # 1. Adicionar importação do sistema de nomes por UUID
    import_section = get_import_section()
    from_typing_pattern = "from typing import Dict, List, Any, Optional"
    modified_content = modified_content.replace(
        from_typing_pattern,
        f"{from_typing_pattern}{import_section}"
    )
    
    # 2. Modificar o método insert_document para usar UUIDs
    insert_doc_pattern = r"def insert_document\(self, content: str, source: str = \"manual\",\s+summary: Optional\[str\] = None,\s+metadata: Optional\[Dict\] = None\) -> Dict:"
    extract_uuid_code = """
        # Extrair UUID do conteúdo ou fonte para persistência de nomes
        uuid = None
        if USING_UUID_NAMES:
            # Tentar extrair do source primeiro
            uuid = extract_uuid(source)
            
            # Se não encontrar, tentar do conteúdo
            if not uuid and content:
                uuid = extract_uuid(content)
                
            # Se encontrou UUID e tem um resumo personalizado, salvar como nome personalizado
            if uuid and summary and not summary.startswith("Conversa Claude:"):
                set_name_for_uuid(uuid, summary)
                
            # Se encontrou UUID mas não tem resumo personalizado, tentar obter nome existente
            elif uuid and (not summary or summary.startswith("Conversa Claude:")):
                existing_name = get_name_for_uuid(uuid)
                if existing_name and not existing_name.startswith("Conversa:"):
                    summary = existing_name
        """
    
    # Encontrar a parte correta para inserir o código de extração de UUID
    doc_id_assignment_pattern = r"doc_id = f\"doc_{int\(datetime\.datetime\.now\(\)\.timestamp\(\) \* 1000\)}\""
    modified_content = modified_content.replace(
        doc_id_assignment_pattern,
        f"{extract_uuid_code}\n        {doc_id_assignment_pattern}"
    )
    
    return modified_content

def patch_database():
    """Aplica o patch ao arquivo database.py"""
    # Verificar se o arquivo existe
    if not os.path.exists(DATABASE_FILE):
        print(f"Erro: Arquivo database.py não encontrado em {DATABASE_FILE}")
        return False
    
    # Fazer backup
    backup_file(DATABASE_FILE)
    
    # Ler conteúdo
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aplicar patches
    modified_content = apply_patches(content)
    
    # Salvar arquivo modificado
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print(f"✅ Arquivo database.py modificado com sucesso")
    return True

def main():
    """Função principal para aplicar o patch"""
    print("=" * 60)
    print("PATCH DO MÓDULO DE BANCO DE DADOS")
    print("=" * 60)
    print()
    
    # Aplicar patch
    success = patch_database()
    
    if success:
        print("=" * 60)
        print("PATCH APLICADO COM SUCESSO!")
        print("=" * 60)
        print()
        print("O módulo de banco de dados foi modificado para usar o sistema de nomes por UUID.")
        print("Agora os nomes personalizados persistirão mesmo quando os IDs mudarem.")
        print()
        print("Backup do arquivo original está em:")
        print(f"  {BACKUP_DIR}")
        print()
    else:
        print("Falha ao aplicar o patch. Verifique os erros acima.")
    
if __name__ == "__main__":
    main()