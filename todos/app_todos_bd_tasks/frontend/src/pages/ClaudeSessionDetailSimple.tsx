import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

interface Todo {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed'
  priority: 'low' | 'medium' | 'high'
}

interface SessionDetail {
  sessionId: string
  todos: Todo[]
  conversation: Array<{
    type: string
    content: string
    timestamp: string
  }> | null
  metadata: {
    summary?: string
  }
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333'

const priorityColors = {
  high: 'bg-red-100 text-red-800 border-red-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200'
}

const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800'
}

const statusLabels = {
  pending: 'Pendente',
  in_progress: 'Em Progresso',
  completed: 'Concluída'
}

export function ClaudeSessionDetailSimple() {
  const { sessionId } = useParams<{ sessionId: string }>()
  
  const { data: session, isLoading, error } = useQuery({
    queryKey: ['claude-session-detail', sessionId],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/claude-sessions/${sessionId}`)
      if (!response.ok) throw new Error('Falha ao buscar sessão')
      const data = await response.json()
      return data.session as SessionDetail
    },
    refetchInterval: 5000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Carregando detalhes da sessão...</div>
      </div>
    )
  }

  if (error || !session) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Erro ao carregar sessão</div>
      </div>
    )
  }

  const stats = {
    total: session.todos.length,
    pending: session.todos.filter(t => t.status === 'pending').length,
    inProgress: session.todos.filter(t => t.status === 'in_progress').length,
    completed: session.todos.filter(t => t.status === 'completed').length
  }

  const progressPercentage = stats.total > 0
    ? Math.round((stats.completed / stats.total) * 100)
    : 0

  return (
    <div className="container mx-auto p-4">
      <div className="mb-6">
        <Link to="/claude-sessions" className="text-blue-600 hover:text-blue-800">
          ← Voltar para sessões
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h1 className="text-2xl font-bold mb-4">
          Sessão: {sessionId?.slice(0, 8)}...
        </h1>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-sm text-gray-600">Total</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded">
            <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
            <div className="text-sm text-gray-600">Pendentes</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">{stats.inProgress}</div>
            <div className="text-sm text-gray-600">Em Progresso</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
            <div className="text-sm text-gray-600">Concluídas</div>
          </div>
        </div>

        <div className="mb-4">
          <div className="bg-gray-200 rounded-full h-6 overflow-hidden">
            <div 
              className="bg-green-500 h-full transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Progresso: {progressPercentage}%
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold mb-4">📋 Tarefas</h2>
        <div className="space-y-3">
          {session.todos.map((todo) => (
            <div
              key={todo.id}
              className={`p-4 rounded-lg border ${
                todo.status === 'completed' ? 'bg-gray-50 opacity-75' : 'bg-white'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 mb-2">
                    {todo.content}
                  </p>
                  <div className="flex gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${statusColors[todo.status]}`}>
                      {statusLabels[todo.status]}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full border ${priorityColors[todo.priority]}`}>
                      {todo.priority === 'high' ? 'Alta' : todo.priority === 'medium' ? 'Média' : 'Baixa'}
                    </span>
                  </div>
                </div>
                <div className="text-xs text-gray-500">
                  #{todo.id}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}