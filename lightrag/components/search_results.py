#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componente para exibição de resultados de busca
Fornece visualização otimizada de resultados de consulta
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

@st.cache_data(ttl=10)
def format_search_result(result: Dict[str, Any], max_context_items: int = 5):
    """
    Formata um resultado de busca para exibição
    
    Args:
        result: Resultado da consulta
        max_context_items: Número máximo de itens de contexto a exibir
    
    Returns:
        Dict: Resultado formatado
    """
    if not result:
        return {
            "response": "Sem resposta",
            "contexts": [],
            "has_error": True,
            "error": "Resultado vazio"
        }
    
    # Extrair resposta principal
    response = result.get('response', 'Sem resposta gerada')
    
    # Formatar contextos
    contexts = []
    for ctx in result.get('context', [])[:max_context_items]:
        contexts.append({
            "content": ctx.get('content', 'Conteúdo não disponível'),
            "source": ctx.get('source', 'Fonte desconhecida'),
            "document_id": ctx.get('document_id', ''),
            "relevance": ctx.get('relevance', 0)
        })
    
    # Verificar se há erro
    has_error = False
    error_msg = ""
    if 'error' in result:
        has_error = True
        error_msg = result['error']
    
    return {
        "response": response,
        "contexts": contexts,
        "has_error": has_error,
        "error": error_msg
    }

def render_search_result(result: Dict[str, Any], elapsed_time: float = 0):
    """
    Renderiza um resultado de busca formatado
    
    Args:
        result: Resultado formatado
        elapsed_time: Tempo de execução da consulta em segundos
    """
    # Exibir resposta principal
    with st.container(border=True):
        st.markdown("### Resposta")
        if result["has_error"]:
            st.error(result["error"] or "Erro na consulta")
        else:
            st.info(result["response"])
            
        # Mostrar tempo de execução se disponível
        if elapsed_time > 0:
            st.caption(f"Consulta executada em {elapsed_time:.2f} segundos")
    
    # Exibir contextos encontrados
    contexts = result.get("contexts", [])
    if contexts:
        st.markdown("### Documentos relevantes encontrados:")
        
        # Usando grid de cartões para melhor apresentação
        cols = st.columns(min(3, len(contexts)))
        
        for i, ctx in enumerate(contexts):
            with cols[i % len(cols)]:
                relevance = ctx.get('relevance', 0)
                relevance_color = "green" if relevance > 0.7 else "orange" if relevance > 0.4 else "red"
                
                with st.container(border=True):
                    st.markdown(f"#### Documento {i+1}")
                    st.markdown(f"**Relevância:** :{relevance_color}[{relevance:.2f}]")
                    st.caption(f"Fonte: {ctx.get('source', 'desconhecido')}")
                    
                    if ctx["document_id"]:
                        st.caption(f"ID: `{ctx['document_id']}`")
                    
                    st.markdown("---")
                    # Limitar o tamanho do texto exibido
                    content = ctx.get("content", "")
                    if len(content) > 300:
                        st.markdown(f"{content[:300]}...")
                        with st.expander("Ver conteúdo completo"):
                            st.markdown(content)
                    else:
                        st.markdown(content)
        
        # Exibição alternativa expandida para contextos (ativada em telas menores)
        with st.expander("Ver todos os resultados em lista"):
            for i, ctx in enumerate(contexts):
                relevance = ctx.get('relevance', 0)
                relevance_color = "green" if relevance > 0.7 else "orange" if relevance > 0.4 else "red"
                
                with st.expander(f"Documento {i+1} - Relevância: **:{relevance_color}[{relevance:.2f}]**"):
                    st.markdown(f"**Fonte:** {ctx.get('source', 'desconhecido')}")
                    if ctx["document_id"]:
                        st.markdown(f"**ID:** `{ctx['document_id']}`")
                    st.markdown("---")
                    st.markdown(ctx.get("content", ""))
    else:
        if not result["has_error"]:
            st.info("Nenhum documento relevante encontrado.")
        
def render_search_form(on_search, default_query="", modes=None):
    """
    Renderiza um formulário de pesquisa otimizado
    
    Args:
        on_search: Função a ser chamada quando a pesquisa for acionada
        default_query: Consulta padrão
        modes: Lista de modos de pesquisa disponíveis
    """
    if modes is None:
        modes = ["hybrid", "semantic", "keyword"]
    
    # Layout com dois painéis
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Pesquisar na base de conhecimento:", 
            value=default_query,
            placeholder="Digite sua consulta aqui..."
        )
    
    with col2:
        mode = st.selectbox("Modo:", modes)
        search_button = st.button("🔍 Consultar", type="primary", use_container_width=True)
    
    if search_button and query:
        on_search(query, mode)
    elif search_button and not query:
        st.warning("Por favor, digite uma consulta.")
        
    return query, mode