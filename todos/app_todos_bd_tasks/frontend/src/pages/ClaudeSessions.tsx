import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Link } from 'react-router-dom'

interface Todo {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed'
  priority: 'low' | 'medium' | 'high'
}

interface Session {
  sessionId: string
  todos: string
  conversation: string | null
  hasConversation: boolean
  lastModified: string
  todoCount: number
  pendingCount: number
  completedCount: number
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333'

export function ClaudeSessions() {
  const { data: sessions, isLoading, error } = useQuery({
    queryKey: ['claude-sessions'],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/claude-sessions`)
      if (!response.ok) throw new Error('Falha ao buscar sessões')
      const data = await response.json()
      return data.sessions as Session[]
    },
    refetchInterval: 5000, // Atualiza a cada 5 segundos
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Carregando sessões...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Erro ao carregar sessões</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Sessões do Claude</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sessions?.map((session) => (
          <SessionCard key={session.sessionId} session={session} />
        ))}
      </div>
      
      {!sessions?.length && (
        <div className="text-center text-gray-500 mt-8">
          Nenhuma sessão encontrada
        </div>
      )}
    </div>
  )
}

function SessionCard({ session }: { session: Session }) {
  const { data: todos } = useQuery({
    queryKey: ['claude-todos', session.sessionId],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/claude-sessions/${session.sessionId}/todos`)
      if (!response.ok) throw new Error('Falha ao buscar todos')
      const data = await response.json()
      return data.todos as Todo[]
    },
    enabled: false, // Carrega apenas quando expandido
  })

  const progressPercentage = session.todoCount > 0
    ? Math.round((session.completedCount / session.todoCount) * 100)
    : 0

  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-semibold text-sm text-gray-800 truncate">
          {session.sessionId.slice(0, 8)}...
        </h3>
        {session.hasConversation && (
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
            Com conversa
          </span>
        )}
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Total de tarefas:</span>
          <span className="font-medium">{session.todoCount}</span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Pendentes:</span>
          <span className="font-medium text-orange-600">{session.pendingCount}</span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Concluídas:</span>
          <span className="font-medium text-green-600">{session.completedCount}</span>
        </div>
      </div>
      
      <div className="mt-4">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>Progresso</span>
          <span>{progressPercentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>
      
      <div className="mt-3 text-xs text-gray-500">
        Última atualização: {format(new Date(session.lastModified), 'dd/MM/yyyy HH:mm')}
      </div>
      
      <Link
        to={`/claude-sessions/${session.sessionId}`}
        className="mt-3 inline-block text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        Ver detalhes →
      </Link>
    </div>
  )
}