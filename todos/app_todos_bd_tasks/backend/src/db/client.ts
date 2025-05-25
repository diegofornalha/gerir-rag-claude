import { drizzle } from 'drizzle-orm/node-postgres/index.js'
import { Pool } from 'pg'
import { env } from '../env.js'

const pool = new Pool({
  connectionString: env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})

export const db = drizzle(pool)