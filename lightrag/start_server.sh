#!/bin/bash

# Script para iniciar o servidor LightRAG

# Definir o diretório base
LIGHTRAG_DIR="/Users/agents/.claude/lightrag"

# Mudar para o diretório do LightRAG
cd "$LIGHTRAG_DIR"

# Adicionar o diretório ao Python path e iniciar o servidor
PYTHONPATH="$LIGHTRAG_DIR:$PYTHONPATH" python3 api/server.py