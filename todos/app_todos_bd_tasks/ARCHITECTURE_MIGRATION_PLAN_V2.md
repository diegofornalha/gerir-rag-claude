# Plano de Migração: localStorage → PGlite + PostgreSQL (v2.0)

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

// Nova tabela para métricas
export const syncMetrics = pgTable('sync_metrics', {
  id: uuid('id').defaultRandom().primaryKey(),
  deviceId: text('device_id').notNull(),
  syncType: text('sync_type').notNull(), // 'push', 'pull', 'conflict'
  latency: integer('latency'), // ms
  recordCount: integer('record_count'),
  bytesTransferred: integer('bytes_transferred'),
  success: boolean('success').notNull(),
  errorMessage: text('error_message'),
  createdAt: timestamp('created_at').defaultNow(),
});
```

## 2. Estratégia de Sincronização Aprimorada

### Fluxo de Sincronização com Resilience

```typescript
class ResilientSyncEngine {
  private ws: WebSocket;
  private reconnectAttempts = 0;
  private baseDelay = 1000;
  private maxDelay = 30000;
  private heartbeatInterval = 30000;
  private syncInProgress = false;
  
  // Métricas em tempo real
  private metrics = {
    syncLatency: [],
    conflictRate: 0,
    bandwidthUsage: 0,
    lastSyncTime: null,
    failureCount: 0,
  };

  async connect() {
    try {
      this.ws = new WebSocket(this.wsUrl);
      this.setupEventHandlers();
      this.startHeartbeat();
      this.reconnectAttempts = 0;
    } catch (error) {
      await this.handleReconnect();
    }
  }

  private async handleReconnect() {
    const delay = Math.min(
      this.baseDelay * Math.pow(2, this.reconnectAttempts),
      this.maxDelay
    );
    
    this.reconnectAttempts++;
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => this.connect(), delay);
  }

  async syncChanges() {
    if (this.syncInProgress) return;
    
    const startTime = Date.now();
    this.syncInProgress = true;
    
    try {
      const pending = await syncQueue.findMany({ 
        where: { syncedAt: null },
        limit: 100 // Batch size limit
      });
      
      if (pending.length === 0) {
        return;
      }

      // Batch sync for efficiency
      const response = await this.sendBatch(pending);
      await this.processBatchResponse(response, pending);
      
      // Update metrics
      const latency = Date.now() - startTime;
      this.updateMetrics({
        syncLatency: latency,
        recordCount: pending.length,
        success: true
      });
      
    } catch (error) {
      await this.handleSyncError(error);
      this.updateMetrics({
        success: false,
        error: error.message
      });
    } finally {
      this.syncInProgress = false;
    }
  }

  // Fallback strategy quando PGlite falha
  private async activateEmergencyMode() {
    console.warn('PGlite failed - activating emergency mode');
    
    // Use in-memory store
    window.emergencyStore = new Map();
    
    // Notify user
    this.notifyUser({
      type: 'warning',
      message: 'Modo offline limitado ativado',
      action: 'Os dados serão salvos temporariamente na memória'
    });
    
    // Try to recover when possible
    this.scheduleRecoveryAttempt();
  }
}
```

## 3. Migração de Dados Robusta

### Processo de Migração com Progress Tracking

```typescript
class EnhancedDataMigration {
  private progress = {
    currentStep: '',
    totalRecords: 0,
    processedRecords: 0,
    estimatedTime: 0,
    errors: []
  };

  async migrate() {
    // Check if already migrated
    if (localStorage.getItem('migrated_to_pglite')) {
      return;
    }

    try {
      // Start migration with progress tracking
      await this.performMigration();
    } catch (error) {
      // Allow resume from failure point
      await this.handleMigrationError(error);
    }
  }

  private async performMigration() {
    // Phase 1: Analyze data size
    this.updateProgress('Analyzing data...');
    const dataSize = await this.analyzeDataSize();
    
    if (dataSize.totalRecords > 1000) {
      // Use batch migration for large datasets
      await this.batchMigration(dataSize);
    } else {
      // Standard migration for smaller datasets
      await this.standardMigration();
    }
  }

  private async batchMigration(dataSize) {
    const batchSize = 100;
    const delayBetweenBatches = 100; // ms
    
    for (let offset = 0; offset < dataSize.totalRecords; offset += batchSize) {
      this.updateProgress(`Migrating batch ${offset / batchSize + 1}...`);
      
      const batch = await this.getBatch(offset, batchSize);
      await this.migrateBatch(batch);
      
      // Update UI progress
      this.progress.processedRecords = offset + batch.length;
      this.notifyProgress();
      
      // Prevent UI blocking
      await new Promise(resolve => setTimeout(resolve, delayBetweenBatches));
      
      // Allow pause/resume
      if (this.isPaused) {
        await this.waitForResume();
      }
    }
  }

  private async migrateBatch(batch) {
    const db = await this.getPGliteInstance();
    
    await db.transaction(async (tx) => {
      for (const record of batch) {
        try {
          await this.migrateRecord(tx, record);
        } catch (error) {
          this.progress.errors.push({
            record: record.id,
            error: error.message
          });
        }
      }
    });
  }

  private notifyProgress() {
    const percentComplete = 
      (this.progress.processedRecords / this.progress.totalRecords) * 100;
    
    // Update UI with progress
    window.postMessage({
      type: 'MIGRATION_PROGRESS',
      progress: {
        ...this.progress,
        percentComplete
      }
    });
  }
}
```

## 4. Monitoramento e Analytics Aprimorados

```typescript
class SyncMonitoring {
  private metricsBuffer: any[] = [];
  private flushInterval = 60000; // 1 minute

  constructor() {
    // Start periodic metrics flush
    setInterval(() => this.flushMetrics(), this.flushInterval);
  }

  recordMetric(metric: {
    type: string;
    value: any;
    timestamp: Date;
    metadata?: any;
  }) {
    this.metricsBuffer.push(metric);
    
    // Real-time critical metrics
    if (metric.type === 'SYNC_FAILURE' || metric.type === 'DATA_CORRUPTION') {
      this.alertImmediate(metric);
    }
  }

  async flushMetrics() {
    if (this.metricsBuffer.length === 0) return;
    
    const metrics = [...this.metricsBuffer];
    this.metricsBuffer = [];
    
    try {
      await this.sendMetricsToBackend(metrics);
    } catch (error) {
      // Re-queue metrics on failure
      this.metricsBuffer.unshift(...metrics);
    }
  }

  getHealthStatus(): HealthStatus {
    const recentMetrics = this.getRecentMetrics(5 * 60 * 1000); // Last 5 min
    
    return {
      syncHealth: this.calculateSyncHealth(recentMetrics),
      conflictRate: this.calculateConflictRate(recentMetrics),
      averageLatency: this.calculateAverageLatency(recentMetrics),
      errorRate: this.calculateErrorRate(recentMetrics),
      storageUsage: this.getStorageUsage(),
      recommendation: this.getHealthRecommendation(recentMetrics)
    };
  }

  private calculateSyncHealth(metrics): 'healthy' | 'degraded' | 'critical' {
    const errorRate = this.calculateErrorRate(metrics);
    const avgLatency = this.calculateAverageLatency(metrics);
    
    if (errorRate > 0.1 || avgLatency > 5000) return 'critical';
    if (errorRate > 0.05 || avgLatency > 2000) return 'degraded';
    return 'healthy';
  }
}
```

## 5. Chaos Engineering e Testes

```typescript
class ChaosEngineering {
  async runChaosTests() {
    const scenarios = [
      this.testRandomDisconnections,
      this.testDataCorruption,
      this.testExtremeLoad,
      this.testStorageQuotaExceeded,
      this.testMigrationFailure,
    ];
    
    for (const scenario of scenarios) {
      await this.runScenario(scenario);
    }
  }

  private async testRandomDisconnections() {
    // Simulate network failures during sync
    const syncEngine = new ResilientSyncEngine();
    
    // Random disconnections every 10-60 seconds
    const chaos = setInterval(() => {
      if (Math.random() > 0.5) {
        syncEngine.disconnect();
        setTimeout(() => syncEngine.connect(), Math.random() * 5000);
      }
    }, Math.random() * 50000 + 10000);
    
    // Run test workload
    await this.runTestWorkload();
    
    clearInterval(chaos);
    
    // Verify data integrity
    await this.verifyDataIntegrity();
  }

  private async testExtremeLoad() {
    // Create 1000+ issues rapidly
    const promises = [];
    
    for (let i = 0; i < 1000; i++) {
      promises.push(
        this.createTestIssue({
          title: `Stress test issue ${i}`,
          description: 'x'.repeat(1000), // 1KB per issue
        })
      );
      
      // Batch to prevent memory issues
      if (promises.length >= 100) {
        await Promise.all(promises);
        promises.length = 0;
      }
    }
    
    // Verify sync performance
    const startTime = Date.now();
    await this.waitForSync();
    const syncTime = Date.now() - startTime;
    
    assert(syncTime < 30000, 'Sync took too long under load');
  }
}
```

## 6. UX Durante Migração e Sync

```typescript
class MigrationUX {
  private progressModal: HTMLElement;
  
  showMigrationUI() {
    this.progressModal = this.createProgressModal();
    document.body.appendChild(this.progressModal);
  }
  
  private createProgressModal() {
    return createElement(`
      <div class="migration-modal">
        <h2>Migrando seus dados...</h2>
        <div class="progress-bar">
          <div class="progress-fill" style="width: 0%"></div>
        </div>
        <p class="status-text">Preparando migração...</p>
        <p class="time-estimate">Tempo estimado: calculando...</p>
        <div class="error-container" style="display: none;">
          <p class="error-text"></p>
          <button class="retry-button">Tentar novamente</button>
        </div>
        <!-- No cancel button - migration must complete -->
      </div>
    `);
  }
  
  updateProgress(progress: MigrationProgress) {
    const fillElement = this.progressModal.querySelector('.progress-fill');
    const statusElement = this.progressModal.querySelector('.status-text');
    const timeElement = this.progressModal.querySelector('.time-estimate');
    
    fillElement.style.width = `${progress.percentComplete}%`;
    statusElement.textContent = progress.currentStep;
    
    // Dynamic time estimation
    if (progress.processedRecords > 10) {
      const timePerRecord = progress.elapsedTime / progress.processedRecords;
      const remainingRecords = progress.totalRecords - progress.processedRecords;
      const estimatedTime = timePerRecord * remainingRecords;
      
      timeElement.textContent = `Tempo estimado: ${this.formatTime(estimatedTime)}`;
    }
  }
  
  showSyncStatus() {
    // Subtle indicator in UI
    const indicator = this.createSyncIndicator();
    
    // Change color based on sync state
    indicator.classList.toggle('syncing', this.isSyncing);
    indicator.classList.toggle('error', this.hasError);
    indicator.classList.toggle('offline', !this.isOnline);
  }
}
```

## 7. Debug Mode e Developer Experience

```typescript
class DebugMode {
  private enabled = process.env.NODE_ENV === 'development';
  private logs: any[] = [];
  
  constructor() {
    if (this.enabled) {
      this.attachDebugUI();
      this.interceptSyncOperations();
    }
  }
  
  private attachDebugUI() {
    // Add debug panel to page
    const panel = createElement(`
      <div id="sync-debug-panel" style="position: fixed; bottom: 0; right: 0;">
        <button onclick="window.syncDebug.togglePanel()">🐛 Debug</button>
        <div class="debug-content" style="display: none;">
          <h3>Sync Debug Panel</h3>
          <button onclick="window.syncDebug.forceSync()">Force Sync</button>
          <button onclick="window.syncDebug.simulateConflict()">Simulate Conflict</button>
          <button onclick="window.syncDebug.clearSyncQueue()">Clear Queue</button>
          <button onclick="window.syncDebug.exportDiagnostics()">Export Diagnostics</button>
          <div class="sync-logs"></div>
        </div>
      </div>
    `);
    
    document.body.appendChild(panel);
    window.syncDebug = this;
  }
  
  logSync(operation: string, data: any) {
    if (!this.enabled) return;
    
    const log = {
      timestamp: new Date(),
      operation,
      data,
      stackTrace: new Error().stack
    };
    
    this.logs.push(log);
    this.updateDebugUI(log);
  }
  
  async exportDiagnostics() {
    const diagnostics = {
      logs: this.logs,
      syncQueue: await this.getSyncQueueState(),
      conflicts: await this.getConflicts(),
      metrics: await this.getMetrics(),
      systemInfo: this.getSystemInfo()
    };
    
    // Download as JSON
    this.downloadJSON(diagnostics, `sync-diagnostics-${Date.now()}.json`);
  }
  
  simulateConflict() {
    // Create same record on client and server with different data
    const testId = uuid();
    
    // Local change
    pglite.insert(issues).values({
      id: testId,
      title: 'Local version',
      updatedAt: new Date()
    });
    
    // Simulate server change
    this.mockServerResponse({
      id: testId,
      title: 'Server version',
      updatedAt: new Date(Date.now() - 1000)
    });
    
    console.log('Conflict simulated for ID:', testId);
  }
}
```

## 8. Otimização de Bundle e Performance

```typescript
// Dynamic imports para reduzir bundle inicial
const PGliteLoader = {
  instance: null,
  
  async getInstance() {
    if (!this.instance) {
      // Lazy load PGlite apenas quando necessário
      const { PGlite } = await import('@electric-sql/pglite');
      this.instance = new PGlite();
    }
    return this.instance;
  }
};

// Service Worker para cache agressivo
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('app-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/static/js/bundle.js',
        '/static/css/main.css',
        // Pre-cache critical migrations
        '/migrations/001_initial.sql',
        '/migrations/002_sync_tables.sql'
      ]);
    })
  );
});

// Preload de recursos críticos
const preloadCriticalResources = () => {
  // Preload migration scripts
  const migrationLink = document.createElement('link');
  migrationLink.rel = 'preload';
  migrationLink.href = '/migrations/bundle.sql';
  migrationLink.as = 'fetch';
  document.head.appendChild(migrationLink);
  
  // Preconnect to WebSocket server
  const wsLink = document.createElement('link');
  wsLink.rel = 'preconnect';
  wsLink.href = 'wss://sync.api.com';
  document.head.appendChild(wsLink);
};
```

## 9. Storage Quota Management

```typescript
class StorageQuotaManager {
  private quotaWarningThreshold = 0.8; // 80%
  private quotaCriticalThreshold = 0.95; // 95%
  
  async checkQuota() {
    const { usage, quota } = await navigator.storage.estimate();
    const percentUsed = usage / quota;
    
    if (percentUsed > this.quotaCriticalThreshold) {
      await this.handleCriticalStorage();
    } else if (percentUsed > this.quotaWarningThreshold) {
      await this.handleStorageWarning(percentUsed);
    }
    
    return { usage, quota, percentUsed };
  }
  
  private async handleCriticalStorage() {
    // Aggressive cleanup
    await this.cleanupOldData(30); // Delete data older than 30 days
    await this.compressBackups();
    await this.clearCaches();
    
    // If still critical, notify user
    const { percentUsed } = await this.checkQuota();
    if (percentUsed > this.quotaCriticalThreshold) {
      this.notifyUser({
        type: 'critical',
        message: 'Espaço de armazenamento crítico',
        actions: [
          { label: 'Limpar dados antigos', action: 'cleanup_old' },
          { label: 'Exportar e limpar', action: 'export_and_clean' }
        ]
      });
    }
  }
  
  private async cleanupOldData(daysOld: number) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);
    
    await db.delete(issues).where(
      and(
        lte(issues.updatedAt, cutoffDate),
        eq(issues.status, 'completed'),
        isNotNull(issues.deletedAt)
      )
    );
  }
  
  private async compressBackups() {
    const backups = await this.getBackups();
    
    for (const backup of backups) {
      if (!backup.compressed && backup.age > 7) {
        const compressed = await this.compressData(backup.data);
        await this.replaceBackup(backup.id, compressed);
      }
    }
  }
}
```

## 10. Métricas de Sucesso Expandidas

```typescript
interface SuccessMetrics {
  // Performance
  queryLatencyP50: number; // < 30ms
  queryLatencyP95: number; // < 50ms
  queryLatencyP99: number; // < 100ms
  
  // Reliability
  syncSuccessRate: number; // > 99.9%
  dataIntegrityScore: number; // 100%
  conflictAutoResolveRate: number; // > 99.9%
  
  // User Experience
  migrationSuccessRate: number; // > 99.5%
  userSatisfactionScore: number; // > 4.5/5
  offlineCapabilityUsage: number; // > 80%
  
  // Technical
  bundleSizeGrowth: number; // < 15%
  memoryCacheHitRate: number; // > 90%
  storagEfficiency: number; // < 50MB per 1000 issues
  
  // Business
  userRetentionImpact: number; // +10%
  syncDelayReduction: number; // -80%
  supportTicketReduction: number; // -50%
}

class MetricsCollector {
  async collectAndReport() {
    const metrics = await this.collectAllMetrics();
    
    // Real-time dashboard update
    this.updateDashboard(metrics);
    
    // Alert on degradation
    if (metrics.syncSuccessRate < 0.99) {
      this.alertOps('Sync success rate below threshold');
    }
    
    // Weekly report
    if (this.isWeeklyReportDue()) {
      await this.generateWeeklyReport(metrics);
    }
  }
}
```

## Conclusão

Esta versão aprimorada do plano de migração incorpora:

1. **Resiliência aprimorada** com reconexão exponential backoff e fallback strategies
2. **Monitoramento granular** com métricas em tempo real e analytics
3. **UX otimizada** durante migração e sincronização
4. **Chaos engineering** para garantir robustez
5. **Developer experience** com modo debug completo
6. **Performance otimizada** com lazy loading e cache strategies
7. **Gestão de quota** proativa com cleanup automático

A implementação seguirá as 5 fases propostas, com checkpoints de validação em cada etapa para garantir uma migração suave e sem riscos.