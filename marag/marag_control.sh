#!/bin/bash
# Script de controle para o marag Agent Daemon
# Uso: ./marag_control.sh [start|stop|restart|status|logs]

marag_DIR="/Users/agents/Desktop/claude-20x/agents/marag"
DAEMON_SCRIPT="$marag_DIR/marag_daemon.py"
LOG_FILE="$marag_DIR/logs/marag_daemon.log"

cd "$marag_DIR"

case "$1" in
    start)
        echo "🚀 Iniciando marag Daemon..."
        python3 "$DAEMON_SCRIPT" start &
        sleep 2
        python3 "$DAEMON_SCRIPT" status
        ;;
    stop)
        echo "🛑 Parando marag Daemon..."
        python3 "$DAEMON_SCRIPT" stop
        ;;
    restart)
        echo "🔄 Reiniciando marag Daemon..."
        python3 "$DAEMON_SCRIPT" restart &
        sleep 2
        python3 "$DAEMON_SCRIPT" status
        ;;
    status)
        python3 "$DAEMON_SCRIPT" status
        ;;
    logs)
        echo "📋 Logs do marag Daemon:"
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "❌ Arquivo de log não encontrado: $LOG_FILE"
        fi
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Comandos:"
        echo "  start   - Inicia o daemon do marag"
        echo "  stop    - Para o daemon do marag"
        echo "  restart - Reinicia o daemon do marag"
        echo "  status  - Mostra o status atual"
        echo "  logs    - Mostra os logs em tempo real"
        exit 1
        ;;
esac