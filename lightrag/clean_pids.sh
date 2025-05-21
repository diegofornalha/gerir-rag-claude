#!/bin/bash

# Script para limpar e consolidar arquivos PID
# Este script remove arquivos PID obsoletos e organiza em uma estrutura centralizada

# Diretório base
BASE_DIR="$(dirname "$(readlink -f "$0")")"
cd "$BASE_DIR" || { echo "Erro ao acessar diretório base"; exit 1; }

# Diretório centralizado para PIDs
PID_DIR="$BASE_DIR/.pids"
mkdir -p "$PID_DIR"

# Função para verificar se um processo está rodando
is_running() {
    local pid=$1
    if [ -n "$pid" ] && [ "$pid" -gt 0 ]; then
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Está rodando
        fi
    fi
    return 1  # Não está rodando
}

# Função para migrar PIDs válidos
migrate_pid() {
    local old_file=$1
    local new_file=$2
    
    if [ -f "$old_file" ]; then
        local pid
        pid=$(cat "$old_file")
        
        # Verificar se o processo está rodando
        if is_running "$pid"; then
            echo "Migrando PID $pid de $old_file para $new_file"
            echo "$pid" > "$new_file"
        else
            echo "Removendo PID inválido: $old_file (PID: $pid não está rodando)"
        fi
        
        # Remover arquivo antigo
        rm -f "$old_file"
    fi
}

echo "=== Limpeza de arquivos PID do LightRAG ==="
echo "Diretório base: $BASE_DIR"
echo "Diretório PID: $PID_DIR"

# Procurar e remover/migrar PIDs antigos
echo
echo "Verificando PIDs antigos..."

# Lista de mapeamentos (arquivo antigo -> arquivo novo)
# Usamos arrays simples em vez de associativos para maior compatibilidade
OLD_FILES=(
    "$BASE_DIR/.lightrag.pid"
    "$BASE_DIR/.lightrag_flask.pid"
    "$BASE_DIR/.server.pid"
    "$BASE_DIR/.streamlit.pid"
    "$BASE_DIR/.lightrag_ui.pid"
    "$BASE_DIR/.improved_monitor.pid"
    "$BASE_DIR/.monitor.pid"
)

NEW_FILES=(
    "$PID_DIR/lightrag_server.pid"
    "$PID_DIR/lightrag_server.pid"
    "$PID_DIR/lightrag_server.pid"
    "$PID_DIR/lightrag_ui.pid"
    "$PID_DIR/lightrag_ui.pid"
    "$PID_DIR/lightrag_monitor.pid"
    "$PID_DIR/lightrag_monitor.pid"
)

# Processar cada mapeamento
for i in "${!OLD_FILES[@]}"; do
    old_file="${OLD_FILES[$i]}"
    new_file="${NEW_FILES[$i]}"
    if [ -f "$old_file" ]; then
        migrate_pid "$old_file" "$new_file"
    fi
done

# Verificar outros arquivos PID não mapeados
echo
echo "Verificando outros arquivos PID não mapeados..."
find "$BASE_DIR" -maxdepth 1 -name "*.pid" -o -name ".*.pid" | while read -r pid_file; do
    if [ -f "$pid_file" ]; then
        echo "Encontrado PID não mapeado: $pid_file"
        pid=$(cat "$pid_file")
        
        if is_running "$pid"; then
            echo "  Processo $pid está rodando"
            # Determinar tipo de PID com base no nome do processo
            process_cmd=$(ps -p "$pid" -o command= | tr -s ' ' | cut -d' ' -f1)
            process_name=$(basename "$process_cmd")
            
            new_file=""
            if [[ "$process_name" == *"python"* ]] || [[ "$process_name" == *"flask"* ]]; then
                if ps -p "$pid" -o command= | grep -q "server"; then
                    new_file="$PID_DIR/lightrag_server.pid"
                elif ps -p "$pid" -o command= | grep -q "monitor"; then
                    new_file="$PID_DIR/lightrag_monitor.pid"
                else
                    new_file="$PID_DIR/unknown_python_$(basename "$pid_file")"
                fi
            elif [[ "$process_name" == *"streamlit"* ]]; then
                new_file="$PID_DIR/lightrag_ui.pid"
            else
                new_file="$PID_DIR/unknown_$(basename "$pid_file")"
            fi
            
            if [ -n "$new_file" ]; then
                echo "  Migrando para $new_file"
                echo "$pid" > "$new_file"
            fi
        else
            echo "  Processo $pid não está rodando, removendo arquivo"
        fi
        
        # Remover arquivo antigo
        rm -f "$pid_file"
    fi
done

# Verificar PIDs no diretório centralizado
echo
echo "Verificando PIDs no diretório centralizado..."
find "$PID_DIR" -name "*.pid" | while read -r pid_file; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ! is_running "$pid"; then
            echo "Removendo PID inválido: $pid_file (PID: $pid não está rodando)"
            rm -f "$pid_file"
        else
            echo "PID válido: $pid_file (PID: $pid está rodando)"
        fi
    fi
done

echo
echo "Limpeza de PIDs concluída."