#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Corretor de IDs Duplicados
Script para detectar e corrigir documentos que fazem referência à mesma conversa
mas usam IDs diferentes baseados em timestamp
"""

import os
import json
import argparse
import hashlib
import re
from typing import Dict, List, Tuple, Set, Optional

# Importar o gerador de IDs consistentes
from fixed_id_generator import extract_uuid_from_filename, generate_consistent_id, is_conversation_id

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
    import shutil
    import datetime
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

def extract_conversation_uuid_from_content(content: str) -> Optional[str]:
    """
    Extrai UUID de conversa do conteúdo de um documento
    
    Args:
        content: Conteúdo do documento
        
    Retorna:
        Optional[str]: UUID extraído ou None se não encontrado
    """
    # Padrão para extrair UUID de conversas Claude no conteúdo
    uuid_pattern = r'sessionId["\']?\s*:\s*["\']?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    
    # Buscar primeira ocorrência
    match = re.search(uuid_pattern, content)
    if match:
        return match.group(1)
    
    # Padrão alternativo procurando por arquivos .jsonl
    jsonl_pattern = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl'
    match = re.search(jsonl_pattern, content)
    if match:
        return match.group(1)
    
    return None

def identify_conversation_documents(documents: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Identifica documentos que se referem à mesma conversa
    
    Args:
        documents: Lista de documentos
        
    Retorna:
        Dict[str, List[Dict]]: Mapeamento de UUID para lista de documentos
    """
    conversation_groups = {}
    
    for doc in documents:
        # Verificar se já é um ID consistente (conv_UUID)
        doc_id = doc.get("id", "")
        if is_conversation_id(doc_id):
            # Extrair UUID do ID
            uuid = doc_id[5:]  # Remover prefixo "conv_"
            if uuid not in conversation_groups:
                conversation_groups[uuid] = []
            conversation_groups[uuid].append(doc)
            continue
        
        # Extrair UUID do conteúdo
        content = doc.get("content", "")
        uuid = extract_conversation_uuid_from_content(content)
        
        if uuid:
            if uuid not in conversation_groups:
                conversation_groups[uuid] = []
            conversation_groups[uuid].append(doc)
    
    # Filtrar apenas grupos com múltiplos documentos
    return {uuid: docs for uuid, docs in conversation_groups.items() if len(docs) > 1}

def consolidate_documents(db: Dict, dry_run: bool = False) -> Tuple[int, int]:
    """
    Consolida documentos duplicados que se referem à mesma conversa
    
    Args:
        db: Banco de dados LightRAG
        dry_run: Se True, apenas simula as alterações sem salvá-las
        
    Retorna:
        Tuple[int, int]: (número de grupos consolidados, número de documentos afetados)
    """
    documents = db.get("documents", [])
    print(f"Analisando {len(documents)} documentos...")
    
    # Identificar grupos de documentos da mesma conversa
    groups = identify_conversation_documents(documents)
    print(f"Encontrados {len(groups)} grupos de documentos relacionados à mesma conversa")
    
    if not groups:
        return 0, 0
    
    # Contar documentos afetados
    affected_docs = sum(len(docs) for docs in groups.values())
    
    if dry_run:
        print(f"SIMULAÇÃO: {len(groups)} grupos seriam consolidados, afetando {affected_docs} documentos")
        return len(groups), affected_docs
    
    # Processar cada grupo
    new_documents = []
    processed_ids = set()
    
    # Primeiro, adicionar documentos consolidados
    for uuid, docs in groups.items():
        # Determinar qual documento manter (o mais recente)
        docs_sorted = sorted(docs, key=lambda d: d.get("created", ""), reverse=True)
        main_doc = docs_sorted[0]
        
        # Gerar novo ID consistente
        new_id = f"conv_{uuid}"
        
        # Atualizar ID do documento principal
        main_doc["id"] = new_id
        main_doc["original_ids"] = [d.get("id") for d in docs]
        
        # Adicionar documento consolidado
        new_documents.append(main_doc)
        
        # Registrar IDs processados
        for doc in docs:
            processed_ids.add(doc.get("id", ""))
    
    # Adicionar documentos não afetados
    for doc in documents:
        if doc.get("id") not in processed_ids:
            new_documents.append(doc)
    
    # Atualizar banco de dados
    db["documents"] = new_documents
    
    # Salvar alterações
    success = save_database(db)
    if success:
        print(f"Consolidados {len(groups)} grupos, afetando {affected_docs} documentos")
    else:
        print(f"ERRO: Falha ao salvar alterações no banco de dados")
    
    return len(groups), affected_docs

def main():
    parser = argparse.ArgumentParser(description="Detecta e corrige IDs duplicados no LightRAG")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simular operações sem fazer alterações")
    args = parser.parse_args()
    
    # Carregar banco de dados
    db = load_database()
    
    # Consolidar documentos
    groups, affected = consolidate_documents(db, dry_run=args.dry_run)
    
    if groups > 0:
        if args.dry_run:
            print(f"SIMULAÇÃO: {groups} grupos seriam consolidados, afetando {affected} documentos")
        else:
            print(f"Consolidados {groups} grupos, afetando {affected} documentos")
            print(f"Banco de dados atualizado: {DB_FILE}")
    else:
        print("Nenhum documento duplicado encontrado.")

if __name__ == "__main__":
    main()