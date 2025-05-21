#!/bin/bash
#
# Inicializador do servidor LightRAG usando nova arquitetura
#

# Obter diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar dependências
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Flask não encontrado, instalando..."
    python3 -m pip install flask
fi

# Criar diretório de logs se não existir
mkdir -p "$SCRIPT_DIR/logs"

# Encerrar instâncias existentes
echo "Verificando se já existe uma instância rodando..."
if pgrep -f "python.*api[/.]app" > /dev/null; then
    echo "Encerrando instância existente..."
    pkill -f "python.*api[/.]app"
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Iniciar servidor usando a nova estrutura modular
echo "Iniciando servidor LightRAG (nova arquitetura)..."
cd "$SCRIPT_DIR"

# Iniciar servidor em segundo plano
nohup python3 "$SCRIPT_DIR/api/app.py" > "$SCRIPT_DIR/logs/flask_lightrag.log" 2>&1 &
PID=$!

# Salvar PID e verificar inicialização
echo $PID > "$SCRIPT_DIR/.lightrag_flask.pid"
sleep 2

# Verificar se o servidor iniciou corretamente
if kill -0 $PID 2>/dev/null; then
    echo "✓ Servidor LightRAG iniciado com sucesso (PID: $PID)"
    echo "  API disponível em: http://127.0.0.1:5000"
    echo "  Logs em: $SCRIPT_DIR/logs/flask_lightrag.log"
else
    echo "✗ Falha ao iniciar servidor LightRAG"
    cat "$SCRIPT_DIR/logs/flask_lightrag.log"
    exit 1
fi

# Verificar status da API
sleep 1
if curl -s "http://127.0.0.1:5000/status" > /dev/null; then
    echo "✓ API respondendo corretamente"
    curl -s "http://127.0.0.1:5000/status" | python3 -m json.tool
else
    echo "✗ API não está respondendo"
    echo "  Verificando logs:"
    tail -n 20 "$SCRIPT_DIR/logs/flask_lightrag.log"
    exit 1
fi

exit 0