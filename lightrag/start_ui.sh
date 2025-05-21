#!/bin/bash
#
# Inicializador da interface Streamlit para LightRAG usando nova arquitetura
#

# Obter diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar dependências
python3 -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Streamlit não encontrado, instalando..."
    python3 -m pip install streamlit
fi

# Criar diretório de logs se não existir
mkdir -p "$SCRIPT_DIR/logs"

# Encerrar instâncias existentes
echo "Verificando se já existe uma instância rodando..."
if pgrep -f "streamlit.*ui[/.]app" > /dev/null; then
    echo "Encerrando instância existente..."
    pkill -f "streamlit.*ui[/.]app"
    sleep 1
fi

# Verificar se o servidor Flask está em execução
if ! curl -s "http://127.0.0.1:5000/status" > /dev/null; then
    echo "O servidor LightRAG não está rodando. Iniciando..."
    "$SCRIPT_DIR/start_flask_lightrag.sh"
    sleep 2
fi

# Iniciar interface Streamlit usando a nova estrutura modular
echo "Iniciando interface LightRAG (nova arquitetura)..."
cd "$SCRIPT_DIR"

# Iniciar Streamlit em segundo plano
nohup streamlit run "$SCRIPT_DIR/ui/app.py" > "$SCRIPT_DIR/logs/streamlit.log" 2>&1 &
PID=$!

# Salvar PID e verificar inicialização
echo $PID > "$SCRIPT_DIR/.lightrag_ui.pid"
sleep 2

# Verificar se a interface Streamlit iniciou corretamente
if kill -0 $PID 2>/dev/null; then
    echo "✓ Interface LightRAG iniciada com sucesso (PID: $PID)"
    echo "  UI disponível em: http://localhost:8501"
    echo "  Logs em: $SCRIPT_DIR/logs/streamlit.log"
else
    echo "✗ Falha ao iniciar interface LightRAG"
    cat "$SCRIPT_DIR/logs/streamlit.log"
    exit 1
fi

exit 0