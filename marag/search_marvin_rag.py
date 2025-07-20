#!/usr/bin/env python3
"""
Buscar informações no RAG que foram salvas pelo marag
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def search_marag_documents(query: str = None) -> List[Dict[str, Any]]:
    """Busca documentos do marag no RAG"""
    
    rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
    
    if not rag_cache_path.exists():
        print("❌ Cache RAG não encontrado")
        return []
    
    try:
        with open(rag_cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            documents = data.get('documents', [])
            
            # Filtrar documentos do marag
            marag_docs = []
            for doc in documents:
                source = doc.get('source', '')
                if source.startswith('marag_session_') or 'marag_agent' in source:
                    marag_docs.append(doc)
            
            # Filtrar por query se fornecida
            if query:
                query_lower = query.lower()
                filtered_docs = []
                for doc in marag_docs:
                    content = f"{doc.get('title', '')} {doc.get('content', '')}".lower()
                    if query_lower in content:
                        filtered_docs.append(doc)
                return filtered_docs
            
            return marag_docs
            
    except Exception as e:
        print(f"❌ Erro ao ler cache RAG: {e}")
        return []


def display_document(doc: Dict[str, Any], index: int = None):
    """Exibe um documento de forma formatada"""
    
    prefix = f"[{index}] " if index is not None else ""
    
    print(f"\n{prefix}📄 {doc.get('title', 'Sem título')}")
    print(f"   🆔 ID: {doc.get('id', 'N/A')}")
    print(f"   📅 Criado: {doc.get('created_at', 'N/A')}")
    print(f"   🏷️  Tipo: {doc.get('type', 'N/A')}")
    print(f"   📍 Fonte: {doc.get('source', 'N/A')}")
    
    # Mostrar conteúdo resumido
    content = doc.get('content', '')
    if len(content) > 200:
        content = content[:200] + "..."
    
    print(f"   📝 Conteúdo: {content}")
    
    # Mostrar metadados se existirem
    metadata = doc.get('metadata', {})
    if metadata:
        print(f"   🔍 Metadados: {metadata}")


def main():
    """Função principal"""
    
    print("🔍 Buscador de Documentos marag no RAG")
    print("=" * 50)
    
    # Buscar todos os documentos do marag
    marag_docs = search_marag_documents()
    
    if not marag_docs:
        print("📭 Nenhum documento do marag encontrado no RAG")
        print("💡 Use o agente marag para extrair informações e elas aparecerão aqui!")
        return
    
    print(f"📊 Encontrados {len(marag_docs)} documentos do marag:")
    
    # Exibir todos os documentos
    for i, doc in enumerate(marag_docs, 1):
        display_document(doc, i)
    
    # Busca interativa
    print("\n" + "=" * 50)
    print("🔍 Busca Interativa")
    print("Digite uma palavra-chave para filtrar os documentos (ou 'sair' para sair):")
    
    while True:
        try:
            query = input("\n🔍 Buscar por: ").strip()
            
            if query.lower() in ['sair', 'exit', 'quit']:
                break
            
            if not query:
                continue
            
            # Buscar documentos que contêm a query
            filtered_docs = search_marag_documents(query)
            
            if not filtered_docs:
                print(f"❌ Nenhum documento encontrado para: '{query}'")
                continue
            
            print(f"\n✅ Encontrados {len(filtered_docs)} documentos para '{query}':")
            
            for i, doc in enumerate(filtered_docs, 1):
                display_document(doc, i)
                
        except KeyboardInterrupt:
            print("\n👋 Até logo!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main() 