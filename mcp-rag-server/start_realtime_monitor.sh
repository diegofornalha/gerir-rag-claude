#!/bin/bash

echo "🚀 Iniciando Monitor em Tempo Real do RAG"
echo "==========================================="

# Diretório do script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Verificar se o arquivo de requirements existe
if [ ! -f "requirements.txt" ]; then
    echo "📝 Criando arquivo requirements.txt..."
    cat > requirements.txt << EOF
numpy
scikit-learn
mcp
EOF
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    exit 1
fi

# Informações do sistema
echo "📊 Informações do Sistema:"
echo "  - Python: $(python3 --version)"
echo "  - Diretório: $DIR"
echo "  - Cache RAG: ~/.claude/mcp-rag-cache"

# Verificar se o cache existe
CACHE_DIR="$HOME/.claude/mcp-rag-cache"
if [ -d "$CACHE_DIR" ]; then
    DOC_COUNT=$(python3 -c "import json; docs=json.load(open('$CACHE_DIR/documents.json')); print(len(docs))" 2>/dev/null || echo "0")
    echo "  - Documentos no cache: $DOC_COUNT"
else
    echo "  - Cache não encontrado (será criado automaticamente)"
fi

echo ""
echo "⚙️ Iniciando monitor com polling..."
echo "  - Intervalo: 5 segundos"
echo "  - Monitorando: ~/.claude/sessions, ~/.claude/todos, ~/.claude/projects"
echo ""
echo "Pressione Ctrl+C para parar"
echo ""

# Executar o monitor
exec python3 monitor_polling.py --interval 5