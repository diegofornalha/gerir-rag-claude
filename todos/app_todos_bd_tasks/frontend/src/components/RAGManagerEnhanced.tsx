import React, { useState } from 'react'
import { useRAGDocuments, useRAGStats, useRAGRemoveDocument, useRAGAddBatch } from '../hooks/useRAGDocuments'
import { useRAGRealtimeSearch } from '../hooks/useRAGSearch'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import toast from 'react-hot-toast'

export function RAGManagerEnhanced() {
  const [activeTab, setActiveTab] = useState<'documents' | 'search' | 'add'>('documents')
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null)
  const [urlsToAdd, setUrlsToAdd] = useState('')
  
  // Hooks de dados
  const { data: documents = [], isLoading: loadingDocs, error: docsError } = useRAGDocuments(50)
  const { data: stats, isLoading: loadingStats } = useRAGStats()
  const removeDoc = useRAGRemoveDocument()
  const addBatch = useRAGAddBatch()
  
  // Hook de busca em tempo real
  const search = useRAGRealtimeSearch({ 
    minQueryLength: 3, 
    debounceMs: 300,
    limit: 20 
  })
  
  // Estatísticas calculadas
  const totalDocs = documents.length
  const webDocs = documents.filter(d => d.metadata?.capturedVia === 'WebFetch').length
  const sessionDocs = documents.filter(d => d.metadata?.type === 'session').length
  
  const handleRemoveDocument = async (docId: string) => {
    removeDoc.mutate(docId)
  }
  
  const handleAddUrls = async () => {
    const urls = urlsToAdd
      .split('\n')
      .map(url => url.trim())
      .filter(url => url.startsWith('http'))
    
    if (urls.length === 0) {
      toast.error('Adicione URLs válidas (uma por linha)')
      return
    }
    
    addBatch.mutate(urls, {
      onSuccess: () => {
        setUrlsToAdd('')
        setActiveTab('documents')
      }
    })
  }
  
  const exportCache = () => {
    const dataStr = JSON.stringify(documents, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    
    const link = document.createElement('a')
    link.setAttribute('href', dataUri)
    link.setAttribute('download', `rag-cache-${new Date().toISOString()}.json`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    toast.success('Cache exportado!')
  }
  
  // Não mostrar erro se for apenas um cache vazio
  if (docsError && !docsError.toString().includes('500')) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <p className="font-semibold">Erro ao carregar documentos</p>
        <p className="text-sm mt-1">{docsError.toString()}</p>
      </div>
    )
  }
  
  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">🧠 RAG Manager - Cache Local</h1>
        <p className="text-gray-600">Sistema de recuperação aumentada por geração em tempo real</p>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-500 text-sm">Total de Documentos</span>
            <span className="text-2xl font-bold text-blue-600">{totalDocs}</span>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-500 text-sm">Via WebFetch</span>
            <span className="text-2xl font-bold text-green-600">{webDocs}</span>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-500 text-sm">Sessões Claude</span>
            <span className="text-2xl font-bold text-purple-600">{sessionDocs}</span>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-500 text-sm">Cache Local</span>
            <span className="text-xs font-mono text-gray-600">~/.claude/mcp-rag-cache</span>
          </div>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-6 py-3 text-sm font-medium ${
                activeTab === 'documents'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              📄 Documentos ({totalDocs})
            </button>
            
            <button
              onClick={() => setActiveTab('search')}
              className={`px-6 py-3 text-sm font-medium ${
                activeTab === 'search'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              🔍 Buscar
            </button>
            
            <button
              onClick={() => setActiveTab('add')}
              className={`px-6 py-3 text-sm font-medium ${
                activeTab === 'add'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              ➕ Adicionar URLs
            </button>
            
            <button
              onClick={exportCache}
              className="ml-auto px-4 py-2 m-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              📥 Exportar Cache
            </button>
          </nav>
        </div>
        
        <div className="p-6">
          {/* Tab: Documents */}
          {activeTab === 'documents' && (
            <div>
              {loadingDocs ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📭</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum documento no cache RAG</h3>
                  <p className="text-gray-600 mb-6">Comece adicionando conteúdo ao sistema de recuperação</p>
                  <div className="space-y-2 text-sm text-gray-500">
                    <p>• Use o WebFetch para capturar páginas web</p>
                    <p>• Adicione URLs manualmente na aba "Adicionar URLs"</p>
                    <p>• Os documentos serão salvos localmente em ~/.claude/mcp-rag-cache</p>
                  </div>
                  <button
                    onClick={() => setActiveTab('add')}
                    className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Adicionar URLs
                  </button>
                </div>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className={`border rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer ${
                        selectedDoc === doc.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                      }`}
                      onClick={() => setSelectedDoc(selectedDoc === doc.id ? null : doc.id)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900">
                            {doc.metadata?.title || doc.source}
                          </h3>
                          {doc.metadata?.url && (
                            <a
                              href={doc.metadata.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {new URL(doc.metadata.url).hostname}
                            </a>
                          )}
                          <p className="text-sm text-gray-600 mt-1">
                            {doc.content.substring(0, 150)}...
                          </p>
                          {selectedDoc === doc.id && (
                            <pre className="mt-3 p-3 bg-gray-100 rounded text-xs overflow-x-auto">
                              {doc.content}
                            </pre>
                          )}
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          <span className="text-xs text-gray-500">
                            {format(new Date(doc.timestamp), 'dd/MM HH:mm')}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleRemoveDocument(doc.id)
                            }}
                            className="text-red-500 hover:text-red-700"
                            disabled={removeDoc.isPending}
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {/* Tab: Search */}
          {activeTab === 'search' && (
            <div>
              <div className="mb-4">
                <input
                  type="text"
                  value={search.query}
                  onChange={(e) => search.setQuery(e.target.value)}
                  placeholder="Digite pelo menos 3 caracteres para buscar..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {search.isSearching && (
                  <p className="text-sm text-gray-500 mt-2">Buscando...</p>
                )}
              </div>
              
              {search.error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                  <p className="text-sm text-red-700">{search.error}</p>
                </div>
              )}
              
              {search.hasResults && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600 mb-2">
                    {search.results.length} resultados encontrados
                  </p>
                  {search.results.map((result) => (
                    <div key={result.id} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">
                            {result.metadata?.title || result.source}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {result.content.substring(0, 200)}...
                          </p>
                          {result.similarity && (
                            <span className="text-xs text-green-600 mt-2 inline-block">
                              Relevância: {(result.similarity * 100).toFixed(1)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {!search.hasResults && search.query && !search.isSearching && (
                <p className="text-center text-gray-500 py-8">
                  Nenhum resultado encontrado
                </p>
              )}
            </div>
          )}
          
          {/* Tab: Add URLs */}
          {activeTab === 'add' && (
            <div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  URLs para Indexar (uma por linha)
                </label>
                <textarea
                  value={urlsToAdd}
                  onChange={(e) => setUrlsToAdd(e.target.value)}
                  placeholder="https://example.com/docs&#10;https://another-site.com/api"
                  className="w-full h-40 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-600">
                  As URLs serão processadas via WebFetch e adicionadas ao cache RAG
                </p>
                <button
                  onClick={handleAddUrls}
                  disabled={!urlsToAdd.trim() || addBatch.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {addBatch.isPending ? 'Processando...' : 'Adicionar URLs'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}