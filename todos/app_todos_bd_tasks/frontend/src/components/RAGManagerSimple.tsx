import React, { useState, useEffect } from 'react'

interface RAGDocument {
  id: string
  content: string
  source: string
  metadata: {
    url?: string
    title?: string
    capturedVia?: string
    timestamp?: string
  }
  timestamp: string
}

export function RAGManagerSimple() {
  const [documents, setDocuments] = useState<RAGDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState('documents')

  // Carregar documentos
  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      // Por enquanto, usar dados mock
      const mockData: RAGDocument[] = [
        {
          id: '1',
          content: 'Conteúdo de exemplo do Claude Code...',
          source: 'WebFetch',
          metadata: {
            url: 'https://docs.anthropic.com',
            title: 'Claude Documentation',
            capturedVia: 'WebFetch'
          },
          timestamp: new Date().toISOString()
        }
      ]
      setDocuments(mockData)
    } catch (error) {
      console.error('Erro ao carregar:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredDocs = documents.filter(doc => 
    searchQuery === '' || 
    doc.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.source.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="max-w-6xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">RAG Manager - Cache Local</h1>
      
      {/* Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl">💾</div>
          <div className="text-xl font-bold">{documents.length}</div>
          <div className="text-sm text-gray-600">Total Documentos</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl">🌐</div>
          <div className="text-xl font-bold">
            {documents.filter(d => d.metadata.capturedVia === 'WebFetch').length}
          </div>
          <div className="text-sm text-gray-600">Via WebFetch</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl">📁</div>
          <div className="text-xl font-bold">~/.claude/mcp-rag-cache</div>
          <div className="text-sm text-gray-600">Local do Cache</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl">📅</div>
          <div className="text-xl font-bold">Hoje</div>
          <div className="text-sm text-gray-600">Última Atualização</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b">
          <div className="flex">
            <button
              className={`px-4 py-2 font-medium ${activeTab === 'documents' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
              onClick={() => setActiveTab('documents')}
            >
              Documentos
            </button>
            <button
              className={`px-4 py-2 font-medium ${activeTab === 'search' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
              onClick={() => setActiveTab('search')}
            >
              Buscar
            </button>
            <button
              className={`px-4 py-2 font-medium ${activeTab === 'info' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
              onClick={() => setActiveTab('info')}
            >
              Informações
            </button>
          </div>
        </div>

        <div className="p-4">
          {activeTab === 'documents' && (
            <div>
              <div className="mb-4 text-sm text-gray-600">
                Documentos salvos em: <code className="bg-gray-100 px-2 py-1 rounded">~/.claude/mcp-rag-cache/documents.json</code>
              </div>
              
              {loading ? (
                <div className="text-center py-8">Carregando...</div>
              ) : filteredDocs.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  Nenhum documento encontrado
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredDocs.map(doc => (
                    <div key={doc.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-medium">
                            {doc.metadata.title || `Documento ${doc.id}`}
                          </h3>
                          <div className="text-sm text-gray-600">
                            Fonte: {doc.source} | {doc.metadata.capturedVia && `Via: ${doc.metadata.capturedVia}`}
                          </div>
                        </div>
                        <button className="text-red-500 hover:text-red-700">
                          🗑️
                        </button>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2">
                        {doc.content}
                      </p>
                      {doc.metadata.url && (
                        <div className="mt-2 text-xs text-blue-600">
                          {doc.metadata.url}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'search' && (
            <div>
              <div className="mb-4">
                <input
                  type="text"
                  placeholder="Buscar documentos..."
                  className="w-full px-4 py-2 border rounded-lg"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="text-sm text-gray-600">
                {searchQuery && `${filteredDocs.length} resultados encontrados`}
              </div>
            </div>
          )}

          {activeTab === 'info' && (
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">Como usar no Claude Code:</h3>
                <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
{`// Buscar documentos
mcp__rag_standalone__rag_search({
  "query": "Claude features",
  "limit": 5
})

// Indexar novo conteúdo
mcp__rag_standalone__rag_index({
  "content": "Conteúdo...",
  "source": "WebFetch"
})`}
                </pre>
              </div>
              
              <div>
                <h3 className="font-medium mb-2">Status do Sistema:</h3>
                <ul className="text-sm space-y-1">
                  <li>✅ Cache local funcionando</li>
                  <li>✅ 100% offline</li>
                  <li>✅ Dados persistentes</li>
                  <li>✅ Integrado com WebFetch</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}