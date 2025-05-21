#!/bin/bash

# Script para limpar nomes personalizados obsoletos no sistema LightRAG
# Autor: Diego/Claude
# Data: 21/05/2025

echo "=== Limpeza de Nomes Personalizados do LightRAG ==="
echo ""

# Verificar se o arquivo Python existe
if [ ! -f "/Users/agents/.claude/lightrag/ui/clean_custom_names.py" ]; then
    echo "Erro: Script de limpeza não encontrado!"
    exit 1
fi

# Verificar primeiro quais nomes seriam removidos (modo de simulação)
echo "Verificando nomes personalizados obsoletos..."
python /Users/agents/.claude/lightrag/ui/clean_custom_names.py --dry-run

# Perguntar se deseja prosseguir com a limpeza
echo ""
read -p "Deseja prosseguir com a limpeza dos nomes obsoletos? (s/N): " resposta

if [[ "$resposta" =~ ^[Ss]$ ]]; then
    echo ""
    echo "Iniciando limpeza..."
    python /Users/agents/.claude/lightrag/ui/clean_custom_names.py
    
    # Verificar se a limpeza foi concluída com sucesso
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Limpeza concluída com sucesso!"
        echo ""
        echo "Nomes personalizados atuais:"
        python /Users/agents/.claude/lightrag/ui/list_custom_docs.py list
    else
        echo ""
        echo "❌ Erro durante a limpeza!"
    fi
else
    echo ""
    echo "Limpeza cancelada pelo usuário."
fi

echo ""
echo "=== Fim do processo de limpeza ==="