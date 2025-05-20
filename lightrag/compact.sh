#!/bin/bash
#
# compact.sh - Inicializador Universal do LightRAG
# Script otimizado para funcionar em qualquer diretório
#

# Determinar diretório base do LightRAG
find_lightrag_dir() {
    # Verificar se estamos no diretório principal
    if [ -d "lightrag" ] && [ -f "lightrag/micro_lightrag.py" ]; then
        echo "$(pwd)/lightrag"
        return 0
    # Verificar se estamos no próprio diretório lightrag
    elif [ -f "micro_lightrag.py" ] && [ -f "start_lightrag.sh" ]; then
        echo "$(pwd)"
        return 0
    # Verificar diretório pessoal
    elif [ -d "$HOME/.claude/lightrag" ] && [ -f "$HOME/.claude/lightrag/micro_lightrag.py" ]; then
        echo "$HOME/.claude/lightrag"
        return 0
    # Verificar ambiente Claude
    elif [ -d "/Users/agents/.claude/lightrag" ] && [ -f "/Users/agents/.claude/lightrag/micro_lightrag.py" ]; then
        echo "/Users/agents/.claude/lightrag"
        return 0
    else
        return 1
    fi
}

# Encontrar Python adequado
find_python() {
    # Verificar ambiente virtual do projeto
    if [ -d "$HOME/.claude/venv/bin" ] && [ -f "$HOME/.claude/venv/bin/python" ]; then
        echo "$HOME/.claude/venv/bin/python"
        return 0
    # Verificar Python3 no sistema
    elif command -v python3 &> /dev/null; then
        echo "python3"
        return 0
    else
        return 1
    fi
}

# Encerrar instâncias existentes
stop_lightrag() {
    echo "Encerrando processos LightRAG existentes..."
    pkill -f "python.*lightrag|flask.*lightrag" 2>/dev/null || true
    pkill -f "flask.*micro_lightrag" 2>/dev/null || true
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    sleep 1
}

# Banner de ajuda
show_help() {
    echo "LightRAG - Sistema simplificado de RAG"
    echo "Uso: compact [comando]"
    echo
    echo "Comandos:"
    echo "  start     - Inicia o servidor LightRAG"
    echo "  stop      - Encerra o servidor LightRAG"
    echo "  restart   - Reinicia o servidor LightRAG"
    echo "  status    - Verifica o status do servidor"
    echo "  help      - Exibe esta ajuda"
    echo
    echo "Sem comando, a operação padrão é iniciar o servidor."
    echo
}

# Verificar status
check_status() {
    LIGHTRAG_DIR="$1"
    PID_FILE="$LIGHTRAG_DIR/.lightrag.pid"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "✓ LightRAG está em execução (PID: $PID)"
            curl -s http://127.0.0.1:5000/status | python3 -m json.tool 2>/dev/null || echo "Servidor não está respondendo"
            return 0
        else
            echo "✗ LightRAG não está em execução (PID inválido: $PID)"
            return 1
        fi
    else
        echo "✗ LightRAG não parece estar em execução (arquivo PID não encontrado)"
        return 1
    fi
}

# Iniciar servidor
start_lightrag() {
    LIGHTRAG_DIR="$1"
    PYTHON="$2"
    LOG_DIR="$LIGHTRAG_DIR/logs"
    
    mkdir -p "$LOG_DIR"
    
    # Verificar se Flask está instalado
    $PYTHON -c "import flask" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Flask não encontrado, instalando..."
        $PYTHON -m pip install flask
    fi
    
    # Encerrar instâncias existentes
    stop_lightrag
    
    # Iniciar servidor Flask
    echo "Iniciando servidor LightRAG..."
    cd "$LIGHTRAG_DIR"
    chmod +x "$LIGHTRAG_DIR/micro_lightrag.py"
    
    export FLASK_APP="$LIGHTRAG_DIR/micro_lightrag.py"
    nohup $PYTHON -m flask run > "$LOG_DIR/lightrag.log" 2>&1 &
    PID=$!
    
    # Salvar PID e verificar inicialização
    echo $PID > "$LIGHTRAG_DIR/.lightrag.pid"
    sleep 2
    
    if kill -0 $PID 2>/dev/null; then
        echo "✓ LightRAG iniciado com sucesso (PID: $PID)"
        echo
        echo "Uso no código Claude:"
        echo "from claude import MCP"
        echo "lightrag = MCP.connect_to_service('lightrag')"
        echo "lightrag.rag_insert_text(text=\"Texto para adicionar à base\")"
        echo "resultado = lightrag.rag_query(query=\"Sua pergunta\")"
        echo
        echo "Servidor disponível em: http://127.0.0.1:5000"
        echo "Logs em: $LOG_DIR/lightrag.log"
        return 0
    else
        echo "✗ Falha ao iniciar LightRAG"
        cat "$LOG_DIR/lightrag.log"
        return 1
    fi
}

# Comando principal
case "${1:-start}" in
    start)
        LIGHTRAG_DIR=$(find_lightrag_dir)
        if [ $? -ne 0 ]; then
            echo "✗ Diretório LightRAG não encontrado"
            exit 1
        fi
        
        PYTHON=$(find_python)
        if [ $? -ne 0 ]; then
            echo "✗ Python não encontrado"
            exit 1
        fi
        
        echo "📂 Diretório LightRAG: $LIGHTRAG_DIR"
        echo "🐍 Python: $PYTHON"
        
        start_lightrag "$LIGHTRAG_DIR" "$PYTHON"
        ;;
    stop)
        LIGHTRAG_DIR=$(find_lightrag_dir)
        if [ $? -ne 0 ]; then
            echo "✗ Diretório LightRAG não encontrado"
            exit 1
        fi
        
        stop_lightrag
        echo "✓ LightRAG encerrado"
        ;;
    restart)
        LIGHTRAG_DIR=$(find_lightrag_dir)
        if [ $? -ne 0 ]; then
            echo "✗ Diretório LightRAG não encontrado"
            exit 1
        fi
        
        PYTHON=$(find_python)
        if [ $? -ne 0 ]; then
            echo "✗ Python não encontrado"
            exit 1
        fi
        
        stop_lightrag
        start_lightrag "$LIGHTRAG_DIR" "$PYTHON"
        ;;
    status)
        LIGHTRAG_DIR=$(find_lightrag_dir)
        if [ $? -ne 0 ]; then
            echo "✗ Diretório LightRAG não encontrado"
            exit 1
        fi
        
        check_status "$LIGHTRAG_DIR"
        ;;
    help)
        show_help
        ;;
    *)
        echo "Comando desconhecido: $1"
        show_help
        exit 1
        ;;
esac

exit 0