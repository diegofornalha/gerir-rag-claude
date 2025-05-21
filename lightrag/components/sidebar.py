#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componente de sidebar para a interface Streamlit do LightRAG
Fornece navegação e informações de status
"""

import streamlit as st
from typing import Dict, Any

from utils.data_processing import check_server

def render_sidebar(active_tab: str = "Documentos"):
    """
    Renderiza a barra lateral com status e navegação
    
    Args:
        active_tab: Aba atualmente ativa
    
    Returns:
        Dict: Configurações e filtros selecionados na barra lateral
    """
    st.sidebar.title("🔍 LightRAG")
    st.sidebar.caption("Sistema de Retrieval Augmented Generation")
    
    # Status do servidor
    server_status = check_server()
    status_color = "green" if server_status.get("status") == "online" else "red"
    
    st.sidebar.markdown(f"### Status do Servidor: <span style='color:{status_color};'>●</span> {server_status.get('status', 'desconhecido')}", unsafe_allow_html=True)
    st.sidebar.write(f"Documentos: {server_status.get('documents', 0)}")
    st.sidebar.write(f"Última atualização: {server_status.get('lastUpdated', 'N/A')}")
    
    st.sidebar.markdown("---")
    
    # Adicionar opções de filtro ou configurações conforme a aba atual
    filters = {}
    
    if active_tab == "Consulta":
        st.sidebar.markdown("### Configurações de Consulta")
        filters["max_results"] = st.sidebar.slider("Máximo de resultados:", 1, 20, 5)
        filters["response_type"] = st.sidebar.radio(
            "Tipo de resposta:",
            ["Completa", "Resumida", "Somente contexto"]
        )
    
    elif active_tab == "Documentos":
        st.sidebar.markdown("### Filtros de Documentos")
        filters["source_filter"] = st.sidebar.text_input(
            "Filtrar por fonte:",
            placeholder="Digite para filtrar..."
        )
        filters["date_sort"] = st.sidebar.checkbox("Ordenar por data", value=True)
    
    elif active_tab == "Inserir":
        st.sidebar.markdown("### Dicas para Inserção")
        st.sidebar.info("""
        **Formatos suportados:**
        - Texto simples
        - Markdown
        - JSONL (uma entrada por linha)
        - Arquivos de texto (.txt, .md)
        
        Para melhores resultados, mantenha os documentos com tamanho entre 300-1000 caracteres.
        """)

    # Informações de ajuda
    with st.sidebar.expander("ℹ️ Sobre o LightRAG"):
        st.markdown("""
        **LightRAG** é um sistema simplificado de RAG (Retrieval Augmented Generation) para 
        melhorar as respostas de LLMs com conhecimento local.
        
        Este sistema permite:
        - Armazenar documentos
        - Consultar informações
        - Gerar respostas contextuais
        
        [Documentação completa](https://github.com/user/lightrag)
        """)
    
    st.sidebar.caption("Desenvolvido com Streamlit")
    
    return filters