import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { IssuesList } from './pages/IssuesList'
import { CreateIssue } from './pages/CreateIssue'
import { IssueDetail } from './pages/IssueDetail'
import { ClaudeSessions } from './pages/ClaudeSessions'

export function App() {
  return (
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
            </div>
          </div>
        </nav>
        
        <Routes>
          <Route path="/" element={<IssuesList />} />
          <Route path="/issues/new" element={<CreateIssue />} />
          <Route path="/issues/:id" element={<IssueDetail />} />
          <Route path="/claude-sessions" element={<ClaudeSessions />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
