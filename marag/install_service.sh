#!/bin/bash
# Script para instalar/desinstalar o serviço marag no macOS usando launchd

marag_DIR="/Users/agents/Desktop/claude-20x/agents/marag"
PLIST_FILE="$marag_DIR/com.marag.agent.plist"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
LAUNCHD_PLIST="$LAUNCHD_DIR/com.marag.agent.plist"

case "$1" in
    install)
        echo "📦 Instalando serviço marag..."
        
        # Criar diretório se não existir
        mkdir -p "$LAUNCHD_DIR"
        mkdir -p "$marag_DIR/logs"
        
        # Copiar arquivo plist
        cp "$PLIST_FILE" "$LAUNCHD_PLIST"
        
        # Carregar o serviço
        launchctl load "$LAUNCHD_PLIST"
        
        echo "✅ Serviço marag instalado e iniciado"
        echo "   O marag agora iniciará automaticamente no login"
        ;;
        
    uninstall)
        echo "🗑️  Removendo serviço marag..."
        
        # Descarregar o serviço
        launchctl unload "$LAUNCHD_PLIST" 2>/dev/null || true
        
        # Remover arquivo plist
        rm -f "$LAUNCHD_PLIST"
        
        echo "✅ Serviço marag removido"
        ;;
        
    start)
        echo "🚀 Iniciando serviço marag..."
        launchctl start com.marag.agent
        ;;
        
    stop)
        echo "🛑 Parando serviço marag..."
        launchctl stop com.marag.agent
        ;;
        
    restart)
        echo "🔄 Reiniciando serviço marag..."
        launchctl stop com.marag.agent
        sleep 2
        launchctl start com.marag.agent
        ;;
        
    status)
        echo "📊 Status do serviço marag:"
        if launchctl list | grep -q com.marag.agent; then
            echo "✅ Serviço carregado"
            launchctl list com.marag.agent
        else
            echo "❌ Serviço não carregado"
        fi
        
        # Verificar se o processo está rodando
        if lsof -i :10030 > /dev/null 2>&1; then
            echo "✅ marag está rodando na porta 10030"
        else
            echo "❌ marag não está rodando na porta 10030"
        fi
        ;;
        
    logs)
        echo "📋 Logs do serviço marag:"
        echo "--- stdout ---"
        tail -n 20 "$marag_DIR/logs/launchd_stdout.log" 2>/dev/null || echo "Nenhum log stdout"
        echo "--- stderr ---"
        tail -n 20 "$marag_DIR/logs/launchd_stderr.log" 2>/dev/null || echo "Nenhum log stderr"
        echo "--- daemon ---"
        tail -n 20 "$marag_DIR/logs/marag_daemon.log" 2>/dev/null || echo "Nenhum log daemon"
        ;;
        
    *)
        echo "Uso: $0 {install|uninstall|start|stop|restart|status|logs}"
        echo ""
        echo "Comandos:"
        echo "  install   - Instala o serviço (auto-start no login)"
        echo "  uninstall - Remove o serviço"
        echo "  start     - Inicia o serviço"
        echo "  stop      - Para o serviço"
        echo "  restart   - Reinicia o serviço"
        echo "  status    - Mostra o status do serviço"
        echo "  logs      - Mostra os logs do serviço"
        exit 1
        ;;
esac