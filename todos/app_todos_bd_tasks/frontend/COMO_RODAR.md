# 🚀 Como Rodar o Frontend (React Local DB)

## 📋 Pré-requisitos

- Node.js 18+ instalado
- npm ou pnpm instalado
- Porta 5173 disponível (padrão do Vite)

## 🔧 Instalação

### 1. Navegue até o diretório do frontend
```bash
cd /Users/agents/Desktop/db/youtube-electric-tanstack-db/react-local-db
# ou se estiver usando a nova estrutura:
cd /Users/agents/Desktop/db/youtube-electric-tanstack-db/apps/frontend
```

### 2. Instale as dependências
```bash
npm install
# ou
pnpm install
```

## ▶️ Rodando o Projeto

### Modo Desenvolvimento
```bash
npm run dev
# ou
pnpm dev
```

O servidor iniciará em:
- Local: http://localhost:5173/
- Network: use --host para expor na rede

### Outros Comandos Disponíveis
```bash
npm run build          # Gera build de produção
npm run preview        # Visualiza build de produção
npm run lint           # Executa o linter
npm run compile-migrations  # Compila migrações do banco local
```

## 🎯 O que o Projeto Faz

Este é um frontend React que demonstra:
- **Banco de dados no navegador** usando PGlite
- **Gerenciamento reativo de dados** com TanStack DB
- **CRUD de Issues** (tarefas/tickets)
- **Interface moderna** com Tailwind CSS

## 🔄 Hot Module Replacement (HMR)

O projeto usa Vite, então alterações nos arquivos são refletidas automaticamente:
- Edite qualquer arquivo `.tsx`, `.ts` ou `.css`
- O navegador atualizará sem precisar recarregar a página
- Mensagens como `[vite] (client) hmr update` indicam atualizações bem-sucedidas

## 🌐 Navegação no App

### Páginas Disponíveis
- `/` - Lista de issues
- `/issues/new` - Criar nova issue
- `/issues/:id` - Detalhes de uma issue

### Funcionalidades
1. **Listar Issues**: Página inicial mostra todas as issues
2. **Criar Issue**: Clique em "Create Issue" para adicionar nova
3. **Ver Detalhes**: Clique em uma issue para ver detalhes
4. **Editar/Deletar**: Disponível na página de detalhes

## 🗄️ Banco de Dados Local

O app usa PGlite (PostgreSQL no navegador):
- Dados salvos no IndexedDB do navegador
- Persiste entre recarregamentos
- Não precisa de servidor de banco de dados

## 🐛 Solução de Problemas

### Porta já em uso
```bash
# Mate o processo usando a porta 5173
lsof -ti:5173 | xargs kill -9

# Ou rode em outra porta
npm run dev -- --port 3000
```

### Erro de dependências
```bash
# Limpe cache e reinstale
rm -rf node_modules package-lock.json
npm install
```

### Tela preta ao criar issue
- Verifique o console do navegador (F12)
- O backend precisa estar rodando se houver integração
- Ou use o modo local (sem API)

## 🔗 Integração com Backend

Se quiser integrar com o backend:

1. Rode o backend em outro terminal:
```bash
cd ../backend
npm run dev
```

2. O backend rodará em http://localhost:3333

3. Atualize as URLs no frontend se necessário

## 📱 Desenvolvimento Mobile

Para testar em dispositivos móveis na mesma rede:
```bash
npm run dev -- --host
```
Acesse pelo IP mostrado no terminal.

---

💡 **Dica**: Use as DevTools do navegador (F12) para debugar e ver os logs do console!