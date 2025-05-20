#!/bin/bash
#
# LightRAG - Script de inicialização
# Script otimizado para iniciar o servidor LightRAG

# Identificar diretório base (onde este script está)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"

# Criar diretório de logs
mkdir -p "$LOG_DIR"

# Definir Python a ser utilizado
if [ -f "$HOME/.claude/venv/bin/python" ]; then
    PYTHON="$HOME/.claude/venv/bin/python"
else
    PYTHON="python3"
fi

# Verificar se Flask está instalado
$PYTHON -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Flask não encontrado, instalando..."
    pip install flask
fi

# Encerrar processos existentes
echo "Verificando processos existentes..."
pkill -f "python.*lightrag|flask.*lightrag" 2>/dev/null || true
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
sleep 1

# Iniciar servidor Flask
echo "Iniciando servidor LightRAG..."
cd "$SCRIPT_DIR"
chmod +x "$SCRIPT_DIR/micro_lightrag.py"

export FLASK_APP="$SCRIPT_DIR/micro_lightrag.py"
nohup $PYTHON -m flask run > "$LOG_DIR/lightrag.log" 2>&1 &
PID=$!

# Salvar PID e aguardar inicialização
echo $PID > "$SCRIPT_DIR/.lightrag.pid"
sleep 3

# Verificar se iniciou corretamente
if kill -0 $PID 2>/dev/null; then
    echo "✓ Servidor LightRAG iniciado com sucesso (PID: $PID)"
    echo
    echo "Para usar no código Claude:"
    echo "from claude import MCP"
    echo "lightrag = MCP.connect_to_service('lightrag')"
    echo "lightrag.rag_insert_text(text=\"Texto para adicionar à base\")"
    echo "resultado = lightrag.rag_query(query=\"Sua pergunta\")"
    echo
    echo "O servidor está disponível em http://127.0.0.1:5000"
    echo "Logs em: $LOG_DIR/lightrag.log"
    exit 0
else
    echo "✗ Falha ao iniciar servidor LightRAG"
    cat "$LOG_DIR/lightrag.log"
    exit 1
fi