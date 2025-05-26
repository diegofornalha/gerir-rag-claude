# Implementação de CRUD de Tarefas com Persistência em JSON

## Visão Geral
Este documento detalha como foi implementada a funcionalidade completa de gerenciamento de tarefas (Create, Read, Update, Delete) com persistência em arquivos JSON no aplicativo de tarefas.

## Arquitetura da Solução

### Frontend (React + TypeScript)
- **Componente Principal**: `ClaudeSessionDetailSimple.tsx`
- **Gerenciamento de Estado**: React hooks (useState)
- **Requisições HTTP**: Tanstack Query (React Query)
- **UI**: Tailwind CSS

### Backend (Fastify + Node.js)
- **Servidor**: `server.ts` e `claude-routes.ts`
- **Integração**: `ClaudeIntegration` class
- **Armazenamento**: Arquivos JSON no diretório `~/.claude/todos/`

## Implementação Detalhada

### 1. Estrutura dos Dados

As tarefas são armazenadas em arquivos JSON com a seguinte estrutura:

```json
[
  {
    "id": "1748250347973",
    "content": "Implementar autenticação de usuários",
    "status": "pending",
    "priority": "high"
  }
]
```

### 2. Backend - Classe ClaudeIntegration

#### Método updateTodo
```typescript
async updateTodo(sessionId: string, todoId: string, updates: { content?: string; status?: string; priority?: string }) {
  const todoPath = path.join(TODOS_DIR, `${sessionId}.json`)
  
  if (!existsSync(todoPath)) {
    return false
  }
  
  const todoContent = await fs.readFile(todoPath, 'utf-8')
  const todos = JSON.parse(todoContent)
  
  const todoIndex = todos.findIndex((t: any) => t.id === todoId)
  if (todoIndex === -1) {
    return false
  }
  
  // Atualiza apenas os campos fornecidos
  if (updates.content !== undefined) todos[todoIndex].content = updates.content
  if (updates.status !== undefined) todos[todoIndex].status = updates.status
  if (updates.priority !== undefined) todos[todoIndex].priority = updates.priority
  
  await fs.writeFile(todoPath, JSON.stringify(todos, null, 2))
  return true
}
```

#### Método deleteTodo
```typescript
async deleteTodo(sessionId: string, todoId: string) {
  const todoPath = path.join(TODOS_DIR, `${sessionId}.json`)
  
  if (!existsSync(todoPath)) {
    return false
  }
  
  const todoContent = await fs.readFile(todoPath, 'utf-8')
  const todos = JSON.parse(todoContent)
  
  const filteredTodos = todos.filter((t: any) => t.id !== todoId)
  
  if (filteredTodos.length === todos.length) {
    return false // Todo não encontrado
  }
  
  await fs.writeFile(todoPath, JSON.stringify(filteredTodos, null, 2))
  return true
}
```

#### Método reorderTodos
```typescript
async reorderTodos(sessionId: string, todoIds: string[]) {
  const todoPath = path.join(TODOS_DIR, `${sessionId}.json`)
  
  if (!existsSync(todoPath)) {
    return false
  }
  
  const todoContent = await fs.readFile(todoPath, 'utf-8')
  const todos = JSON.parse(todoContent)
  
  // Cria um mapa para lookup rápido
  const todoMap = new Map(todos.map((t: any) => [t.id, t]))
  
  // Reconstrói o array na nova ordem
  const reorderedTodos = todoIds.map(id => todoMap.get(id)).filter(Boolean)
  
  await fs.writeFile(todoPath, JSON.stringify(reorderedTodos, null, 2))
  return true
}
```

### 3. Backend - Rotas API

As rotas foram adicionadas ao arquivo `claude-routes.ts`:

```typescript
// Atualizar uma tarefa
app.put('/claude-sessions/:sessionId/todos/:todoId', {
  schema: {
    params: z.object({
      sessionId: z.string(),
      todoId: z.string()
    }),
    body: z.object({
      content: z.string().optional(),
      status: z.string().optional(),
      priority: z.string().optional()
    })
  }
}, async (request, reply) => {
  const { sessionId, todoId } = request.params
  const updates = request.body
  
  const success = await claud.updateTodo(sessionId, todoId, updates)
  
  if (!success) {
    return reply.status(404).send({ error: 'Todo not found' })
  }
  
  return { success: true }
})

// Deletar uma tarefa
app.delete('/claude-sessions/:sessionId/todos/:todoId', {
  schema: {
    params: z.object({
      sessionId: z.string(),
      todoId: z.string()
    })
  }
}, async (request, reply) => {
  const { sessionId, todoId } = request.params
  
  const success = await claud.deleteTodo(sessionId, todoId)
  
  if (!success) {
    return reply.status(404).send({ error: 'Todo not found' })
  }
  
  return { success: true }
})

// Reordenar tarefas
app.put('/claude-sessions/:sessionId/todos/reorder', {
  schema: {
    params: z.object({
      sessionId: z.string()
    }),
    body: z.object({
      todoIds: z.array(z.string())
    })
  }
}, async (request, reply) => {
  const { sessionId } = request.params
  const { todoIds } = request.body
  
  const success = await claud.reorderTodos(sessionId, todoIds)
  
  if (!success) {
    return reply.status(404).send({ error: 'Session not found' })
  }
  
  return { success: true }
})
```

### 4. Frontend - Componente React

#### Estados para Edição Inline
```typescript
const [editingTodoId, setEditingTodoId] = useState<string | null>(null)
const [editingTodoContent, setEditingTodoContent] = useState('')
const [editingStatusId, setEditingStatusId] = useState<string | null>(null)
const [editingPriorityId, setEditingPriorityId] = useState<string | null>(null)
const [deletingTodoId, setDeletingTodoId] = useState<string | null>(null)
```

#### Mutations do React Query
```typescript
// Atualizar tarefa
const updateTodoMutation = useMutation({
  mutationFn: async ({ todoId, updates }: { todoId: string; updates: any }) => {
    const response = await fetch(`${API_URL}/api/claude-sessions/${sessionId}/todos/${todoId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    })
    
    if (!response.ok) {
      throw new Error('Failed to update todo')
    }
    
    return response.json()
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['claude-session', sessionId] })
    setEditingTodoId(null)
    setEditingTodoContent('')
    setEditingStatusId(null)
    setEditingPriorityId(null)
  }
})

// Deletar tarefa
const deleteTodoMutation = useMutation({
  mutationFn: async (todoId: string) => {
    const response = await fetch(`${API_URL}/api/claude-sessions/${sessionId}/todos/${todoId}`, {
      method: 'DELETE',
    })
    
    if (!response.ok) {
      throw new Error('Failed to delete todo')
    }
    
    return response.json()
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['claude-session', sessionId] })
    setDeletingTodoId(null)
  }
})
```

#### Interface de Edição Inline

1. **Edição de Conteúdo**: Clique no botão ✏️ para entrar no modo de edição
2. **Edição de Status**: Clique no badge de status para abrir dropdown
3. **Edição de Prioridade**: Clique no badge de prioridade para abrir dropdown
4. **Exclusão**: Clique no botão 🗑️ para abrir modal de confirmação

### 5. Funcionalidades Implementadas

#### Reordenação de Tarefas
- Botões ⬆️ e ⬇️ aparecem apenas na visualização "Pendentes"
- Ao clicar, a tarefa troca de posição com a adjacente
- A nova ordem é persistida no JSON

#### Limpar Concluídas
```typescript
const handleClearCompleted = () => {
  const remainingTodos = session.todos.filter(todo => todo.status !== 'completed')
  const newTodo = {
    id: Date.now().toString(),
    content: '',
    status: 'pending' as const,
    priority: 'medium' as const
  }
  
  clearCompletedMutation.mutate([...remainingTodos, newTodo])
}
```

### 6. Fluxo de Dados

1. **Usuário faz uma ação** (editar/deletar/reordenar)
2. **Frontend dispara mutation** via React Query
3. **Requisição HTTP** é enviada para o backend
4. **Backend processa** através da ClaudeIntegration
5. **Arquivo JSON é atualizado** no sistema de arquivos
6. **Frontend invalida cache** e recarrega dados
7. **UI é atualizada** com os novos dados

### 7. Tratamento de Erros

- Validação de dados no backend com Zod
- Verificação de existência de arquivos e tarefas
- Feedback visual de loading states
- Modal de confirmação para ações destrutivas

### 8. Problemas Encontrados e Soluções

#### Problema 1: Rotas retornando 404
**Causa**: As rotas foram inicialmente adicionadas ao arquivo errado (server-simple.ts)
**Solução**: Adicionar as rotas ao arquivo correto (claude-routes.ts)

#### Problema 2: Puppeteer não funcionando
**Causa**: Problemas com seletores e estado do navegador
**Solução**: Usar seletores mais específicos e reiniciar navegação quando necessário

## Conclusão

A implementação permite gerenciamento completo de tarefas com:
- ✅ Criação automática de tarefas em branco
- ✅ Edição inline de conteúdo, status e prioridade
- ✅ Exclusão com confirmação
- ✅ Reordenação com botões up/down
- ✅ Limpeza de tarefas concluídas
- ✅ Persistência em tempo real no arquivo JSON
- ✅ Interface responsiva e intuitiva

Todas as alterações são imediatamente persistidas no arquivo JSON correspondente à sessão, garantindo que os dados não sejam perdidos.