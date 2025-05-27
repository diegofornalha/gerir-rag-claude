#!/usr/bin/env python3
"""
Indexador de sessões Claude para RAG
Processa arquivos JSONL grandes de forma eficiente
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Generator

def extract_session_content(jsonl_path: Path) -> Generator[Dict, None, None]:
    """
    Extrai conteúdo relevante de uma sessão Claude
    Processa linha por linha para economizar memória
    """
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            try:
                data = json.loads(line)
                
                # Extrair mensagens do usuário e assistente
                if data.get('type') in ['user', 'assistant'] and data.get('message'):
                    message = data['message']
                    
                    # Processar conteúdo
                    content_parts = []
                    
                    if isinstance(message.get('content'), list):
                        for item in message['content']:
                            if item.get('type') == 'text':
                                content_parts.append(item.get('text', ''))
                            elif item.get('type') == 'tool_use':
                                # Incluir uso de ferramentas
                                tool_name = item.get('name', 'unknown')
                                content_parts.append(f"[Tool: {tool_name}]")
                    
                    if content_parts:
                        yield {
                            'type': data['type'],
                            'content': ' '.join(content_parts),
                            'timestamp': data.get('timestamp'),
                            'uuid': data.get('uuid'),
                            'sessionId': data.get('sessionId'),
                            'line_number': line_num
                        }
                        
            except json.JSONDecodeError:
                print(f"Erro ao processar linha {line_num}")
                continue

def chunk_session_content(session_path: Path, chunk_size: int = 1000) -> List[Dict]:
    """
    Divide sessão em chunks menores para indexação
    """
    chunks = []
    current_chunk = []
    current_size = 0
    
    for item in extract_session_content(session_path):
        content = item['content']
        current_chunk.append(content)
        current_size += len(content.split())
        
        if current_size >= chunk_size:
            # Criar chunk
            chunks.append({
                'content': '\n'.join(current_chunk),
                'source': f"{session_path.name}:chunk{len(chunks)+1}",
                'metadata': {
                    'session_id': item['sessionId'],
                    'chunk_index': len(chunks),
                    'type': 'claude_session_chunk',
                    'timestamp': item['timestamp']
                }
            })
            current_chunk = []
            current_size = 0
    
    # Último chunk
    if current_chunk:
        chunks.append({
            'content': '\n'.join(current_chunk),
            'source': f"{session_path.name}:chunk{len(chunks)+1}",
            'metadata': {
                'session_id': item.get('sessionId'),
                'chunk_index': len(chunks),
                'type': 'claude_session_chunk'
            }
        })
    
    return chunks

def index_all_sessions(sessions_dir: Path) -> List[Dict]:
    """
    Indexa todas as sessões em um diretório
    """
    all_chunks = []
    
    for jsonl_file in sessions_dir.glob('*.jsonl'):
        print(f"Processando {jsonl_file.name}...")
        chunks = chunk_session_content(jsonl_file)
        all_chunks.extend(chunks)
        print(f"  -> {len(chunks)} chunks criados")
    
    return all_chunks

if __name__ == "__main__":
    # Exemplo de uso
    session_file = Path("/Users/agents/.claude/projects/-Users-agents--claude/431f9873-d237-490f-83cc-a3d31c527e98.jsonl")
    
    if session_file.exists():
        print(f"Analisando sessão: {session_file.name}")
        
        # Extrair algumas mensagens
        messages = list(extract_session_content(session_file))
        print(f"Total de mensagens: {len(messages)}")
        
        # Mostrar primeiras mensagens
        for msg in messages[:5]:
            print(f"\n[{msg['type']}] {msg['content'][:100]}...")
        
        # Criar chunks
        chunks = chunk_session_content(session_file)
        print(f"\nChunks criados: {len(chunks)}")
        print(f"Primeiro chunk: {chunks[0]['content'][:200]}...")