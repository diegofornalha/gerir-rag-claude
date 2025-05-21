#!/bin/bash

# Script para testar o Gerenciador de Duplicatas do LightRAG

# Caminho para o script
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
DUPLICATE_MANAGER="$SCRIPT_DIR/duplicate_manager.py"

# Verificar se o script existe
if [ ! -f "$DUPLICATE_MANAGER" ]; then
    echo "❌ Erro: Script duplicate_manager.py não encontrado em $SCRIPT_DIR"
    exit 1
fi

# Tornar o script executável
chmod +x "$DUPLICATE_MANAGER"

echo "=== Testando LightRAG Duplicate Manager ==="
echo

# Mostrar estatísticas
echo "🔍 Exibindo estatísticas atuais:"
python "$DUPLICATE_MANAGER" --stats
echo

# Simular consolidação
echo "🧪 Simulando consolidação de documentos de conversas:"
python "$DUPLICATE_MANAGER" --consolidate --dry-run
echo

# Simular remoção de duplicatas de conteúdo
echo "🧪 Simulando remoção de documentos com conteúdo duplicado:"
python "$DUPLICATE_MANAGER" --remove-content-duplicates --dry-run
echo

# Simular remoção de duplicatas de arquivo
echo "🧪 Simulando remoção de documentos referentes ao mesmo arquivo:"
python "$DUPLICATE_MANAGER" --remove-file-duplicates --dry-run
echo

echo "✅ Testes concluídos com sucesso!"
echo "Para executar operações reais, remova a opção --dry-run"
echo
echo "Exemplos de uso:"
echo "  python $DUPLICATE_MANAGER --consolidate"
echo "  python $DUPLICATE_MANAGER --remove-content-duplicates"
echo "  python $DUPLICATE_MANAGER --all"