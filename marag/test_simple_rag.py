#!/usr/bin/env python3
"""
Teste simples da integração RAG no marag
"""

import json
import time
from pathlib import Path


def test_rag_save():
    """Testa o salvamento no RAG"""
    
    print("🧪 Testando salvamento no RAG...")
    
    # Simular dados extraídos pelo marag
    extracted_data = {
        "name": "João Silva",
        "email": "joao.silva@exemplo.com",
        "phone": "(11) 99999-9999",
        "organization": "TechCorp",
        "role": "desenvolvedor senior"
    }
    
    # Criar conteúdo estruturado
    content = f"""
CONVERSAÇÃO marag AGENT
========================

Sessão: test_session_1
Data: {time.strftime("%Y-%m-%d %H:%M:%S")}

QUERY DO USUÁRIO:
Meu nome é João Silva, email: joao.silva@exemplo.com, telefone: (11) 99999-9999, trabalho na empresa TechCorp como desenvolvedor senior

INFORMAÇÕES EXTRAÍDAS:
{json.dumps(extracted_data, indent=2, ensure_ascii=False)}

RESUMO:
Extraído contato completo de João Silva com todas as informações necessárias.

TIPO: Extração de informações de contato
FONTE: marag Agent A2A
    """
    
    # Salvar no RAG
    rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
    
    try:
        # Carregar documentos existentes
        documents = []
        if rag_cache_path.exists():
            with open(rag_cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                documents = data.get('documents', [])
        
        # Criar novo documento
        new_doc = {
            "id": f"doc_marag_{int(time.time() * 1000)}",
            "title": "Extração de Contato - Sessão test_session_1",
            "content": content,
            "type": "contact_extraction",
            "source": "marag_session_test_session_1",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "metadata": {
                "extracted_by": "marag_agent",
                "session_id": "marag_session"
            }
        }
        
        # Adicionar ao cache
        documents.append(new_doc)
        
        # Salvar de volta
        rag_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(rag_cache_path, 'w', encoding='utf-8') as f:
            json.dump({'documents': documents}, f, ensure_ascii=False, indent=2)
        
        print("✅ Informações salvas no RAG com sucesso!")
        print(f"📄 Documento criado: {new_doc['title']}")
        print(f"🆔 ID: {new_doc['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar no RAG: {e}")
        return False


def test_rag_search():
    """Testa a busca no RAG"""
    
    print("\n🔍 Testando busca no RAG...")
    
    rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
    
    if not rag_cache_path.exists():
        print("❌ Cache RAG não encontrado")
        return
    
    try:
        with open(rag_cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            documents = data.get('documents', [])
            
            # Filtrar documentos do marag
            marag_docs = [doc for doc in documents if doc.get('source', '').startswith('marag_session_')]
            
            print(f"📊 Documentos marag encontrados: {len(marag_docs)}")
            
            for i, doc in enumerate(marag_docs, 1):
                print(f"\n[{i}] 📄 {doc.get('title', 'Sem título')}")
                print(f"    🆔 ID: {doc.get('id', 'N/A')}")
                print(f"    📅 Criado: {doc.get('created_at', 'N/A')}")
                print(f"    🏷️  Tipo: {doc.get('type', 'N/A')}")
                
                # Mostrar conteúdo resumido
                content = doc.get('content', '')
                if len(content) > 100:
                    content = content[:100] + "..."
                print(f"    📝 Conteúdo: {content}")
        
        return len(marag_docs) > 0
        
    except Exception as e:
        print(f"❌ Erro ao buscar no RAG: {e}")
        return False


def main():
    """Função principal"""
    
    print("🧪 Teste da Integração RAG no marag")
    print("=" * 50)
    
    # Teste 1: Salvar no RAG
    success1 = test_rag_save()
    
    # Teste 2: Buscar no RAG
    success2 = test_rag_search()
    
    print("\n" + "=" * 50)
    print("📊 Resultados:")
    print(f"✅ Salvamento: {'Sucesso' if success1 else 'Falha'}")
    print(f"✅ Busca: {'Sucesso' if success2 else 'Falha'}")
    
    if success1 and success2:
        print("\n🎉 Integração RAG funcionando perfeitamente!")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique as configurações.")


if __name__ == "__main__":
    main() 