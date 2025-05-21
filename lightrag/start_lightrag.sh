#!/bin/bash
#
# Inicializador unificado LightRAG com nova arquitetura
#

# Obter diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Tornar os scripts executáveis
chmod +x "$SCRIPT_DIR/start_flask_lightrag_new.sh"
chmod +x "$SCRIPT_DIR/start_ui_new.sh"

# Verificar se o servidor Flask está rodando
if ! curl -s "http://127.0.0.1:5000/status" > /dev/null; then
    echo "O servidor LightRAG não está rodando. Iniciando..."
    "$SCRIPT_DIR/start_flask_lightrag_new.sh"
    sleep 2
fi

# Verificar se tudo foi inicializado corretamente
if ! curl -s "http://127.0.0.1:5000/status" > /dev/null; then
    echo "✗ Falha ao iniciar servidor LightRAG"
    exit 1
fi

# Iniciar a interface Streamlit
echo "Iniciando interface web do LightRAG..."
"$SCRIPT_DIR/start_ui_new.sh"

# Se chegarmos aqui, tudo foi iniciado com sucesso
echo "✓ LightRAG inicializado com sucesso!"
echo
echo "Servidor API: http://127.0.0.1:5000"
echo "Interface Web: http://localhost:8501"
echo
echo "Para usar via MCP no Claude:"
echo "from claude import MCP"
echo "lightrag = MCP.connect_to_service('lightrag')"
echo "lightrag.rag_insert_text(text=\"Texto para adicionar à base\")"
echo "resultado = lightrag.rag_query(query=\"Sua pergunta\")"
echo

exit 0