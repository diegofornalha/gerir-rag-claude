#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componente para visualização de documentos no LightRAG
Fornece um visualizador detalhado para documentos na base de conhecimento
"""

import streamlit as st
import pandas as pd
import time
from typing import Dict, List, Any, Optional

from utils.data_processing import extract_entities, delete_document

def render_document_details(doc: Dict[str, Any], custom_names: Dict[str, str] = None):
    """
    Renderiza os detalhes de um documento
    
    Args:
        doc: Documento para exibir
        custom_names: Dicionário com nomes personalizados
    """
    if not doc:
        return
        
    with st.expander("Documento Detalhado", expanded=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(doc.get("summary", "Documento"))
            content = doc.get("content", "")
            st.text_area("Conteúdo:", content, height=300)
            
            # Detectar e mostrar entidades
            entities = extract_entities(content)
            if entities:
                st.markdown("#### Entidades Detectadas:")
                for entity in entities:
                    st.markdown(f"- `{entity}`")
        
        with col2:
            st.markdown("### Metadados")
            doc_id = doc.get('id', 'N/A')
            st.write(f"ID: {doc_id}")
            st.write(f"Fonte: {doc.get('source', 'desconhecido')}")
            st.write(f"Criado em: {doc.get('created', 'N/A')}")
            
            # Adicionar campo para nome personalizado
            if custom_names is not None:
                st.markdown("### Nome Personalizado")
                custom_name = custom_names.get(doc_id, "")
                
                # Mostrar o ID do documento (útil para depuração)
                st.code(f"ID: {doc_id}")
                
                new_custom_name = st.text_input("Nome de identificação:", 
                                              value=custom_name, 
                                              key=f"custom_name_{doc_id}",
                                              placeholder="Digite um nome amigável...")
                
                return_value = {
                    "doc_id": doc_id,
                    "custom_name": new_custom_name if new_custom_name != custom_name else None
                }
                
                return return_value
                
def render_documents_table(documents: List[Dict[str, Any]], custom_names: Dict[str, str] = None):
    """
    Renderiza uma tabela com os documentos disponíveis
    
    Args:
        documents: Lista de documentos para exibir
        custom_names: Dicionário com nomes personalizados
    
    Returns:
        DataFrame: Tabela formatada com os documentos
    """
    if not documents:
        st.info("Nenhum documento encontrado na base de conhecimento.")
        return None
        
    # Exibir tabela de documentos
    docs_data = []
    for doc in documents:
        # Truncar conteúdo longo
        content = doc.get("content", "")
        if len(content) > 100:
            content = content[:97] + "..."
        
        # Adicionar nome personalizado se existir
        doc_id = doc.get("id", "")
        custom_name = custom_names.get(doc_id, "") if custom_names else ""
            
        docs_data.append({
            "ID": doc_id,
            "Nome Personalizado": custom_name,
            "Resumo": doc.get("summary", "Arquivo de histórico de conversa"),
            "Conteúdo": content,
            "Criado": doc.get("created", "").split("T")[0]
        })
    
    # Exibir tabela de documentos
    df = pd.DataFrame(docs_data)
    st.dataframe(df, use_container_width=True)
    
    return df