#!/bin/bash
#
# Inicializador LightRAG com carregamento automático de projetos
#

# Obter diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar se o LightRAG está rodando
if ! curl -s "http://127.0.0.1:5000/status" > /dev/null; then
    echo "O servidor LightRAG não está rodando. Iniciando..."
    ./compact start
    sleep 2
fi

# Carregar automaticamente os projetos
echo "Carregando projetos na base LightRAG..."
python3 load_projects.py

# Iniciar a interface Streamlit
echo "Iniciando interface web do LightRAG..."
./start_ui.sh

echo "LightRAG inicializado com sucesso!"