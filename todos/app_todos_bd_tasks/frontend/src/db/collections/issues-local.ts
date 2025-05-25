import { z } from 'zod'

export const issueSchema = z.object({
  id: z.number().int(),
  title: z.string(),
  description: z.string().nullable(),
  userId: z.number(),
  createdAt: z.string(),
})

export type Issue = z.infer<typeof issueSchema>

// Simple local storage implementation
class LocalCollection<T extends { id: number }> {
  private key: string
  private data: T[]

  constructor(key: string, initialData: T[] = []) {
    this.key = key
    const stored = localStorage.getItem(this.key)
    this.data = stored ? JSON.parse(stored) : initialData
    if (!stored && initialData.length > 0) {
      this.save()
    }
  }

  private save() {
    localStorage.setItem(this.key, JSON.stringify(this.data))
  }

  getAll(): T[] {
    return [...this.data]
  }

  getById(id: number): T | undefined {
    return this.data.find(item => item.id === id)
  }

  create(item: T): T {
    this.data.push(item)
    this.save()
    return item
  }

  update(id: number, updates: Partial<T>): T | undefined {
    const index = this.data.findIndex(item => item.id === id)
    if (index !== -1) {
      this.data[index] = { ...this.data[index], ...updates }
      this.save()
      return this.data[index]
    }
    return undefined
  }

  delete(id: number): boolean {
    const index = this.data.findIndex(item => item.id === id)
    if (index !== -1) {
      this.data.splice(index, 1)
      this.save()
      return true
    }
    return false
  }
}

export const issues = new LocalCollection<Issue>('issues', [
  {
    id: 1,
    title: 'Exemplo de Missão',
    description: 'Esta é uma missão de exemplo para demonstrar o funcionamento',
    userId: 1,
    createdAt: new Date().toISOString(),
  }
])