# 📋 Comportamentos Especiais do Sistema

Este documento detalha comportamentos únicos e importantes do sistema que desenvolvedores devem conhecer.

## 🔄 Comportamentos do Frontend

### 1. **Duas Versões do App**
O frontend possui duas implementações diferentes:
- `app.tsx` - Versão completa com PGlite (PostgreSQL no browser)
- `app-simple.tsx` - Versão simplificada com LocalStorage

**Como alternar:**
```typescript
// Em main.tsx, mude o import:
import App from './app'          // Versão PGlite
import App from './app-simple'   // Versão LocalStorage
```

### 2. **Persistência Automática**
- **LocalStorage**: Dados salvos instantaneamente, sem botão "salvar"
- **PGlite**: Transações são commitadas automaticamente
- **Sem perda de dados**: Refresh da página mantém tudo

### 3. **IDs Auto-incrementais**
```typescript
// O sistema gera IDs baseados no timestamp
const newId = Date.now()
```
⚠️ **Atenção**: Em criações muito rápidas, pode haver colisão de IDs

### 4. **Roteamento Condicional**
```typescript
// Após criar uma issue, redireciona automaticamente
navigate(`/issues/${newId}`)
```

## 🗄️ Comportamentos do Banco de Dados

### 1. **Migrations Compiladas**
O frontend compila migrations SQL em JSON:
```bash
pnpm compile-migrations
# Gera: src/db/future/migrations.json
```
**Por quê?** Vite não suporta importação de arquivos .sql diretamente

### 2. **IndexedDB vs LocalStorage**
- **PGlite**: Usa IndexedDB (sem limite de tamanho)
- **Simple**: Usa LocalStorage (limite ~5-10MB)
- **Fallback**: Se IndexedDB falhar, não há fallback automático

### 3. **Schema Evolution**
```sql
-- Migrations são aplicadas em ordem
-- NUNCA edite migrations já aplicadas
-- Sempre crie uma nova migration
```

## ⚡ Comportamentos de Performance

### 1. **Cache In-Memory (Backend)**
```typescript
// Cache com TTL de 5 minutos
const cached = cache.get(key)
if (cached && Date.now() - cached.timestamp < TTL) {
  return cached.data
}
```

### 2. **Lazy Loading de Dados**
- Issues são carregadas sob demanda
- Não há pré-carregamento de detalhes
- Lista mostra apenas campos essenciais

### 3. **Debounce Ausente**
⚠️ **Importante**: Formulários não têm debounce
- Cada keystroke pode triggerar re-render
- Em forms grandes, considere adicionar debounce

## 🔒 Comportamentos de Segurança

### 1. **Sem Autenticação Real**
```typescript
// userId é hardcoded
const userId = 1
```
📌 **TODO**: Implementar autenticação antes de produção

### 2. **Validação Client-Side Only**
- Frontend valida com Zod
- Backend também valida (redundância intencional)
- Nunca confie apenas em validação client-side

### 3. **CORS Permissivo em Dev**
```typescript
// backend/src/http/server.ts
cors: {
  origin: true // Aceita qualquer origem em dev
}
```
⚠️ **Produção**: Configure origens específicas

## 🐛 Comportamentos Conhecidos

### 1. **Tela Preta ao Criar Issue**
**Causa**: Erro de roteamento ou state não inicializado
**Solução**: Verificar console do navegador

### 2. **Estado Não Persiste Entre Abas**
- LocalStorage compartilha entre abas
- PGlite tem instância por aba
- Sincronização entre abas não implementada

### 3. **Limite de Queries Simultâneas**
```typescript
// Pool PostgreSQL limitado a 20 conexões
max: 20
```
Muitas queries paralelas podem causar espera

## 🔧 Comportamentos de Desenvolvimento

### 1. **Hot Reload Seletivo**
- CSS: Atualiza sem reload
- Componentes: Preserva estado quando possível
- Schema DB: Requer restart completo

### 2. **Logs Estruturados**
```typescript
// Backend usa Pino
logger.info({ userId, issueId }, 'Issue created')
```
Logs em JSON facilitam parsing e análise

### 3. **TypeScript Nativo**
```bash
# Node.js 22 roda TS diretamente
node --experimental-strip-types app.ts
```
Sem necessidade de build step em dev

## 📱 Comportamentos Mobile

### 1. **Touch vs Click**
- Botões respondem a touch
- Não há swipe gestures
- Long press não implementado

### 2. **Viewport Responsivo**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```
UI adapta automaticamente

### 3. **Offline Capability**
- Frontend funciona 100% offline
- PWA manifest não configurado ainda
- Service Worker ausente

## 🚀 Comportamentos de Deploy

### 1. **Build Otimizado**
```bash
pnpm build
# Gera bundle minificado em dist/
```

### 2. **Variáveis de Ambiente**
```typescript
// Frontend: Vite prefix
VITE_API_URL=http://localhost:3333

// Backend: Arquivo .env
DATABASE_URL=postgresql://...
```

### 3. **Assets Estáticos**
- Imagens: Não há upload implementado
- Fontes: Usa system fonts
- Icons: SVG inline no código

## 💡 Dicas e Truques

### 1. **Debug do PGlite**
```javascript
// Console do navegador
const db = await window.__pglite__
await db.query('SELECT * FROM issues')
```

### 2. **Reset Completo**
```javascript
// Limpar todos os dados
localStorage.clear()
indexedDB.deleteDatabase('pglite')
```

### 3. **Modo Verbose**
```typescript
// Ativar logs detalhados
localStorage.setItem('DEBUG', '*')
```

---

⚠️ **Nota**: Este documento reflete o estado atual do projeto. Alguns comportamentos podem mudar em versões futuras.