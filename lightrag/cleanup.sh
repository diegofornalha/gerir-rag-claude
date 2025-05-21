#!/bin/bash
#
# Script para limpar e arquivar arquivos obsoletos
# e criar uma estrutura de backups regulares

# Diretório base
BASE_DIR="$(dirname "$(readlink -f "$0")")"
cd "$BASE_DIR" || { echo "Erro ao acessar diretório base"; exit 1; }

# Diretório de backups
BACKUP_DIR="$BASE_DIR/backups"
mkdir -p "$BACKUP_DIR"

# Data e timestamp para backups
DATE_FORMAT=$(date +"%Y%m%d")
BACKUP_NAME="lightrag_backup_$DATE_FORMAT.tar.gz"

echo "=== LightRAG Cleanup e Backup ==="
echo "Diretório base: $BASE_DIR"

# Verificar arquivos obsoletos
echo
echo "Verificando arquivos obsoletos..."

# Lista de padrões de arquivos obsoletos
OBSOLETE_PATTERNS=(
    "*.pid"
    ".*.pid"
    "*~"
    "*.pyc"
    "*.bak*"
    "*.swp"
    ".DS_Store"
    "__pycache__"
)

# Procurar e contar arquivos obsoletos
total_obsolete=0

for pattern in "${OBSOLETE_PATTERNS[@]}"; do
    count=$(find "$BASE_DIR" -name "$pattern" -not -path "$BASE_DIR/obsolete/*" | wc -l)
    count_trimmed=$(echo "$count" | tr -d '[:space:]')
    
    if [ "$count_trimmed" -gt 0 ]; then
        echo "Encontrados $count_trimmed arquivos do tipo: $pattern"
        total_obsolete=$((total_obsolete + count_trimmed))
    fi
done

# Limpar arquivos __pycache__ e .pyc
echo
echo "Removendo arquivos de cache Python..."
find "$BASE_DIR" -name "__pycache__" -type d -exec rm -rf {} +
find "$BASE_DIR" -name "*.pyc" -delete

# Limpar arquivos temporários e backups antigos no diretório principal
echo "Removendo arquivos temporários..."
find "$BASE_DIR" -maxdepth 1 -name "*.tmp" -delete
find "$BASE_DIR" -maxdepth 1 -name "*.bak*" -mtime +7 -delete

# Criar backup do banco de dados
echo
echo "Criando backup do banco de dados..."
python3 "$BASE_DIR/tools/migration_tools.py" backup

# Compactar todos os arquivos importantes
echo
echo "Criando backup completo do sistema..."
tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    --exclude="*.pid" \
    --exclude=".*.pid" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="*.swp" \
    --exclude=".DS_Store" \
    --exclude="backups/*" \
    --exclude="obsolete/*" \
    --exclude="*.tmp" \
    .

echo "Backup criado: $BACKUP_DIR/$BACKUP_NAME"

# Remover backups antigos (mais de 30 dias)
echo
echo "Removendo backups antigos..."
find "$BACKUP_DIR" -name "lightrag_backup_*.tar.gz" -mtime +30 -delete

echo
echo "Limpeza concluída."
echo "Arquivos temporários removidos, backup criado e arquivos antigos removidos."