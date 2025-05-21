#!/bin/bash
#
# Script para resincronizar bancos de dados LightRAG
# Este script força uma limpeza completa e reconstrução da sincronização

# Diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Executar script Python
echo "Iniciando resincronização..."
python3 resync_databases.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo "✅ Resincronização concluída com sucesso!"
else
    echo "❌ Houve problemas na resincronização, verifique os logs."
fi

echo ""
echo "O LightRAG está disponível em: http://localhost:8501"