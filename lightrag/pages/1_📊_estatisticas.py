#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Página de estatísticas
Visualizações estatísticas da base de conhecimento
"""

import streamlit as st
import pandas as pd
import os
import sys

# Garantir que o diretório raiz esteja no PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar componentes
from components.sidebar import render_sidebar
from utils.data_processing import load_knowledge_base

def main():
    """Função principal para a página de estatísticas"""
    # Configuração da página
    st.set_page_config(
        page_title="LightRAG - Estatísticas",
        page_icon="📊",
        layout="wide"
    )
    
    # Renderizar sidebar com informações e filtros
    render_sidebar("Estatísticas")
    
    # Título principal
    st.title("📊 Estatísticas da Base de Conhecimento")
    
    # Carregar base de conhecimento para estatísticas
    kb = load_knowledge_base()
    documents = kb.get("documents", [])
    
    if documents:
        # Layout com métricas principais
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de documentos", len(documents))
        
        # Análise de tamanho dos documentos
        doc_sizes = [len(doc.get("content", "")) for doc in documents]
        avg_size = sum(doc_sizes) / len(doc_sizes) if doc_sizes else 0
        max_size = max(doc_sizes) if doc_sizes else 0
        min_size = min(doc_sizes) if doc_sizes else 0
        
        col2.metric("Tamanho médio (caracteres)", f"{avg_size:.1f}")
        col3.metric("Maior documento", max_size)
        col4.metric("Menor documento", min_size)
        
        # Estatísticas por fonte
        st.markdown("### Documentos por fonte")
        sources = {}
        for doc in documents:
            source = doc.get("source", "desconhecido")
            sources[source] = sources.get(source, 0) + 1
        
        source_df = pd.DataFrame({"Fonte": list(sources.keys()), "Documentos": list(sources.values())})
        st.bar_chart(source_df.set_index("Fonte"))
        
        # Gráfico de distribuição de tamanho
        st.markdown("### Distribuição de tamanho dos documentos")
        df_sizes = pd.DataFrame({
            "ID": [doc.get("id", f"Doc {i}") for i, doc in enumerate(documents)], 
            "Tamanho": doc_sizes,
            "Resumo": [doc.get("summary", "Sem resumo") for doc in documents]
        })
        
        # Configurar tooltip para mostrar resumo ao passar o mouse
        st.bar_chart(df_sizes.set_index("ID")["Tamanho"])
        
        # Análise temporal
        st.markdown("### Histórico de inserções")
        if any("created" in doc for doc in documents):
            dates = [doc.get("created", "") for doc in documents if "created" in doc]
            dates = [d.split("T")[0] for d in dates]  # Extrair apenas a data
            
            date_counts = {}
            for date in dates:
                date_counts[date] = date_counts.get(date, 0) + 1
                
            df_dates = pd.DataFrame({
                "Data": list(date_counts.keys()),
                "Documentos inseridos": list(date_counts.values())
            })
            
            if not df_dates.empty:
                df_dates = df_dates.sort_values("Data")
                st.line_chart(df_dates.set_index("Data"))
            else:
                st.info("Dados temporais insuficientes para gerar o gráfico.")
        else:
            st.info("Dados temporais não disponíveis nos documentos.")
    else:
        st.info("Nenhum documento encontrado para gerar estatísticas.")
    
    # Rodapé
    st.markdown("---")
    st.caption("LightRAG - Sistema simplificado de RAG © 2025")

if __name__ == "__main__":
    main()