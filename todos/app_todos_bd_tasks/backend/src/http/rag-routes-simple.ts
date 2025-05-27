import { Hono } from 'hono'
import { z } from 'zod'
import { ragService } from '../services/rag-service'

const app = new Hono()

// Schemas
const searchSchema = z.object({
  query: z.string().min(1),
  limit: z.number().int().positive().default(5)
})

const addDocumentSchema = z.object({
  title: z.string().min(1),
  content: z.string().min(1),
  type: z.string().default('general'),
  source: z.string().default('manual'),
  metadata: z.record(z.any()).optional()
})

/**
 * GET /rag/stats - Estatísticas do cache RAG
 */
app.get('/stats', async (c) => {
  const stats = await ragService.getStats()
  return c.json(stats)
})

/**
 * GET /rag/documents - Lista documentos
 */
app.get('/documents', async (c) => {
  const documents = await ragService.listDocuments()
  return c.json({ 
    documents,
    total: documents.length 
  })
})

/**
 * POST /rag/search - Busca documentos
 */
app.post('/search', async (c) => {
  const body = await c.req.json()
  const { query, limit } = searchSchema.parse(body)
  
  const results = await ragService.search(query, limit)
  return c.json({ 
    results,
    query,
    total: results.length 
  })
})

/**
 * POST /rag/add - Adiciona documento
 */
app.post('/add', async (c) => {
  const body = await c.req.json()
  const doc = addDocumentSchema.parse(body)
  
  const newDoc = await ragService.addDocument(doc)
  return c.json({ 
    success: true,
    document: newDoc 
  })
})

/**
 * DELETE /rag/documents/:id - Remove documento
 */
app.delete('/documents/:id', async (c) => {
  const id = c.req.param('id')
  
  const success = await ragService.removeDocument(id)
  if (success) {
    return c.json({ 
      success: true,
      message: 'Documento removido com sucesso' 
    })
  } else {
    return c.json({ 
      error: 'Documento não encontrado' 
    }, 404)
  }
})

/**
 * POST /rag/index-session - Indexa sessão do Claude
 */
app.post('/index-session', async (c) => {
  const { sessionId, messages } = await c.req.json()
  
  await ragService.indexClaudeSession(sessionId, messages)
  
  return c.json({ 
    success: true,
    message: 'Sessão indexada com sucesso' 
  })
})

export default app