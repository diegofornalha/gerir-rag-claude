import logging
import os
import threading
import json
import requests
import time
from collections.abc import AsyncIterable
from typing import Annotated, Any, ClassVar
from pathlib import Path

from a2a.types import TextPart
from pydantic import BaseModel, Field

import marag

logger = logging.getLogger(__name__)


ClarifyingQuestion = Annotated[
    str, Field(description="A clarifying question to ask the user")
]


def _to_text_part(text: str) -> TextPart:
    return TextPart(type="text", text=text)


class ExtractionOutcome[T](BaseModel):
    """Represents the result of trying to extract contact info."""

    extracted_data: T
    summary: str = Field(
        description="summary of the extracted information.",
    )


class RAGIntegration:
    """Integração com MCP RAG para salvar informações extraídas"""
    
    def __init__(self):
        self.rag_server_url = "http://localhost:8020"  # Se usar HTTP
        self.rag_cache_path = Path.home() / ".claude" / "mcp-rag-cache" / "documents.json"
    
    def save_to_rag(self, title: str, content: str, source: str = "marag_agent", doc_type: str = "conversation"):
        """Salva informações no RAG via arquivo local"""
        try:
            # Carregar documentos existentes
            documents = []
            if self.rag_cache_path.exists():
                with open(self.rag_cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    documents = data.get('documents', [])
            
            # Criar novo documento
            import time
            new_doc = {
                "id": f"doc_marag_{int(time.time() * 1000)}",
                "title": title,
                "content": content,
                "type": doc_type,
                "source": source,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "metadata": {
                    "extracted_by": "marag_agent",
                    "session_id": "marag_session"
                }
            }
            
            # Adicionar ao cache
            documents.append(new_doc)
            
            # Salvar de volta
            self.rag_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.rag_cache_path, 'w', encoding='utf-8') as f:
                json.dump({'documents': documents}, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Informações salvas no RAG: {title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar no RAG: {e}")
            return False
    
    def extract_and_save_conversation(self, query: str, session_id: str, extracted_data: dict, summary: str):
        """Extrai e salva informações da conversa no RAG"""
        
        # Criar conteúdo estruturado
        content = f"""
CONVERSAÇÃO marag AGENT
========================

Sessão: {session_id}
Data: {time.strftime("%Y-%m-%d %H:%M:%S")}

QUERY DO USUÁRIO:
{query}

INFORMAÇÕES EXTRAÍDAS:
{json.dumps(extracted_data, indent=2, ensure_ascii=False)}

RESUMO:
{summary}

TIPO: Extração de informações de contato
FONTE: marag Agent A2A
        """
        
        # Salvar no RAG
        title = f"Extração de Contato - Sessão {session_id}"
        return self.save_to_rag(title, content, f"marag_session_{session_id}", "contact_extraction")


class ExtractorAgent[T]:
    """Contact information extraction agent using marag framework with RAG integration."""

    SUPPORTED_CONTENT_TYPES: ClassVar[list[str]] = [
        "text",
        "text/plain",
        "application/json",
    ]

    def __init__(self, instructions: str, result_type: type[T]):
        self.instructions = instructions
        self.result_type = result_type
        self.rag = RAGIntegration()

    async def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
        """Process a user query with marag and save to RAG

        Args:
            query: The user's input text.
            sessionId: The session identifier

        Returns:
            A dictionary describing the outcome and necessary next steps.
        """
        try:
            logger.debug(
                f"[Session: {sessionId}] PID: {os.getpid()} | PyThread: {threading.get_ident()} | Using/Creating maragThread ID: {sessionId}"
            )

            result = await marag.run_async(
                query,
                context={
                    "your personality": self.instructions,
                    "reminder": "Use your memory to help fill out the form",
                },
                thread=marag.Thread(id=sessionId),
                result_type=ExtractionOutcome[self.result_type] | ClarifyingQuestion,
            )

            if isinstance(result, ExtractionOutcome):
                # Salvar informações extraídas no RAG
                extracted_data = result.extracted_data.model_dump()
                self.rag.extract_and_save_conversation(
                    query=query,
                    session_id=sessionId,
                    extracted_data=extracted_data,
                    summary=result.summary
                )
                
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "text_parts": [_to_text_part(result.summary)],
                    "data": extracted_data,
                }
            else:
                assert isinstance(result, str)
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "text_parts": [_to_text_part(result)],
                    "data": None,
                }

        except Exception as e:
            logger.exception(f"Error during agent invocation for session {sessionId}")
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "text_parts": [
                    _to_text_part(
                        f"Sorry, I encountered an error processing your request: {str(e)}"
                    )
                ],
                "data": None,
            }

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[dict[str, Any]]:
        """Stream the response for a user query.

        Args:
            query: The user's input text.
            sessionId: The session identifier.

        Returns:
            An asynchronous iterable of response dictionaries.
        """
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Analyzing your text for contact information and saving to RAG...",
        }

        yield await self.invoke(query, sessionId)