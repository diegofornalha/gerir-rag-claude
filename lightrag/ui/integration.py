import os
import json
import time
import sqlite3
import streamlit as st
from datetime import datetime

# Arquivo de sincronização compartilhado com o monitor
SYNC_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".sync_timestamp")
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents.db")

@st.cache_data(ttl=5)
def get_sync_timestamp():
    """Lê o timestamp de sincronização do arquivo compartilhado"""
    if os.path.exists(SYNC_FILE):
        try:
            with open(SYNC_FILE, 'r') as f:
                return float(f.read().strip())
        except Exception:
            return 0
    return 0

def get_projects_from_db():
    """Lê os documentos do banco de dados SQLite"""
    if not os.path.exists(DB_FILE):
        return []
    
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # Para acessar as colunas por nome
        cursor = conn.cursor()
        
        # Buscar todos os documentos
        cursor.execute("""
            SELECT file_path, doc_id, content_hash, file_size, last_modified, metadata
            FROM documents
            ORDER BY last_modified DESC
        """)
        
        result = []
        for row in cursor.fetchall():
            # Converter para dicionário
            doc = {
                "id": row['doc_id'],
                "file_path": row['file_path'],
                "content_hash": row['content_hash'],
                "file_size": row['file_size']
            }
            
            # Adicionar metadados se disponíveis
            if row['metadata']:
                try:
                    metadata = json.loads(row['metadata'])
                    doc.update(metadata)
                except:
                    pass
            
            # Adicionar nome do projeto inferido do arquivo
            file_name = os.path.basename(row['file_path'])
            doc["title"] = file_name.replace('.jsonl', '')
            
            # Adicionar data formatada
            if row['last_modified']:
                try:
                    date = datetime.fromtimestamp(row['last_modified'])
                    doc["last_updated"] = date.strftime("%Y-%m-%d")
                except:
                    doc["last_updated"] = "Desconhecida"
            
            result.append(doc)
        
        conn.close()
        return result
    
    except Exception as e:
        st.error(f"Erro ao ler banco de dados: {e}")
        if 'conn' in locals():
            conn.close()
        return []

def get_first_message(file_path):
    """Lê a primeira mensagem do usuário de um arquivo JSONL"""
    if not os.path.exists(file_path):
        return "Arquivo não encontrado"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Ler as primeiras 10 linhas para buscar a primeira mensagem real
            for _ in range(10):
                line = f.readline().strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Ignorar linhas de sumário
                    if data.get('type') == 'summary':
                        continue
                    
                    # Verificar se é uma mensagem do usuário
                    if isinstance(data.get('message'), dict) and data.get('message', {}).get('role') == 'user':
                        content = data.get('message', {}).get('content', '')
                        # Retornar apenas texto (não comandos ou metadados)
                        if isinstance(content, str) and not content.startswith('<command-name>'):
                            return content[:150] + ('...' if len(content) > 150 else '')
                
                except:
                    pass
        
        return "Nenhuma mensagem encontrada"
    
    except Exception as e:
        return f"Erro ao ler arquivo: {e}"

def check_for_updates():
    """Verifica se houve atualizações na base desde a última verificação"""
    if 'last_sync_time' not in st.session_state:
        st.session_state.last_sync_time = 0
    
    current_sync_time = get_sync_timestamp()
    
    # Se o timestamp de sincronização for mais recente que o armazenado na sessão
    if current_sync_time > st.session_state.last_sync_time:
        st.session_state.last_sync_time = current_sync_time
        # Limpar o cache para forçar releitura dos dados
        st.cache_data.clear()
        return True
    
    return False

def render_projects_tab():
    """Renderiza a aba de projetos Claude no Streamlit"""
    st.markdown("## Projetos Claude")
    st.caption("Visualização das conversas com Claude Code indexadas no LightRAG")
    
    # Adicionar botão para atualizar manualmente a lista de projetos
    refresh_col, info_col = st.columns([1, 3])
    with refresh_col:
        if st.button("🔄 Atualizar projetos", use_container_width=True):
            # Limpar o cache para forçar releitura dos dados
            st.cache_data.clear()
            st.session_state.last_sync_time = time.time()
            st.success("Projetos atualizados!")
            st.rerun()
    
    with info_col:
        st.info("Esta aba mostra projetos do Claude Code que foram automaticamente indexados no LightRAG")
    
    # Verificar atualizações automaticamente
    if check_for_updates():
        st.rerun()
    
    # Carregar projetos
    projects = get_projects_from_db()
    
    if not projects:
        st.warning("Nenhum projeto encontrado na base de dados.")
        return
    
    # Preparar dados para a tabela
    projects_data = []
    for project in projects:
        # Formatação do tamanho
        size_kb = project.get("file_size", 0) / 1024
        if size_kb < 1:
            size_str = f"{project.get('file_size', 0)} bytes"
        elif size_kb < 1024:
            size_str = f"{size_kb:.1f} KB"
        else:
            size_str = f"{size_kb/1024:.1f} MB"
        
        projects_data.append({
            "ID": project.get("id", ""),
            "Título": project.get("title", "Sem título"),
            "Atualizado": project.get("last_updated", "N/A"),
            "Tamanho": size_str
        })
    
    # Exibir tabela de projetos
    df = pd.DataFrame(projects_data)
    st.dataframe(df, use_container_width=True)
    
    # Visualizar projeto selecionado
    selected_project_id = st.selectbox(
        "Selecione um projeto para visualizar:", 
        [""] + [p.get("id", "") for p in projects]
    )
    
    if selected_project_id:
        selected_project = next((p for p in projects if p.get("id") == selected_project_id), None)
        if selected_project:
            with st.expander("Detalhes do Projeto", expanded=True):
                st.subheader(selected_project.get("title", "Projeto sem título"))
                
                # Layout em colunas para informações e ações
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("### Primeira mensagem")
                    file_path = selected_project.get("file_path", "")
                    first_msg = get_first_message(file_path)
                    st.info(first_msg)
                
                with col2:
                    st.markdown("### Informações")
                    st.write(f"**ID:** {selected_project.get('id', 'N/A')}")
                    st.write(f"**Atualizado:** {selected_project.get('last_updated', 'N/A')}")
                    st.write(f"**Hash:** {selected_project.get('content_hash', 'N/A')[:8]}...")
                    
                    file_path = selected_project.get("file_path", "")
                    if file_path and os.path.exists(file_path):
                        st.write(f"**Tamanho:** {selected_project.get('file_size', 0) / 1024:.1f} KB")
                        st.download_button(
                            label="📥 Baixar JSONL",
                            data=open(file_path, 'rb'),
                            file_name=os.path.basename(file_path),
                            mime="application/json"
                        )

# Importação condicional para permitir o uso em módulos que importam este
if __name__ == "__main__":
    import pandas as pd
    st.set_page_config(page_title="Projetos Claude", page_icon="🤖", layout="wide")
    render_projects_tab()
else:
    import pandas as pd