#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG UI - Interface Streamlit
Implementação consolidada da interface Streamlit para o LightRAG
"""

import streamlit as st
import json
import os
import re
import pandas as pd
import time

# Importar módulo de nomeação
from ui.name_selection import select_document_with_naming
from typing import Dict, List, Any, Optional

# Importar componentes do LightRAG
from core.client import LightRAGClient, ensure_server_running
from core.settings import DB_FILE, MEMORY_SUMMARY_FILE
from utils.logger import get_ui_logger
from lightrag.ui.integration import render_projects_tab

# Configurar logger
logger = get_ui_logger()

class LightRAGUI:
    """Classe principal da interface Streamlit para o LightRAG"""
    
    def __init__(self):
        """Inicializa a interface com configurações básicas"""
        # Configurações da página
        st.set_page_config(
            page_title="LightRAG - Interface", 
            page_icon="🔍", 
            layout="wide"
        )
        
        # Inicializar cliente
        self.client = LightRAGClient()
        
        # Garantir que o servidor esteja rodando
        if not ensure_server_running():
            logger.error("Não foi possível garantir que o servidor esteja rodando")
            st.error("Não foi possível conectar ao servidor LightRAG.")
    
    @st.cache_data(ttl=5)
    def check_server(_self):
        """
        Verifica o status do servidor
        
        Retorna:
            Dict: Status do servidor
        """
        try:
            result = _self.client.status()
            logger.debug(f"Status do servidor verificado: {result}")
            return result
        except Exception as e:
            logger.error(f"Erro ao verificar status do servidor: {str(e)}")
            return {"status": "offline", "error": str(e)}
    
    @st.cache_data(ttl=5)
    def load_knowledge_base(_self):
        """
        Carrega a base de conhecimento diretamente do arquivo
        
        Retorna:
            Dict: Conteúdo da base de conhecimento
        """
        logger.debug("Carregando base de conhecimento do arquivo")
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar base de conhecimento: {str(e)}")
                st.error(f"Erro ao carregar base de conhecimento: {str(e)}")
        return {"documents": [], "lastUpdated": ""}
    
    def load_memory_summary(self):
        """
        Carrega o arquivo de resumo da integração com Memory e Model Context Protocol (MCP)
        
        Retorna:
            str: Conteúdo do arquivo de resumo
        """
        logger.debug("Carregando resumo da integração com Memory e Model Context Protocol (MCP)")
        if os.path.exists(MEMORY_SUMMARY_FILE):
            try:
                with open(MEMORY_SUMMARY_FILE, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Erro ao carregar resumo da integração: {str(e)}")
                return f"Erro ao carregar resumo da integração Memory: {str(e)}"
        return "Resumo da integração com Memory e Model Context Protocol (MCP) não encontrado."
    
    def delete_document(self, doc_id):
        """
        Remove um documento da base de conhecimento
        
        Args:
            doc_id: ID do documento a ser removido
            
        Retorna:
            bool: True se sucesso, False se falha
        """
        logger.info(f"Solicitada exclusão do documento: {doc_id}")
        try:
            result = self.client.delete(doc_id)
            if result.get("success"):
                logger.info(f"Documento {doc_id} excluído com sucesso!")
                st.success(f"Documento {doc_id} excluído com sucesso!")
                st.cache_data.clear()  # Limpar cache para atualizar a lista
                return True
            else:
                error_msg = result.get("error", "Erro desconhecido")
                logger.error(f"Erro na exclusão: {error_msg}")
                st.error(error_msg)
        except Exception as e:
            logger.error(f"Erro ao conectar ao servidor: {str(e)}")
            st.error(f"Erro ao conectar ao servidor: {str(e)}")
        return False
    
    def extract_entities(self, text):
        """
        Extrai entidades mencionadas em um texto (menções a Memory e Model Context Protocol (MCP))
        
        Args:
            text: Texto para análise
            
        Retorna:
            list: Lista de entidades encontradas
        """
        logger.debug("Extraindo entidades do texto")
        # Expressão regular para encontrar entidades em formato JSON
        entity_pattern = r'"name"\s*:\s*"([^"]+)"'
        relation_patterns = [
            r'"from"\s*:\s*"([^"]+)"',
            r'"to"\s*:\s*"([^"]+)"'
        ]
        
        entities = set()
        
        # Encontrar entidades diretas
        for match in re.finditer(entity_pattern, text):
            entities.add(match.group(1))
        
        # Encontrar entidades em relações
        for pattern in relation_patterns:
            for match in re.finditer(pattern, text):
                entities.add(match.group(1))
        
        return list(entities)
    
    def render_documents_tab(self):
        """Renderiza a aba de visualização de documentos"""
        st.markdown("## Base de Conhecimento LightRAG")
        
        # Status do servidor
        server_status = self.check_server()
        status_color = "green" if server_status.get("status") == "online" else "red"
        
        st.markdown(f"### Status do Servidor: <span style='color:{status_color};'>●</span> {server_status.get('status', 'desconhecido')}", unsafe_allow_html=True)
        st.write(f"Documentos: {server_status.get('documents', 0)}")
        st.write(f"Última atualização: {server_status.get('lastUpdated', 'N/A')}")
        
        # Carregar base de conhecimento
        kb = self.load_knowledge_base()
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
            
            # Visualizar documento completo usando widget de seleção com nomeação
            selected_doc = select_document_with_naming(
                documents,
                label="Selecione um documento para visualizar:",
                empty_option=True
            )
            
            if selected_doc:
                doc = selected_doc
                if doc:
                    with st.expander("Documento Detalhado", expanded=True):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.subheader(doc.get("summary", "Documento"))
                            content = doc.get("content", "")
                            st.text_area("Conteúdo:", content, height=300)
                            
                            # Detectar e mostrar entidades
                            entities = self.extract_entities(content)
                            if entities:
                                st.markdown("#### Entidades Detectadas:")
                                for entity in entities:
                                    st.markdown(f"- `{entity}`")
                        
                        with col2:
                            st.markdown("### Metadados")
                            st.write(f"ID: {doc.get('id', 'N/A')}")
                            st.write(f"Fonte: {doc.get('source', 'desconhecido')}")
                            st.write(f"Criado em: {doc.get('created', 'N/A')}")
                            
                            st.markdown("### Ações")
                            if st.button("🗑️ Excluir documento", type="primary", key=f"delete_{selected_doc_id}"):
                                if self.delete_document(selected_doc_id):
                                    st.rerun()  # Recarregar a página para atualizar
        else:
            st.info("Nenhum documento encontrado na base de conhecimento.")
    
    def render_query_tab(self):
        """Renderiza a aba de consulta"""
        st.markdown("## Consulta RAG")
        
        # Campo de consulta
        query = st.text_input("Pesquisar na base de conhecimento:", placeholder="Digite sua consulta aqui...")
        mode = st.radio("Modo de consulta:", ["hybrid", "semantic", "keyword"], horizontal=True)
        max_results = st.slider("Máximo de resultados:", 1, 10, 5)
        
        if st.button("🔍 Consultar"):
            if query:
                try:
                    with st.spinner("Consultando base de conhecimento..."):
                        start_time = time.time()
                        result = self.client.query(query, max_results, mode)
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
                    logger.error(f"Erro ao conectar ao servidor: {str(e)}")
                    st.error(f"Erro ao conectar ao servidor: {str(e)}")
            else:
                st.warning("Por favor, digite uma consulta.")
    
    def render_insert_tab(self):
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
                            result = self.client.insert(doc_content, doc_summary, doc_source)
                            if result.get("success"):
                                logger.info(f"Documento inserido: ID={result.get('documentId')}")
                                st.success(f"Documento inserido com sucesso! ID: {result.get('documentId')}")
                                st.cache_data.clear()  # Limpar cache para atualizar a lista
                            else:
                                logger.error(f"Erro na inserção: {result.get('error')}")
                                st.error(result.get("error", "Erro desconhecido"))
                        except Exception as e:
                            logger.error(f"Erro ao conectar ao servidor: {str(e)}")
                            st.error(f"Erro ao conectar ao servidor: {str(e)}")
                    else:
                        st.warning("Por favor, digite o conteúdo do documento.")
        
        elif insert_method == "Arquivo JSONL":
            st.markdown("### Inserir a partir de arquivo JSONL")
            jsonl_path = st.text_input("Caminho do arquivo JSONL:", placeholder="/caminho/para/arquivo.jsonl")
            max_lines = st.slider("Máximo de linhas a processar:", 10, 500, 100)
            
            if st.button("Processar Arquivo JSONL"):
                if os.path.exists(jsonl_path):
                    logger.info(f"Processando arquivo JSONL: {jsonl_path}")
                    st.info(f"Processando arquivo: {jsonl_path}")
                    # Esta parte seria implementada com a extração real de JSONL
                    st.success("Implementação pendente - Funcionalidade em desenvolvimento")
                else:
                    logger.error(f"Arquivo não encontrado: {jsonl_path}")
                    st.error(f"Arquivo não encontrado: {jsonl_path}")
        
        else:  # Texto em arquivo
            st.markdown("### Inserir a partir de texto em arquivo")
            file_path = st.text_input("Caminho do arquivo:", placeholder="/caminho/para/arquivo.txt")
            
            if st.button("Processar Arquivo de Texto"):
                if os.path.exists(file_path):
                    logger.info(f"Processando arquivo de texto: {file_path}")
                    st.info(f"Processando arquivo: {file_path}")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Preparar metadados
                        file_name = os.path.basename(file_path)
                        summary = f"Arquivo: {file_name}"
                        source = f"file:{file_name}"
                        
                        # Inserir conteúdo
                        result = self.client.insert(
                            content, 
                            summary, 
                            source, 
                            {"file_path": file_path, "file_name": file_name}
                        )
                        
                        if result.get("success"):
                            logger.info(f"Arquivo inserido: ID={result.get('documentId')}")
                            st.success(f"Arquivo inserido com sucesso! ID: {result.get('documentId')}")
                            st.cache_data.clear()
                        else:
                            logger.error(f"Erro na inserção: {result.get('error')}")
                            st.error(result.get("error", "Erro desconhecido"))
                            
                    except Exception as e:
                        logger.error(f"Erro ao processar arquivo: {str(e)}")
                        st.error(f"Erro ao processar arquivo: {str(e)}")
                else:
                    logger.error(f"Arquivo não encontrado: {file_path}")
                    st.error(f"Arquivo não encontrado: {file_path}")
        
        # Opção para limpar base
        with st.expander("Gerenciamento da Base de Dados"):
            st.markdown("## Gerenciamento da Base")
            st.warning("⚠️ Estas operações são irreversíveis!")
            if st.button("🗑️ Limpar toda a base de conhecimento", type="primary", use_container_width=True):
                try:
                    logger.warning("Solicitada limpeza da base de conhecimento")
                    result = self.client.clear(True)
                    if result.get("success"):
                        logger.info(f"Base limpa: {result.get('message')}")
                        st.success(result.get("message", "Base limpa com sucesso"))
                        if "backup" in result:
                            logger.info(f"Backup criado: {result['backup']}")
                            st.info(f"Backup criado: {result.get('backup', 'N/A')}")
                        st.cache_data.clear()  # Limpar cache para atualizar a lista
                    else:
                        logger.error(f"Erro ao limpar base: {result.get('error')}")
                        st.error(result.get("error", "Erro desconhecido"))
                except Exception as e:
                    logger.error(f"Erro ao conectar ao servidor: {str(e)}")
                    st.error(f"Erro ao conectar ao servidor: {str(e)}")
    
    def render_stats_tab(self):
        """Renderiza a aba de estatísticas"""
        st.markdown("## Estatísticas da Base de Conhecimento")
        
        # Carregar base de conhecimento para estatísticas
        kb = self.load_knowledge_base()
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
    
    def render_memory_tab(self):
        """Renderiza a aba de integração com Memory e Model Context Protocol (MCP)"""
        st.markdown("## Integração com Memory e Model Context Protocol (MCP)")
        
        # Carregar resumo da integração
        memory_summary = self.load_memory_summary()
        
        # Exibir resumo da integração
        st.markdown(memory_summary)
        
        # Adicionar visualização das entidades e relações
        st.markdown("## Entidades no Grafo de Conhecimento")
        
        # Lista de entidades conhecidas (extraídas do resumo)
        known_entities = self.extract_entities(memory_summary)
        
        # Criar colunas para exibir as entidades
        if known_entities:
            num_cols = 3
            cols = st.columns(num_cols)
            
            for i, entity in enumerate(known_entities):
                with cols[i % num_cols]:
                    st.markdown(f"### {entity}")
                    if entity == "LightRAG":
                        st.markdown("""
                        **Tipo:** ServicoModelContextProtocol
                        
                        **Observações:**
                        - Sistema RAG simplificado
                        - Fornece endpoints para consulta e inserção
                        - Implementado como servidor Flask
                        - Armazena documentos em JSON
                        """)
                    elif entity == "EcossistemaAgentes":
                        st.markdown("""
                        **Tipo:** SistemaAgentes
                        
                        **Relações:**
                        - Utiliza LightRAG
                        """)
                    elif entity == "IntegradorModelContextProtocol":
                        st.markdown("""
                        **Tipo:** ServicoIntegrador
                        
                        **Relações:**
                        - ConectaCom LightRAG
                        """)
                    elif entity == "GerenciadorDeConhecimento":
                        st.markdown("""
                        **Tipo:** GerenciadorDados
                        
                        **Relações:**
                        - UtilizaRAG LightRAG
                        """)
                    else:
                        st.markdown(f"*Entidade detectada no grafo*")
        else:
            st.info("Nenhuma entidade detectada no resumo de integração.")
        
        # Desenhar relações simples
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
    
    def run(self):
        """Executa a aplicação Streamlit"""
        # Cabeçalho com logo e título
        st.title("🔍 LightRAG - Sistema de RAG")
        st.caption("Retrieval Augmented Generation integrado com Memory e Model Context Protocol (MCP)")
        
        # Layout principal com abas
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Documentos", 
            "Consulta", 
            "Projetos Claude",
            "Inserir", 
            "Estatísticas", 
            "Integração Model Context Protocol"
        ])
        
        # Renderizar conteúdo de cada aba
        with tab1:
            self.render_documents_tab()
            
        with tab2:
            self.render_query_tab()
            
        with tab3:
            render_projects_tab()
            
        with tab4:
            self.render_insert_tab()
            
        with tab5:
            self.render_stats_tab()
            
        with tab6:
            self.render_memory_tab()
        
        # Rodapé
        st.markdown("---")
        st.caption("LightRAG - Sistema simplificado de RAG © 2025")
        st.caption("Desenvolvido com Streamlit e Flask | Integração com Memory e Model Context Protocol (MCP)")