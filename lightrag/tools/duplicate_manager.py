#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Gerenciador de Duplicatas
Módulo consolidado para detectar, corrigir e remover documentos duplicados na base LightRAG.
Combina funcionalidades de correct_duplicate_ids.py e remover_duplicatas_auto.py.
"""

import os
import json
import argparse
import hashlib
import re
import sys
import datetime
import shutil
from typing import Dict, List, Tuple, Set, Optional, Any, Union

# Importar o gerador de IDs consistentes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fixed_id_generator import extract_uuid_from_filename, generate_consistent_id, is_conversation_id

# Arquivo do banco de dados LightRAG
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "lightrag_db.json")

# Constantes
LIGHTRAG_URL = "http://127.0.0.1:5000"

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

def create_backup() -> str:
    """
    Cria um backup do banco de dados LightRAG
    
    Retorna:
        str: Caminho do arquivo de backup ou string vazia se falhar
    """
    if not os.path.exists(DB_FILE):
        return ""
    
    timestamp = int(datetime.datetime.now().timestamp())
    backup_file = f"{DB_FILE}.bak.{timestamp}"
    
    try:
        shutil.copy2(DB_FILE, backup_file)
        print(f"Backup criado em: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"Erro ao criar backup: {e}")
        return ""

def save_database(db: Dict) -> bool:
    """
    Salva o banco de dados LightRAG
    
    Args:
        db: Conteúdo do banco de dados
        
    Retorna:
        bool: True se salvo com sucesso, False caso contrário
    """
    # Criar backup
    backup_file = create_backup()
    if not backup_file and os.path.exists(DB_FILE):
        print("Aviso: Não foi possível criar backup. Continuando mesmo assim...")
    
    try:
        # Atualizar lastUpdated
        db["lastUpdated"] = datetime.datetime.now().isoformat()
        
        # Salvar dados
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Erro ao salvar banco de dados: {e}")
        return False

def extract_conversation_uuid(content: str) -> Optional[str]:
    """
    Extrai UUID de conversa do conteúdo de um documento
    
    Args:
        content: Conteúdo do documento
        
    Retorna:
        Optional[str]: UUID extraído ou None se não encontrado
    """
    # Padrão para extrair UUID de conversas Claude no conteúdo
    patterns = [
        # UUID em formato sessionId
        r'sessionId["\']?\s*:\s*["\']?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
        # UUID em nome de arquivo .jsonl
        r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl',
        # UUID em caminho completo
        r'/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    
    return None

def extract_file_info(doc: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrai informações de arquivo do documento
    
    Args:
        doc: Documento a analisar
        
    Retorna:
        Tuple[Optional[str], Optional[str]]: (nome do arquivo, hash do conteúdo)
    """
    content = doc.get("content", "")
    source = doc.get("source", "")
    
    # Extrair nome do arquivo
    file_name = None
    
    # Tentar extrair do conteúdo
    file_patterns = [
        r"Arquivo JSONL:\s*([^\n]+)",
        r"Arquivo:\s*([^\n]+)",
        r"File:\s*([^\n]+)"
    ]
    
    for pattern in file_patterns:
        match = re.search(pattern, content)
        if match:
            file_name = match.group(1).strip()
            break
    
    # Usar source se não encontrado no conteúdo
    if not file_name and source:
        file_name = source
    
    # Calcular hash do conteúdo para comparação
    content_hash = None
    if content:
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    
    return file_name, content_hash

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
        uuid = extract_conversation_uuid(content)
        
        if uuid:
            if uuid not in conversation_groups:
                conversation_groups[uuid] = []
            conversation_groups[uuid].append(doc)
    
    # Filtrar apenas grupos com múltiplos documentos
    return {uuid: docs for uuid, docs in conversation_groups.items() if len(docs) > 1}

def identify_content_duplicates(documents: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Identifica documentos com conteúdo duplicado
    
    Args:
        documents: Lista de documentos
        
    Retorna:
        Dict[str, List[Dict]]: Mapeamento de hash para lista de documentos
    """
    content_groups = {}
    
    for doc in documents:
        content = doc.get("content", "")
        if not content:
            continue
        
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        if content_hash not in content_groups:
            content_groups[content_hash] = []
        content_groups[content_hash].append(doc)
    
    # Filtrar apenas grupos com múltiplos documentos
    return {hash_val: docs for hash_val, docs in content_groups.items() if len(docs) > 1}

def identify_file_duplicates(documents: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Identifica documentos que se referem ao mesmo arquivo
    
    Args:
        documents: Lista de documentos
        
    Retorna:
        Dict[str, List[Dict]]: Mapeamento de nome de arquivo para lista de documentos
    """
    file_groups = {}
    
    for doc in documents:
        file_name, _ = extract_file_info(doc)
        if not file_name:
            continue
        
        if file_name not in file_groups:
            file_groups[file_name] = []
        file_groups[file_name].append(doc)
    
    # Filtrar apenas grupos com múltiplos documentos
    return {file: docs for file, docs in file_groups.items() if len(docs) > 1}

def consolidate_conversation_documents(db: Dict, dry_run: bool = False) -> Tuple[int, int]:
    """
    Consolida documentos duplicados que se referem à mesma conversa
    
    Args:
        db: Banco de dados LightRAG
        dry_run: Se True, apenas simula as alterações sem salvá-las
        
    Retorna:
        Tuple[int, int]: (número de grupos consolidados, número de documentos afetados)
    """
    documents = db.get("documents", [])
    print(f"Analisando {len(documents)} documentos para conversas duplicadas...")
    
    # Identificar grupos de documentos da mesma conversa
    groups = identify_conversation_documents(documents)
    print(f"Encontrados {len(groups)} grupos de documentos relacionados à mesma conversa")
    
    if not groups:
        return 0, 0
    
    # Contar documentos afetados
    affected_docs = sum(len(docs) for docs in groups.values())
    
    if dry_run:
        print(f"SIMULAÇÃO: {len(groups)} grupos seriam consolidados, afetando {affected_docs} documentos")
        for uuid, docs in groups.items():
            print(f"\nGrupo UUID: {uuid}")
            for i, doc in enumerate(docs):
                print(f"  {i+1}. ID: {doc.get('id')}")
                print(f"     Source: {doc.get('source', 'desconhecido')}")
                print(f"     Criado: {doc.get('created', 'desconhecido')}")
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
        print(f"Consolidados {len(groups)} grupos de conversas, afetando {affected_docs} documentos")
    else:
        print(f"ERRO: Falha ao salvar alterações no banco de dados")
    
    return len(groups), affected_docs

def remove_duplicate_content(db: Dict, dry_run: bool = False) -> Tuple[int, int]:
    """
    Remove documentos com conteúdo duplicado
    
    Args:
        db: Banco de dados LightRAG
        dry_run: Se True, apenas simula as alterações sem salvá-las
        
    Retorna:
        Tuple[int, int]: (número de grupos afetados, número de documentos removidos)
    """
    documents = db.get("documents", [])
    print(f"Analisando {len(documents)} documentos para conteúdo duplicado...")
    
    # Identificar grupos de documentos com conteúdo duplicado
    groups = identify_content_duplicates(documents)
    print(f"Encontrados {len(groups)} grupos de documentos com conteúdo duplicado")
    
    if not groups:
        return 0, 0
    
    # Contar documentos a serem removidos (todos exceto o mais recente de cada grupo)
    docs_to_remove = []
    for content_hash, docs in groups.items():
        # Ordenar por data de criação (mais recente primeiro)
        docs_sorted = sorted(docs, key=lambda d: d.get("created", ""), reverse=True)
        # Manter o mais recente, remover os demais
        for doc in docs_sorted[1:]:
            docs_to_remove.append(doc.get("id"))
    
    if dry_run:
        print(f"SIMULAÇÃO: {len(docs_to_remove)} documentos seriam removidos de {len(groups)} grupos")
        for i, doc_id in enumerate(docs_to_remove):
            # Encontrar o documento
            for doc in documents:
                if doc.get("id") == doc_id:
                    print(f"\n{i+1}. ID: {doc_id}")
                    print(f"   Source: {doc.get('source', 'desconhecido')}")
                    print(f"   Criado: {doc.get('created', 'desconhecido')}")
                    break
        return len(groups), len(docs_to_remove)
    
    # Filtrar documentos
    new_documents = [doc for doc in documents if doc.get("id") not in docs_to_remove]
    
    # Atualizar banco de dados
    db["documents"] = new_documents
    
    # Salvar alterações
    success = save_database(db)
    if success:
        print(f"Removidos {len(docs_to_remove)} documentos com conteúdo duplicado de {len(groups)} grupos")
    else:
        print(f"ERRO: Falha ao salvar alterações no banco de dados")
    
    return len(groups), len(docs_to_remove)

def remove_file_duplicates(db: Dict, dry_run: bool = False) -> Tuple[int, int]:
    """
    Remove documentos que se referem ao mesmo arquivo
    
    Args:
        db: Banco de dados LightRAG
        dry_run: Se True, apenas simula as alterações sem salvá-las
        
    Retorna:
        Tuple[int, int]: (número de grupos afetados, número de documentos removidos)
    """
    documents = db.get("documents", [])
    print(f"Analisando {len(documents)} documentos para arquivos duplicados...")
    
    # Identificar grupos de documentos do mesmo arquivo
    groups = identify_file_duplicates(documents)
    print(f"Encontrados {len(groups)} grupos de documentos referentes ao mesmo arquivo")
    
    if not groups:
        return 0, 0
    
    # Contar documentos a serem removidos (todos exceto o mais recente de cada grupo)
    docs_to_remove = []
    for file_name, docs in groups.items():
        # Ordenar por data de criação (mais recente primeiro)
        docs_sorted = sorted(docs, key=lambda d: d.get("created", ""), reverse=True)
        # Manter o mais recente, remover os demais
        for doc in docs_sorted[1:]:
            docs_to_remove.append(doc.get("id"))
    
    if dry_run:
        print(f"SIMULAÇÃO: {len(docs_to_remove)} documentos seriam removidos de {len(groups)} grupos de arquivos")
        for i, doc_id in enumerate(docs_to_remove):
            # Encontrar o documento
            for doc in documents:
                if doc.get("id") == doc_id:
                    print(f"\n{i+1}. ID: {doc_id}")
                    print(f"   Source: {doc.get('source', 'desconhecido')}")
                    print(f"   Criado: {doc.get('created', 'desconhecido')}")
                    break
        return len(groups), len(docs_to_remove)
    
    # Filtrar documentos
    new_documents = [doc for doc in documents if doc.get("id") not in docs_to_remove]
    
    # Atualizar banco de dados
    db["documents"] = new_documents
    
    # Salvar alterações
    success = save_database(db)
    if success:
        print(f"Removidos {len(docs_to_remove)} documentos referentes a arquivos duplicados de {len(groups)} grupos")
    else:
        print(f"ERRO: Falha ao salvar alterações no banco de dados")
    
    return len(groups), len(docs_to_remove)

def get_db_stats(db: Dict) -> Dict[str, Any]:
    """
    Calcula estatísticas sobre o banco de dados
    
    Args:
        db: Banco de dados LightRAG
        
    Retorna:
        Dict[str, Any]: Estatísticas do banco de dados
    """
    documents = db.get("documents", [])
    
    # Estatísticas básicas
    stats = {
        "total_documents": len(documents),
        "last_updated": db.get("lastUpdated", "desconhecido"),
        "conv_id_count": 0,
        "doc_id_count": 0,
        "sources": {},
        "largest_document": 0,
        "smallest_document": float('inf') if documents else 0,
        "avg_document_size": 0
    }
    
    if not documents:
        return stats
    
    # Calcular estatísticas detalhadas
    total_size = 0
    for doc in documents:
        # Contagem por tipo de ID
        doc_id = doc.get("id", "")
        if is_conversation_id(doc_id):
            stats["conv_id_count"] += 1
        elif doc_id.startswith("doc_"):
            stats["doc_id_count"] += 1
        
        # Contagem por fonte
        source = doc.get("source", "desconhecido")
        if source not in stats["sources"]:
            stats["sources"][source] = 0
        stats["sources"][source] += 1
        
        # Estatísticas de tamanho
        content = doc.get("content", "")
        content_size = len(content)
        total_size += content_size
        
        if content_size > stats["largest_document"]:
            stats["largest_document"] = content_size
        
        if content_size < stats["smallest_document"]:
            stats["smallest_document"] = content_size
    
    # Calcular média
    stats["avg_document_size"] = total_size / len(documents) if documents else 0
    
    return stats

def main():
    # Configurar argumentos da linha de comando
    parser = argparse.ArgumentParser(
        description="Gerenciador de Duplicatas LightRAG - Detecta, corrige e remove documentos duplicados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python duplicate_manager.py --consolidate --dry-run
  python duplicate_manager.py --remove-content-duplicates
  python duplicate_manager.py --stats
  python duplicate_manager.py --all
"""
    )
    
    parser.add_argument("--stats", action="store_true",
                        help="Exibir estatísticas do banco de dados")
    parser.add_argument("--consolidate", action="store_true",
                        help="Consolidar documentos que se referem à mesma conversa")
    parser.add_argument("--remove-content-duplicates", action="store_true",
                        help="Remover documentos com conteúdo duplicado")
    parser.add_argument("--remove-file-duplicates", action="store_true",
                        help="Remover documentos que se referem ao mesmo arquivo")
    parser.add_argument("--all", action="store_true",
                        help="Executar todas as operações (consolidar e remover duplicatas)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simular operações sem fazer alterações")
    
    args = parser.parse_args()
    
    # Exibir cabeçalho
    print("=== LightRAG - Gerenciador de Duplicatas ===\n")
    
    # Carregar banco de dados
    db = load_database()
    documents = db.get("documents", [])
    print(f"Banco de dados carregado: {len(documents)} documentos encontrados.\n")
    
    # Se nenhuma opção foi especificada, mostrar ajuda
    if not any([args.stats, args.consolidate, args.remove_content_duplicates, 
                args.remove_file_duplicates, args.all]):
        parser.print_help()
        return
    
    # Executar estatísticas
    if args.stats or args.all:
        print("\n== Estatísticas do Banco de Dados ==")
        stats = get_db_stats(db)
        print(f"Total de documentos: {stats['total_documents']}")
        print(f"Última atualização: {stats['last_updated']}")
        print(f"Documentos com ID de conversa (conv_): {stats['conv_id_count']}")
        print(f"Documentos com ID de documento (doc_): {stats['doc_id_count']}")
        print(f"Tamanho médio dos documentos: {stats['avg_document_size']:.1f} caracteres")
        print(f"Maior documento: {stats['largest_document']} caracteres")
        print(f"Menor documento: {stats['smallest_document']} caracteres")
        
        print("\nFontes de documentos:")
        for source, count in sorted(stats["sources"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} documentos")
        print()
    
    # Consolidar documentos de conversas
    if args.consolidate or args.all:
        print("\n== Consolidando Documentos de Conversas ==")
        groups, affected = consolidate_conversation_documents(db, dry_run=args.dry_run)
        if not args.dry_run and groups > 0:
            # Recarregar o banco de dados após a consolidação
            db = load_database()
    
    # Remover documentos com conteúdo duplicado
    if args.remove_content_duplicates or args.all:
        print("\n== Removendo Documentos com Conteúdo Duplicado ==")
        groups, removed = remove_duplicate_content(db, dry_run=args.dry_run)
        if not args.dry_run and removed > 0:
            # Recarregar o banco de dados após a remoção
            db = load_database()
    
    # Remover documentos que se referem ao mesmo arquivo
    if args.remove_file_duplicates or args.all:
        print("\n== Removendo Documentos que se Referem ao Mesmo Arquivo ==")
        groups, removed = remove_file_duplicates(db, dry_run=args.dry_run)
    
    print("\n=== Operação concluída ===")

if __name__ == "__main__":
    main()