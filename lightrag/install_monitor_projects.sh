#!/bin/bash

# Script para instalar o monitor de projetos como serviço no macOS
# Este script configura o monitor para ser executado automaticamente
# ao iniciar o sistema

# Diretório do projeto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Definir caminhos
SERVICE_NAME="com.user.lightrag_monitor.plist"
SERVICE_PATH="$HOME/Library/LaunchAgents/$SERVICE_NAME"
MONITOR_SCRIPT="$SCRIPT_DIR/start_monitor_projects.sh"

# Criar arquivo de serviço plist
echo "Criando arquivo de serviço..."
cat > "$SERVICE_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.lightrag_monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$MONITOR_SCRIPT</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/logs/lightrag_monitor_output.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/logs/lightrag_monitor_error.log</string>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
</dict>
</plist>
EOF

# Definir permissões
echo "Ajustando permissões..."
chmod 644 "$SERVICE_PATH"
chmod +x "$MONITOR_SCRIPT"

# Verificar se already loaded e descarregar se necessário
if launchctl list | grep -q "com.user.lightrag_monitor"; then
    echo "Descarregando serviço existente..."
    launchctl unload "$SERVICE_PATH"
fi

# Carregar o serviço
echo "Carregando serviço..."
launchctl load "$SERVICE_PATH"

# Verificar status
if launchctl list | grep -q "com.user.lightrag_monitor"; then
    echo "✅ Serviço instalado e carregado com sucesso!"
    echo "O monitor de projetos será iniciado automaticamente na próxima inicialização do sistema."
    echo "Para iniciar agora, execute: ./start_monitor_projects.sh"
else
    echo "❌ Falha ao instalar serviço. Verifique os logs para mais detalhes."
fi