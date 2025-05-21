#!/bin/bash

# Script para iniciar o monitor aprimorado para LightRAG
# Este script inicia um processo em segundo plano que monitora arquivos JSONL
# e sincroniza com o LightRAG usando o novo sistema baseado em SQLite

# Diretório do projeto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Verificar se já existe uma instância rodando
MONITOR_PID=$(pgrep -f "python.*improved_monitor.py" || echo "")
if [ ! -z "$MONITOR_PID" ]; then
    echo "Uma instância do monitor já está rodando (PID: $MONITOR_PID)"
    echo "Para interromper, use: kill $MONITOR_PID"
    exit 0
fi

# Verificar se o LightRAG está rodando
curl -s http://127.0.0.1:5000/status > /dev/null
if [ $? -ne 0 ]; then
    echo "LightRAG não está rodando. Iniciando server primeiro..."
    # Iniciar LightRAG se não estiver rodando
    bash ./start_lightrag.sh &
    sleep 5  # Dar tempo para o servidor iniciar
fi

# Criar diretório de logs se não existir
mkdir -p logs

# Instalar dependências necessárias
pip install watchdog sqlite3 2>/dev/null

echo "Iniciando monitor aprimorado de projetos..."
# Iniciar o monitor em segundo plano
python improved_monitor.py > logs/improved_monitor.log 2>&1 &
MONITOR_PID=$!

# Registrar o PID para referência futura
echo $MONITOR_PID > .improved_monitor_pid

echo "Monitor aprimorado iniciado com PID: $MONITOR_PID"
echo "Os logs estão disponíveis em: logs/improved_monitor.log"
echo "Para interromper, use: kill $MONITOR_PID"