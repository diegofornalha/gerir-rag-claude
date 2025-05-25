#!/bin/bash

# Script para sincronização automática em tempo real
# Monitora mudanças e sincroniza imediatamente

echo "🚀 Iniciando sincronização automática .claude → Google Drive"

SOURCE="/Users/agents/.claude"
DEST="/Users/agents/Library/CloudStorage/GoogleDrive-diegodg3web@gmail.com/Meu Drive/claude_backup"

# Fazer sync inicial
echo "📦 Sincronização inicial..."
rsync -av --delete \
    --exclude='*.log' \
    --exclude='*.pid' \
    --exclude='node_modules/' \
    --exclude='__pycache__/' \
    --exclude='.DS_Store' \
    --exclude='*.lock' \
    "$SOURCE/" "$DEST/"

echo "✅ Sincronização inicial completa!"
echo ""
echo "👀 Monitorando mudanças em tempo real..."
echo "   Pressione Ctrl+C para parar"
echo ""

# Usar fswatch para monitorar mudanças (macOS)
fswatch -r -e ".*\.log$" -e ".*\.pid$" -e "node_modules" -e "__pycache__" -e "\.DS_Store" "$SOURCE" | while read file
do
    echo "📝 Mudança detectada: $file"
    
    # Sincronizar apenas o arquivo modificado
    rel_path="${file#$SOURCE/}"
    
    if [ -f "$file" ]; then
        # É um arquivo
        dest_dir=$(dirname "$DEST/$rel_path")
        mkdir -p "$dest_dir"
        cp "$file" "$DEST/$rel_path"
        echo "✅ Sincronizado: $rel_path"
    elif [ ! -e "$file" ]; then
        # Foi deletado
        rm -f "$DEST/$rel_path"
        echo "🗑️  Removido: $rel_path"
    fi
done