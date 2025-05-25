# 🚀 Guia de Integração Claude Sessions

Este guia mostra como executar a integração entre o sistema de todos/tasks e as sessões do Claude.

## 📋 Pré-requisitos

- Node.js 18+
- pnpm instalado
- PostgreSQL rodando (se quiser persistência)

## 🔧 Instalação

### 1. Instalar dependências do Backend

```bash
cd /Users/agents/.claude/todos/app_todos_bd_tasks/backend
pnpm install
pnpm add chokidar @types/chokidar
```

### 2. Instalar dependências do Frontend

```bash
cd /Users/agents/.claude/todos/app_todos_bd_tasks/frontend
pnpm install
pnpm add date-fns
```

## ▶️ Executar o Sistema

### Terminal 1 - Backend

```bash
cd /Users/agents/.claude/todos/app_todos_bd_tasks/backend
pnpm dev
```

O backend iniciará em http://localhost:3333

### Terminal 2 - Frontend

```bash
cd /Users/agents/.claude/todos/app_todos_bd_tasks/frontend
pnpm dev
```

O frontend iniciará em http://localhost:5173

## 🌐 Acessar o Dashboard

1. Abra o navegador em http://localhost:5173
2. Clique em "Claude Sessions" no menu superior
3. Você verá todas as suas sessões do Claude com:
   - Total de tarefas
   - Tarefas pendentes
   - Tarefas concluídas
   - Barra de progresso visual
   - Última atualização

## 🔄 Funcionalidades

### Visualização em Tempo Real
- As sessões são atualizadas automaticamente a cada 5 segundos
- Mostra o progresso de cada sessão com tarefas

### API Endpoints Disponíveis

- `GET http://localhost:3333/api/claude-sessions` - Lista todas as sessões
- `GET http://localhost:3333/api/claude-sessions/:sessionId` - Detalhes de uma sessão
- `GET http://localhost:3333/api/claude-sessions/:sessionId/todos` - Todos de uma sessão
- `GET http://localhost:3333/api/claude-sessions/active` - Apenas sessões com tarefas pendentes

## 🎯 Próximos Passos

1. **WebSocket para atualizações em tempo real**
   - Substituir polling por conexão persistente
   
2. **Gráficos e Analytics**
   - Adicionar visualizações de produtividade
   - Métricas por período

3. **Sincronização com PostgreSQL**
   - Persistir dados das sessões
   - Histórico completo

4. **Export de Relatórios**
   - PDF/CSV das sessões
   - Análise de produtividade

## 🐛 Troubleshooting

### Erro de CORS
Se houver erro de CORS, verifique se o backend está rodando em http://localhost:3333

### Sessões não aparecem
Verifique se existem arquivos JSON em `/Users/agents/.claude/todos/`

### Erro de dependências
Execute `pnpm install` novamente nos diretórios backend e frontend

## 📝 Arquivos Criados

- `/backend/src/claude/integration.ts` - Integração com arquivos do Claude
- `/backend/src/http/claude-routes.ts` - Rotas da API
- `/frontend/src/pages/ClaudeSessions.tsx` - Componente do dashboard
- `/lightrag/api/claude_sessions_api.py` - API Python alternativa