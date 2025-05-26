import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
// Removido imports de ícones - usando emojis diretamente
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface Document {
  sessionId: string;
  customName?: string;
  size: number;
  modifiedAt: string;
  lines: number;
  path: string;
  hasTodos?: boolean;
  todosCount?: number;
}

interface DocumentContent {
  content: string;
  lines: number;
}

export default function Documents() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [documentContent, setDocumentContent] = useState<DocumentContent | null>(null);
  const [customName, setCustomName] = useState('');
  const [viewPage, setViewPage] = useState(1);
  const linesPerPage = 100;

  // Buscar lista de documentos
  const { data: documents, isLoading, error } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await fetch('http://localhost:3333/api/documents');
      if (!response.ok) throw new Error('Erro ao buscar documentos');
      return response.json();
    },
  });

  // Buscar conteúdo de um documento
  const fetchDocumentContent = async (sessionId: string, page: number = 1) => {
    const response = await fetch(
      `http://localhost:3333/api/documents/${sessionId}/content?page=${page}&limit=${linesPerPage}`
    );
    if (!response.ok) throw new Error('Erro ao buscar conteúdo');
    const data = await response.json();
    setDocumentContent(data);
  };

  // Mutation para atualizar nome customizado
  const updateNameMutation = useMutation({
    mutationFn: async ({ sessionId, customName }: { sessionId: string; customName: string }) => {
      const response = await fetch(`http://localhost:3333/api/documents/${sessionId}/name`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customName }),
      });
      if (!response.ok) throw new Error('Erro ao atualizar nome');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setEditModalOpen(false);
      setSelectedDocument(null);
    },
  });

  // Mutation para excluir documento
  const deleteMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await fetch(`http://localhost:3333/api/documents/${sessionId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Erro ao excluir documento');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setDeleteModalOpen(false);
      setSelectedDocument(null);
    },
  });

  // Download de documento
  const handleDownload = async (doc: Document) => {
    try {
      const response = await fetch(`http://localhost:3333/api/documents/${doc.sessionId}/download`);
      if (!response.ok) throw new Error('Erro ao baixar arquivo');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${doc.customName || doc.sessionId}.jsonl`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Erro ao baixar:', error);
    }
  };

  // Abrir modal de visualização
  const handleView = async (doc: Document) => {
    setSelectedDocument(doc);
    setViewPage(1);
    await fetchDocumentContent(doc.sessionId, 1);
    setViewModalOpen(true);
  };

  // Abrir modal de edição
  const handleEdit = (doc: Document) => {
    setSelectedDocument(doc);
    setCustomName(doc.customName || '');
    setEditModalOpen(true);
  };

  // Abrir modal de exclusão
  const handleDelete = (doc: Document) => {
    setSelectedDocument(doc);
    setDeleteModalOpen(true);
  };

  // Formatar tamanho do arquivo
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Filtrar documentos
  const filteredDocuments = documents?.filter(doc => {
    const searchLower = searchTerm.toLowerCase();
    return (
      doc.sessionId.toLowerCase().includes(searchLower) ||
      (doc.customName && doc.customName.toLowerCase().includes(searchLower))
    );
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600 text-center p-4">
        Erro ao carregar documentos: {error.message}
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Documentos / Projects</h1>
        <p className="text-gray-600">Gerencie os arquivos JSONL do sistema</p>
      </div>

      {/* Barra de busca */}
      <div className="mb-6">
        <div className="relative">
          <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
          <input
            type="text"
            placeholder="Buscar por nome ou ID..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Lista de documentos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Documento
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tamanho
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Linhas
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Modificado
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tem Todos
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Tarefas
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredDocuments?.map((doc) => (
              <tr key={doc.sessionId} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className="text-gray-400 mr-3">📄</span>
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {doc.customName || doc.sessionId}
                      </div>
                      {doc.customName && (
                        <div className="text-xs text-gray-500">{doc.sessionId}</div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-900">
                    <span className="text-gray-400 mr-2">💾</span>
                    {formatFileSize(doc.size)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {doc.lines.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm text-gray-900">
                    <span className="text-gray-400 mr-2">📅</span>
                    {format(new Date(doc.modifiedAt), 'dd/MM/yyyy HH:mm', { locale: ptBR })}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  {doc.hasTodos ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      ✅ Sim
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      ❌ Não
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                  {doc.hasTodos ? (
                    <Link
                      to={`/claude-sessions/${doc.sessionId}`}
                      className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                    >
                      {(doc.todosCount || 0).toLocaleString()}
                    </Link>
                  ) : (
                    '-'
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => handleView(doc)}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                    title="Visualizar"
                  >
                    <span>👁️</span>
                  </button>
                  <button
                    onClick={() => handleEdit(doc)}
                    className="text-green-600 hover:text-green-900 mr-3"
                    title="Editar nome"
                  >
                    <span>✏️</span>
                  </button>
                  <button
                    onClick={() => handleDownload(doc)}
                    className="text-gray-600 hover:text-gray-900 mr-3"
                    title="Download"
                  >
                    <span>⬇️</span>
                  </button>
                  <button
                    onClick={() => handleDelete(doc)}
                    className="text-red-600 hover:text-red-900"
                    title="Excluir"
                  >
                    <span>🗑️</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredDocuments?.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Nenhum documento encontrado
          </div>
        )}
      </div>

      {/* Modal de Visualização */}
      {viewModalOpen && selectedDocument && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                {selectedDocument.customName || selectedDocument.sessionId}
              </h3>
              <button
                onClick={() => setViewModalOpen(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">Fechar</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {documentContent && (
              <>
                <div className="mb-4 text-sm text-gray-600">
                  Mostrando linhas {((viewPage - 1) * linesPerPage) + 1} - {Math.min(viewPage * linesPerPage, selectedDocument.lines)} de {selectedDocument.lines}
                </div>

                <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto max-h-96 text-xs">
                  {documentContent.content}
                </pre>

                <div className="mt-4 flex justify-between">
                  <button
                    onClick={async () => {
                      const newPage = viewPage - 1;
                      setViewPage(newPage);
                      await fetchDocumentContent(selectedDocument.sessionId, newPage);
                    }}
                    disabled={viewPage === 1}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Anterior
                  </button>
                  <span className="flex items-center text-gray-600">
                    Página {viewPage} de {Math.ceil(selectedDocument.lines / linesPerPage)}
                  </span>
                  <button
                    onClick={async () => {
                      const newPage = viewPage + 1;
                      setViewPage(newPage);
                      await fetchDocumentContent(selectedDocument.sessionId, newPage);
                    }}
                    disabled={viewPage * linesPerPage >= selectedDocument.lines}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Próxima
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Modal de Edição */}
      {editModalOpen && selectedDocument && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Editar Nome do Documento
            </h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID do Documento
              </label>
              <input
                type="text"
                value={selectedDocument.sessionId}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nome Customizado
              </label>
              <input
                type="text"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                placeholder="Digite um nome descritivo..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setEditModalOpen(false);
                  setSelectedDocument(null);
                }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  updateNameMutation.mutate({
                    sessionId: selectedDocument.sessionId,
                    customName: customName.trim(),
                  });
                }}
                disabled={updateNameMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {updateNameMutation.isPending ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmação de Exclusão */}
      {deleteModalOpen && selectedDocument && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Confirmar Exclusão
            </h3>
            
            <p className="text-gray-600 mb-6">
              Tem certeza que deseja excluir o documento{' '}
              <strong>{selectedDocument.customName || selectedDocument.sessionId}</strong>?
              Esta ação não pode ser desfeita.
            </p>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setDeleteModalOpen(false);
                  setSelectedDocument(null);
                }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              >
                Cancelar
              </button>
              <button
                onClick={() => deleteMutation.mutate(selectedDocument.sessionId)}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMutation.isPending ? 'Excluindo...' : 'Excluir'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}