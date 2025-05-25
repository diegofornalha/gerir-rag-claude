import fastify from 'fastify'
import cors from '@fastify/cors'
import { ClaudeIntegration } from '../claude/integration'

const app = fastify({
  logger: true
})

// Registrar CORS
await app.register(cors, {
  origin: true,
  credentials: true
})

const claude = new ClaudeIntegration()

// Rota de teste
app.get('/api/health', async (request, reply) => {
  return { status: 'ok', timestamp: new Date().toISOString() }
})

// Rotas do Claude
app.get('/api/claude-sessions', async (request, reply) => {
  try {
    const sessions = await claude.getAllSessions()
    return {
      success: true,
      count: sessions.length,
      sessions
    }
  } catch (error) {
    console.error('Erro ao buscar sessões:', error)
    return reply.status(500).send({
      success: false,
      error: 'Erro ao buscar sessões'
    })
  }
})

app.get('/api/claude-sessions/:sessionId', async (request, reply) => {
  const { sessionId } = request.params as { sessionId: string }
  
  try {
    const session = await claude.getSessionDetails(sessionId)
    
    if (!session) {
      return reply.status(404).send({
        success: false,
        error: 'Sessão não encontrada'
      })
    }

    return {
      success: true,
      session
    }
  } catch (error) {
    console.error('Erro ao buscar sessão:', error)
    return reply.status(500).send({
      success: false,
      error: 'Erro ao buscar detalhes da sessão'
    })
  }
})

app.get('/api/claude-sessions/:sessionId/todos', async (request, reply) => {
  const { sessionId } = request.params as { sessionId: string }
  
  try {
    const session = await claude.getSessionDetails(sessionId)
    
    if (!session) {
      return reply.status(404).send({
        success: false,
        error: 'Sessão não encontrada'
      })
    }

    const todos = session.todos
    const stats = {
      total: todos.length,
      pending: todos.filter((t: any) => t.status === 'pending').length,
      inProgress: todos.filter((t: any) => t.status === 'in_progress').length,
      completed: todos.filter((t: any) => t.status === 'completed').length
    }

    return {
      success: true,
      sessionId,
      todos,
      stats
    }
  } catch (error) {
    console.error('Erro ao buscar todos:', error)
    return reply.status(500).send({
      success: false,
      error: 'Erro ao buscar todos da sessão'
    })
  }
})

// Iniciar servidor
const start = async () => {
  try {
    await app.listen({ port: 3333, host: '0.0.0.0' })
    console.log('Servidor rodando em http://localhost:3333')
  } catch (err) {
    app.log.error(err)
    process.exit(1)
  }
}

start()