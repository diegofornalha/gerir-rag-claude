#!/bin/bash
#
# LightRAG - Script de Instalação Completo
# Instala e configura o serviço LightRAG

# Cores para feedback visual
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Identificar diretórios
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
HOME_DIR="$HOME/.claude"
USER_LIBRARY="$HOME/Library/LaunchAgents"

echo -e "${BLUE}=== Instalação do LightRAG ===${NC}"
echo -e "${BLUE}Diretório de instalação: ${SCRIPT_DIR}${NC}"

# Verificar Python
echo -e "${BLUE}Verificando dependências...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python encontrado: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 não encontrado. Instalação abortada.${NC}"
    echo -e "${YELLOW}Instale Python 3 usando Homebrew: brew install python${NC}"
    exit 1
fi

# Verificar Flask
if python3 -c "import flask" &> /dev/null; then
    echo -e "${GREEN}✓ Flask encontrado${NC}"
else
    echo -e "${YELLOW}⚠ Flask não encontrado, instalando...${NC}"
    pip3 install flask || pip install flask
    
    # Verificar novamente
    if python3 -c "import flask" &> /dev/null; then
        echo -e "${GREEN}✓ Flask instalado com sucesso${NC}"
    else
        echo -e "${RED}✗ Falha ao instalar Flask. Instalação abortada.${NC}"
        exit 1
    fi
fi

# Criar diretório de logs
echo -e "${BLUE}Configurando diretórios...${NC}"
mkdir -p "$SCRIPT_DIR/logs"

# Configurar permissões de execução
echo -e "${BLUE}Configurando permissões...${NC}"
chmod +x "$SCRIPT_DIR/start_lightrag.sh"
chmod +x "$SCRIPT_DIR/micro_lightrag.py"
chmod +x "$SCRIPT_DIR/demo.py"
chmod +x "$SCRIPT_DIR/lightrag_mcp.py"

# Criar links simbólicos
echo -e "${BLUE}Criando links simbólicos...${NC}"
ln -sf "$SCRIPT_DIR/start_lightrag.sh" "$HOME_DIR/start_lightrag.sh"

# Verificar se .claude existe no $PYTHONPATH
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
CLAUDE_PATH="$SITE_PACKAGES/claude"

if [ -d "$CLAUDE_PATH" ]; then
    echo -e "${BLUE}Configurando integração MCP...${NC}"
    
    # Criar link para o módulo MCP no diretório claude
    ln -sf "$SCRIPT_DIR/lightrag_mcp.py" "$CLAUDE_PATH/lightrag_mcp.py"
    
    # Criar arquivo __init__.py se não existir
    if [ ! -f "$CLAUDE_PATH/mcp_services/__init__.py" ]; then
        mkdir -p "$CLAUDE_PATH/mcp_services"
        touch "$CLAUDE_PATH/mcp_services/__init__.py"
    fi
    
    # Criar módulo de serviço
    LIGHTRAG_SERVICE="$CLAUDE_PATH/mcp_services/lightrag.py"
    echo -e "${BLUE}Criando módulo de serviço MCP...${NC}"
    cat > "$LIGHTRAG_SERVICE" << 'EOL'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de serviço LightRAG para MCP
"""

from claude.lightrag_mcp import rag_query, rag_insert_text, rag_status, rag_clear, ensure_server_running

# Garantir que o servidor esteja em execução
ensure_server_running()

# Funções expostas pelo serviço
__all__ = ['rag_query', 'rag_insert_text', 'rag_status', 'rag_clear']
EOL
    
    echo -e "${GREEN}✓ Integração MCP configurada${NC}"
else
    echo -e "${YELLOW}⚠ Diretório Claude não encontrado em $SITE_PACKAGES${NC}"
    echo -e "${YELLOW}  A integração MCP não foi configurada automaticamente${NC}"
fi

# Configurar lançamento automático
echo -e "${BLUE}Configurando inicialização automática...${NC}"
PLIST_FILE="$SCRIPT_DIR/com.user.lightrag.plist"
DEST_PLIST="$USER_LIBRARY/com.user.lightrag.plist"

# Substituir variáveis no arquivo plist
sed "s|\$HOME|$HOME|g" "$PLIST_FILE" > "$DEST_PLIST"

# Carregar serviço
launchctl unload "$DEST_PLIST" 2>/dev/null || true
launchctl load -w "$DEST_PLIST"

echo -e "${BLUE}Iniciando servidor LightRAG...${NC}"
"$SCRIPT_DIR/start_lightrag.sh" > /dev/null 2>&1 &
sleep 3

# Teste final
echo -e "${BLUE}Verificando instalação...${NC}"
if curl -s http://127.0.0.1:5000/status > /dev/null; then
    echo -e "${GREEN}✓ Servidor LightRAG instalado e funcionando!${NC}"
    echo -e "${GREEN}✓ Serviço registrado para iniciar automaticamente${NC}"
    
    echo -e "\n${BLUE}Como usar o LightRAG:${NC}"
    echo -e "${YELLOW}# No Python ou dentro do Claude:${NC}"
    echo -e "from claude import MCP"
    echo -e "lightrag = MCP.connect_to_service('lightrag')"
    echo -e "lightrag.rag_insert_text(text=\"Texto para adicionar à base\")"
    echo -e "resultado = lightrag.rag_query(query=\"Sua pergunta\")"
    
    echo -e "\n${YELLOW}# Usar o demo interativo:${NC}"
    echo -e "cd ~/.claude/lightrag && python3 demo.py"
    
    echo -e "\n${YELLOW}# Testar de qualquer lugar:${NC}"
    echo -e "curl -X POST -H \"Content-Type: application/json\" \\"
    echo -e "     -d '{\"query\":\"O que é LightRAG?\"}' \\"
    echo -e "     http://127.0.0.1:5000/query"
    
    echo -e "\n${BLUE}Servidor disponível em:${NC} http://127.0.0.1:5000"
    echo -e "${BLUE}Logs em:${NC} $SCRIPT_DIR/logs/"
else
    echo -e "${RED}✗ Falha ao iniciar o servidor LightRAG${NC}"
    echo -e "${YELLOW}Verifique os logs:${NC} $SCRIPT_DIR/logs/lightrag.log"
fi