import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { IssuesListLocal } from './pages/IssuesListLocal'
import { CreateIssue } from './pages/CreateIssue'
import { IssueDetail } from './pages/IssueDetail'
import { ClaudeSessions } from './pages/ClaudeSessions'
import { ClaudeSessionDetail } from './pages/ClaudeSessionDetail'
import { CurrentSession } from './pages/CurrentSession'

const queryClient = new QueryClient()

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-100">
          <nav className="bg-white shadow-sm mb-6">
            <div className="container mx-auto px-4 py-3">
              <div className="flex space-x-6">
                <Link to="/" className="text-blue-600 hover:text-blue-800 font-medium">
                  Issues
                </Link>
                <Link to="/claude-sessions" className="text-blue-600 hover:text-blue-800 font-medium">
                  Claude Sessions
                </Link>
                <Link to="/current-session" className="text-blue-600 hover:text-blue-800 font-medium">
                  Sessão Atual
                </Link>
              </div>
            </div>
          </nav>
          
          <Routes>
            <Route path="/" element={<IssuesListLocal />} />
            <Route path="/issues/new" element={<CreateIssue />} />
            <Route path="/issues/:id" element={<IssueDetail />} />
            <Route path="/claude-sessions" element={<ClaudeSessions />} />
            <Route path="/claude-sessions/:sessionId" element={<ClaudeSessionDetail />} />
            <Route path="/current-session" element={<CurrentSession />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
