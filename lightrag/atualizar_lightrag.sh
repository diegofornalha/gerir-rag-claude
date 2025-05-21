#!/bin/bash

# Script para atualizar o LightRAG com as melhorias de verificação de documentos
# Autor: Diego (via Claude)
# Data: $(date +%Y-%m-%d)

echo "=== Atualizando LightRAG com verificação avançada de documentos duplicados ==="
echo

# Diretório base do LightRAG
LIGHTRAG_DIR=$(dirname "$0")
cd "$LIGHTRAG_DIR" || { echo "Não foi possível acessar o diretório LightRAG"; exit 1; }

# Verificar se o servidor está rodando
if pgrep -f "python.*micro_lightrag.py" > /dev/null; then
    echo "⚠️ O servidor LightRAG está em execução."
    echo "Recomenda-se parar o servidor antes de atualizar os arquivos."
    read -p "Deseja continuar mesmo assim? (s/N): " response
    if [[ ! "$response" =~ ^[sSyY]$ ]]; then
        echo "Atualização cancelada."
        exit 0
    fi
fi

# Fazer backup dos arquivos originais
echo "📦 Criando backups dos arquivos originais..."
BACKUP_DIR="$LIGHTRAG_DIR/backups_$(date +%Y%m%d%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Arquivos para fazer backup
BACKUP_FILES=(
    "lightrag_mcp.py"
    "insert_to_rag.py"
)

for file in "${BACKUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/" && echo "✅ Backup de $file criado"
    fi
done

# Verificar se os novos arquivos existem
REQUIRED_FILES=(
    "improved_rag_insert_file.py"
    "lightrag_mcp_improved.py"
    "insert_to_rag_improved.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Arquivo $file não encontrado. Atualização cancelada."
        exit 1
    fi
done

# Instalar pacotes Python necessários
echo "📦 Verificando dependências..."
pip install --quiet hashlib || echo "⚠️ Aviso: não foi possível instalar o pacote hashlib (pode já estar incluído no Python padrão)"

# Atualizar arquivos
echo "🔄 Atualizando arquivos do sistema..."

# Atualizar o cliente MCP
echo "Atualizando lightrag_mcp.py..."
cp lightrag_mcp_improved.py lightrag_mcp.py && echo "✅ lightrag_mcp.py atualizado"

# Atualizar o script de inserção
echo "Atualizando insert_to_rag.py..."
cp insert_to_rag_improved.py insert_to_rag.py && echo "✅ insert_to_rag.py atualizado"

# Adicionar permissão de execução aos scripts
chmod +x improved_rag_insert_file.py
chmod +x test_improved_rag_insert.py
chmod +x insert_to_rag_improved.py

echo
echo "✅ Atualização concluída com sucesso!"
echo
echo "Novos arquivos:"
echo "- improved_rag_insert_file.py: Implementação principal da verificação avançada"
echo "- test_improved_rag_insert.py: Testes para verificar o funcionamento"
echo "- documentacao_melhorias.md: Documentação detalhada das melhorias"
echo
echo "Arquivos atualizados:"
echo "- lightrag_mcp.py: Cliente MCP com funcionalidade melhorada"
echo "- insert_to_rag.py: Script de linha de comando atualizado"
echo
echo "Backups criados em: $BACKUP_DIR"
echo
echo "Para testar a nova funcionalidade, execute:"
echo "  python test_improved_rag_insert.py [caminho_arquivo_opcional]"
echo
echo "Para reverter a atualização, execute:"
echo "  cp $BACKUP_DIR/lightrag_mcp.py ."
echo "  cp $BACKUP_DIR/insert_to_rag.py ."
echo
echo "Documentação disponível em: documentacao_melhorias.md"