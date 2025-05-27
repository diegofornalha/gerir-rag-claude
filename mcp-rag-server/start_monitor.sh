#!/bin/bash

# Script para iniciar o monitor em tempo real do RAG

echo "Iniciando Monitor em Tempo Real do RAG..."

# Verificar se o servidor MCP está rodando
if ! pgrep -f "integrated_rag.py" > /dev/null; then
    echo "⚠️  Servidor MCP RAG não está rodando!"
    echo "Iniciando servidor MCP RAG..."
    python integrated_rag.py &
    sleep 2
fi

# Instalar dependências se necessário
pip install watchdog aiohttp > /dev/null 2>&1

# Iniciar o monitor
echo "🔍 Iniciando monitoramento de arquivos Claude..."
python realtime_monitor.py

echo "Monitor encerrado."