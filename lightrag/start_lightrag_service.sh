#!/bin/bash

# Script para iniciar serviço LightRAG em modo daemon
# Este script inicia o servidor LightRAG e monitor de projetos como serviços
# Versão 2.0 - Reorganização e melhorias

# Diretório base
BASE_DIR="$(dirname "$(readlink -f "$0")")"
cd "$BASE_DIR" || { echo "Erro ao acessar diretório base"; exit 1; }

# Diretório de logs
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

# Arquivos PID centralizados
PID_DIR="$BASE_DIR/.pids"
mkdir -p "$PID_DIR"

SERVER_PID="$PID_DIR/lightrag_server.pid"
MONITOR_PID="$PID_DIR/lightrag_monitor.pid"
UI_PID="$PID_DIR/lightrag_ui.pid"

# Função para verificar se um processo está rodando
is_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Está rodando
        fi
    fi
    return 1  # Não está rodando
}

# Função para iniciar servidor
start_server() {
    echo "Iniciando servidor LightRAG..."
    
    # Verificar se já está rodando
    if is_running "$SERVER_PID"; then
        echo "Servidor já está rodando (PID: $(cat "$SERVER_PID"))"
        return
    fi
    
    # Matar qualquer processo na porta 8020
    lsof -ti:8020 | xargs kill -9 2>/dev/null || true
    sleep 1
    
    # Iniciar servidor em background
    nohup python3 -m core.server > "$LOG_DIR/lightrag_server.log" 2>&1 &
    echo $! > "$SERVER_PID"
    echo "Servidor iniciado com PID: $(cat "$SERVER_PID")"
}

# Função para iniciar monitor de projetos
start_monitor() {
    echo "Iniciando monitor de projetos..."
    
    # Verificar se já está rodando
    if is_running "$MONITOR_PID"; then
        echo "Monitor já está rodando (PID: $(cat "$MONITOR_PID"))"
        return
    fi
    
    # Iniciar monitor unificado em background
    nohup python3 unified_monitor.py > "$LOG_DIR/lightrag_monitor.log" 2>&1 &
    echo $! > "$MONITOR_PID"
    echo "Monitor unificado iniciado com PID: $(cat "$MONITOR_PID")"
}

# Função para iniciar interface Streamlit
start_ui() {
    echo "Iniciando interface Streamlit..."
    
    # Verificar se já está rodando
    if is_running "$UI_PID"; then
        echo "Interface já está rodando (PID: $(cat "$UI_PID"))"
        return
    fi
    
    # Iniciar Streamlit em background
    nohup streamlit run app.py > "$LOG_DIR/lightrag_ui.log" 2>&1 &
    echo $! > "$UI_PID"
    echo "Interface iniciada com PID: $(cat "$UI_PID")"
}

# Função para parar todos os serviços
stop_services() {
    echo "Parando serviços LightRAG..."
    
    # Parar UI
    if is_running "$UI_PID"; then
        echo "Parando interface (PID: $(cat "$UI_PID"))..."
        kill "$(cat "$UI_PID")" 2>/dev/null
        rm -f "$UI_PID"
    fi
    
    # Parar monitor
    if is_running "$MONITOR_PID"; then
        echo "Parando monitor (PID: $(cat "$MONITOR_PID"))..."
        kill "$(cat "$MONITOR_PID")" 2>/dev/null
        rm -f "$MONITOR_PID"
    fi
    
    # Parar servidor
    if is_running "$SERVER_PID"; then
        echo "Parando servidor (PID: $(cat "$SERVER_PID"))..."
        kill "$(cat "$SERVER_PID")" 2>/dev/null
        rm -f "$SERVER_PID"
    fi
    
    echo "Todos os serviços parados."
}

# Função para verificar status dos serviços
check_status() {
    echo "Status dos serviços LightRAG:"
    
    if is_running "$SERVER_PID"; then
        echo "✅ Servidor: ATIVO (PID: $(cat "$SERVER_PID"))"
    else
        echo "❌ Servidor: INATIVO"
    fi
    
    if is_running "$MONITOR_PID"; then
        echo "✅ Monitor: ATIVO (PID: $(cat "$MONITOR_PID"))"
    else
        echo "❌ Monitor: INATIVO"
    fi
    
    if is_running "$UI_PID"; then
        echo "✅ Interface: ATIVA (PID: $(cat "$UI_PID"))"
    else
        echo "❌ Interface: INATIVA"
    fi
}

# Função para limpar PIDs antigos
clean_pids() {
    echo "Limpando arquivos PID antigos..."
    
    # Remover PIDs antigos no diretório raiz
    find "$BASE_DIR" -maxdepth 1 -name "*.pid" -o -name ".*.pid" -delete
    
    # Verificar PIDs no diretório centralizado
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid
            pid=$(cat "$pid_file")
            if ! ps -p "$pid" > /dev/null 2>&1; then
                echo "Removendo PID inválido: $pid_file"
                rm -f "$pid_file"
            fi
        fi
    done
    
    echo "Limpeza concluída."
}

# Processamento de argumentos
case "$1" in
    start)
        clean_pids
        start_server
        sleep 2  # Aguardar servidor inicializar
        start_monitor
        start_ui
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        clean_pids
        start_server
        sleep 2
        start_monitor
        start_ui
        ;;
    status)
        check_status
        ;;
    clean)
        stop_services
        clean_pids
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|clean}"
        exit 1
        ;;
esac

exit 0