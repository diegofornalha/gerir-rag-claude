#!/bin/bash

echo "🚀 Iniciando integração Claude Sessions..."

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Diretório base
BASE_DIR="/Users/agents/.claude/todos/app_todos_bd_tasks"

echo -e "${BLUE}📦 Instalando dependências...${NC}"

# Backend
echo -e "${YELLOW}Backend:${NC}"
cd "$BASE_DIR/backend"
if [ ! -d "node_modules" ]; then
    pnpm install
fi

# Frontend
echo -e "${YELLOW}Frontend:${NC}"
cd "$BASE_DIR/frontend"
if [ ! -d "node_modules" ]; then
    pnpm install
    pnpm add date-fns
fi

echo -e "${GREEN}✅ Dependências instaladas!${NC}"

# Iniciar serviços
echo -e "${BLUE}🔧 Iniciando serviços...${NC}"

# Backend
cd "$BASE_DIR/backend"
echo -e "${YELLOW}Iniciando backend na porta 3344...${NC}"
pnpm dev &
BACKEND_PID=$!

sleep 3

# Frontend
cd "$BASE_DIR/frontend"
echo -e "${YELLOW}Iniciando frontend na porta 5173...${NC}"
pnpm dev &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Serviços iniciados!${NC}"
echo ""
echo -e "${BLUE}URLs:${NC}"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:3344"
echo "  Claude Sessions: http://localhost:5173/claude-sessions"
echo ""
echo -e "${YELLOW}PIDs dos processos:${NC}"
echo "  Backend: $BACKEND_PID"
echo "  Frontend: $FRONTEND_PID"
echo ""
echo -e "${RED}Para parar os serviços, execute:${NC}"
echo "  kill $BACKEND_PID $FRONTEND_PID"

# Manter script rodando
wait