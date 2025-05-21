#!/bin/bash

# Script para gerenciar processos LightRAG
# Integra o gerenciador de processos Python com o sistema de manutenção

# Diretório base
BASE_DIR="$(dirname "$(readlink -f "$0")")"
cd "$BASE_DIR" || { echo "Erro ao acessar diretório base"; exit 1; }

# Arquivo do gerenciador de processos Python
PROCESS_MANAGER="$BASE_DIR/process_manager.py"

# Verificar se o arquivo do gerenciador existe
if [ ! -f "$PROCESS_MANAGER" ]; then
    echo "Erro: Gerenciador de processos não encontrado em $PROCESS_MANAGER"
    exit 1
fi

# Verificar permissões de execução
if [ ! -x "$PROCESS_MANAGER" ]; then
    echo "Definindo permissões de execução para o gerenciador de processos..."
    chmod +x "$PROCESS_MANAGER"
fi

# Função de ajuda
show_help() {
    echo "Gerenciador de Processos LightRAG"
    echo ""
    echo "Uso: $0 [opção]"
    echo ""
    echo "Opções:"
    echo "  status       Exibe o status dos processos do LightRAG"
    echo "  clean        Limpa processos duplicados mantendo o mais antigo"
    echo "  verify       Verifica a integridade do sistema"
    echo "  force-clean  Força a remoção de processos problemáticos (SIGKILL)"
    echo "  restart      Reinicia todos os serviços LightRAG"
    echo "  help         Exibe esta mensagem de ajuda"
    echo ""
    echo "Exemplo: $0 status"
}

# Processar argumentos
case "$1" in
    status)
        echo "Verificando status dos processos LightRAG..."
        python3 "$PROCESS_MANAGER" --status --verbose
        ;;
    clean)
        echo "Limpando processos duplicados..."
        python3 "$PROCESS_MANAGER" --clean
        ;;
    verify)
        echo "Verificando integridade do sistema..."
        python3 "$PROCESS_MANAGER" --verify
        ;;
    force-clean)
        echo "Forçando limpeza de processos duplicados..."
        python3 "$PROCESS_MANAGER" --clean --force
        ;;
    restart)
        echo "Reiniciando serviços LightRAG..."
        
        # Primeiro, verificar se o script start_lightrag_service.sh existe
        if [ -f "$BASE_DIR/start_lightrag_service.sh" ]; then
            # Limpar processos duplicados primeiro
            python3 "$PROCESS_MANAGER" --clean --force
            
            # Reiniciar os serviços
            echo "Executando start_lightrag_service.sh restart..."
            bash "$BASE_DIR/start_lightrag_service.sh" restart
            
            # Verificar status após reinício
            echo ""
            echo "Status após reinício:"
            python3 "$PROCESS_MANAGER" --status
        else
            echo "Erro: Script start_lightrag_service.sh não encontrado"
            exit 1
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Opção inválida ou não especificada."
        show_help
        exit 1
        ;;
esac

exit 0