#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Sistema de Retrieval Augmented Generation
Aplicação principal Streamlit
"""

import streamlit as st
import os
import json
import time
from typing import Dict, List, Any, Optional

# Garantir que o diretório raiz esteja no PYTHONPATH
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar componentes
from components.sidebar import render_sidebar
from components.document_viewer import render_document_details, render_documents_table
from utils.data_processing import (
    check_server, 
    load_knowledge_base, 
    load_memory_summary,
    delete_document
)

# Importar módulos do LightRAG
from core.client import LightRAGClient, ensure_server_running

# Arquivo para armazenar nomes personalizados
CUSTOM_NAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_project_names.json")

def load_custom_names():
    """Carrega os nomes personalizados do arquivo JSON"""
    if os.path.exists(CUSTOM_NAMES_FILE):
        try:
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar nomes personalizados: {e}")
    return {}

def save_custom_name(project_id, custom_name):
    """Salva um nome personalizado para um projeto"""
    custom_names = load_custom_names()
    custom_names[project_id] = custom_name
    
    try:
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_names, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar nome personalizado: {e}")
        return False

def render_documents_tab():
    """Renderiza a aba de visualização de documentos"""
    st.markdown("## Base de Conhecimento LightRAG")
    
    # Carregar nomes personalizados
    custom_names = load_custom_names()
    
    # Carregar base de conhecimento
    kb = load_knowledge_base()
    documents = kb.get("documents", [])
    
    # Mostrar tabela de documentos
    df = render_documents_table(documents, custom_names)
    
    if df is not None:
        # Visualizar documento completo
        selected_doc_id = st.selectbox("Selecione um documento para visualizar:", 
                                      [""] + [doc.get("id", "") for doc in documents])
        
        if selected_doc_id:
            doc = next((d for d in documents if d.get("id") == selected_doc_id), None)
            if doc:
                result = render_document_details(doc, custom_names)
                
                if result and result.get("custom_name") is not None:
                    # Botão para salvar nome personalizado
                    if st.button("💾 Salvar Nome", key=f"save_name_{selected_doc_id}"):
                        # Salvar o nome personalizado
                        success = save_custom_name(result["doc_id"], result["custom_name"])
                        
                        if success:
                            st.success(f"Nome personalizado salvo com sucesso!")
                            # Limpar o cache para garantir que os dados sejam recarregados
                            st.cache_data.clear()
                            # Recarregar a página após um breve atraso
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Falha ao salvar o nome personalizado.")
                
                # Botão para excluir documento
                if st.button("🗑️ Excluir documento", type="primary", key=f"delete_{selected_doc_id}"):
                    if delete_document(selected_doc_id):
                        st.rerun()  # Recarregar a página para atualizar

def render_query_tab():
    """Renderiza a aba de consulta"""
    st.markdown("## Consulta RAG")
    
    # Campo de consulta
    query = st.text_input("Pesquisar na base de conhecimento:", placeholder="Digite sua consulta aqui...")
    mode = st.radio("Modo de consulta:", ["hybrid", "semantic", "keyword"], horizontal=True)
    
    # Os filtros max_results e response_type vêm da barra lateral
    
    if st.button("🔍 Consultar"):
        if query:
            try:
                with st.spinner("Consultando base de conhecimento..."):
                    start_time = time.time()
                    client = LightRAGClient()
                    result = client.query(query, st.session_state.get("max_results", 5), mode)
                    elapsed = time.time() - start_time
                    
                    # Exibir resposta principal
                    with st.container(border=True):
                        st.markdown("### Resposta")
                        st.info(result.get("response", "Sem resposta"))
                        st.caption(f"Consulta executada em {elapsed:.2f} segundos")
                    
                    # Exibir contextos encontrados
                    if result.get("context"):
                        st.markdown("### Documentos relevantes encontrados:")
                        for i, ctx in enumerate(result.get("context", [])):
                            relevance = ctx.get('relevance', 0)
                            relevance_color = "green" if relevance > 0.7 else "orange" if relevance > 0.4 else "red"
                            
                            with st.expander(f"Documento {i+1} - Relevância: **:{relevance_color}[{relevance:.2f}]**", expanded=i==0):
                                st.markdown(f"**Fonte:** {ctx.get('source', 'desconhecido')}")
                                if "document_id" in ctx:
                                    st.markdown(f"**ID:** `{ctx.get('document_id', '')}`")
                                st.markdown("---")
                                st.markdown(ctx.get("content", ""))
                    else:
                        st.info("Nenhum documento relevante encontrado.")
            except Exception as e:
                st.error(f"Erro ao conectar ao servidor: {str(e)}")
        else:
            st.warning("Por favor, digite uma consulta.")

def render_insert_tab():
    """Renderiza a aba de inserção de novos documentos"""
    st.markdown("## Adicionar Novo Documento")
    
    # Opções de inserção
    insert_method = st.radio("Método de inserção:", ["Manual", "Arquivo JSONL", "Texto em arquivo"], horizontal=True)
    
    if insert_method == "Manual":
        # Formulário para adicionar documento manualmente
        with st.form("insert_form_manual"):
            doc_content = st.text_area("Conteúdo do documento:", height=200)
            doc_source = st.text_input("Fonte:", "manual")
            doc_summary = st.text_input("Resumo do documento:", "Nota manual")
            
            submitted = st.form_submit_button("Inserir Documento")
            if submitted:
                if doc_content:
                    try:
                        client = LightRAGClient()
                        result = client.insert(doc_content, doc_summary, doc_source)
                        if result.get("success"):
                            st.success(f"Documento inserido com sucesso! ID: {result.get('documentId')}")
                            st.cache_data.clear()  # Limpar cache para atualizar a lista
                        else:
                            st.error(result.get("error", "Erro desconhecido"))
                    except Exception as e:
                        st.error(f"Erro ao conectar ao servidor: {str(e)}")
                else:
                    st.warning("Por favor, digite o conteúdo do documento.")
    
    elif insert_method == "Arquivo JSONL":
        st.markdown("### Inserir a partir de arquivo JSONL")
        jsonl_path = st.text_input("Caminho do arquivo JSONL:", placeholder="/caminho/para/arquivo.jsonl")
        max_lines = st.slider("Máximo de linhas a processar:", 10, 500, 100)
        
        if st.button("Processar Arquivo JSONL"):
            if os.path.exists(jsonl_path):
                st.info(f"Processando arquivo: {jsonl_path}")
                # Esta parte seria implementada com a extração real de JSONL
                st.success("Implementação pendente - Funcionalidade em desenvolvimento")
            else:
                st.error(f"Arquivo não encontrado: {jsonl_path}")
    
    else:  # Texto em arquivo
        st.markdown("### Inserir a partir de texto em arquivo")
        file_path = st.text_input("Caminho do arquivo:", placeholder="/caminho/para/arquivo.txt")
        
        if st.button("Processar Arquivo de Texto"):
            if os.path.exists(file_path):
                st.info(f"Processando arquivo: {file_path}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Preparar metadados
                    file_name = os.path.basename(file_path)
                    summary = f"Arquivo: {file_name}"
                    source = f"file:{file_name}"
                    
                    # Inserir conteúdo
                    client = LightRAGClient()
                    result = client.insert(
                        content, 
                        summary, 
                        source, 
                        {"file_path": file_path, "file_name": file_name}
                    )
                    
                    if result.get("success"):
                        st.success(f"Arquivo inserido com sucesso! ID: {result.get('documentId')}")
                        st.cache_data.clear()
                    else:
                        st.error(result.get("error", "Erro desconhecido"))
                        
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {str(e)}")
            else:
                st.error(f"Arquivo não encontrado: {file_path}")
    
    # Opção para limpar base
    with st.expander("Gerenciamento da Base de Dados"):
        st.markdown("## Gerenciamento da Base")
        st.warning("⚠️ Estas operações são irreversíveis!")
        if st.button("🗑️ Limpar toda a base de conhecimento", type="primary", use_container_width=True):
            try:
                client = LightRAGClient()
                result = client.clear(True)
                if result.get("success"):
                    st.success(result.get("message", "Base limpa com sucesso"))
                    if "backup" in result:
                        st.info(f"Backup criado: {result.get('backup', 'N/A')}")
                    st.cache_data.clear()  # Limpar cache para atualizar a lista
                else:
                    st.error(result.get("error", "Erro desconhecido"))
            except Exception as e:
                st.error(f"Erro ao conectar ao servidor: {str(e)}")

def render_statistics_tab():
    """Renderiza a aba de estatísticas do sistema"""
    st.markdown("## Estatísticas do Sistema LightRAG")
    
    try:
        # Carregar dados da base de conhecimento
        kb = load_knowledge_base()
        documents = kb.get("documents", [])
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Documentos", len(documents))
        
        with col2:
            total_chars = sum(len(doc.get("content", "")) for doc in documents)
            st.metric("Total de Caracteres", f"{total_chars:,}")
        
        with col3:
            avg_chars = total_chars / len(documents) if documents else 0
            st.metric("Média de Caracteres/Doc", f"{avg_chars:.0f}")
        
        with col4:
            sources = set(doc.get("source", "unknown") for doc in documents)
            st.metric("Fontes Diferentes", len(sources))
        
        # Gráfico de distribuição por fonte
        if documents:
            st.markdown("### Distribuição por Fonte")
            source_counts = {}
            for doc in documents:
                source = doc.get("source", "unknown")
                source_counts[source] = source_counts.get(source, 0) + 1
            
            if source_counts:
                import pandas as pd
                df_sources = pd.DataFrame(list(source_counts.items()), columns=["Fonte", "Quantidade"])
                st.bar_chart(df_sources.set_index("Fonte"))
        
        # Estatísticas de tamanho dos documentos
        if documents:
            st.markdown("### Distribuição de Tamanho dos Documentos")
            doc_sizes = [len(doc.get("content", "")) for doc in documents]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Estatísticas de Tamanho:**")
                st.write(f"- Menor documento: {min(doc_sizes):,} caracteres")
                st.write(f"- Maior documento: {max(doc_sizes):,} caracteres")
                st.write(f"- Mediana: {sorted(doc_sizes)[len(doc_sizes)//2]:,} caracteres")
            
            with col2:
                # Histograma simplificado
                import pandas as pd
                df_sizes = pd.DataFrame({"Tamanho": doc_sizes})
                st.bar_chart(df_sizes["Tamanho"])
        
        # Estatísticas de tempo (se disponível)
        st.markdown("### Informações do Sistema")
        
        # Verificar status do servidor
        server_status = check_server()
        status_color = "🟢" if server_status else "🔴"
        st.write(f"Status do Servidor: {status_color} {'Online' if server_status else 'Offline'}")
        
        # Informações de arquivo
        db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lightrag_db.json")
        if os.path.exists(db_file):
            file_size = os.path.getsize(db_file)
            file_size_mb = file_size / (1024 * 1024)
            st.write(f"Tamanho da Base de Dados: {file_size_mb:.2f} MB")
            
            # Data de última modificação
            import datetime
            mod_time = os.path.getmtime(db_file)
            mod_date = datetime.datetime.fromtimestamp(mod_time)
            st.write(f"Última Modificação: {mod_date.strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Nomes personalizados
        custom_names = load_custom_names()
        st.write(f"Documentos com Nomes Personalizados: {len(custom_names)}")
        
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {str(e)}")

def render_memory_tab():
    """Renderiza a aba de integração com Memory e Model Context Protocol (MCP)"""
    st.markdown("## Integração com Memory e Model Context Protocol (MCP)")
    
    # Carregar resumo da integração
    memory_summary = load_memory_summary()
    
    # Exibir resumo da integração
    st.markdown(memory_summary)
    
    # Adicionar visualização das entidades e relações
    st.markdown("## Diagrama de Relações")
    st.markdown("""
    ```mermaid
    graph LR
        EcossistemaAgentes -- utiliza --> LightRAG
        IntegradorModelContextProtocol -- conectaCom --> LightRAG
        GerenciadorDeConhecimento -- utilizaRAG --> LightRAG
        LightRAG -- complementa --> Memory
        LightRAG -- utiliza --> ModelContextProtocol
        
        classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
        classDef principal fill:#d4f1f9,stroke:#0077b6,stroke-width:2px;
        class LightRAG,Memory,ModelContextProtocol principal;
    ```
    """)

def main():
    """Função principal para a aplicação Streamlit"""
    # Configurações da página
    st.set_page_config(
        page_title="LightRAG - Interface",
        page_icon="🔍",
        layout="wide"
    )
    
    # Verificar se o servidor está rodando
    if not ensure_server_running():
        st.error("Não foi possível conectar ao servidor LightRAG.")
        st.info("Verifique se o servidor está rodando com o comando: ./start_lightrag.sh")
        return
    
    # Navegação principal
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Documentos", 
        "Consulta", 
        "Inserir", 
        "Estatísticas",
        "Integração MCP"
    ])
    
    # Renderizar sidebar com informações e filtros
    active_tab = "Documentos"  # Default
    if tab2.selected:
        active_tab = "Consulta"
    elif tab3.selected:
        active_tab = "Inserir"
    elif tab4.selected:
        active_tab = "Estatísticas"
    elif tab5.selected:
        active_tab = "Integração MCP"
    
    # Renderizar a barra lateral e armazenar os filtros na session_state
    filters = render_sidebar(active_tab)
    for key, value in filters.items():
        st.session_state[key] = value
    
    # Renderizar conteúdo de cada aba
    with tab1:
        render_documents_tab()
        
    with tab2:
        render_query_tab()
        
    with tab3:
        render_insert_tab()
        
    with tab4:
        render_statistics_tab()
        
    with tab5:
        render_memory_tab()
    
    # Rodapé
    st.markdown("---")
    st.caption("LightRAG - Sistema simplificado de RAG © 2025")
    st.caption("Desenvolvido com Streamlit e Flask | Integração com Memory e Model Context Protocol (MCP)")

if __name__ == "__main__":
    main()