#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo que implementa a aba de projetos Claude no Streamlit
Exibe e monitora projetos do Claude Code indexados no LightRAG
"""

import streamlit as st
import os
import pandas as pd
import datetime
import time
from typing import Dict, List, Any, Optional

# Importar o carregador de projetos
from ui.load_claude_projects import get_projects, scan_projects

def render_projects_tab():
    """Renderiza a aba de projetos Claude no Streamlit"""
    st.markdown("## Projetos Claude")
    st.caption("Visualização das conversas com Claude Code indexadas no LightRAG")
    
    # Adicionar botão para atualizar manualmente a lista de projetos
    refresh_col, info_col = st.columns([1, 3])
    with refresh_col:
        if st.button("🔄 Atualizar projetos", use_container_width=True):
            with st.spinner("Atualizando projetos..."):
                scan_projects()
                st.success("Projetos atualizados!")
                st.rerun()
    
    with info_col:
        st.info("Esta aba mostra projetos do Claude Code que foram automaticamente indexados no LightRAG")
        
    # Verificar atualizações automaticamente a cada 10 segundos
    if 'last_check_time' not in st.session_state:
        st.session_state.last_check_time = time.time()
        
    current_time = time.time()
    if current_time - st.session_state.last_check_time > 10:
        # Forçar uma nova verificação a cada 10 segundos
        scan_projects()
        st.session_state.last_check_time = current_time
        st.rerun() # Atualiza a interface
    
    # Carregar projetos
    try:
        projects = get_projects()
        
        if not projects:
            st.warning("Nenhum projeto encontrado.")
            return
        
        # Preparar dados para a tabela
        projects_data = []
        for project in projects:
            # Formatar data
            date_str = project.get("last_updated", "")
            if date_str:
                try:
                    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d/%m/%Y")
                except:
                    formatted_date = date_str
            else:
                formatted_date = "N/A"
                
            # Formatar tamanho do arquivo
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
                "Atualizado": formatted_date,
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
                        first_msg = selected_project.get("first_message", "")
                        if first_msg:
                            st.info(first_msg)
                        else:
                            st.info("Mensagem inicial não disponível")
                    
                    with col2:
                        st.markdown("### Informações")
                        st.write(f"**ID:** {selected_project.get('id', 'N/A')}")
                        st.write(f"**Última atualização:** {selected_project.get('last_updated', 'N/A')}")
                        
                        file_path = selected_project.get("file_path", "")
                        if file_path and os.path.exists(file_path):
                            st.write(f"**Tamanho:** {selected_project.get('file_size', 0) / 1024:.1f} KB")
                            st.download_button(
                                label="📥 Baixar JSONL",
                                data=open(file_path, 'rb'),
                                file_name=os.path.basename(file_path),
                                mime="application/json"
                            )
    
    except Exception as e:
        st.error(f"Erro ao carregar projetos: {e}")

# Para teste direto deste módulo
if __name__ == "__main__":
    import streamlit as st
    st.set_page_config(page_title="Projetos Claude", page_icon="🤖", layout="wide")
    render_projects_tab()