/**
 * Integração com Claude Sessions
 * Conecta o sistema de tasks com as sessões do Claude
 */

import { z } from 'zod'
// import { db } from '../db/client' // Removido pois não está sendo usado
// import { eq } from 'drizzle-orm' // Removido pois não está sendo usado
import fs from 'fs/promises'
import path from 'path'
import { watch } from 'chokidar'

// Schemas
const TodoSchema = z.object({
  id: z.string(),
  content: z.string(),
  status: z.enum(['pending', 'in_progress', 'completed']),
  priority: z.enum(['low', 'medium', 'high'])
})

const SessionSchema = z.object({
  sessionId: z.string(),
  todos: z.string(),
  conversation: z.string().nullable(),
  hasConversation: z.boolean(),
  lastModified: z.string(),
  todoCount: z.number(),
  pendingCount: z.number(),
  completedCount: z.number()
})

// Configuração
const CLAUDE_BASE = '/Users/agents/.claude'
const TODOS_DIR = path.join(CLAUDE_BASE, 'todos')
const PROJECTS_DIR = path.join(CLAUDE_BASE, 'projects')

export class ClaudeIntegration {
  private watcher: any = null

  /**
   * Busca todas as sessões do Claude
   */
  async getAllSessions() {
    const todoFiles = await fs.readdir(TODOS_DIR)
    const sessions = []

    for (const file of todoFiles) {
      if (!file.endsWith('.json')) continue
      
      const sessionId = file.replace('.json', '')
      const todoPath = path.join(TODOS_DIR, file)
      
      try {
        const stats = await fs.stat(todoPath)
        const todoContent = await fs.readFile(todoPath, 'utf-8')
        const todos = JSON.parse(todoContent)
        
        // Buscar conversa correspondente
        const conversationPath = await this.findConversationFile(sessionId)
        
        // Verificar se é continuação lendo o arquivo de conversa
        let isContinuation = false
        let originalSessionId = null
        
        if (conversationPath) {
          try {
            const conversationContent = await fs.readFile(conversationPath, 'utf-8')
            const firstLines = conversationContent.split('\n').slice(0, 10).filter(l => l.trim())
            
            for (const line of firstLines) {
              try {
                const entry = JSON.parse(line)
                if (entry.sessionId && entry.sessionId !== sessionId) {
                  isContinuation = true
                  originalSessionId = entry.sessionId
                  break
                }
              } catch {
                // Linha inválida
              }
            }
          } catch {
            // Erro ao ler conversa
          }
        }
        
        sessions.push({
          sessionId,
          todos: todoPath,
          conversation: conversationPath,
          hasConversation: !!conversationPath,
          lastModified: stats.mtime.toISOString(),
          todoCount: todos.length,
          pendingCount: todos.filter((t: any) => t.status === 'pending').length,
          completedCount: todos.filter((t: any) => t.status === 'completed').length,
          isContinuation,
          originalSessionId
        })
      } catch (error) {
        console.error(`Erro ao processar sessão ${sessionId}:`, error)
      }
    }

    return sessions.sort((a, b) => 
      new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime()
    )
  }

  /**
   * Busca arquivo de conversa para uma sessão
   */
  private async findConversationFile(sessionId: string): Promise<string | null> {
    try {
      const projectDirs = await fs.readdir(PROJECTS_DIR)
      
      for (const dir of projectDirs) {
        const conversationPath = path.join(PROJECTS_DIR, dir, `${sessionId}.jsonl`)
        try {
          await fs.access(conversationPath)
          return conversationPath
        } catch {
          // Arquivo não existe neste diretório
        }
      }
    } catch {
      // Erro ao ler diretório de projetos
    }
    
    return null
  }

  /**
   * Busca detalhes de uma sessão específica
   */
  async getSessionDetails(sessionId: string) {
    const todoPath = path.join(TODOS_DIR, `${sessionId}.json`)
    
    try {
      const todoContent = await fs.readFile(todoPath, 'utf-8')
      const todos = JSON.parse(todoContent)
      const conversationPath = await this.findConversationFile(sessionId)
      
      const result = {
        sessionId,
        todos,
        conversation: null as any,
        metadata: {
          isContinuation: false,
          originalSessionId: null as string | null
        } as any
      }

      // Ler conversa se existir
      if (conversationPath) {
        const conversationContent = await fs.readFile(conversationPath, 'utf-8')
        const lines = conversationContent.split('\n').filter(l => l.trim())
        
        // Buscar summary e verificar se é continuação
        for (const line of lines.slice(0, 20)) {
          try {
            const entry = JSON.parse(line)
            
            // Buscar summary
            if (entry.type === 'summary') {
              result.metadata.summary = entry.summary
            }
            
            // Verificar se é continuação (sessionId diferente do arquivo)
            if (entry.sessionId && entry.sessionId !== sessionId) {
              result.metadata.isContinuation = true
              result.metadata.originalSessionId = entry.sessionId
            }
          } catch {
            // Linha inválida
          }
        }
        
        // Pegar primeiras mensagens
        result.conversation = []
        for (const line of lines.slice(0, 20)) {
          try {
            const entry = JSON.parse(line)
            if (entry.type === 'user' && entry.message) {
              result.conversation.push({
                type: 'user',
                content: entry.message.content,
                timestamp: entry.timestamp
              })
            }
          } catch {
            // Linha inválida
          }
        }
      }

      return result
    } catch (error) {
      console.error(`Erro ao buscar detalhes da sessão ${sessionId}:`, error)
      return null
    }
  }

  /**
   * Inicia monitoramento de mudanças nos todos
   */
  startWatching(onChange: (sessionId: string, todos: any[]) => void) {
    this.watcher = watch(path.join(TODOS_DIR, '*.json'), {
      persistent: true,
      ignoreInitial: true
    })

    this.watcher.on('change', async (filePath: string) => {
      const sessionId = path.basename(filePath).replace('.json', '')
      
      try {
        const content = await fs.readFile(filePath, 'utf-8')
        const todos = JSON.parse(content)
        onChange(sessionId, todos)
      } catch (error) {
        console.error(`Erro ao processar mudança em ${filePath}:`, error)
      }
    })

    console.log('Monitoramento de todos iniciado')
  }

  /**
   * Para o monitoramento
   */
  stopWatching() {
    if (this.watcher) {
      this.watcher.close()
      this.watcher = null
      console.log('Monitoramento de todos parado')
    }
  }

  /**
   * Sincroniza todos do Claude com o banco local
   */
  async syncTodosToDatabase(sessionId: string, todos: any[]) {
    // Implementar sincronização com o banco de dados local
    // Pode mapear todos para issues ou criar uma nova tabela
    console.log(`Sincronizando ${todos.length} todos da sessão ${sessionId}`)
    
    // TODO: Implementar lógica de sincronização
    // Por exemplo, criar issues a partir dos todos
  }
}