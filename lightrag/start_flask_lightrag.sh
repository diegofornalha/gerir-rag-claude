#!/bin/bash

# Script para iniciar o servidor LightRAG usando Flask
# Esta versão é mais robusta e compatível com a maioria dos ambientes Python

# Diretório base
BASE_DIR="/Users/agents/.claude"
cd "$BASE_DIR"

# Definir Python a ser utilizado (preferindo o do ambiente virtual)
if [ -f "$BASE_DIR/venv/bin/python" ]; then
    PYTHON="$BASE_DIR/venv/bin/python"
else
    PYTHON="python3"
fi

# Verificar se Flask está instalado
$PYTHON -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Flask não encontrado, instalando..."
    pip install flask
fi

# Garantir que o diretório de logs existe
mkdir -p "$BASE_DIR/logs"

# Verificar se já existe uma porta ocupada em 8020
echo "Verificando se porta 8020 já está em uso..."
if netstat -an | grep -q "127.0.0.1.8020" || lsof -i:8020 &>/dev/null; then
    echo "Porta 8020 já está em uso!"
    echo "Tentando encontrar e encerrar o processo..."
    
    # Encontrar PIDs usando a porta
    PIDS=$(lsof -i:8020 -t 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "Encerrando processos: $PIDS"
        kill -15 $PIDS
        sleep 2
    fi
fi

# Encerrar quaisquer processos LightRAG existentes
echo "Encerrando quaisquer processos LightRAG existentes..."
pkill -f "lightrag|start_lightrag|python.*lightrag" || true
sleep 2

# Dar permissão de execução ao script Python
chmod +x "$BASE_DIR/micro_lightrag.py"

# Iniciar o servidor Flask em segundo plano
echo "Iniciando servidor LightRAG com Flask..."
export FLASK_APP="$BASE_DIR/micro_lightrag.py"
export FLASK_ENV=development
nohup $PYTHON -m flask run --host=127.0.0.1 --port=8020 > "$BASE_DIR/logs/flask_lightrag.log" 2>&1 &
SERVER_PID=$!

# Salvar PID
echo $SERVER_PID > "$BASE_DIR/.lightrag.pid"

# Aguardar o servidor iniciar
echo "Aguardando o servidor iniciar..."
sleep 5

# Verificar se o servidor está rodando
curl -s -o /dev/null -w "%{http_code}" -X OPTIONS http://127.0.0.1:8020/query
RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "Servidor LightRAG Flask iniciado com sucesso! (PID: $SERVER_PID)"
    echo ""
    echo "Para testar o servidor, execute:"
    echo "curl -X POST -H \"Content-Type: application/json\" -d '{\"query\": \"teste\"}' http://127.0.0.1:8020/query"
    echo ""
    echo "Para usar o LightRAG no chat, execute:"
    echo "from claude import MCP"
    echo "lightrag = MCP.connect_to_service('lightrag')"
    echo "resultado = lightrag.rag_query(query=\"Sua pergunta\")"
    echo ""
    echo "Logs disponíveis em: $BASE_DIR/logs/flask_lightrag.log"
else
    echo "Falha ao iniciar o servidor LightRAG Flask."
    echo "Verifique o log em $BASE_DIR/logs/flask_lightrag.log"
    cat "$BASE_DIR/logs/flask_lightrag.log"
fi