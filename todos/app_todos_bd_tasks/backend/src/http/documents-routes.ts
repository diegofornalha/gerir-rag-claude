import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { readdir, stat, readFile } from 'fs/promises';
import { join } from 'path';
import { createReadStream } from 'fs';
import { unlink } from 'fs/promises';

const PROJECTS_DIR = '/Users/agents/.claude/projects/-Users-agents--claude';
const CUSTOM_NAMES_FILE = '/Users/agents/.claude/todos/app_todos_bd_tasks/document-names.json';

// Interface para armazenar nomes customizados
interface CustomNames {
  [sessionId: string]: string;
}

// Carregar nomes customizados
async function loadCustomNames(): Promise<CustomNames> {
  try {
    const data = await readFile(CUSTOM_NAMES_FILE, 'utf-8');
    return JSON.parse(data);
  } catch {
    return {};
  }
}

// Salvar nomes customizados
async function saveCustomNames(names: CustomNames): Promise<void> {
  await readFile(CUSTOM_NAMES_FILE, 'utf-8').catch(() => '{}'); // Criar arquivo se não existir
  await readFile(CUSTOM_NAMES_FILE, 'utf-8').then(async () => {
    await readFile(CUSTOM_NAMES_FILE, 'utf-8');
  }).catch(async () => {
    await readFile(CUSTOM_NAMES_FILE, 'utf-8').catch(() => '{}');
  });
  const { writeFile } = await import('fs/promises');
  await writeFile(CUSTOM_NAMES_FILE, JSON.stringify(names, null, 2));
}

export async function documentsRoutes(app: FastifyInstance) {
  // Listar todos os documentos
  app.get('/api/documents', async (request, reply) => {
    try {
      const files = await readdir(PROJECTS_DIR);
      const jsonlFiles = files.filter(f => f.endsWith('.jsonl'));
      const customNames = await loadCustomNames();
      
      const documents = await Promise.all(
        jsonlFiles.map(async (file) => {
          const filePath = join(PROJECTS_DIR, file);
          const stats = await stat(filePath);
          const sessionId = file.replace('.jsonl', '');
          
          // Contar linhas do arquivo
          const content = await readFile(filePath, 'utf-8');
          const lines = content.trim().split('\n').filter(line => line.trim()).length;
          
          // Verificar se existe arquivo de todos associado e contar tarefas
          const todosPath = `/Users/agents/.claude/todos/${sessionId}.json`;
          let hasTodos = false;
          let todosCount = 0;
          try {
            await stat(todosPath);
            hasTodos = true;
            // Ler arquivo de todos e contar tarefas
            const todosContent = await readFile(todosPath, 'utf-8');
            const todosData = JSON.parse(todosContent);
            if (Array.isArray(todosData)) {
              todosCount = todosData.length;
            }
          } catch {
            hasTodos = false;
            todosCount = 0;
          }
          
          return {
            sessionId,
            customName: customNames[sessionId],
            size: stats.size,
            modifiedAt: stats.mtime.toISOString(),
            lines,
            path: filePath,
            hasTodos,
            todosCount
          };
        })
      );
      
      // Ordenar por data de modificação (mais recente primeiro)
      documents.sort((a, b) => new Date(b.modifiedAt).getTime() - new Date(a.modifiedAt).getTime());
      
      return reply.send(documents);
    } catch (error) {
      app.log.error('Erro ao listar documentos:', error);
      return reply.status(500).send({ error: 'Erro ao listar documentos' });
    }
  });
  
  // Obter conteúdo de um documento com paginação
  app.get('/api/documents/:sessionId/content', {
    schema: {
      params: z.object({
        sessionId: z.string()
      }),
      querystring: z.object({
        page: z.coerce.number().int().positive().default(1),
        limit: z.coerce.number().int().positive().max(500).default(100)
      })
    }
  }, async (request, reply) => {
    try {
      const { sessionId } = request.params;
      const { page, limit } = request.query;
      const filePath = join(PROJECTS_DIR, `${sessionId}.jsonl`);
      
      const content = await readFile(filePath, 'utf-8');
      const allLines = content.trim().split('\n').filter(line => line.trim());
      
      const startIndex = (page - 1) * limit;
      const endIndex = startIndex + limit;
      const paginatedLines = allLines.slice(startIndex, endIndex);
      
      return reply.send({
        content: paginatedLines.join('\n'),
        lines: allLines.length,
        page,
        limit,
        totalPages: Math.ceil(allLines.length / limit)
      });
    } catch (error) {
      app.log.error('Erro ao buscar conteúdo:', error);
      return reply.status(404).send({ error: 'Documento não encontrado' });
    }
  });
  
  // Atualizar nome customizado
  app.put('/api/documents/:sessionId/name', {
    schema: {
      params: z.object({
        sessionId: z.string()
      }),
      body: z.object({
        customName: z.string().min(1).max(255)
      })
    }
  }, async (request, reply) => {
    try {
      const { sessionId } = request.params;
      const { customName } = request.body;
      
      // Verificar se o arquivo existe
      const filePath = join(PROJECTS_DIR, `${sessionId}.jsonl`);
      await stat(filePath);
      
      const customNames = await loadCustomNames();
      customNames[sessionId] = customName;
      await saveCustomNames(customNames);
      
      return reply.send({ success: true, customName });
    } catch (error) {
      app.log.error('Erro ao atualizar nome:', error);
      return reply.status(404).send({ error: 'Documento não encontrado' });
    }
  });
  
  // Download de documento
  app.get('/api/documents/:sessionId/download', {
    schema: {
      params: z.object({
        sessionId: z.string()
      })
    }
  }, async (request, reply) => {
    try {
      const { sessionId } = request.params;
      const filePath = join(PROJECTS_DIR, `${sessionId}.jsonl`);
      
      // Verificar se o arquivo existe
      await stat(filePath);
      
      const customNames = await loadCustomNames();
      const filename = customNames[sessionId] 
        ? `${customNames[sessionId]}.jsonl`
        : `${sessionId}.jsonl`;
      
      reply.header('Content-Disposition', `attachment; filename="${filename}"`);
      reply.type('application/jsonl');
      
      return reply.send(createReadStream(filePath));
    } catch (error) {
      app.log.error('Erro ao baixar documento:', error);
      return reply.status(404).send({ error: 'Documento não encontrado' });
    }
  });
  
  // Excluir documento
  app.delete('/api/documents/:sessionId', {
    schema: {
      params: z.object({
        sessionId: z.string()
      })
    }
  }, async (request, reply) => {
    try {
      const { sessionId } = request.params;
      const filePath = join(PROJECTS_DIR, `${sessionId}.jsonl`);
      
      // Verificar se o arquivo existe
      await stat(filePath);
      
      // Excluir arquivo
      await unlink(filePath);
      
      // Remover nome customizado se existir
      const customNames = await loadCustomNames();
      if (customNames[sessionId]) {
        delete customNames[sessionId];
        await saveCustomNames(customNames);
      }
      
      return reply.send({ success: true });
    } catch (error) {
      app.log.error('Erro ao excluir documento:', error);
      return reply.status(404).send({ error: 'Documento não encontrado' });
    }
  });
}