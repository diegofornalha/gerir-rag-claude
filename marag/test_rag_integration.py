#!/usr/bin/env python3
"""
Teste da integração RAG no agente marag
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório pai ao path
sys.path.append(str(Path(__file__).parent.parent))

from agent import ExtractorAgent
from pydantic import BaseModel, EmailStr, Field


class ContactInfo(BaseModel):
    """Structured contact information extracted from text."""
    name: str = Field(description="Person's first and last name")
    email: EmailStr = Field(description="Email address")
    phone: str = Field(description="Phone number if present")
    organization: str | None = Field(None, description="Organization or company if mentioned")
    role: str | None = Field(None, description="Job title or role if mentioned")


async def test_marag_rag_integration():
    """Testa a integração RAG no agente marag"""
    
    print("🧪 Testando integração RAG no agente marag...\n")
    
    # Criar o agente
    agent = ExtractorAgent(
        instructions="Politely interrogate the user for their contact information. The schema of the result type implies what things you _need_ to get from the user.",
        result_type=ContactInfo
    )
    
    # Teste 1: Query com informações completas
    print("📝 Teste 1: Query com informações completas")
    query1 = "Meu nome é João Silva, email: joao.silva@exemplo.com, telefone: (11) 99999-9999, trabalho na empresa TechCorp como desenvolvedor senior"
    
    result1 = await agent.invoke(query1, "test_session_1")
    print(f"✅ Resultado: {result1['is_task_complete']}")
    print(f"📊 Dados extraídos: {result1.get('data', {})}")
    print()
    
    # Teste 2: Query incompleta (deve pedir mais informações)
    print("📝 Teste 2: Query incompleta")
    query2 = "Meu nome é Maria Santos"
    
    result2 = await agent.invoke(query2, "test_session_2")
    print(f"✅ Resultado: {result2['is_task_complete']}")
    print(f"📊 Requer input: {result2['require_user_input']}")
    print()
    
    # Teste 3: Verificar se dados foram salvos no RAG
    print("🔍 Teste 3: Verificando dados no RAG")
    rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
    
    if rag_cache_path.exists():
        import json
        with open(rag_cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            documents = data.get('documents', [])
            
            # Procurar por documentos do marag
            marag_docs = [doc for doc in documents if doc.get('source', '').startswith('marag_session_')]
            
            print(f"📊 Documentos marag encontrados: {len(marag_docs)}")
            for doc in marag_docs:
                print(f"  - {doc.get('title', 'Sem título')} (ID: {doc.get('id', 'N/A')})")
    else:
        print("❌ Cache RAG não encontrado")
    
    print("\n🎉 Teste concluído!")


if __name__ == "__main__":
    asyncio.run(test_marag_rag_integration()) 