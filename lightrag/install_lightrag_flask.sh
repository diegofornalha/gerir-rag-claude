#!/bin/bash

# Script para instalar o servidor LightRAG Flask como serviço no macOS
# Esta é a instalação permanente que fará o LightRAG iniciar automaticamente

# Diretório base
BASE_DIR="/Users/agents/.claude"
cd "$BASE_DIR"

# Criar diretório de logs se não existir
mkdir -p "$BASE_DIR/logs"

# Verificar permissões dos scripts
chmod +x "$BASE_DIR/start_flask_lightrag.sh" "$BASE_DIR/micro_lightrag.py"

# Configurar o LaunchAgent
PLIST_FILE="$BASE_DIR/com.user.lightrag_flask.plist"
LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"

# Garantir que o diretório LaunchAgents existe
mkdir -p "$LAUNCHAGENTS_DIR"

# Copiar o arquivo plist
cp "$PLIST_FILE" "$LAUNCHAGENTS_DIR/"

# Descarregar qualquer versão anterior
launchctl unload "$LAUNCHAGENTS_DIR/com.user.lightrag_flask.plist" 2>/dev/null

# Carregar o LaunchAgent
launchctl load "$LAUNCHAGENTS_DIR/com.user.lightrag_flask.plist"

# Verificar se carregou
sleep 3
LOADED=$(launchctl list | grep com.user.lightrag_flask)
if [ -n "$LOADED" ]; then
    echo "Serviço LightRAG Flask instalado e carregado com sucesso!"
    echo "Agora o serviço será iniciado automaticamente toda vez que você fizer login."
    echo "Logs do serviço estão em $BASE_DIR/logs/"
    
    # Verificar se o serviço está respondendo
    sleep 3
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS http://127.0.0.1:8020/query)
    if [ "$RESPONSE" = "204" ]; then
        echo "O servidor LightRAG está respondendo corretamente!"
        
        # Testar consulta
        TEST_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"query":"teste de instalação"}' http://127.0.0.1:8020/query)
        echo "Teste de consulta: $TEST_RESPONSE"
    else
        echo "Aviso: O servidor pode não estar respondendo ainda. Aguarde alguns instantes."
    fi
else
    echo "Falha ao carregar o serviço. Tente iniciar manualmente com:"
    echo "$BASE_DIR/start_flask_lightrag.sh"
fi