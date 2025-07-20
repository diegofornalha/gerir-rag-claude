#!/usr/bin/env python3
"""
Iniciar servidor marag com integração RAG
"""

import uvicorn
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório pai ao path
sys.path.append(str(Path(__file__).parent.parent))

from agent import ExtractorAgent
from agent_executor import ExtractorAgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from pydantic import BaseModel, EmailStr, Field


class ContactInfo(BaseModel):
    """Structured contact information extracted from text."""
    name: str = Field(description="Person's first and last name")
    email: EmailStr = Field(description="Email address")
    phone: str = Field(description="Phone number if present")
    organization: str | None = Field(None, description="Organization or company if mentioned")
    role: str | None = Field(None, description="Job title or role if mentioned")


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the ExtractorAgent with RAG integration."""
    capabilities = AgentCapabilities(streaming=True)
    skill = AgentSkill(
        id="extract_contacts_with_rag",
        name="Contact Information Extraction with RAG",
        description="Extracts structured contact information from text and saves to RAG for future reference",
        tags=["contact info", "structured extraction", "information extraction", "rag", "memory"],
        examples=["My name is John Doe, email: john@example.com, phone: (555) 123-4567"],
    )
    return AgentCard(
        name="marag Contact Extractor with RAG",
        description="Extracts structured contact information from text using marag's extraction capabilities and saves to RAG for persistent memory",
        url=f"http://{host}:{port}/",
        version="2.0.0",
        defaultInputModes=["text", "text/plain", "application/json"],
        defaultOutputModes=["text", "text/plain", "application/json"],
        capabilities=capabilities,
        skills=[skill],
    )


def main():
    """Iniciar o servidor marag com RAG"""
    host = "localhost"
    port = 10031
    
    print(f"🚀 Iniciando servidor marag com RAG em {host}:{port}...")
    print("📊 Funcionalidades:")
    print("  ✅ Extração de informações de contato")
    print("  ✅ Salvamento automático no RAG")
    print("  ✅ Memória persistente de conversas")
    print("  ✅ Busca semântica em histórico")
    print()
    
    # Criar o agente com RAG
    agent = ExtractorAgent(
        instructions="Politely interrogate the user for their contact information. The schema of the result type implies what things you _need_ to get from the user. Always save extracted information to RAG for future reference.",
        result_type=ContactInfo
    )
    
    # Criar o handler de requisições
    request_handler = DefaultRequestHandler(
        agent_executor=ExtractorAgentExecutor(agent=agent),
        task_store=InMemoryTaskStore(),
    )
    
    # Criar o servidor
    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), 
        http_handler=request_handler
    )
    
    print("✅ Servidor configurado com RAG, iniciando...")
    print(f"🌐 Acesse: http://{host}:{port}")
    print("📝 Use o agente para extrair informações e elas serão salvas automaticamente no RAG!")
    print()
    
    # Iniciar o servidor
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main() 