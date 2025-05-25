import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { IssuesListSimple } from './pages/IssuesListSimple'
import { CreateIssueSimple } from './pages/CreateIssueSimple'
import { IssueDetailSimple } from './pages/IssueDetailSimple'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<IssuesListSimple />} />
        <Route path="/issues/new" element={<CreateIssueSimple />} />
        <Route path="/issues/:id" element={<IssueDetailSimple />} />
      </Routes>
    </BrowserRouter>
  )
}