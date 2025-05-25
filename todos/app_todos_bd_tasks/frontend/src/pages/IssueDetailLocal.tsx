import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { issues } from '../db/collections/issues-local'
import { users } from '../db/collections/users-local'

export function IssueDetailLocal() {
  const { id } = useParams<{ id: string }>()
  const [issue, setIssue] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Buscar issue por ID
    const foundIssue = issues.getById(Number(id))
    
    if (foundIssue) {
      // Buscar usuário
      const user = users.getById(foundIssue.userId)
      setIssue({
        ...foundIssue,
        userName: user?.name || 'Unknown'
      })
    }
    
    setLoading(false)
  }, [id])

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center py-12">
          <p className="text-gray-500">Carregando...</p>
        </div>
      </div>
    )
  }

  if (!issue) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Missão não encontrada</h2>
          <Link to="/" className="text-blue-600 hover:text-blue-700">
            Voltar para lista
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Voltar para lista
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="mb-6">
            <div className="flex items-start justify-between mb-4">
              <h1 className="text-3xl font-bold text-gray-800">
                Missão #{issue.id}
              </h1>
              <div className="flex gap-2">
                <Link
                  to={`/issues/${issue.id}/edit`}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg transition-colors"
                >
                  Editar
                </Link>
                <button
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Excluir
                </button>
              </div>
            </div>
            
            <h2 className="text-xl text-gray-700 mb-4">{issue.title}</h2>
            
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Por {issue.userName}</span>
              <span>•</span>
              <span>Criada em {new Date(issue.createdAt).toLocaleDateString('pt-BR')}</span>
            </div>
          </div>

          {issue.description && (
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Descrição</h3>
              <p className="text-gray-600 whitespace-pre-wrap">{issue.description}</p>
            </div>
          )}

          {!issue.description && (
            <div className="border-t pt-6">
              <p className="text-gray-500 italic">Sem descrição</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}