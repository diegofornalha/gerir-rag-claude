#!/bin/bash
#
# LightRAG - Script de Manutenção Unificado
# Consolida funcionalidades de clean_pids.sh, cleanup.sh e limpar_banco.sh
#

# Diretório do script e diretório base
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR" || { echo "Erro ao acessar diretório base"; exit 1; }

# Diretórios importantes
PID_DIR="$BASE_DIR/.pids"
BACKUP_DIR="$BASE_DIR/backups"
LOG_DIR="$BASE_DIR/logs"
OBSOLETE_DIR="$BASE_DIR/obsolete"

# Criar diretórios necessários
mkdir -p "$PID_DIR" "$BACKUP_DIR" "$LOG_DIR" "$OBSOLETE_DIR"

# Data e timestamp para backups
DATE_FORMAT=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="lightrag_backup_$DATE_FORMAT.tar.gz"
DB_BACKUP_NAME="lightrag_db_$DATE_FORMAT.json"

# Mostrar menu interativo
show_menu() {
    clear
    echo "=============================="
    echo "🛠️  LightRAG - Ferramenta de Manutenção"
    echo "=============================="
    echo ""
    echo "Selecione uma opção:"
    echo "  1) Limpar e organizar arquivos PID"
    echo "  2) Limpar arquivos temporários e cache"
    echo "  3) Criar backup do sistema"
    echo "  4) Limpar e reiniciar banco de dados"
    echo "  5) Gerenciar processos LightRAG"
    echo "  6) Verificar integridade do sistema"
    echo "  7) Executar todas as tarefas de manutenção"
    echo "  0) Sair"
    echo ""
    read -p "Opção: " choice
    echo ""
    return "$choice"
}

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

# Função para limpar arquivos PID
clean_pids() {
    echo "=== Limpeza de arquivos PID do LightRAG ==="
    echo "Diretório base: $BASE_DIR"
    echo "Diretório PID: $PID_DIR"
    
    # Procurar e remover/migrar PIDs antigos
    echo
    echo "Verificando PIDs antigos..."
    
    # Lista de mapeamentos (arquivo antigo -> arquivo novo)
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
}

# Função para limpar arquivos temporários e cache
clean_temp_files() {
    echo "=== Limpeza de Arquivos Temporários e Cache ==="
    
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
    
    echo
    echo "Limpeza de arquivos temporários concluída."
}

# Função para criar backup do sistema
create_backup() {
    echo "=== Criando Backup do Sistema LightRAG ==="
    
    # Criar backup do banco de dados
    echo "Criando backup do banco de dados..."
    DB_FILE="$BASE_DIR/lightrag_db.json"
    if [ -f "$DB_FILE" ]; then
        cp "$DB_FILE" "$BACKUP_DIR/$DB_BACKUP_NAME"
        echo "Backup do banco de dados criado: $BACKUP_DIR/$DB_BACKUP_NAME"
    else
        echo "Arquivo de banco de dados não encontrado: $DB_FILE"
    fi
    
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
        -C "$BASE_DIR" .
    
    echo "Backup completo criado: $BACKUP_DIR/$BACKUP_NAME"
    
    # Remover backups antigos (mais de 30 dias)
    echo
    echo "Removendo backups antigos..."
    find "$BACKUP_DIR" -name "lightrag_backup_*.tar.gz" -mtime +30 -delete
    
    echo
    echo "Backup concluído com sucesso."
}

# Função para limpar e reiniciar o banco de dados
clean_database() {
    echo "=== Limpar e Reiniciar Banco de Dados ==="
    echo
    echo "Este processo irá:"
    echo "  1. Criar um backup do banco de dados atual"
    echo "  2. Limpar completamente o banco de dados"
    echo "  3. Opcionalmente, reiniciar os serviços LightRAG"
    echo
    echo "⚠️  ATENÇÃO: Todos os documentos serão removidos do banco de dados!"
    echo
    
    read -p "Deseja continuar? (s/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Operação cancelada pelo usuário."
        return
    fi
    
    # Criar backup do banco de dados
    DB_FILE="$BASE_DIR/lightrag_db.json"
    if [ -f "$DB_FILE" ]; then
        echo "Criando backup do banco de dados..."
        cp "$DB_FILE" "$BACKUP_DIR/$DB_BACKUP_NAME"
        echo "Backup criado: $BACKUP_DIR/$DB_BACKUP_NAME"
        
        # Limpar banco de dados
        echo
        echo "Limpando banco de dados..."
        echo '{"documents":[],"lastUpdated":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}' > "$DB_FILE"
        echo "Banco de dados limpo com sucesso."
        
        # Perguntar se deseja reiniciar serviços
        echo
        read -p "Deseja reiniciar os serviços LightRAG? (s/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            echo "Reiniciando serviços..."
            if [ -f "$BASE_DIR/start_lightrag_service.sh" ]; then
                "$BASE_DIR/start_lightrag_service.sh" restart
                echo "Serviços reiniciados com sucesso."
            else
                echo "Script de inicialização não encontrado: $BASE_DIR/start_lightrag_service.sh"
            fi
        fi
    else
        echo "Erro: Arquivo de banco de dados não encontrado: $DB_FILE"
    fi
    
    echo
    echo "Operação concluída."
}

# Função para gerenciar processos LightRAG
manage_processes() {
    echo "=== Gerenciamento de Processos LightRAG ==="
    
    # Verificar se o script process_manager.py existe
    if [ -f "$BASE_DIR/process_manager.py" ]; then
        # Apresentar opções
        echo
        echo "Opções disponíveis:"
        echo "  1) Verificar status dos processos"
        echo "  2) Limpar processos duplicados"
        echo "  3) Verificar integridade do sistema"
        echo
        read -p "Escolha uma opção (1-3): " -n 1 -r
        echo
        
        case $REPLY in
            1)
                echo "Verificando status dos processos..."
                python "$BASE_DIR/process_manager.py" --status
                ;;
            2)
                echo "Limpando processos duplicados..."
                python "$BASE_DIR/process_manager.py" --clean
                ;;
            3)
                echo "Verificando integridade do sistema..."
                python "$BASE_DIR/process_manager.py" --verify
                ;;
            *)
                echo "Opção inválida."
                ;;
        esac
    else
        echo "Erro: Script process_manager.py não encontrado."
    fi
    
    echo
    echo "Gerenciamento de processos concluído."
}

# Função para verificar integridade do sistema
check_system_integrity() {
    echo "=== Verificação de Integridade do Sistema LightRAG ==="
    
    # Lista de componentes a verificar
    echo
    echo "Verificando componentes principais..."
    components=(
        "$BASE_DIR/lightrag_db.json"
        "$BASE_DIR/start_lightrag_service.sh"
        "$BASE_DIR/process_manager.py"
        "$BASE_DIR/unified_monitor.py"
    )
    
    all_good=true
    
    for component in "${components[@]}"; do
        if [ -f "$component" ]; then
            echo "✅ $component: OK"
        else
            echo "❌ $component: Não encontrado"
            all_good=false
        fi
    done
    
    # Verificar diretórios essenciais
    echo
    echo "Verificando diretórios essenciais..."
    directories=(
        "$PID_DIR"
        "$LOG_DIR"
        "$BASE_DIR/api"
        "$BASE_DIR/core"
        "$BASE_DIR/tools"
        "$BASE_DIR/ui"
    )
    
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            echo "✅ $dir: OK"
        else
            echo "❌ $dir: Não encontrado"
            all_good=false
        fi
    done
    
    # Verificar processos ativos
    echo
    echo "Verificando processos ativos..."
    
    server_running=false
    ui_running=false
    
    # Verificar servidor
    if [ -f "$PID_DIR/lightrag_server.pid" ]; then
        server_pid=$(cat "$PID_DIR/lightrag_server.pid")
        if is_running "$server_pid"; then
            echo "✅ Servidor LightRAG: Ativo (PID: $server_pid)"
            server_running=true
        else
            echo "❌ Servidor LightRAG: Inativo (PID inválido: $server_pid)"
        fi
    else
        echo "❌ Servidor LightRAG: Não iniciado (arquivo PID não existe)"
    fi
    
    # Verificar interface
    if [ -f "$PID_DIR/lightrag_ui.pid" ]; then
        ui_pid=$(cat "$PID_DIR/lightrag_ui.pid")
        if is_running "$ui_pid"; then
            echo "✅ Interface LightRAG: Ativa (PID: $ui_pid)"
            ui_running=true
        else
            echo "❌ Interface LightRAG: Inativa (PID inválido: $ui_pid)"
        fi
    else
        echo "❌ Interface LightRAG: Não iniciada (arquivo PID não existe)"
    fi
    
    # Resumo
    echo
    if $all_good && $server_running && $ui_running; then
        echo "✅ Sistema íntegro: Todos os componentes verificados estão OK."
    else
        echo "⚠️  Sistema com problemas: Alguns componentes não estão íntegros."
        
        if ! $server_running; then
            echo "  - Servidor LightRAG não está ativo"
        fi
        
        if ! $ui_running; then
            echo "  - Interface LightRAG não está ativa"
        fi
        
        echo 
        echo "Recomendação: Execute o script de reinicialização:"
        echo "  $BASE_DIR/start_lightrag_service.sh restart"
    fi
    
    echo
    echo "Verificação de integridade concluída."
}

# Executar todas as tarefas de manutenção
run_all_maintenance() {
    echo "=== Executando Todas as Tarefas de Manutenção ==="
    echo
    
    clean_pids
    echo
    
    clean_temp_files
    echo
    
    create_backup
    echo
    
    check_system_integrity
    echo
    
    # Perguntar se deseja limpar o banco de dados
    read -p "Deseja limpar o banco de dados também? (s/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        clean_database
    fi
    
    echo
    echo "Todas as tarefas de manutenção foram concluídas."
}

# Verificar argumentos de linha de comando
if [ "$#" -gt 0 ]; then
    case "$1" in
        --clean-pids)
            clean_pids
            ;;
        --clean-temp)
            clean_temp_files
            ;;
        --backup)
            create_backup
            ;;
        --clean-db)
            clean_database
            ;;
        --manage-processes)
            manage_processes
            ;;
        --check-integrity)
            check_system_integrity
            ;;
        --all)
            run_all_maintenance
            ;;
        --help)
            echo "Uso: $0 [OPÇÃO]"
            echo "Opções:"
            echo "  --clean-pids       Limpar e organizar arquivos PID"
            echo "  --clean-temp       Limpar arquivos temporários e cache"
            echo "  --backup           Criar backup do sistema"
            echo "  --clean-db         Limpar e reiniciar banco de dados"
            echo "  --manage-processes Gerenciar processos LightRAG"
            echo "  --check-integrity  Verificar integridade do sistema"
            echo "  --all              Executar todas as tarefas de manutenção"
            echo "  --help             Exibir esta ajuda"
            echo
            echo "Sem opções, exibe o menu interativo."
            exit 0
            ;;
        *)
            echo "Opção desconhecida: $1"
            echo "Use --help para mais informações."
            exit 1
            ;;
    esac
    exit 0
fi

# Menu interativo
while true; do
    show_menu
    choice=$?
    
    case $choice in
        0)
            echo "Encerrando..."
            exit 0
            ;;
        1)
            clean_pids
            ;;
        2)
            clean_temp_files
            ;;
        3)
            create_backup
            ;;
        4)
            clean_database
            ;;
        5)
            manage_processes
            ;;
        6)
            check_system_integrity
            ;;
        7)
            run_all_maintenance
            ;;
        *)
            echo "Opção inválida. Tente novamente."
            ;;
    esac
    
    echo
    read -p "Pressione Enter para continuar..."
done