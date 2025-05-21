#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Código para executar rag_insert_file via Model Context Protocol (MCP)
import json
from claude import MCP  # Model Context Protocol

# Conectar ao serviço lightrag
lightrag_service = MCP.connect_to_service('lightrag')

# Parâmetros para o comando
params = {
    "file_path": "/Users/agents/.claude/projects/-Users-agents--claude/53fc207e-0c8e-40ad-881e-718667fc8d47.jsonl"
}

# Executar comando
try:
    resultado = lightrag_service.rag_insert_file(**params)
    # Exibir resultado
    print(f"Resultado da operação rag_insert_file:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Erro ao inserir arquivo: {e}")
    print("Verifique se o servidor LightRAG está em execução na porta 8020")
    print("Para iniciar: uvicorn lightrag.server:app --host 127.0.0.1 --port 8020")