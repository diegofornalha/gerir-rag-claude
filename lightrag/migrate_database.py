#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Migração de Base de Dados
Script para migrar o banco de dados LightRAG para o novo formato de IDs (conv_UUID)
"""

import os
import json
import argparse
import shutil
import re
import datetime
from typing import Dict, List, Tuple, Optional

# Importar o gerador de IDs consistentes
from fixed_id_generator import extract_uuid_from_filename, generate_consistent_id
from correct_duplicate_ids import extract_conversation_uuid_from_content

# Arquivo do banco de dados LightRAG
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "lightrag", "lightrag_db.json")

def load_database() -> Dict:
    """
    Carrega o banco de dados LightRAG
    
    Retorna:
        Dict: Conteúdo do banco de dados
    """
    if not os.path.exists(DB_FILE):
        print(f"Arquivo de banco de dados não encontrado: {DB_FILE}")
        return {"documents": []}
    
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Erro ao decodificar arquivo de banco de dados. Retornando vazio.")
        return {"documents": []}

def save_database(db: Dict) -> bool:
    """
    Salva o banco de dados LightRAG
    
    Args:
        db: Conteúdo do banco de dados
        
    Retorna:
        bool: True se salvo com sucesso, False caso contrário
    """
    # Fazer backup do arquivo original
    timestamp = int(datetime.datetime.now().timestamp())
    backup_file = f"{DB_FILE}.bak.{timestamp}"
    
    try:
        if os.path.exists(DB_FILE):
            shutil.copy2(DB_FILE, backup_file)
            print(f"Backup criado em: {backup_file}")
        
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Erro ao salvar banco de dados: {e}")
        return False

def is_conversation_document(doc: Dict) -> bool:
    """
    Verifica se um documento é uma conversa do Claude
    
    Args:
        doc: Documento a verificar
        
    Retorna:
        bool: True se for uma conversa, False caso contrário
    """
    # Verificar pelo conteúdo
    content = doc.get("content", "")
    has_session_id = "sessionId" in content
    has_claude_reference = "claude" in content.lower() or "Claude" in content
    has_jsonl_reference = ".jsonl" in content
    
    # Verificar por metadados
    source = doc.get("source", "")
    summary = doc.get("summary", "")
    
    is_jsonl_source = source.endswith(".jsonl")
    has_conversa_in_summary = "conversa" in summary.lower() or "Conversa" in summary
    
    return (has_session_id and has_claude_reference) or has_jsonl_reference or is_jsonl_source or has_conversa_in_summary

def migrate_document_id(doc: Dict) -> Tuple[Dict, bool]:
    """
    Migra o ID de um documento para o novo formato se necessário
    
    Args:
        doc: Documento a migrar
        
    Retorna:
        Tuple[Dict, bool]: Documento (possivelmente modificado) e flag indicando se houve alteração
    """
    # Verificar se já está no formato correto
    current_id = doc.get("id", "")
    if current_id.startswith("conv_"):
        return doc, False
    
    # Verificar se é uma conversa
    if not is_conversation_document(doc):
        return doc, False
    
    # Extrair UUID do conteúdo
    content = doc.get("content", "")
    uuid = extract_conversation_uuid_from_content(content)
    
    if not uuid:
        # Tentar extrair do source ou summary
        source = doc.get("source", "")
        uuid = extract_uuid_from_filename(source)
        
        if not uuid:
            summary = doc.get("summary", "")
            uuid = extract_uuid_from_filename(summary)
            
            if not uuid:
                # Último recurso: manter o ID atual
                return doc, False
    
    # Gerar novo ID
    new_id = f"conv_{uuid}"
    
    # Criar cópia do documento para não modificar o original
    doc_copy = doc.copy()
    
    # Registrar ID original para rastreabilidade
    if "original_id" not in doc_copy:
        doc_copy["original_id"] = current_id
    
    # Atualizar ID
    doc_copy["id"] = new_id
    
    # Atualizar summary se necessário
    if not doc_copy.get("summary", "").startswith("Conversa Claude"):
        doc_copy["summary"] = f"Conversa Claude: {uuid}.jsonl"
    
    return doc_copy, True

def migrate_database(dry_run: bool = False) -> Tuple[int, int]:
    """
    Migra o banco de dados LightRAG para o novo formato de IDs
    
    Args:
        dry_run: Se True, apenas simula as alterações sem salvá-las
        
    Retorna:
        Tuple[int, int]: (número de documentos migrados, número total de documentos)
    """
    # Carregar banco de dados
    db = load_database()
    documents = db.get("documents", [])
    total_docs = len(documents)
    
    if total_docs == 0:
        print("Banco de dados vazio.")
        return 0, 0
    
    print(f"Analisando {total_docs} documentos...")
    
    # Migrar IDs
    new_documents = []
    migrated_count = 0
    
    for doc in documents:
        migrated_doc, modified = migrate_document_id(doc)
        new_documents.append(migrated_doc)
        
        if modified:
            migrated_count += 1
    
    if migrated_count == 0:
        print("Nenhum documento precisa ser migrado.")
        return 0, total_docs
    
    if dry_run:
        print(f"SIMULAÇÃO: {migrated_count} documentos seriam migrados de {total_docs} total")
        return migrated_count, total_docs
    
    # Atualizar banco de dados
    db["documents"] = new_documents
    
    # Registrar timestamp da atualização
    db["lastUpdated"] = datetime.datetime.now().isoformat()
    
    # Salvar alterações
    success = save_database(db)
    if success:
        print(f"Migrados {migrated_count} documentos de {total_docs} total")
    else:
        print(f"ERRO: Falha ao salvar alterações no banco de dados")
    
    return migrated_count, total_docs

def main():
    parser = argparse.ArgumentParser(description="Migra o banco de dados LightRAG para o novo formato de IDs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simular operações sem fazer alterações")
    args = parser.parse_args()
    
    # Migrar banco de dados
    migrated, total = migrate_database(dry_run=args.dry_run)
    
    if migrated > 0:
        if args.dry_run:
            print(f"SIMULAÇÃO: {migrated} documentos seriam migrados de {total} total")
        else:
            print(f"Migrados {migrated} documentos de {total} total")
            print(f"Banco de dados atualizado: {DB_FILE}")
    else:
        print(f"Nenhum documento migrado de {total} total.")
    
    # Recomendar próximos passos
    print("\nPróximos passos recomendados:")
    print("1. Executar update_custom_names.py para mapear nomes amigáveis")
    print("2. Executar correct_duplicate_ids.py para corrigir duplicatas")
    print("3. Substituir utils/formatters.py pelo arquivo utils/formatters_updated.py")

if __name__ == "__main__":
    main()