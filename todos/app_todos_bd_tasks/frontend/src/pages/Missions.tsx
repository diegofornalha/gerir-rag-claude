import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Link } from 'react-router-dom'

interface Mission {
  id: number
  title: string
  description: string | null
  status: 'pending' | 'processing' | 'completed' | 'error'
  sessionId: string | null
  response: string | null
  error: string | null
  createdAt: string
  updatedAt: string | null
}

interface Todo {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed'
  priority: 'low' | 'medium' | 'high'
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3333'

export function Missions() {
  const [newMission, setNewMission] = useState({ title: '', description: '' })
  const queryClient = useQueryClient()

  const { data: missions, isLoading } = useQuery({
    queryKey: ['missions'],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/missions`)
      if (!response.ok) throw new Error('Falha ao buscar missões')
      const data = await response.json()
      return data as Mission[]
    },
    refetchInterval: 2000, // Atualiza a cada 2 segundos
  })

  const createMission = useMutation({
    mutationFn: async (mission: { title: string; description?: string }) => {
      const response = await fetch(`${API_URL}/missions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mission),
      })
      if (!response.ok) throw new Error('Falha ao criar missão')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions'] })
      setNewMission({ title: '', description: '' })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (newMission.title.trim()) {
      createMission.mutate({
        title: newMission.title,
        description: newMission.description || undefined,
      })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Carregando missões...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Missões</h1>
      
      {/* Formulário de criação */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Criar Nova Missão</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Título
            </label>
            <input
              type="text"
              value={newMission.title}
              onChange={(e) => setNewMission({ ...newMission, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: Implementar sistema de notificações"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrição (opcional)
            </label>
            <textarea
              value={newMission.description}
              onChange={(e) => setNewMission({ ...newMission, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Descreva os detalhes da missão..."
            />
          </div>
          <button
            type="submit"
            disabled={createMission.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {createMission.isPending ? 'Criando...' : 'Criar Missão'}
          </button>
        </div>
      </form>

      {/* Lista de missões */}
      <div className="space-y-4">
        {missions?.map((mission) => (
          <MissionCard key={mission.id} mission={mission} />
        ))}
      </div>
      
      {!missions?.length && (
        <div className="text-center text-gray-500 mt-8">
          Nenhuma missão criada ainda
        </div>
      )}
    </div>
  )
}

function MissionCard({ mission }: { mission: Mission }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const queryClient = useQueryClient()
  
  const { data: missionDetails } = useQuery({
    queryKey: ['mission', mission.id],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/missions/${mission.id}`)
      if (!response.ok) throw new Error('Falha ao buscar detalhes da missão')
      return response.json()
    },
    enabled: isExpanded,
    refetchInterval: mission.status === 'processing' ? 1000 : false,
  })
  
  const deleteMission = useMutation({
    mutationFn: async (id: number) => {
      const response = await fetch(`${API_URL}/missions/${id}`, {
        method: 'DELETE',
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Falha ao deletar missão')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions'] })
    },
  })

  const getStatusColor = (status: Mission['status']) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-100'
      case 'processing': return 'text-blue-600 bg-blue-100'
      case 'completed': return 'text-green-600 bg-green-100'
      case 'error': return 'text-red-600 bg-red-100'
    }
  }

  const getStatusText = (status: Mission['status']) => {
    switch (status) {
      case 'pending': return 'Pendente'
      case 'processing': return 'Processando'
      case 'completed': return 'Concluída'
      case 'error': return 'Erro'
    }
  }

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'high': return 'Alta'
      case 'medium': return 'Média'
      case 'low': return 'Baixa'
      default: return priority
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="font-semibold text-lg text-gray-800">
            {mission.title}
          </h3>
          {mission.sessionId && (
            <p className="text-xs text-gray-500 mt-1">Session: {mission.sessionId}</p>
          )}
          {mission.description && (
            <p className="text-gray-600 mt-1">{mission.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(mission.status)}`}>
            {getStatusText(mission.status)}
          </span>
          <button
            onClick={() => deleteMission.mutate(mission.id)}
            disabled={deleteMission.isPending}
            className="px-3 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
            title="Deletar missão"
          >
            {deleteMission.isPending ? '...' : '🗑️'}
          </button>
        </div>
      </div>
      
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          Criada em: {format(new Date(mission.createdAt), 'dd/MM/yyyy HH:mm')}
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          {isExpanded ? 'Ocultar detalhes' : 'Ver detalhes'} →
        </button>
      </div>

      {isExpanded && (
        <div className="mt-4 border-t pt-4">
          {mission.sessionId && (
            <div className="mb-3">
              <span className="text-sm text-gray-600">ID da </span>
              <Link
                to={`/claude-sessions/${mission.sessionId}`}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                {mission.sessionId}
              </Link>
            </div>
          )}
          
          {mission.error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-3">
              <p className="text-sm text-red-800 font-medium">Erro:</p>
              <p className="text-sm text-red-600 mt-1">{mission.error}</p>
            </div>
          )}
          
          {mission.response && (
            <div className="bg-gray-50 rounded-md p-3 mb-3">
              <p className="text-sm text-gray-800 font-medium">Resposta:</p>
              <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">{mission.response}</p>
            </div>
          )}
          
          {missionDetails?.todos && missionDetails.todos.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-800 mb-2">
                Tarefas ({missionDetails.todos.length}):
              </p>
              <div className="space-y-1">
                {missionDetails.todos.map((todo: Todo) => (
                  <div
                    key={todo.id}
                    className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded"
                  >
                    <span className={todo.status === 'completed' ? 'line-through text-gray-500' : ''}>
                      {todo.content}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      todo.priority === 'high' ? 'bg-red-100 text-red-700' :
                      todo.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {getPriorityText(todo.priority)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}