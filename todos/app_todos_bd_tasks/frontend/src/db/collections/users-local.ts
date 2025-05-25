import { createQueryCollection } from '@tanstack/db-collections'
import { z } from 'zod'

export const userSchema = z.object({
  id: z.number().int(),
  name: z.string(),
  email: z.string(),
})

export type User = z.infer<typeof userSchema>

export const users = createQueryCollection({
  id: 'users',
  primaryKey: ['id'],
  schema: userSchema,
  initialData: [
    {
      id: 1,
      name: 'Diego',
      email: 'diego@example.com',
    }
  ]
})