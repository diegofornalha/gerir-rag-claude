# Plano de Migração: localStorage → PGlite + PostgreSQL

## Visão Geral

Este documento detalha o plano completo de migração do sistema atual (localStorage) para uma arquitetura offline-first com PGlite no frontend e PostgreSQL no backend, mantendo sincronização bidirecional.

## Arquitetura Atual

```
Frontend (React 19)          Backend (Fastify)
    │                             │
    ├─ localStorage               ├─ PostgreSQL (Drizzle ORM)
    ├─ React Query               ├─ Cache em memória
    └─ API calls ────────────────┘
```

## Arquitetura Proposta

```
Frontend (React 19)          Backend (Fastify)
    │                             │
    ├─ PGlite (SQL local)        ├─ PostgreSQL (source of truth)
    ├─ React Query (cache)       ├─ Redis (cache distribuído)
    ├─ Sync Engine               ├─ WebSocket Server
    └─ WebSocket ────────────────┤
                                  └─ Claude Integration
```

## 1. Schema Unificado (Drizzle ORM)

### Tabelas Principais

```typescript
// Compartilhado entre frontend e backend
export const users = pgTable('users', {
  id: uuid('id').defaultRandom().primaryKey(),
  name: text('name').notNull(),
  email: text('email').unique(),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
  lastSyncAt: timestamp('last_sync_at'),
  deviceId: text('device_id'),
});

export const issues = pgTable('issues', {
  id: uuid('id').defaultRandom().primaryKey(),
  title: text('title').notNull(),
  description: text('description'),
  status: text('status').notNull().default('pending'),
  priority: text('priority').notNull().default('medium'),
  userId: uuid('user_id').references(() => users.id),
  
  // Integração Claude
  sessionId: text('session_id'),
  claudeTaskId: text('claude_task_id'),
  
  // Timestamps
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
  completedAt: timestamp('completed_at'),
  
  // Controle de versão
  version: integer('version').default(1),
  locallyModified: boolean('locally_modified').default(false),
  deletedAt: timestamp('deleted_at'), // Soft delete
});

export const syncQueue = pgTable('sync_queue', {
  id: uuid('id').defaultRandom().primaryKey(),
  tableName: text('table_name').notNull(),
  recordId: uuid('record_id').notNull(),
  operation: text('operation').notNull(),
  data: jsonb('data').notNull(),
  deviceId: text('device_id').notNull(),
  createdAt: timestamp('created_at').defaultNow(),
  syncedAt: timestamp('synced_at'),
  error: text('error'),
  retries: integer('retries').default(0),
});
```

## 2. Estratégia de Sincronização

### Fluxo de Sincronização

1. **Operação Offline**
   ```
   User Action → PGlite → sync_queue → locallyModified = true
   ```

2. **Detecção Online**
   ```
   WebSocket Connected → Process sync_queue → Send to Backend
   ```

3. **Resolução de Conflitos**
   ```
   Version mismatch → Conflict Detector → Resolution Strategy → Update
   ```

### Implementação do Sync Engine

```typescript
class SyncEngine {
  private ws: WebSocket;
  private syncInProgress = false;
  
  async syncChanges() {
    if (this.syncInProgress) return;
    
    this.syncInProgress = true;
    const pending = await syncQueue.findMany({ syncedAt: null });
    
    for (const change of pending) {
      try {
        const response = await this.sendChange(change);
        await this.handleResponse(response, change);
      } catch (error) {
        await this.handleSyncError(change, error);
      }
    }
    
    this.syncInProgress = false;
  }
  
  private async handleConflict(local, remote) {
    // Default: Last Write Wins
    if (local.updatedAt > remote.updatedAt) {
      return local;
    }
    return remote;
  }
}
```

## 3. Migração de Dados

### Processo de Migração

```typescript
class DataMigration {
  async migrate() {
    // 1. Verificar se já foi migrado
    if (localStorage.getItem('migrated_to_pglite')) {
      return;
    }
    
    // 2. Ler dados do localStorage
    const localIssues = JSON.parse(localStorage.getItem('issues') || '[]');
    const localUsers = JSON.parse(localStorage.getItem('users') || '[]');
    
    // 3. Inicializar PGlite
    const db = await initPGlite();
    
    // 4. Migrar dados em transação
    await db.transaction(async (tx) => {
      // Inserir usuários
      for (const user of localUsers) {
        await tx.insert(users).values({
          ...user,
          createdAt: new Date(user.createdAt),
          updatedAt: new Date(user.updatedAt),
        });
      }
      
      // Inserir issues
      for (const issue of localIssues) {
        await tx.insert(issues).values({
          ...issue,
          createdAt: new Date(issue.createdAt),
          updatedAt: new Date(issue.updatedAt),
          version: 1,
          locallyModified: true, // Marcar para sync
        });
      }
    });
    
    // 5. Marcar como migrado
    localStorage.setItem('migrated_to_pglite', 'true');
    localStorage.setItem('migration_date', new Date().toISOString());
  }
}
```

## 4. Estratégias de Performance

### Cache Multi-camada

```
┌─────────────────┐
│  React Query    │ ← In-memory cache (5-10 min)
├─────────────────┤
│     PGlite      │ ← Local SQL database
├─────────────────┤
│   WebSocket     │ ← Real-time updates
├─────────────────┤
│     Redis       │ ← Server cache (1 min)
├─────────────────┤
│   PostgreSQL    │ ← Source of truth
└─────────────────┘
```

### Otimizações

1. **Query Optimization**
   - Índices em campos frequentes (status, userId, sessionId)
   - Pagination com cursor
   - Lazy loading de relações

2. **Batch Operations**
   - Agrupar mudanças em transações
   - Debounce em auto-save
   - Bulk sync a cada 30 segundos

3. **Storage Management**
   - Cleanup de registros deletados após 30 dias
   - Compactação de backups antigos
   - Limite de 1000 items no sync_queue

## 5. Tratamento de Conflitos

### Tipos de Conflito

1. **UPDATE_UPDATE**: Ambos modificaram o mesmo registro
2. **UPDATE_DELETE**: Um atualizou, outro deletou
3. **CREATE_CREATE**: IDs duplicados (raro com UUID)

### Estratégias de Resolução

```typescript
const resolutionStrategies = {
  lastWriteWins: (local, remote) => {
    return local.updatedAt > remote.updatedAt ? local : remote;
  },
  
  mergeFields: (local, remote) => {
    return {
      ...remote,
      ...local,
      updatedAt: new Date(),
      version: Math.max(local.version, remote.version) + 1
    };
  },
  
  userDecision: async (conflict) => {
    // Salvar conflito para resolução manual
    await saveConflict(conflict);
    // UI mostra modal para usuário escolher
  }
};
```

## 6. Backup e Recuperação

### Estratégia de Backup

1. **Frontend (PGlite)**
   - Backup incremental a cada hora
   - Backup completo diário às 2AM
   - Export manual em SQL/JSON/CSV

2. **Backend (PostgreSQL)**
   - pg_dump diário
   - Replicação streaming
   - Snapshots a cada 6 horas
   - Backup S3 com retenção 30 dias

### Processo de Recuperação

```typescript
async function recoverDatabase() {
  // 1. Verificar integridade
  const isCorrupted = await checkIntegrity();
  
  if (isCorrupted) {
    // 2. Tentar recuperar local
    const localBackup = await getLatestLocalBackup();
    if (localBackup) {
      await restoreFromBackup(localBackup);
    } else {
      // 3. Recuperar do servidor
      await fullSyncFromServer();
    }
  }
}
```

## 7. Monitoramento e Health Checks

```typescript
const healthChecks = {
  dbIntegrity: async () => {
    const result = await db.query('PRAGMA integrity_check');
    return result[0].integrity_check === 'ok';
  },
  
  storageSpace: async () => {
    const quota = await navigator.storage.estimate();
    return quota.usage / quota.quota < 0.9;
  },
  
  syncStatus: async () => {
    const pending = await syncQueue.count({ syncedAt: null });
    return pending < 100;
  },
  
  connectionStatus: () => {
    return ws.readyState === WebSocket.OPEN;
  }
};
```

## 8. Fases de Implementação

### Fase 1: Preparação (1 semana)
- [ ] Configurar PGlite no frontend
- [ ] Criar schemas compartilhados
- [ ] Implementar migração de dados
- [ ] Testes unitários

### Fase 2: Sincronização Básica (2 semanas)
- [ ] Implementar Sync Engine
- [ ] WebSocket server
- [ ] Sync queue processing
- [ ] Testes de integração

### Fase 3: Conflitos e Performance (1 semana)
- [ ] Detector de conflitos
- [ ] Estratégias de resolução
- [ ] Otimizações de cache
- [ ] Testes de stress

### Fase 4: Backup e Monitoring (1 semana)
- [ ] Sistema de backup automático
- [ ] Health checks
- [ ] Dashboard de monitoramento
- [ ] Documentação

### Fase 5: Deploy e Migração (1 semana)
- [ ] Deploy gradual (feature flag)
- [ ] Migração de usuários em lotes
- [ ] Monitoramento pós-deploy
- [ ] Rollback plan

## 9. Considerações de Segurança

1. **Criptografia**
   - HTTPS para todas comunicações
   - WSS para WebSocket
   - Criptografia opcional de backups

2. **Autenticação**
   - JWT tokens
   - Device fingerprinting
   - Session management

3. **Autorização**
   - Row-level security
   - User isolation
   - Rate limiting

## 10. Métricas de Sucesso

- **Performance**: Queries < 50ms no PGlite
- **Confiabilidade**: 99.9% uptime de sync
- **Conflitos**: < 0.1% necessitam intervenção manual
- **Storage**: < 100MB por usuário
- **Sync Delay**: < 5 segundos quando online

## Conclusão

Esta arquitetura fornece uma solução robusta offline-first que mantém a simplicidade do desenvolvimento enquanto oferece sincronização confiável e performance otimizada. A migração pode ser feita de forma gradual, minimizando riscos e permitindo rollback se necessário.