import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { issues } from '../db/collections/issues-local'
import { users } from '../db/collections/users-local'

export function IssuesListLocal() {
  const [issuesList, setIssuesList] = useState<any[]>([])

  useEffect(() => {
    // Buscar issues e fazer join manual com users
    const allIssues = issues.getAll()
    const allUsers = users.getAll()
    
    const issuesWithUsers = allIssues.map(issue => {
      const user = allUsers.find(u => u.id === issue.userId)
      return {
        ...issue,
        userName: user?.name || 'Unknown'
      }
    }).sort((a, b) => b.id - a.id)
    
    setIssuesList(issuesWithUsers)
  }, [])

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-4xl font-bold">Issues</h1>
          <Link
            to="/issues/new"
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Nova Issue
          </Link>
        </div>

        <div className="grid gap-4">
          {issuesList.map((issue) => (
            <Link
              key={issue.id}
              to={`/issues/${issue.id}`}
              className="block rounded-lg bg-zinc-900 p-6 hover:bg-zinc-800"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h2 className="text-xl font-semibold">
                    #{issue.id} - {issue.title}
                  </h2>
                  {issue.description && (
                    <p className="mt-2 text-zinc-400">
                      {issue.description}
                    </p>
                  )}
                  <div className="mt-4 flex items-center gap-4 text-sm text-zinc-500">
                    <span>Por {issue.userName}</span>
                    <span>
                      {new Date(issue.createdAt).toLocaleDateString('pt-BR')}
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {issuesList.length === 0 && (
          <div className="text-center text-zinc-500 mt-8">
            Nenhuma issue encontrada
          </div>
        )}
      </div>
    </div>
  )
}