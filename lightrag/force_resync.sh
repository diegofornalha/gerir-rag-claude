#!/bin/bash
#
# Script para forçar resincronização sem confirmação
# Útil para uso em scripts ou em caso de erros

# Diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Executar resincronização direta
./resync.sh

exit $?