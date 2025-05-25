#!/bin/bash

echo "🔧 Configurando sincronização automática..."

# Opção 1: Usar fswatch (precisa instalar)
if ! command -v fswatch &> /dev/null; then
    echo "📦 Instalando fswatch..."
    brew install fswatch
fi

# Fazer sync inicial
echo "📦 Fazendo sincronização inicial..."
rsync -av --delete \
    --exclude='*.log' \
    --exclude='*.pid' \
    --exclude='node_modules/' \
    --exclude='__pycache__/' \
    --exclude='.DS_Store' \
    /Users/agents/.claude/ \
    "/Users/agents/Library/CloudStorage/GoogleDrive-diegodg3web@gmail.com/Meu Drive/claude_backup/"

echo "✅ Sincronização inicial completa!"

# Opção para o usuário
echo ""
echo "Escolha como quer rodar a sincronização automática:"
echo "1) Rodar agora em tempo real (precisa manter terminal aberto)"
echo "2) Instalar como serviço do sistema (roda em background)"
echo "3) Usar cron para sincronizar a cada 5 minutos"
read -p "Opção (1/2/3): " opcao

case $opcao in
    1)
        echo "🚀 Iniciando sincronização em tempo real..."
        echo "   Pressione Ctrl+C para parar"
        chmod +x /Users/agents/.claude/start_auto_sync.sh
        /Users/agents/.claude/start_auto_sync.sh
        ;;
    
    2)
        echo "📝 Instalando serviço..."
        cp /Users/agents/.claude/com.claude.backup.plist ~/Library/LaunchAgents/
        launchctl load ~/Library/LaunchAgents/com.claude.backup.plist
        echo "✅ Serviço instalado! Sincronização automática ativada."
        echo "   Para desativar: launchctl unload ~/Library/LaunchAgents/com.claude.backup.plist"
        ;;
    
    3)
        echo "⏰ Configurando cron..."
        # Adicionar ao crontab
        (crontab -l 2>/dev/null; echo "*/5 * * * * rsync -av --delete --exclude='*.log' --exclude='node_modules/' /Users/agents/.claude/ '/Users/agents/Library/CloudStorage/GoogleDrive-diegodg3web@gmail.com/Meu Drive/claude_backup/'") | crontab -
        echo "✅ Cron configurado! Sincronização a cada 5 minutos."
        echo "   Para ver: crontab -l"
        echo "   Para remover: crontab -r"
        ;;
esac

echo ""
echo "🎉 Pronto! Verifique se o arquivo BACKUP_GDRIVE_SUCESSO.md aparece no Google Drive."