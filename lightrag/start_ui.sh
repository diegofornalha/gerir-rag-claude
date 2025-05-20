#!/bin/bash
#
# Inicializador da Interface Streamlit para LightRAG
#

# Obter diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Função para encontrar porta disponível
find_available_port() {
    local port=8510
    while netstat -an | grep -q "LISTEN.*:$port"; do
        port=$((port + 1))
    done
    echo $port
}

# Verificar se o LightRAG está rodando
if ! curl -s "http://127.0.0.1:5000/status" > /dev/null; then
    echo "O servidor LightRAG não está rodando. Iniciando..."
    ./compact start
    sleep 2
fi

# Encontrar porta disponível
PORT=$(find_available_port)
echo "Usando porta $PORT para o Streamlit"

# Iniciar Streamlit
echo "Iniciando interface web do LightRAG..."
mkdir -p "$SCRIPT_DIR/logs"
streamlit run lightrag_ui.py --server.port $PORT > "$SCRIPT_DIR/logs/streamlit.log" 2>&1 &

# Salvar PID
echo $! > "$SCRIPT_DIR/.streamlit.pid"

echo "Interface LightRAG iniciada em http://localhost:$PORT"
echo "Logs em: $SCRIPT_DIR/logs/streamlit.log"
echo "Execute './start_ui.sh stop' para encerrar a interface"

# Gerenciar encerramento
if [ "$1" = "stop" ]; then
    if [ -f "$SCRIPT_DIR/.streamlit.pid" ]; then
        PID=$(cat "$SCRIPT_DIR/.streamlit.pid")
        echo "Encerrando interface LightRAG (PID: $PID)..."
        kill $PID 2>/dev/null || true
        rm "$SCRIPT_DIR/.streamlit.pid"
        echo "Interface encerrada"
    else
        echo "Interface LightRAG não está em execução"
    fi
fi