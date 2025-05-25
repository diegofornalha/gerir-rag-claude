# Guia de Implementação: Migração PGlite

## Quick Start para Desenvolvedores

Este guia fornece instruções práticas para implementar a arquitetura descrita no plano de migração.

## 1. Setup Inicial do PGlite

### Instalação de Dependências

```bash
# Frontend
npm install @electric-sql/pglite drizzle-orm drizzle-orm/pg-core
npm install -D @types/websocket

# Backend (adicional ao existente)
npm install ws redis ioredis
npm install -D @types/ws
```

### Configuração do PGlite no Frontend

```typescript
// src/db/pglite-instance.ts
import { PGlite } from '@electric-sql/pglite';
import { drizzle } from 'drizzle-orm/pglite';
import * as schema from '@/shared/schema';

class PGliteManager {
  private static instance: PGlite | null = null;
  private static db: ReturnType<typeof drizzle> | null = null;
  private static initPromise: Promise<void> | null = null;

  static async initialize() {
    if (this.initPromise) return this.initPromise;
    
    this.initPromise = this.performInit();
    return this.initPromise;
  }

  private static async performInit() {
    try {
      // Verificar suporte do navegador
      if (!window.indexedDB) {
        throw new Error('IndexedDB not supported');
      }

      // Inicializar PGlite
      this.instance = new PGlite({
        dataDir: 'idb://app-todos-db',
        relaxedDurability: true, // Melhor performance
      });

      // Aguardar inicialização
      await this.instance.waitReady;

      // Criar instância do Drizzle
      this.db = drizzle(this.instance, { schema });

      // Executar migrations
      await this.runMigrations();

      console.log('PGlite initialized successfully');
    } catch (error) {
      console.error('Failed to initialize PGlite:', error);
      // Ativar modo emergência
      await this.activateEmergencyMode();
      throw error;
    }
  }

  private static async runMigrations() {
    // Migrations serão aplicadas aqui
    const migrations = await import('./migrations');
    await migrations.applyAll(this.instance);
  }

  private static async activateEmergencyMode() {
    // Fallback para in-memory store
    window.emergencyStore = new Map();
    window.isEmergencyMode = true;
    
    // Notificar usuário
    if (window.showNotification) {
      window.showNotification({
        type: 'warning',
        message: 'Modo offline limitado ativado',
        description: 'Seus dados serão salvos temporariamente'
      });
    }
  }

  static getDb() {
    if (!this.db) {
      throw new Error('PGlite not initialized. Call initialize() first.');
    }
    return this.db;
  }

  static getInstance() {
    if (!this.instance) {
      throw new Error('PGlite not initialized. Call initialize() first.');
    }
    return this.instance;
  }
}

export { PGliteManager };
```

## 2. Schema Compartilhado

### Estrutura de Diretórios

```
src/
  shared/
    schema/
      index.ts        # Export principal
      users.ts        # Schema de usuários
      issues.ts       # Schema de issues
      sync.ts         # Tabelas de sincronização
      metrics.ts      # Tabelas de métricas
    types/
      index.ts        # Tipos TypeScript derivados
```

### Schema Base

```typescript
// src/shared/schema/issues.ts
import { pgTable, uuid, text, timestamp, integer, boolean } from 'drizzle-orm/pg-core';
import { users } from './users';

export const issues = pgTable('issues', {
  id: uuid('id').defaultRandom().primaryKey(),
  title: text('title').notNull(),
  description: text('description'),
  status: text('status', { 
    enum: ['pending', 'in_progress', 'completed', 'cancelled'] 
  }).notNull().default('pending'),
  priority: text('priority', { 
    enum: ['low', 'medium', 'high', 'urgent'] 
  }).notNull().default('medium'),
  
  // Relações
  userId: uuid('user_id').references(() => users.id),
  
  // Integração Claude
  sessionId: text('session_id'),
  claudeTaskId: text('claude_task_id'),
  
  // Timestamps
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
  completedAt: timestamp('completed_at'),
  
  // Controle de versão para sincronização
  version: integer('version').default(1).notNull(),
  locallyModified: boolean('locally_modified').default(false),
  deletedAt: timestamp('deleted_at'), // Soft delete
  
  // Metadados
  metadata: text('metadata').$type<Record<string, any>>(), // JSON string
});

// Índices para performance
export const issuesIndexes = {
  statusIdx: 'CREATE INDEX idx_issues_status ON issues(status)',
  userIdx: 'CREATE INDEX idx_issues_user_id ON issues(user_id)',
  sessionIdx: 'CREATE INDEX idx_issues_session_id ON issues(session_id)',
  updatedIdx: 'CREATE INDEX idx_issues_updated_at ON issues(updated_at DESC)',
  deletedIdx: 'CREATE INDEX idx_issues_deleted_at ON issues(deleted_at) WHERE deleted_at IS NOT NULL',
};
```

## 3. Sistema de Sincronização

### Sync Engine Implementation

```typescript
// src/sync/sync-engine.ts
import { WebSocketManager } from './websocket-manager';
import { SyncQueue } from './sync-queue';
import { ConflictResolver } from './conflict-resolver';
import { MetricsCollector } from './metrics-collector';

export class SyncEngine {
  private ws: WebSocketManager;
  private queue: SyncQueue;
  private resolver: ConflictResolver;
  private metrics: MetricsCollector;
  private syncInProgress = false;
  private lastSyncTime: Date | null = null;

  constructor() {
    this.ws = new WebSocketManager({
      url: process.env.REACT_APP_WS_URL || 'ws://localhost:3333/sync',
      reconnectOptions: {
        maxAttempts: 10,
        baseDelay: 1000,
        maxDelay: 30000,
      }
    });

    this.queue = new SyncQueue();
    this.resolver = new ConflictResolver();
    this.metrics = new MetricsCollector();

    this.setupEventHandlers();
    this.startPeriodicSync();
  }

  private setupEventHandlers() {
    // Quando conectar, sincronizar imediatamente
    this.ws.on('connected', () => {
      console.log('WebSocket connected, starting sync...');
      this.sync();
    });

    // Receber atualizações do servidor
    this.ws.on('server-update', async (data) => {
      await this.handleServerUpdate(data);
    });

    // Detectar conflitos
    this.ws.on('conflict', async (conflict) => {
      await this.handleConflict(conflict);
    });
  }

  private startPeriodicSync() {
    // Sync a cada 30 segundos se houver mudanças pendentes
    setInterval(async () => {
      const hasPending = await this.queue.hasPendingChanges();
      if (hasPending && !this.syncInProgress) {
        await this.sync();
      }
    }, 30000);
  }

  async sync() {
    if (this.syncInProgress) {
      console.log('Sync already in progress, skipping...');
      return;
    }

    const startTime = Date.now();
    this.syncInProgress = true;

    try {
      // 1. Processar fila de mudanças locais
      const pendingChanges = await this.queue.getPendingChanges(100); // Batch de 100
      
      if (pendingChanges.length > 0) {
        const response = await this.ws.sendBatch({
          type: 'sync-batch',
          changes: pendingChanges,
          deviceId: this.getDeviceId(),
        });

        await this.processSyncResponse(response, pendingChanges);
      }

      // 2. Buscar atualizações do servidor
      await this.pullServerUpdates();

      // 3. Registrar métricas
      const syncTime = Date.now() - startTime;
      await this.metrics.recordSync({
        duration: syncTime,
        changesCount: pendingChanges.length,
        success: true,
      });

      this.lastSyncTime = new Date();

    } catch (error) {
      console.error('Sync failed:', error);
      
      await this.metrics.recordSync({
        duration: Date.now() - startTime,
        success: false,
        error: error.message,
      });

      // Re-tentar em breve
      setTimeout(() => this.sync(), 5000);
      
    } finally {
      this.syncInProgress = false;
    }
  }

  private async processSyncResponse(response: any, changes: any[]) {
    for (let i = 0; i < response.results.length; i++) {
      const result = response.results[i];
      const change = changes[i];

      if (result.success) {
        // Marcar como sincronizado
        await this.queue.markAsSynced(change.id);
      } else if (result.conflict) {
        // Resolver conflito
        await this.handleConflict({
          local: change,
          remote: result.remoteVersion,
          type: result.conflictType,
        });
      } else {
        // Erro - incrementar retry count
        await this.queue.incrementRetry(change.id);
      }
    }
  }

  private async handleConflict(conflict: any) {
    const resolution = await this.resolver.resolve(conflict);
    
    if (resolution.strategy === 'user-decision') {
      // Notificar UI para mostrar modal de conflito
      window.dispatchEvent(new CustomEvent('sync-conflict', {
        detail: conflict
      }));
    } else {
      // Aplicar resolução automática
      await this.applyResolution(resolution);
    }
  }

  private getDeviceId(): string {
    let deviceId = localStorage.getItem('deviceId');
    if (!deviceId) {
      deviceId = crypto.randomUUID();
      localStorage.setItem('deviceId', deviceId);
    }
    return deviceId;
  }
}
```

## 4. Migração de Dados

### Migration Manager

```typescript
// src/migration/migration-manager.ts
import { PGliteManager } from '@/db/pglite-instance';
import { LocalStorageReader } from './localStorage-reader';
import { MigrationProgress } from './migration-progress';

export class MigrationManager {
  private progress: MigrationProgress;
  private abortController: AbortController | null = null;

  constructor() {
    this.progress = new MigrationProgress();
  }

  async migrate() {
    // Verificar se já foi migrado
    if (this.isMigrated()) {
      console.log('Data already migrated');
      return;
    }

    try {
      this.abortController = new AbortController();
      
      // Mostrar UI de progresso
      this.progress.show();
      
      // Executar migração
      await this.performMigration();
      
      // Marcar como concluído
      this.markAsMigrated();
      
      // Esconder UI
      this.progress.hide();
      
      // Notificar sucesso
      this.notifySuccess();
      
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Migration paused by user');
      } else {
        console.error('Migration failed:', error);
        this.handleMigrationError(error);
      }
    }
  }

  private async performMigration() {
    const db = PGliteManager.getDb();
    const reader = new LocalStorageReader();
    
    // 1. Analisar tamanho dos dados
    this.progress.update({ step: 'Analisando dados...', percent: 0 });
    const dataInfo = await reader.analyzeData();
    
    // 2. Migrar usuários
    this.progress.update({ step: 'Migrando usuários...', percent: 10 });
    await this.migrateUsers(db, reader, dataInfo.users);
    
    // 3. Migrar issues em lotes
    this.progress.update({ step: 'Migrando issues...', percent: 30 });
    await this.migrateIssuesInBatches(db, reader, dataInfo.issues);
    
    // 4. Verificar integridade
    this.progress.update({ step: 'Verificando dados...', percent: 90 });
    await this.verifyMigration(db, dataInfo);
    
    // 5. Criar backup do localStorage
    this.progress.update({ step: 'Finalizando...', percent: 95 });
    await this.backupLocalStorage();
  }

  private async migrateIssuesInBatches(db: any, reader: any, totalCount: number) {
    const batchSize = 100;
    const batches = Math.ceil(totalCount / batchSize);
    
    for (let i = 0; i < batches; i++) {
      // Verificar se foi pausado
      if (this.abortController?.signal.aborted) {
        throw new Error('Migration paused');
      }
      
      const offset = i * batchSize;
      const batch = await reader.getIssuesBatch(offset, batchSize);
      
      await db.transaction(async (tx) => {
        for (const issue of batch) {
          await tx.insert(issues).values({
            ...issue,
            version: 1,
            locallyModified: true,
            createdAt: new Date(issue.createdAt),
            updatedAt: new Date(issue.updatedAt),
          });
        }
      });
      
      // Atualizar progresso
      const percent = 30 + (60 * (i + 1) / batches);
      this.progress.update({
        step: `Migrando issues... (${offset + batch.length}/${totalCount})`,
        percent,
      });
      
      // Pequena pausa para não bloquear UI
      await new Promise(resolve => setTimeout(resolve, 10));
    }
  }

  pause() {
    this.abortController?.abort();
  }

  async resume() {
    // Retomar do ponto onde parou
    await this.migrate();
  }

  private isMigrated(): boolean {
    return localStorage.getItem('pglite_migration_completed') === 'true';
  }

  private markAsMigrated() {
    localStorage.setItem('pglite_migration_completed', 'true');
    localStorage.setItem('pglite_migration_date', new Date().toISOString());
  }
}
```

## 5. Componentes React

### Hook para PGlite

```typescript
// src/hooks/usePGlite.ts
import { useEffect, useState } from 'react';
import { PGliteManager } from '@/db/pglite-instance';

export function usePGlite() {
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    PGliteManager.initialize()
      .then(() => setIsReady(true))
      .catch(setError);
  }, []);

  return { isReady, error, db: isReady ? PGliteManager.getDb() : null };
}
```

### Provider de Sincronização

```typescript
// src/providers/SyncProvider.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { SyncEngine } from '@/sync/sync-engine';

interface SyncContextValue {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime: Date | null;
  pendingChanges: number;
  forceSync: () => Promise<void>;
}

const SyncContext = createContext<SyncContextValue | null>(null);

export function SyncProvider({ children }: { children: React.ReactNode }) {
  const [syncEngine] = useState(() => new SyncEngine());
  const [state, setState] = useState<SyncContextValue>({
    isOnline: navigator.onLine,
    isSyncing: false,
    lastSyncTime: null,
    pendingChanges: 0,
    forceSync: async () => {
      await syncEngine.sync();
    }
  });

  useEffect(() => {
    // Monitorar status online/offline
    const handleOnline = () => setState(s => ({ ...s, isOnline: true }));
    const handleOffline = () => setState(s => ({ ...s, isOnline: false }));
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Monitorar eventos de sync
    const handleSyncStart = () => setState(s => ({ ...s, isSyncing: true }));
    const handleSyncComplete = (e: CustomEvent) => {
      setState(s => ({
        ...s,
        isSyncing: false,
        lastSyncTime: new Date(),
        pendingChanges: e.detail.pendingChanges || 0
      }));
    };
    
    window.addEventListener('sync-start', handleSyncStart);
    window.addEventListener('sync-complete', handleSyncComplete);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('sync-start', handleSyncStart);
      window.removeEventListener('sync-complete', handleSyncComplete);
    };
  }, []);

  return (
    <SyncContext.Provider value={state}>
      {children}
    </SyncContext.Provider>
  );
}

export function useSync() {
  const context = useContext(SyncContext);
  if (!context) {
    throw new Error('useSync must be used within SyncProvider');
  }
  return context;
}
```

## 6. Debug Panel

```typescript
// src/components/DebugPanel.tsx
import React, { useState, useEffect } from 'react';
import { SyncDebugger } from '@/debug/sync-debugger';

export function DebugPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);
  const debugger = SyncDebugger.getInstance();

  useEffect(() => {
    const unsubscribe = debugger.subscribe((newLogs) => {
      setLogs(newLogs);
    });

    return unsubscribe;
  }, []);

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-purple-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-purple-700"
      >
        🐛 Debug
      </button>

      {isOpen && (
        <div className="absolute bottom-12 right-0 w-96 bg-white rounded-lg shadow-xl border p-4 max-h-96 overflow-auto">
          <h3 className="font-bold mb-2">Sync Debug Panel</h3>
          
          <div className="space-y-2 mb-4">
            <button
              onClick={() => debugger.forceSync()}
              className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
            >
              Force Sync
            </button>
            
            <button
              onClick={() => debugger.simulateConflict()}
              className="px-3 py-1 bg-yellow-500 text-white rounded text-sm ml-2"
            >
              Simulate Conflict
            </button>
            
            <button
              onClick={() => debugger.exportDiagnostics()}
              className="px-3 py-1 bg-green-500 text-white rounded text-sm ml-2"
            >
              Export Diagnostics
            </button>
          </div>

          <div className="space-y-1 text-xs font-mono">
            {logs.map((log, i) => (
              <div key={i} className="p-1 bg-gray-100 rounded">
                <span className="text-gray-500">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                {' '}
                <span className={`font-bold ${
                  log.level === 'error' ? 'text-red-600' : 
                  log.level === 'warn' ? 'text-yellow-600' : 
                  'text-blue-600'
                }`}>
                  {log.operation}
                </span>
                {log.details && (
                  <pre className="text-xs mt-1">
                    {JSON.stringify(log.details, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

## 7. Testes

### Teste de Migração

```typescript
// src/__tests__/migration.test.ts
import { MigrationManager } from '@/migration/migration-manager';
import { LocalStorageReader } from '@/migration/localStorage-reader';

describe('Data Migration', () => {
  let manager: MigrationManager;

  beforeEach(() => {
    // Setup localStorage mock data
    localStorage.setItem('issues', JSON.stringify([
      { id: '1', title: 'Test Issue 1', createdAt: new Date().toISOString() },
      { id: '2', title: 'Test Issue 2', createdAt: new Date().toISOString() },
    ]));
    
    manager = new MigrationManager();
  });

  test('should migrate localStorage data to PGlite', async () => {
    await manager.migrate();
    
    // Verificar que dados foram migrados
    const db = PGliteManager.getDb();
    const migratedIssues = await db.select().from(issues);
    
    expect(migratedIssues).toHaveLength(2);
    expect(migratedIssues[0].locallyModified).toBe(true);
  });

  test('should handle large datasets with batching', async () => {
    // Criar 1000 issues
    const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
      id: `issue-${i}`,
      title: `Issue ${i}`,
      createdAt: new Date().toISOString(),
    }));
    
    localStorage.setItem('issues', JSON.stringify(largeDataset));
    
    await manager.migrate();
    
    const db = PGliteManager.getDb();
    const count = await db.select({ count: count() }).from(issues);
    
    expect(count[0].count).toBe(1000);
  });

  test('should resume migration after interruption', async () => {
    // Simular interrupção após 50ms
    setTimeout(() => manager.pause(), 50);
    
    try {
      await manager.migrate();
    } catch (error) {
      expect(error.message).toBe('Migration paused');
    }
    
    // Retomar migração
    await manager.resume();
    
    expect(localStorage.getItem('pglite_migration_completed')).toBe('true');
  });
});
```

## 8. Configuração do WebSocket Server

```typescript
// backend/src/websocket/sync-server.ts
import { WebSocketServer } from 'ws';
import { Redis } from 'ioredis';
import { db } from '@/db/client';
import { ConflictDetector } from './conflict-detector';

export class SyncServer {
  private wss: WebSocketServer;
  private redis: Redis;
  private clients: Map<string, WebSocket> = new Map();

  constructor(server: any) {
    this.wss = new WebSocketServer({ server, path: '/sync' });
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379'),
    });

    this.setupWebSocketServer();
  }

  private setupWebSocketServer() {
    this.wss.on('connection', (ws, req) => {
      const deviceId = this.extractDeviceId(req);
      
      console.log(`New WebSocket connection from device: ${deviceId}`);
      
      this.clients.set(deviceId, ws);
      
      ws.on('message', async (message) => {
        try {
          const data = JSON.parse(message.toString());
          await this.handleMessage(deviceId, data, ws);
        } catch (error) {
          console.error('Error handling message:', error);
          ws.send(JSON.stringify({
            type: 'error',
            error: error.message
          }));
        }
      });
      
      ws.on('close', () => {
        this.clients.delete(deviceId);
        console.log(`Device ${deviceId} disconnected`);
      });
      
      // Enviar estado inicial
      ws.send(JSON.stringify({
        type: 'connected',
        deviceId,
        serverTime: new Date()
      }));
    });
  }

  private async handleMessage(deviceId: string, data: any, ws: WebSocket) {
    switch (data.type) {
      case 'sync-batch':
        await this.handleSyncBatch(deviceId, data.changes, ws);
        break;
        
      case 'pull-updates':
        await this.handlePullUpdates(deviceId, data.lastSyncTime, ws);
        break;
        
      case 'heartbeat':
        ws.send(JSON.stringify({ type: 'heartbeat-ack' }));
        break;
        
      default:
        console.warn(`Unknown message type: ${data.type}`);
    }
  }

  private async handleSyncBatch(deviceId: string, changes: any[], ws: WebSocket) {
    const results = [];
    const detector = new ConflictDetector();
    
    for (const change of changes) {
      try {
        // Verificar conflitos
        const conflict = await detector.check(change);
        
        if (conflict) {
          results.push({
            id: change.id,
            success: false,
            conflict: true,
            conflictType: conflict.type,
            remoteVersion: conflict.remoteVersion
          });
        } else {
          // Aplicar mudança
          await this.applyChange(change);
          
          // Broadcast para outros dispositivos
          await this.broadcastChange(change, deviceId);
          
          results.push({
            id: change.id,
            success: true
          });
        }
      } catch (error) {
        results.push({
          id: change.id,
          success: false,
          error: error.message
        });
      }
    }
    
    // Responder ao cliente
    ws.send(JSON.stringify({
      type: 'sync-batch-response',
      results
    }));
    
    // Registrar métricas
    await this.recordSyncMetrics(deviceId, changes.length, results);
  }

  private async broadcastChange(change: any, excludeDeviceId: string) {
    const message = JSON.stringify({
      type: 'server-update',
      change
    });
    
    // Publicar no Redis para outros servidores
    await this.redis.publish('sync-updates', JSON.stringify({
      excludeDeviceId,
      message
    }));
    
    // Broadcast local
    this.clients.forEach((ws, deviceId) => {
      if (deviceId !== excludeDeviceId && ws.readyState === WebSocket.OPEN) {
        ws.send(message);
      }
    });
  }
}
```

## 9. Próximos Passos

1. **Fase 1 - Setup (Esta semana)**
   - [ ] Instalar dependências
   - [ ] Configurar PGlite no frontend
   - [ ] Criar schemas compartilhados
   - [ ] Setup WebSocket server

2. **Fase 2 - Migração (Próxima semana)**
   - [ ] Implementar migration manager
   - [ ] Criar UI de progresso
   - [ ] Testes de migração
   - [ ] Fallback para emergency mode

3. **Fase 3 - Sincronização (2 semanas)**
   - [ ] Implementar sync engine
   - [ ] Conflict resolution
   - [ ] Métricas e monitoring
   - [ ] Debug panel

4. **Fase 4 - Testes (1 semana)**
   - [ ] Chaos engineering
   - [ ] Load testing
   - [ ] User acceptance testing

5. **Fase 5 - Deploy (1 semana)**
   - [ ] Feature flags
   - [ ] Gradual rollout
   - [ ] Monitoring
   - [ ] Documentation

## Checklist de Validação

- [ ] PGlite inicializa corretamente em todos os navegadores suportados
- [ ] Migração funciona para datasets pequenos e grandes
- [ ] Sincronização funciona offline e online
- [ ] Conflitos são resolvidos corretamente
- [ ] Performance dentro dos limites estabelecidos
- [ ] Fallback para emergency mode funciona
- [ ] Debug panel mostra informações úteis
- [ ] Métricas são coletadas corretamente
- [ ] Testes passam consistentemente
- [ ] Documentação está completa