#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Módulo de Seleção e Nomeação na UI
Permite que o usuário nomeie conversas diretamente na interface Streamlit
"""

import os
import re
import sys
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple

# Diretório do LightRAG
LIGHTRAG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Adicionar ao caminho para importar módulos do diretório principal
sys.path.append(LIGHTRAG_DIR)

# Importar módulo de nomes por UUID
try:
    from uuid_names import extract_uuid, set_name_for_uuid, get_name_for_uuid, load_uuid_names
    USING_UUID_NAMES = True
except ImportError:
    USING_UUID_NAMES = False
    print("Aviso: Sistema de nomes por UUID não encontrado.")

# Padrão para detectar nomes técnicos gerados pelo sistema
TECHNICAL_NAME_PATTERN = r'Conversa(:)?\s+Claude:\s+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(.jsonl)?'

def is_technical_name(name: str) -> bool:
    """
    Verifica se um nome é um nome técnico gerado pelo sistema
    
    Args:
        name: Nome a verificar
        
    Retorna:
        bool: True se for nome técnico, False caso contrário
    """
    return re.match(TECHNICAL_NAME_PATTERN, name) is not None

def format_document_options(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formata opções para selectbox de documentos com nomes mais amigáveis
    
    Args:
        documents: Lista de documentos
        
    Retorna:
        List[Dict[str, Any]]: Lista de opções formatadas
    """
    options = []
    
    # Carregar mapeamento de nomes por UUID
    uuid_names = {}
    if USING_UUID_NAMES:
        uuid_names = load_uuid_names()
    
    for i, doc in enumerate(documents):
        doc_id = doc.get("id", "")
        source = doc.get("source", "")
        summary = doc.get("summary", "")
        
        # Extrair UUID do documento
        uuid = extract_uuid(doc_id) or extract_uuid(source) or extract_uuid(summary)
        
        # Determinar o nome de exibição
        display_name = None
        
        # Se tiver UUID, verificar se tem nome personalizado
        if uuid and uuid in uuid_names:
            display_name = uuid_names[uuid]
        
        # Se não tiver nome personalizado, usar resumo
        if not display_name and summary:
            # Verificar se o resumo é um nome técnico
            if not is_technical_name(summary):
                display_name = summary
        
        # Se ainda não tiver nome, usar nome genérico
        if not display_name:
            display_name = f"Conversa {i+1}"
            if uuid:
                # Usar apenas os primeiros 8 caracteres do UUID para tornar o nome mais legível
                short_uuid = uuid.split("-")[0]
                display_name = f"Conversa {short_uuid}"
        
        # Adicionar opção
        options.append({
            "id": doc_id,
            "uuid": uuid,
            "label": display_name,
            "has_custom_name": (uuid and uuid in uuid_names),
            "is_technical_name": (summary and is_technical_name(summary)),
            "original": doc
        })
    
    return options

def select_document_with_naming(
    documents: List[Dict[str, Any]], 
    label: str = "Selecione um documento:",
    empty_option: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Widget Streamlit para selecionar documentos com capacidade de nomeação
    
    Args:
        documents: Lista de documentos
        label: Rótulo para o selectbox
        empty_option: Se deve incluir opção vazia
        
    Retorna:
        Optional[Dict[str, Any]]: Documento selecionado ou None
    """
    if not documents:
        st.info("Nenhum documento disponível para seleção.")
        return None
    
    # Formatar opções de documentos
    options = format_document_options(documents)
    
    # Preparar opções para o selectbox
    select_options = options
    if empty_option:
        # Adicionar opção vazia
        select_options = [{"id": "", "uuid": None, "label": "", "has_custom_name": True, "is_technical_name": False, "original": None}] + options
    
    # Criar selectbox
    selected_label = st.selectbox(
        label,
        options=[opt["label"] for opt in select_options],
        format_func=lambda x: x or "Selecione um documento..."
    )
    
    # Encontrar a opção selecionada
    selected_option = None
    for opt in select_options:
        if opt["label"] == selected_label:
            selected_option = opt
            break
    
    # Se não selecionou nada, retornar None
    if not selected_option or not selected_option["id"]:
        return None
    
    # Verificar se o documento tem nome personalizado
    if not selected_option["has_custom_name"] and selected_option["uuid"]:
        # Mostrar interface para definir nome personalizado
        st.info("💡 Esta conversa não tem um nome personalizado. Defina um nome mais descritivo:")
        
        # Campo para nome personalizado
        custom_name = st.text_input(
            "Nome personalizado:",
            value=selected_option["label"],
            key=f"custom_name_{selected_option['uuid']}"
        )
        
        # Botão para salvar
        if st.button("Salvar nome", key=f"save_name_{selected_option['uuid']}"):
            if USING_UUID_NAMES and custom_name:
                # Salvar nome personalizado
                success = set_name_for_uuid(selected_option["uuid"], custom_name)
                
                if success:
                    st.success(f"✅ Nome personalizado '{custom_name}' definido com sucesso!")
                    # Forçar atualização da página
                    st.experimental_rerun()
                else:
                    st.error("❌ Erro ao definir nome personalizado.")
    
    # Retornar documento selecionado
    return selected_option["original"]

# Exemplo de uso
if __name__ == "__main__":
    st.set_page_config(page_title="Teste de Seleção com Nomeação", layout="wide")
    
    st.title("Teste de Seleção com Nomeação")
    
    # Dados de exemplo
    sample_docs = [
        {"id": "doc_1234567890", "summary": "Conversa Claude: 8b225707-6263-4081-bc38-df505a930293.jsonl", "content": "Conteúdo 1"},
        {"id": "doc_0987654321", "summary": "Documento importante", "content": "Conteúdo 2"},
        {"id": "doc_1122334455", "summary": "Conversa Claude: a7b8c9d0-e1f2-3456-7890-abcdef123456", "content": "Conteúdo 3"}
    ]
    
    # Selecionar documento com capacidade de nomeação
    selected_doc = select_document_with_naming(sample_docs)
    
    # Exibir documento selecionado
    if selected_doc:
        st.write("Documento selecionado:")
        st.json(selected_doc)