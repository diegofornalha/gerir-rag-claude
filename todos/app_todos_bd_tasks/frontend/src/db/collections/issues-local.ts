import { createCollection } from '@tanstack/db-collections'
import { z } from 'zod'

export const issueSchema = z.object({
  id: z.number().int(),
  title: z.string(),
  description: z.string().nullable(),
  userId: z.number(),
  createdAt: z.string(),
})

export type Issue = z.infer<typeof issueSchema>

export const issues = createCollection({
  id: 'issues',
  primaryKey: ['id'],
  schema: issueSchema,
  initialData: [
    {
      id: 1,
      title: 'Exemplo de Issue',
      description: 'Esta é uma issue de exemplo para demonstrar o funcionamento',
      userId: 1,
      createdAt: new Date().toISOString(),
    }
  ]
})