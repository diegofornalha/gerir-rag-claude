import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useState, useRef, useEffect } from 'react'

// Importar páginas antigas
import { PotentialIssues } from './pages/PotentialIssues'
import { Missions } from './pages/Missions'
import { ClaudeSessions } from './pages/ClaudeSessions'
import { Chat } from './pages/Chat'
import Documents from './pages/Documents'
import { ClaudeSessionDetailSimple } from './pages/ClaudeSessionDetailSimple'
import { RAGManagerEnhanced } from './components/RAGManagerEnhanced'

// Criar QueryClient
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: false // Desabilitar retry por enquanto para evitar erros
    }
  }
})

// Componente de Navegação
function Navigation() {
  const location = useLocation()
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  const isActive = (path: string) => {
    return location.pathname === path
  }
  
  // Fechar dropdown ao clicar fora
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])
  
  return (
    <nav className="bg-white shadow-sm mb-6">
      <div className="container mx-auto px-4 py-3">
        <div className="flex space-x-6 flex-wrap items-center">
          {/* Páginas Antigas */}
          
          <Link 
            to="/claude-sessions" 
            className={`font-medium transition-colors ${
              isActive('/claude-sessions') || location.pathname.startsWith('/claude-sessions/') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Claude Sessions
          </Link>
          
          <Link 
            to="/documents" 
            className={`font-medium transition-colors ${
              isActive('/documents') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Documentos
          </Link>
          
          {/* Separador */}
          <span className="text-gray-300">|</span>
          
          {/* Páginas Novas - Sistema de Migração */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className={`font-medium transition-colors flex items-center gap-1 ${
                isActive('/') || isActive('/potential-issues') || isActive('/missions') || isActive('/chat') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
              }`}
            >
              Em desenvolvimento
              <svg className={`w-4 h-4 transition-transform ${showDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showDropdown && (
              <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                <Link
                  to="/"
                  onClick={() => setShowDropdown(false)}
                  className={`block px-4 py-2 text-sm hover:bg-gray-100 ${
                    isActive('/') ? 'bg-gray-100 text-blue-800' : 'text-gray-700'
                  }`}
                >
                  Dashboard Principal
                </Link>
                <Link
                  to="/potential-issues"
                  onClick={() => setShowDropdown(false)}
                  className={`block px-4 py-2 text-sm hover:bg-gray-100 ${
                    isActive('/potential-issues') ? 'bg-gray-100 text-blue-800' : 'text-gray-700'
                  }`}
                >
                  Potenciais Problemas
                </Link>
                <Link
                  to="/missions"
                  onClick={() => setShowDropdown(false)}
                  className={`block px-4 py-2 text-sm hover:bg-gray-100 ${
                    isActive('/missions') ? 'bg-gray-100 text-blue-800' : 'text-gray-700'
                  }`}
                >
                  Missões
                </Link>
                <Link
                  to="/chat"
                  onClick={() => setShowDropdown(false)}
                  className={`block px-4 py-2 text-sm hover:bg-gray-100 ${
                    isActive('/chat') ? 'bg-gray-100 text-blue-800' : 'text-gray-700'
                  }`}
                >
                  Chat
                </Link>
                <Link
                  to="/rag"
                  onClick={() => setShowDropdown(false)}
                  className={`block px-4 py-2 text-sm hover:bg-gray-100 ${
                    isActive('/rag') ? 'bg-gray-100 text-blue-800' : 'text-gray-700'
                  }`}
                >
                  RAG Manager
                </Link>
              </div>
            )}
          </div>
          



        </div>
      </div>
    </nav>
  )
}

// Dashboard Principal
function MigrationDashboard() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Abas do Menu em Desenvolvimento</h1>
      
      <div className="bg-white rounded-lg shadow-md p-6 max-w-2xl">
        <ul className="space-y-4">
          <li className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <span className="font-medium">Potenciais Problemas</span>
            <span className="text-green-600 text-sm">✓ Funcionando</span>
          </li>
          <li className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <span className="font-medium">Claude Sessions</span>
            <span className="text-green-600 text-sm">✓ Funcionando</span>
          </li>
          <li className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <span className="font-medium">Documentos</span>
            <span className="text-green-600 text-sm">✓ Funcionando</span>
          </li>
          <li className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg border border-yellow-200">
            <span className="font-medium">Dashboard Principal</span>
            <span className="text-yellow-600 text-sm">🚧 Em desenvolvimento</span>
          </li>
          <li className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg border border-yellow-200">
            <span className="font-medium">Missões</span>
            <span className="text-yellow-600 text-sm">🚧 Em desenvolvimento</span>
          </li>
          <li className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg border border-yellow-200">
            <span className="font-medium">Chat</span>
            <span className="text-yellow-600 text-sm">🚧 Em desenvolvimento</span>
          </li>
          <li className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
            <span className="font-medium">RAG Manager</span>
            <span className="text-green-600 text-sm">✨ Novo</span>
          </li>
        </ul>
      </div>
    </div>
  )
}



// Página de Rollout
function RolloutPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Controle de Rollout</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Progresso do Rollout</h3>
          <div className="text-center">
            <div className="text-5xl font-bold text-blue-600 mb-2">15%</div>
            <div className="text-gray-600">dos usuários migrados</div>
            <div className="mt-4 bg-gray-200 rounded-full h-3">
              <div className="bg-blue-600 h-3 rounded-full" style={{ width: '15%' }}></div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Métricas de Sucesso</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Taxa de Erro</span>
              <span className="font-bold text-green-600">0.2%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Performance</span>
              <span className="font-bold text-green-600">+12%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Satisfação</span>
              <span className="font-bold text-green-600">4.8/5</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Controles</h3>
          <div className="space-y-3">
            <button className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600">
              Aumentar para 20%
            </button>
            <button className="w-full bg-yellow-500 text-white py-2 rounded hover:bg-yellow-600">
              Pausar Rollout
            </button>
            <button className="w-full bg-red-500 text-white py-2 rounded hover:bg-red-600">
              Rollback
            </button>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Feature Flags Ativos</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
            <div>
              <div className="font-medium">offline-first-mode</div>
              <div className="text-sm text-gray-600">Habilita modo offline completo</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" checked readOnly className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
            <div>
              <div className="font-medium">local-embeddings</div>
              <div className="text-sm text-gray-600">Processamento de embeddings local</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" checked readOnly className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  )
}

// Página de Configurações
function SettingsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Configurações do Sistema</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Banco de Dados</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Modo de Armazenamento
              </label>
              <select className="w-full p-2 border rounded">
                <option>IndexedDB (Recomendado)</option>
                <option>WebSQL</option>
                <option>LocalStorage</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tamanho Máximo (MB)
              </label>
              <input type="number" defaultValue="500" className="w-full p-2 border rounded" />
            </div>
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" defaultChecked />
                <span className="text-sm">Compressão automática</span>
              </label>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Sincronização</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Intervalo (segundos)
              </label>
              <input type="number" defaultValue="15" className="w-full p-2 border rounded" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estratégia de Conflito
              </label>
              <select className="w-full p-2 border rounded">
                <option>Última escrita vence</option>
                <option>Merge automático</option>
                <option>Perguntar ao usuário</option>
              </select>
            </div>
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" defaultChecked />
                <span className="text-sm">Sync automático ao ficar online</span>
              </label>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Performance</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cache TTL (minutos)
              </label>
              <input type="number" defaultValue="60" className="w-full p-2 border rounded" />
            </div>
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" defaultChecked />
                <span className="text-sm">Lazy loading de componentes</span>
              </label>
            </div>
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" defaultChecked />
                <span className="text-sm">Pré-cache de recursos críticos</span>
              </label>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Segurança</h2>
          <div className="space-y-4">
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" defaultChecked />
                <span className="text-sm">Criptografia local</span>
              </label>
            </div>
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="mr-2" defaultChecked />
                <span className="text-sm">Validação de integridade</span>
              </label>
            </div>
            <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
              Limpar todos os dados locais
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}


// App Principal
function AppContent() {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation />
      
      <Routes>
        {/* Páginas Antigas */}
        <Route path="/potential-issues" element={<PotentialIssues />} />
        <Route path="/missions" element={<Missions />} />
        <Route path="/claude-sessions" element={<ClaudeSessions />} />
        <Route path="/claude-sessions/:sessionId" element={<ClaudeSessionDetailSimple />} />
        <Route path="/claude-sessions/:sessionId/:filter" element={<ClaudeSessionDetailSimple />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/rag" element={<RAGManagerEnhanced />} />
        
        {/* Dashboard Principal - Sistema de Migração */}
        <Route path="/" element={<MigrationDashboard />} />
        
        {/* Páginas do Sistema de Migração */}
      </Routes>
    </div>
  )
}

// Componente App com Providers
export function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
        <Toaster position="top-right" />
      </QueryClientProvider>
    </ErrorBoundary>
  )
}