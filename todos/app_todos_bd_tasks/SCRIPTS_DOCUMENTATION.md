# Documentação dos Scripts de Desenvolvimento

Este documento descreve os scripts criados para facilitar o desenvolvimento e manutenção do projeto Node Local DB.

## 📁 Arquivos Criados

### 1. `dev.sh` - Script Principal de Desenvolvimento
Script bash completo para gerenciar o ciclo de vida dos serviços (backend e frontend).

### 2. `Makefile` - Interface Simplificada
Wrapper que fornece comandos make mais intuitivos, delegando para o `dev.sh`.

## 🚀 Instalação e Uso

### Primeira vez
```bash
# Torne o script executável (já feito)
chmod +x dev.sh

# Instale todas as dependências
make install
# ou
./dev.sh install
```

## 📋 Comandos Disponíveis

### Comandos Básicos

#### `make start` ou `./dev.sh start`
Inicia o backend (porta 3333) e frontend (porta 5173).

#### `make stop` ou `./dev.sh stop`
Para todos os serviços em execução.

#### `make restart` ou `./dev.sh restart`
Para e reinicia todos os serviços.

#### `make status` ou `./dev.sh status`
Mostra o status atual dos serviços:
- Backend (porta 3333)
- Frontend (porta 5173)
- PostgreSQL

### Limpeza e Cache

#### `make clean` ou `./dev.sh clean`
Limpa todos os caches e arquivos temporários:
- Backend: `dist/`, `.tsbuildinfo`, `node_modules/.cache`
- Frontend: `dist/`, `.vite`, `node_modules/.cache`

**Nota**: Para limpar o IndexedDB do navegador (banco local do PGlite):
1. Abra o DevTools (F12)
2. Application > Storage > Clear site data

#### `make clean-start` ou `./dev.sh clean-start`
Executa limpeza completa e reinicia os serviços. Útil quando há problemas de cache.

### Desenvolvimento

#### `make dev`
Comando especial que:
1. Limpa caches
2. Inicia serviços
3. Mostra URLs disponíveis
4. Sugere comando para logs

#### `make logs` ou `./dev.sh logs`
Mostra as últimas 20 linhas dos logs de cada serviço.

Para acompanhar em tempo real:
```bash
tail -f backend.log
tail -f frontend.log
```

### Banco de Dados

#### `make db-reset` ou `./dev.sh db-reset`
Reseta completamente o banco de dados:
1. Executa migrations
2. Popula com dados de exemplo (seed)

#### `make db-migrate`
Apenas aplica as migrations.

#### `make db-seed`
Apenas executa o seed (dados de exemplo).

#### `make db-generate`
Gera novas migrations baseadas em mudanças no schema.

### Qualidade de Código

#### `make lint`
Verifica problemas de código em ambos os projetos.

#### `make lint-fix`
Corrige automaticamente problemas de lint.

#### `make format`
Formata o código com Prettier.

#### `make typecheck`
Verifica tipos TypeScript.

#### `make test`
Executa testes do backend.

#### `make check`
Executa TODAS as verificações:
- Lint
- Format check
- Type check
- Testes

### Build e Deploy

#### `make build`
Compila ambos os projetos para produção.

## 🔄 Fluxo de Trabalho Recomendado

### Início do Dia
```bash
# Atualiza dependências e inicia limpo
make update
make clean-start
```

### Durante Desenvolvimento
```bash
# Verifica status
make status

# Se precisar reiniciar
make restart

# Ver logs
make logs
```

### Antes de Commit
```bash
# Executa todas as verificações
make check

# Corrige problemas automáticos
make lint-fix
make format
```

### Problemas Comuns

#### "Porta já em uso"
```bash
make stop
make start
```

#### Cache corrompido
```bash
make clean-start
```

#### Banco de dados com problemas
```bash
make db-reset
```

## 🎯 Casos de Uso Específicos

### Resetar Completamente o Ambiente
```bash
make stop
make clean
make install
make db-reset
make start
```

### Debug de Performance
```bash
# Limpa todos os caches
make clean

# Inicia com logs detalhados
make start
tail -f backend.log frontend.log
```

### Preparar para Demo
```bash
make clean-start
make db-seed  # Garante dados de exemplo
```

## 📊 Estrutura de Logs

Os logs são salvos na raiz do projeto:
- `backend.log` - Logs do servidor Fastify
- `frontend.log` - Logs do Vite dev server

## 🔧 Personalização

### Adicionar Novos Comandos

No `Makefile`:
```makefile
## meu-comando: Descrição do comando
meu-comando:
	@echo "Executando meu comando..."
	@cd backend && pnpm meu-script
```

No `dev.sh`:
```bash
# Adicione novo case
meu-comando)
    echo "Executando meu comando..."
    # Sua lógica aqui
    ;;
```

## 🚨 Notas Importantes

1. **Portas Padrão**:
   - Backend: 3333
   - Frontend: 5173

2. **Pré-requisitos**:
   - Node.js 18+
   - pnpm
   - PostgreSQL (para backend)

3. **Arquivos Ignorados**:
   - Os logs (`*.log`) devem ser adicionados ao `.gitignore`
   - Diretórios de cache são limpos automaticamente

4. **Performance**:
   - O comando `clean` não limpa `node_modules`
   - Para limpeza total, delete manualmente e use `make install`

## 🆘 Troubleshooting

### Script não executa
```bash
chmod +x dev.sh
```

### Make não encontrado
```bash
# macOS
brew install make

# Linux
sudo apt-get install make
```

### pnpm não encontrado
```bash
npm install -g pnpm
```