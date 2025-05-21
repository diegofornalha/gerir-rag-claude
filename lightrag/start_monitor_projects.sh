#!/bin/bash

# Script para iniciar o monitor de projetos para indexação automática
# Este script inicia um processo em segundo plano que monitora novos arquivos JSONL
# e os indexa automaticamente no LightRAG

# Diretório do projeto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Verificar se já existe uma instância rodando
MONITOR_PID=$(pgrep -f "python.*monitor_projects.py" || echo "")
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

# Instalar dependências necessárias se não existirem
pip install watchdog 2>/dev/null

echo "Iniciando monitor de projetos..."
# Iniciar o monitor em segundo plano
python monitor_projects.py > logs/monitor_projects.log 2>&1 &
MONITOR_PID=$!

# Registrar o PID para referência futura
echo $MONITOR_PID > .monitor_pid

echo "Monitor de projetos iniciado com PID: $MONITOR_PID"
echo "Os logs estão disponíveis em: logs/monitor_projects.log"
echo "Para interromper, use: kill $MONITOR_PID"