import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useHiddenSessions } from '../hooks/useHiddenSessions'

interface Session {
  sessionId: string
  todos: string
  conversation: string | null
  hasConversation: boolean
  lastModified: string
  todoCount: number
  pendingCount: number
  completedCount: number
  isContinuation?: boolean
  originalSessionId?: string | null
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333'

export function ClaudeSessions() {
  const [showHidden, setShowHidden] = useState(false)
  const { hideSession, unhideSession, isHidden, hiddenCount } = useHiddenSessions()
  
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

  const visibleSessions = sessions?.filter(session => 
    showHidden ? isHidden(session.sessionId) : !isHidden(session.sessionId)
  ) || []

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
      
      {/* Tabs para alternar entre visíveis e ocultas */}
      <div className="flex gap-4 mb-6 border-b">
        <button
          onClick={() => setShowHidden(false)}
          className={`pb-2 px-1 font-medium transition-colors ${
            !showHidden 
              ? 'text-blue-600 border-b-2 border-blue-600' 
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Sessões Ativas
        </button>
        <button
          onClick={() => setShowHidden(true)}
          className={`pb-2 px-1 font-medium transition-colors ${
            showHidden 
              ? 'text-blue-600 border-b-2 border-blue-600' 
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Sessões Ocultas {hiddenCount > 0 && `(${hiddenCount})`}
        </button>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {visibleSessions.map((session) => (
          <SessionCard 
            key={session.sessionId} 
            session={session} 
            isHidden={isHidden(session.sessionId)}
            onHide={() => hideSession(session.sessionId)}
            onUnhide={() => unhideSession(session.sessionId)}
          />
        ))}
      </div>
      
      {!visibleSessions.length && (
        <div className="text-center text-gray-500 mt-8">
          {showHidden ? 'Nenhuma sessão oculta' : 'Nenhuma sessão encontrada'}
        </div>
      )}
    </div>
  )
}

interface SessionCardProps {
  session: Session
  isHidden: boolean
  onHide: () => void
  onUnhide: () => void
}

function SessionCard({ session, isHidden, onHide, onUnhide }: SessionCardProps) {

  const progressPercentage = session.todoCount > 0
    ? Math.round((session.completedCount / session.todoCount) * 100)
    : 0

  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow relative">
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-semibold text-sm text-gray-800 truncate">
          {session.todoCount} {session.todoCount === 1 ? 'tarefa' : 'tarefas'}
        </h3>
        <div className="flex items-center gap-1">
          {session.hasConversation && (
            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded" title="Sessão com conversa">
              💬
            </span>
          )}
          {session.isContinuation && (
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded font-mono" title={`Continuação de ${session.originalSessionId?.slice(0, 8)}`}>
              claude -c:{session.originalSessionId?.slice(0, 6)}
            </span>
          )}
          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded font-mono" title="ID da sessão">
            {session.sessionId.slice(0, 6)}
          </span>
        </div>
      </div>
      
      <div className="space-y-2">
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
      
      <div className="mt-3 flex justify-between items-center">
        <Link
          to={`/claude-sessions/${session.sessionId}`}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Ver detalhes →
        </Link>
        
        {/* Botão de ocultar/desocultar */}
        <button
          onClick={isHidden ? onUnhide : onHide}
          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          title={isHidden ? 'Desocultar sessão' : 'Ocultar sessão'}
        >
          {isHidden ? '👁️' : '👁️‍🗨️'}
        </button>
      </div>
    </div>
  )
}