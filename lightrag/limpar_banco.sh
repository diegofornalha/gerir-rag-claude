#!/bin/bash
#
# Script para limpar e resincronizar o banco de dados LightRAG
# Versão 2.0 - Utiliza o novo sistema de sincronização aprimorado

# Diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================"
echo "🧹 LIMPEZA E RESINCRONIZAÇÃO"
echo "============================"
echo ""

# Verificar se o script de resincronização existe
if [ ! -f "$SCRIPT_DIR/resync.sh" ]; then
    echo "❌ Script de resincronização não encontrado!"
    echo "Por favor, verifique se o arquivo resync.sh está no diretório $SCRIPT_DIR"
    exit 1
fi

echo "Este script irá:"
echo "  1. Parar todos os serviços LightRAG"
echo "  2. Limpar completamente o banco de dados"
echo "  3. Reiniciar todos os serviços"
echo "  4. Reindexar apenas os arquivos existentes no sistema"
echo ""
echo "⚠️  ATENÇÃO: Todos os documentos serão removidos do banco de dados!"
echo ""

read -p "Deseja continuar? (s/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Operação cancelada pelo usuário."
    exit 0
fi

echo ""
echo "Iniciando limpeza..."
echo ""

# Executar script de resincronização
"$SCRIPT_DIR/resync.sh"

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Limpeza e resincronização concluídas com sucesso!"
    echo "  ✅ Banco de dados limpo"
    echo "  ✅ Arquivos reindexados"
    echo "  ✅ Serviços reiniciados"
    echo ""
    echo "Acesse a interface em: http://localhost:8501"
    echo ""
else
    echo ""
    echo "❌ Ocorreu um erro durante a limpeza e resincronização!"
    echo "Por favor, verifique os logs para mais detalhes:"
    echo "  $SCRIPT_DIR/logs/resync.log"
    echo ""
fi

exit 0