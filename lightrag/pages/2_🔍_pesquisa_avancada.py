#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Página de pesquisa avançada
Interface para consultas avançadas à base de conhecimento
"""

import streamlit as st
import time
import os
import sys

# Garantir que o diretório raiz esteja no PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar componentes
from components.sidebar import render_sidebar
from components.search_results import render_search_result, render_search_form, format_search_result
from utils.data_processing import check_server

# Importar módulos do LightRAG
from core.client import LightRAGClient

def perform_search(query, mode, max_results=5, response_type="Completa"):
    """
    Executa uma consulta no LightRAG
    
    Args:
        query: Texto da consulta
        mode: Modo de consulta (hybrid, semantic, keyword)
        max_results: Número máximo de resultados
        response_type: Tipo de resposta desejada
    
    Returns:
        Dict: Resultado formatado da consulta
        float: Tempo de execução em segundos
    """
    try:
        # Verificar se a API está disponível
        server_status = check_server()
        if server_status.get("status") != "online":
            return {
                "response": "",
                "contexts": [],
                "has_error": True,
                "error": "Servidor LightRAG não está disponível"
            }, 0
        
        # Mostrar spinner durante a consulta
        with st.spinner("Consultando base de conhecimento..."):
            start_time = time.time()
            client = LightRAGClient()
            
            # Configurações adicionais para o tipo de resposta
            only_context = response_type == "Somente contexto"
            
            # Executar consulta
            result = client.query(
                query, 
                max_results=max_results, 
                mode=mode, 
                only_context=only_context
            )
            
            elapsed = time.time() - start_time
            
            # Formatar resultado
            formatted_result = format_search_result(result)
            
            return formatted_result, elapsed
    except Exception as e:
        return {
            "response": "",
            "contexts": [],
            "has_error": True,
            "error": f"Erro ao executar consulta: {str(e)}"
        }, 0

def main():
    """Função principal para a página de pesquisa avançada"""
    # Configuração da página
    st.set_page_config(
        page_title="LightRAG - Pesquisa Avançada",
        page_icon="🔍",
        layout="wide"
    )
    
    # Título principal
    st.title("🔍 Pesquisa Avançada")
    
    # Renderizar sidebar com informações e filtros
    filters = render_sidebar("Pesquisa Avançada")
    
    # Extrair configurações da sidebar
    max_results = filters.get("max_results", 5)
    response_type = filters.get("response_type", "Completa")
    
    # Inicializar estado da sessão para histórico de pesquisas
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    
    # Layout principal
    st.markdown("""
    ### Consulta Avançada à Base de Conhecimento
    
    Esta interface permite realizar consultas avançadas usando diferentes modos de busca:
    - **Hybrid**: Combina busca semântica e por palavras-chave
    - **Semantic**: Usa embeddings para encontrar conteúdo semanticamente similar
    - **Keyword**: Busca por correspondência exata de palavras-chave
    """)
    
    # Separador
    st.markdown("---")
    
    # Formulário de pesquisa
    def handle_search(query, mode):
        result, elapsed = perform_search(
            query, 
            mode, 
            max_results=max_results,
            response_type=response_type
        )
        
        # Adicionar ao histórico
        if not result["has_error"]:
            st.session_state.search_history.append({
                "query": query,
                "mode": mode,
                "response": result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"],
                "timestamp": time.strftime("%H:%M:%S")
            })
            
            # Limitar histórico a 10 itens
            if len(st.session_state.search_history) > 10:
                st.session_state.search_history = st.session_state.search_history[-10:]
        
        # Exibir resultado
        render_search_result(result, elapsed)
    
    # Renderizar formulário de pesquisa
    query, mode = render_search_form(
        handle_search,
        modes=["hybrid", "semantic", "keyword", "fuzzy"]
    )
    
    # Mostrar histórico de pesquisas
    if st.session_state.search_history:
        with st.expander("Histórico de Pesquisas", expanded=False):
            for i, item in enumerate(reversed(st.session_state.search_history)):
                cols = st.columns([3, 1, 1])
                with cols[0]:
                    st.markdown(f"**{item['query']}**")
                    st.caption(item["response"])
                with cols[1]:
                    st.caption(f"Modo: {item['mode']}")
                with cols[2]:
                    st.caption(f"Hora: {item['timestamp']}")
                    
                    # Botão para repetir pesquisa
                    if st.button("Repetir", key=f"repeat_{i}"):
                        handle_search(item["query"], item["mode"])
                
                if i < len(st.session_state.search_history) - 1:
                    st.markdown("---")
    
    # Rodapé
    st.markdown("---")
    st.caption("LightRAG - Sistema simplificado de RAG © 2025")

if __name__ == "__main__":
    main()