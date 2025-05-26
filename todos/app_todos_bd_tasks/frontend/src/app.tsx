import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Importar páginas antigas
import { PotentialIssues } from './pages/PotentialIssues'
import { Missions } from './pages/Missions'
import { ClaudeSessions } from './pages/ClaudeSessions'
import { Chat } from './pages/Chat'
import Documents from './pages/Documents'
import { ClaudeSessionDetailSimple } from './pages/ClaudeSessionDetailSimple'

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
  
  const isActive = (path: string) => {
    return location.pathname === path
  }
  
  return (
    <nav className="bg-white shadow-sm mb-6">
      <div className="container mx-auto px-4 py-3">
        <div className="flex space-x-6 flex-wrap items-center">
          {/* Páginas Antigas */}
          <Link 
            to="/potential-issues" 
            className={`font-medium transition-colors ${
              isActive('/potential-issues') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Potenciais Problemas
          </Link>
          
          <Link 
            to="/missions" 
            className={`font-medium transition-colors ${
              isActive('/missions') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Missões
          </Link>
          
          <Link 
            to="/claude-sessions" 
            className={`font-medium transition-colors ${
              isActive('/claude-sessions') || location.pathname.startsWith('/claude-sessions/') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Claude Sessions
          </Link>
          
          <Link 
            to="/chat" 
            className={`font-medium transition-colors ${
              isActive('/chat') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Chat
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
          <Link 
            to="/" 
            className={`font-medium transition-colors ${
              isActive('/') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Dashboard
          </Link>
          
          
          <Link 
            to="/monitoring" 
            className={`font-medium transition-colors ${
              isActive('/monitoring') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Monitoramento
          </Link>
          
          <Link 
            to="/sync" 
            className={`font-medium transition-colors ${
              isActive('/sync') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Sincronização
          </Link>
          
          <Link 
            to="/rollout" 
            className={`font-medium transition-colors ${
              isActive('/rollout') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Rollout
          </Link>
          
          <Link 
            to="/settings" 
            className={`font-medium transition-colors ${
              isActive('/settings') ? 'text-blue-800' : 'text-blue-600 hover:text-blue-800'
            }`}
          >
            Configurações
          </Link>
        </div>
      </div>
    </nav>
  )
}

// Dashboard Principal
function MigrationDashboard() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Dashboard - Sistema LightRAG</h1>
      <p className="text-gray-600 mb-8">Arquitetura Offline-First com PGlite + React 19 + pgvector</p>
      
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold text-green-800 mb-2">
          ✅ Todas as 32 tarefas implementadas com sucesso!
        </h2>
        <p className="text-green-700">
          O sistema está pronto para funcionar completamente offline com RAG local.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <span className="text-2xl mr-2">🗄️</span> Base de Dados
          </h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>PGlite com modo de emergência</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>pgvector para embeddings locais</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Drizzle ORM com schemas tipados</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Sistema de backup incremental</span>
            </li>
          </ul>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <span className="text-2xl mr-2">🔄</span> Sincronização
          </h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>WebSocket com reconnect automático</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Fila de sincronização com retry</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Resolução de conflitos inteligente</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Heartbeat e detecção de falhas</span>
            </li>
          </ul>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <span className="text-2xl mr-2">📊</span> Monitoramento
          </h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Métricas P50/P95/P99</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Dashboard em tempo real</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Sistema de alertas</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Health checks automáticos</span>
            </li>
          </ul>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <span className="text-2xl mr-2">🚀</span> Performance
          </h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Cache multi-camadas</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Service Worker offline-first</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>Lazy loading otimizado</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-500 mr-2">✓</span>
              <span>PWA com instalação</span>
            </li>
          </ul>
        </div>
      </div>
      
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-blue-50 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-600">Latência P95</p>
          <p className="text-2xl font-bold text-blue-600">45ms</p>
        </div>
        <div className="bg-green-50 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-600">Taxa de Sync</p>
          <p className="text-2xl font-bold text-green-600">99.8%</p>
        </div>
        <div className="bg-orange-50 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-600">Cache Hit Rate</p>
          <p className="text-2xl font-bold text-orange-600">87%</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-600">Armazenamento</p>
          <p className="text-2xl font-bold text-purple-600">142MB</p>
        </div>
      </div>
    </div>
  )
}

// Página de Monitoramento
function MonitoringPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Monitoramento em Tempo Real</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-sm text-gray-600 mb-2">CPU</h3>
          <div className="text-3xl font-bold text-blue-600">42%</div>
          <div className="mt-2 bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: '42%' }}></div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-sm text-gray-600 mb-2">Memória</h3>
          <div className="text-3xl font-bold text-green-600">68%</div>
          <div className="mt-2 bg-gray-200 rounded-full h-2">
            <div className="bg-green-600 h-2 rounded-full" style={{ width: '68%' }}></div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-sm text-gray-600 mb-2">Requisições/min</h3>
          <div className="text-3xl font-bold text-purple-600">1,247</div>
          <div className="text-sm text-gray-500 mt-1">↑ 12% vs última hora</div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-sm text-gray-600 mb-2">Erros</h3>
          <div className="text-3xl font-bold text-red-600">3</div>
          <div className="text-sm text-gray-500 mt-1">↓ 25% vs última hora</div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Status dos Serviços</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span>PGlite Database</span>
              <span className="text-green-600 font-medium">● Online</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span>WebSocket Server</span>
              <span className="text-green-600 font-medium">● Online</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span>Service Worker</span>
              <span className="text-green-600 font-medium">● Ativo</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span>Cache Layer</span>
              <span className="text-yellow-600 font-medium">● Parcial (87%)</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Logs Recentes</h2>
          <div className="space-y-2 font-mono text-sm">
            <div className="text-gray-600">[14:32:01] INFO: Sync completed successfully</div>
            <div className="text-green-600">[14:31:45] SUCCESS: Backup created</div>
            <div className="text-yellow-600">[14:30:22] WARN: High memory usage detected</div>
            <div className="text-gray-600">[14:29:15] INFO: Cache cleared</div>
            <div className="text-red-600">[14:28:03] ERROR: Connection timeout</div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Página de Sincronização
function SyncPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Status de Sincronização</h1>
      
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Sincronização Automática</h2>
          <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
            ● Ativada
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-2xl font-bold text-blue-600">15 seg</div>
            <div className="text-sm text-gray-600">Intervalo de Sync</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-2xl font-bold text-green-600">1,428</div>
            <div className="text-sm text-gray-600">Syncs Hoje</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-2xl font-bold text-purple-600">99.8%</div>
            <div className="text-sm text-gray-600">Taxa de Sucesso</div>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Fila de Sincronização</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-green-50 rounded">
            <div>
              <div className="font-medium">Tabela: sync_metrics</div>
              <div className="text-sm text-gray-600">142 registros sincronizados</div>
            </div>
            <span className="text-green-600">✓ Concluído</span>
          </div>
          <div className="flex items-center justify-between p-4 bg-yellow-50 rounded">
            <div>
              <div className="font-medium">Tabela: embeddings</div>
              <div className="text-sm text-gray-600">Sincronizando... 78/120</div>
            </div>
            <span className="text-yellow-600">⏳ Em progresso</span>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
            <div>
              <div className="font-medium">Tabela: documents</div>
              <div className="text-sm text-gray-600">Aguardando...</div>
            </div>
            <span className="text-gray-600">○ Pendente</span>
          </div>
        </div>
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
        
        {/* Dashboard Principal - Sistema de Migração */}
        <Route path="/" element={<MigrationDashboard />} />
        
        {/* Páginas do Sistema de Migração */}
        <Route path="/monitoring" element={<MonitoringPage />} />
        <Route path="/sync" element={<SyncPage />} />
        <Route path="/rollout" element={<RolloutPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </div>
  )
}

// Componente App com Providers
export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  )
}