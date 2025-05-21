#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Patch de UI
Este script aplica modificações à interface do LightRAG para substituir
IDs por nomes personalizados.
"""

import os
import re
import sys
import shutil
from typing import List, Dict

# Diretório do LightRAG
LIGHTRAG_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(LIGHTRAG_DIR, "ui")

# Arquivos a modificar
UI_FILES = [
    os.path.join(UI_DIR, "ui.py"),
    os.path.join(UI_DIR, "lightrag_ui.py"),
    os.path.join(UI_DIR, "integration.py")
]

# Diretório de backups
BACKUP_DIR = os.path.join(LIGHTRAG_DIR, "backups", "ui_patch")

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
    """Aplica modificações ao arquivo ui.py"""
    ui_file = os.path.join(UI_DIR, "ui.py")
    
    # Fazer backup
    backup_file(ui_file)
    
    # Ler conteúdo
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituições a serem feitas
    replacements = [
        # 1. Importar o módulo display_names
        (
            "import streamlit as st\nimport json\nimport os\nimport re\nimport pandas as pd\nimport time",
            "import streamlit as st\nimport json\nimport os\nimport re\nimport pandas as pd\nimport time\n\n# Importar módulo de nomes personalizados\nfrom ui.display_names import get_display_name, process_documents_for_display, get_document_options, get_documents_dataframe"
        ),
        
        # 2. Modificar a exibição da tabela de documentos
        (
            """            # Exibir tabela de documentos
            docs_data = []
            for doc in documents:
                # Truncar conteúdo longo
                content = doc.get("content", "")
                if len(content) > 100:
                    content = content[:97] + "..."
                    
                docs_data.append({
                    "ID": doc.get("id", ""),
                    "Resumo": doc.get("summary", "Arquivo de histórico de conversa"),
                    "Arquivo": content,
                    "Criado": doc.get("created", "").split("T")[0]
                })
            
            # Exibir tabela de documentos
            df = pd.DataFrame(docs_data)""",
            
            """            # Processar documentos para exibição
            docs_data = get_documents_dataframe(documents)
            
            # Exibir tabela de documentos
            df = pd.DataFrame(docs_data)"""
        ),
        
        # 3. Modificar a seleção de documentos
        (
            """            # Visualizar documento completo
            selected_doc_id = st.selectbox("Selecione um documento para visualizar:", 
                                          [""] + [doc.get("id", "") for doc in documents])""",
            
            """            # Visualizar documento completo
            document_options = get_document_options(documents)
            selected_option = st.selectbox(
                "Selecione um documento para visualizar:",
                options=[""] + [opt["label"] for opt in document_options],
                format_func=lambda x: x
            )
            
            # Obter o ID do documento selecionado
            selected_doc_id = ""
            if selected_option and selected_option != "":
                # Encontrar o ID correspondente ao nome selecionado
                for opt in document_options:
                    if opt["label"] == selected_option:
                        selected_doc_id = opt["id"]
                        break"""
        ),
        
        # 4. Modificar metadados para não mostrar ID
        (
            """                            st.markdown("### Metadados")
                            st.write(f"ID: {doc.get('id', 'N/A')}")
                            st.write(f"Fonte: {doc.get('source', 'desconhecido')}")
                            st.write(f"Criado em: {doc.get('created', 'N/A')}")""",
            
            """                            st.markdown("### Metadados")
                            st.write(f"Nome: {get_display_name(doc.get('id', ''), doc.get('source', ''), doc.get('summary', 'N/A'))}")
                            st.write(f"Fonte: {doc.get('source', 'desconhecido')}")
                            st.write(f"Criado em: {doc.get('created', 'N/A')}")"""
        ),
        
        # 5. Ocultar o ID nos contextos de consulta
        (
            """                                    if "document_id" in ctx:
                                        st.markdown(f"**ID:** `{ctx.get('document_id', '')}`")""",
            
            """                                    if "document_id" in ctx:
                                        doc_id = ctx.get('document_id', '')
                                        display_name = get_display_name(doc_id, ctx.get('source', ''))
                                        st.markdown(f"**Documento:** `{display_name}`")"""
        ),
        
        # 6. Substituir exibição de ID após inserção
        (
            """                                st.success(f"Documento inserido com sucesso! ID: {result.get('documentId')}")""",
            
            """                                doc_id = result.get('documentId')
                                display_name = get_display_name(doc_id, doc_source)
                                st.success(f"Documento inserido com sucesso! Nome: {display_name}")"""
        ),
        
        # 7. Substituir mensagens de exclusão
        (
            """                                if self.delete_document(selected_doc_id):""",
            
            """                                display_name = get_display_name(selected_doc_id)
                                if self.delete_document(selected_doc_id):
                                    st.success(f"Documento '{display_name}' excluído com sucesso!")"""
        ),
        
        # 8. Substituir mensagem de sucesso na exclusão
        (
            """                st.success(f"Documento {doc_id} excluído com sucesso!")""",
            
            """                display_name = get_display_name(doc_id)
                st.success(f"Documento '{display_name}' excluído com sucesso!")"""
        )
    ]
    
    # Aplicar substituições
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Salvar arquivo modificado
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Arquivo ui.py modificado com sucesso")

def patch_lightrag_ui():
    """Aplica modificações ao arquivo lightrag_ui.py"""
    ui_file = os.path.join(UI_DIR, "lightrag_ui.py")
    
    # Fazer backup
    backup_file(ui_file)
    
    # Ler conteúdo
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituições a serem feitas
    replacements = [
        # 1. Importar o módulo display_names
        (
            "# Importar componentes do LightRAG\nfrom core.client import LightRAGClient, ensure_server_running\nfrom core.settings import DB_FILE, MEMORY_SUMMARY_FILE\nfrom utils.logger import get_ui_logger",
            "# Importar componentes do LightRAG\nfrom core.client import LightRAGClient, ensure_server_running\nfrom core.settings import DB_FILE, MEMORY_SUMMARY_FILE\nfrom utils.logger import get_ui_logger\nfrom ui.display_names import get_display_name, process_documents_for_display, get_document_options, get_documents_dataframe"
        ),
        
        # 2. Substituir a função load_custom_names para usar o novo sistema
        (
            """def load_custom_names():
    """Carrega os nomes personalizados do arquivo JSON"""
    if os.path.exists(CUSTOM_NAMES_FILE):
        try:
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar nomes personalizados: {e}")
    return {}""",
            
            """def load_custom_names():
    """Carrega os nomes personalizados do arquivo JSON"""
    # Esta função está sendo substituída pelo módulo display_names
    from ui.display_names import load_custom_names
    return load_custom_names()"""
        )
    ]
    
    # Aplicar substituições
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Salvar arquivo modificado
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Arquivo lightrag_ui.py modificado com sucesso")

def patch_integration():
    """Aplica modificações ao arquivo integration.py"""
    ui_file = os.path.join(UI_DIR, "integration.py")
    
    # Fazer backup
    backup_file(ui_file)
    
    # Ler conteúdo
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituições a serem feitas
    replacements = [
        # 1. Importar o módulo display_names
        (
            "import os\nimport json\nimport time\nimport sqlite3\nimport streamlit as st\nfrom datetime import datetime",
            "import os\nimport json\nimport time\nimport sqlite3\nimport streamlit as st\nfrom datetime import datetime\n\n# Importar módulo de nomes personalizados\nsys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\nfrom ui.display_names import get_display_name"
        ),
        
        # 2. Modificar para incluir display_name nos documentos
        (
            """            # Adicionar nome do projeto inferido do arquivo
            file_name = os.path.basename(row['file_path'])
            doc["title"] = file_name.replace('.jsonl', '')""",
            
            """            # Adicionar nome do projeto inferido do arquivo
            file_name = os.path.basename(row['file_path'])
            doc["title"] = file_name.replace('.jsonl', '')
            
            # Adicionar nome personalizado
            display_name = get_display_name(doc["id"], row['file_path'])
            doc["display_name"] = display_name"""
        )
    ]
    
    # Aplicar substituições
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Salvar arquivo modificado
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Arquivo integration.py modificado com sucesso")

def main():
    """Função principal para aplicar todas as modificações"""
    print("===== LightRAG UI Patch =====")
    print("Este script modifica a interface do LightRAG para ocultar IDs\ne mostrar apenas nomes personalizados.")
    print("")
    
    # Aplicar modificações
    patch_ui_py()
    patch_lightrag_ui()
    patch_integration()
    
    print("\n🎉 Modificações concluídas com sucesso!")
    print("A interface agora mostrará nomes personalizados em vez de IDs.")
    print("Os backups dos arquivos originais estão em: " + BACKUP_DIR)

if __name__ == "__main__":
    main()