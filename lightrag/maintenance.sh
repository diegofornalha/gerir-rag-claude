#!/bin/bash

# Script para manutenção do LightRAG
# Executa operações de migração, limpeza e atualização

# Diretório base
BASE_DIR="$(dirname "$(readlink -f "$0")")"
cd "$BASE_DIR" || { echo "Erro ao acessar diretório base"; exit 1; }

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não encontrado. Por favor, instale o Python 3."
    exit 1
fi

# Verificar se a ferramenta de migração existe
if [ ! -f "$BASE_DIR/tools/migration_tools.py" ]; then
    echo "Erro: ferramenta de migração não encontrada."
    echo "Verifique se o arquivo tools/migration_tools.py existe."
    exit 1
fi

# Verificar se o gerenciador de processos existe
if [ ! -f "$BASE_DIR/process_manager.py" ]; then
    echo "Aviso: gerenciador de processos não encontrado."
    echo "Algumas funcionalidades podem não estar disponíveis."
fi

# Função para exibir ajuda
show_help() {
    echo "Manutenção do LightRAG"
    echo
    echo "Uso: $0 [OPÇÃO]"
    echo
    echo "Opções:"
    echo "  migrate      Migrar banco para IDs baseados em UUID"
    echo "  dedup        Remover documentos duplicados"
    echo "  patch        Aplicar patches de atualização"
    echo "  clean        Limpar arquivos temporários e PIDs"
    echo "  backup       Criar backup da base de dados"
    echo "  check        Verificar serviços e processos duplicados"
    echo "  fix          Corrigir processos duplicados automaticamente"
    echo "  restart      Reiniciar todos os serviços LightRAG"
    echo "  resync       Forçar ressincronização completa dos bancos de dados"
    echo "  all          Executar todas as operações (migração, dedup, patch, clean)"
    echo "  help         Exibir esta ajuda"
    echo
}

# Verificar número de argumentos
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# Processar argumentos
case "$1" in
    migrate)
        echo "Executando migração para UUIDs..."
        python3 "$BASE_DIR/tools/migration_tools.py" migrate-uuid
        ;;
    dedup)
        echo "Removendo documentos duplicados..."
        python3 "$BASE_DIR/tools/migration_tools.py" remove-duplicates --keep-newer
        ;;
    patch)
        echo "Aplicando patches..."
        python3 "$BASE_DIR/tools/migration_tools.py" apply-patches
        ;;
    clean)
        echo "Limpando arquivos temporários e PIDs..."
        bash "$BASE_DIR/clean_pids.sh"
        
        # Remover arquivos __pycache__
        find "$BASE_DIR" -name "__pycache__" -type d -exec rm -rf {} +
        find "$BASE_DIR" -name "*.pyc" -delete
        
        # Remover outros arquivos temporários
        find "$BASE_DIR" -name "*.tmp" -delete
        find "$BASE_DIR" -name "*.bak*" -mtime +7 -delete  # Backups com mais de 7 dias
        ;;
    backup)
        echo "Criando backup da base de dados..."
        python3 "$BASE_DIR/tools/migration_tools.py" backup
        ;;
    check)
        echo "Verificando serviços e processos duplicados..."
        if [ -f "$BASE_DIR/process_manager.py" ]; then
            python3 "$BASE_DIR/process_manager.py" --status --verify --verbose
        else
            echo "Erro: Gerenciador de processos não encontrado"
            exit 1
        fi
        ;;
    fix)
        echo "Corrigindo processos duplicados automaticamente..."
        if [ -f "$BASE_DIR/process_manager.py" ]; then
            python3 "$BASE_DIR/process_manager.py" --clean
            echo "Processos duplicados corrigidos."
        else
            echo "Erro: Gerenciador de processos não encontrado"
            exit 1
        fi
        ;;
    restart)
        echo "Reiniciando serviços LightRAG..."
        if [ -f "$BASE_DIR/manage_processes.sh" ]; then
            bash "$BASE_DIR/manage_processes.sh" restart
        elif [ -f "$BASE_DIR/start_lightrag_service.sh" ]; then
            bash "$BASE_DIR/start_lightrag_service.sh" restart
        else
            echo "Erro: Scripts de gerenciamento de serviços não encontrados"
            exit 1
        fi
        ;;
    resync)
        echo "Forçando ressincronização completa dos bancos de dados..."
        
        # Parar serviços antes da ressincronização
        if [ -f "$BASE_DIR/start_lightrag_service.sh" ]; then
            echo "Parando serviços..."
            bash "$BASE_DIR/start_lightrag_service.sh" stop
        fi
        
        # Criar backup antes da ressincronização
        echo "Criando backup da base de dados..."
        python3 "$BASE_DIR/tools/migration_tools.py" backup
        
        # Limpar bancos de dados
        echo "Limpando bancos de dados..."
        if [ -f "$BASE_DIR/documents.db" ]; then
            rm -f "$BASE_DIR/documents.db"
            echo "Banco SQLite removido"
        fi
        
        # Limpar timestamp de sincronização
        if [ -f "$BASE_DIR/.sync_timestamp" ]; then
            rm -f "$BASE_DIR/.sync_timestamp"
        fi
        
        # Reiniciar serviços com banco limpo
        echo "Reiniciando serviços..."
        if [ -f "$BASE_DIR/start_lightrag_service.sh" ]; then
            bash "$BASE_DIR/start_lightrag_service.sh" start
        fi
        
        echo "Ressincronização iniciada. Aguarde enquanto o monitor indexa os documentos."
        ;;
    all)
        echo "Executando todas as operações de manutenção..."
        
        # Backup inicial
        python3 "$BASE_DIR/tools/migration_tools.py" backup
        
        # Executar todas as operações de migração
        python3 "$BASE_DIR/tools/migration_tools.py" all
        
        # Limpar temporários
        bash "$BASE_DIR/clean_pids.sh"
        find "$BASE_DIR" -name "__pycache__" -type d -exec rm -rf {} +
        find "$BASE_DIR" -name "*.pyc" -delete
        find "$BASE_DIR" -name "*.tmp" -delete
        
        # Verificar e corrigir processos duplicados
        if [ -f "$BASE_DIR/process_manager.py" ]; then
            echo "Verificando e corrigindo processos duplicados..."
            python3 "$BASE_DIR/process_manager.py" --clean
        fi
        
        echo "Manutenção completa finalizada!"
        ;;
    help)
        show_help
        ;;
    *)
        echo "Opção desconhecida: $1"
        show_help
        exit 1
        ;;
esac

exit 0