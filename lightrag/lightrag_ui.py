#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG UI - Interface para o sistema LightRAG
Implementação com Streamlit para visualização e gerenciamento da base de conhecimento
"""

import streamlit as st
import json
import os
import requests
import datetime
import pandas as pd

# Configuração
LIGHTRAG_URL = "http://127.0.0.1:5000"
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lightrag_db.json')

# Título e introdução
st.set_page_config(
    page_title="LightRAG - Interface", 
    page_icon="🔍", 
    layout="wide"
)

st.title("🔍 LightRAG - Sistema de RAG")
st.subheader("Retrieval Augmented Generation")

# Verificar conexão com o servidor
@st.cache_data(ttl=5)
def check_server():
    try:
        response = requests.get(f"{LIGHTRAG_URL}/status", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {"status": "offline", "error": f"Código de resposta: {response.status_code}"}
    except Exception as e:
        return {"status": "offline", "error": str(e)}

# Carregar base de conhecimento
@st.cache_data(ttl=5)
def load_knowledge_base():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar base de conhecimento: {str(e)}")
    return {"documents": [], "lastUpdated": ""}

# Função para excluir documento
def delete_document(doc_id):
    try:
        response = requests.post(
            f"{LIGHTRAG_URL}/delete", 
            json={"id": doc_id},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                st.success(f"Documento {doc_id} excluído com sucesso!")
                st.cache_data.clear()  # Limpar cache para atualizar a lista
                return True
            else:
                st.error(result.get("error", "Erro desconhecido"))
        else:
            st.error(f"Erro na exclusão: {response.status_code}")
    except Exception as e:
        st.error(f"Erro ao conectar ao servidor: {str(e)}")
    return False

# Verificar status do servidor
server_status = check_server()
status_color = "green" if server_status.get("status") == "online" else "red"

# Layout com colunas para status e pesquisa
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown(f"### Status do Servidor: <span style='color:{status_color};'>●</span> {server_status.get('status', 'desconhecido')}", unsafe_allow_html=True)
    st.write(f"Documentos: {server_status.get('documents', 0)}")
    st.write(f"Última atualização: {server_status.get('lastUpdated', 'N/A')}")

with col2:
    # Campo de consulta
    query = st.text_input("Pesquisar na base de conhecimento:", placeholder="Digite sua consulta aqui...")
    if st.button("Consultar"):
        if query:
            try:
                response = requests.post(
                    f"{LIGHTRAG_URL}/query", 
                    json={"query": query, "max_results": 10},
                    timeout=5
                )
                if response.status_code == 200:
                    result = response.json()
                    st.success(result.get("response", "Sem resposta"))
                    
                    # Exibir contextos encontrados
                    if result.get("context"):
                        st.markdown("### Documentos relevantes encontrados:")
                        for i, ctx in enumerate(result.get("context", [])):
                            with st.expander(f"Documento {i+1} - Relevância: {ctx.get('relevance', 0):.2f}"):
                                st.write(ctx.get("content", ""))
                                st.caption(f"Fonte: {ctx.get('source', 'desconhecido')}")
                                if "document_id" in ctx:
                                    st.caption(f"ID: {ctx.get('document_id', '')}")
                    else:
                        st.info("Nenhum documento relevante encontrado.")
                else:
                    st.error(f"Erro na consulta: {response.status_code}")
            except Exception as e:
                st.error(f"Erro ao conectar ao servidor: {str(e)}")
        else:
            st.warning("Por favor, digite uma consulta.")

# Abas para diferentes funcionalidades
tab1, tab2, tab3 = st.tabs(["Documentos", "Inserir", "Estatísticas"])

# Aba de visualização de documentos
with tab1:
    st.markdown("## Documentos na Base de Conhecimento")
    
    # Carregar base de conhecimento
    kb = load_knowledge_base()
    documents = kb.get("documents", [])
    
    if documents:
        # Exibir tabela de documentos
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
        df = pd.DataFrame(docs_data)
        st.dataframe(df, use_container_width=True)
        
        # Visualizar documento completo
        selected_doc_id = st.selectbox("Selecione um documento para visualizar:", 
                                      [""] + [doc.get("id", "") for doc in documents])
        
        if selected_doc_id:
            doc = next((d for d in documents if d.get("id") == selected_doc_id), None)
            if doc:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(doc.get("summary", "Documento"))
                    st.text_area("Conteúdo completo:", doc.get("content", ""), height=200)
                    st.write(f"Caminho: {doc.get('path', 'desconhecido')}")
                    st.write(f"Criado em: {doc.get('created', 'N/A')}")
                with col2:
                    st.write("### Ações do documento")
                    if st.button("🗑️ Excluir documento", type="primary", key=f"delete_{selected_doc_id}"):
                        if delete_document(selected_doc_id):
                            st.rerun()  # Recarregar a página para atualizar
    else:
        st.info("Nenhum documento encontrado na base de conhecimento.")

# Aba de inserção de novos documentos
with tab2:
    st.markdown("## Adicionar Novo Documento")
    
    # Formulário para adicionar documento
    with st.form("insert_form"):
        doc_content = st.text_area("Conteúdo do documento:", height=200)
        doc_source = st.text_input("Fonte:", "manual")
        doc_summary = st.text_input("Resumo do documento:", "Nota manual")
        
        submitted = st.form_submit_button("Inserir Documento")
        if submitted:
            if doc_content:
                try:
                    response = requests.post(
                        f"{LIGHTRAG_URL}/insert", 
                        json={"text": doc_content, "source": doc_source, "summary": doc_summary},
                        timeout=5
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            st.success(f"Documento inserido com sucesso! ID: {result.get('documentId')}")
                            st.cache_data.clear()  # Limpar cache para atualizar a lista
                        else:
                            st.error(result.get("error", "Erro desconhecido"))
                    else:
                        st.error(f"Erro na inserção: {response.status_code}")
                except Exception as e:
                    st.error(f"Erro ao conectar ao servidor: {str(e)}")
            else:
                st.warning("Por favor, digite o conteúdo do documento.")
    
    # Opção para limpar base
    st.markdown("## Gerenciamento da Base")
    if st.button("Limpar toda a base de conhecimento", type="primary", use_container_width=True):
        try:
            response = requests.post(
                f"{LIGHTRAG_URL}/clear", 
                json={"confirm": True},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    st.success(result.get("message", "Base limpa com sucesso"))
                    st.info(f"Backup criado: {result.get('backup', 'N/A')}")
                    st.cache_data.clear()  # Limpar cache para atualizar a lista
                else:
                    st.error(result.get("error", "Erro desconhecido"))
            else:
                st.error(f"Erro ao limpar base: {response.status_code}")
        except Exception as e:
            st.error(f"Erro ao conectar ao servidor: {str(e)}")

# Aba de estatísticas
with tab3:
    st.markdown("## Estatísticas da Base de Conhecimento")
    
    # Carregar base de conhecimento para estatísticas
    kb = load_knowledge_base()
    documents = kb.get("documents", [])
    
    if documents:
        # Estatísticas básicas
        st.metric("Total de documentos", len(documents))
        
        # Análise de tamanho dos documentos
        doc_sizes = [len(doc.get("content", "")) for doc in documents]
        avg_size = sum(doc_sizes) / len(doc_sizes) if doc_sizes else 0
        max_size = max(doc_sizes) if doc_sizes else 0
        min_size = min(doc_sizes) if doc_sizes else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Tamanho médio (caracteres)", f"{avg_size:.1f}")
        col2.metric("Maior documento", max_size)
        col3.metric("Menor documento", min_size)
        
        # Gráfico de distribuição de tamanho
        st.markdown("### Distribuição de tamanho dos documentos")
        df_sizes = pd.DataFrame({"Documento": [doc.get("id", f"Doc {i}") for i, doc in enumerate(documents)], 
                                "Tamanho": doc_sizes})
        st.bar_chart(df_sizes.set_index("Documento"))
        
        # Histórico de inserções
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
st.caption("Desenvolvido com Streamlit e Flask")