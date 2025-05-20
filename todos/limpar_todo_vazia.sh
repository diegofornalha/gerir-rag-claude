#!/bin/bash
# Script para limpar arquivos vazios ou com apenas um array vazio no diretório todos

# Cores para saída
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

TODOS_DIR="${HOME}/.claude/todos"

echo -e "${CYAN}=== Limpeza de Arquivos de Tarefas (Todos) ===${NC}\n"

# Verifica se o diretório existe
if [ ! -d "$TODOS_DIR" ]; then
  echo -e "${YELLOW}Diretório $TODOS_DIR não encontrado.${NC}"
  exit 1
fi

# Contador de arquivos removidos
removed_count=0
empty_array_count=0
preserved_count=0

# Função para verificar se o arquivo contém apenas "[]"
is_empty_array() {
  local file="$1"
  local content=$(cat "$file" | tr -d '[:space:]')
  if [ "$content" = "[]" ]; then
    return 0  # Verdadeiro (é um array vazio)
  else
    return 1  # Falso (não é um array vazio)
  fi
}

# Função para verificar se o arquivo tem tarefas válidas
has_valid_tasks() {
  local file="$1"
  # Verifica se o arquivo contém pelo menos uma tarefa com content, status e id
  if grep -q "\"content\":" "$file" && grep -q "\"status\":" "$file" && grep -q "\"id\":" "$file"; then
    return 0  # Verdadeiro (tem tarefas válidas)
  else
    return 1  # Falso (não tem tarefas válidas)
  fi
}

# Lista todos os arquivos JSON no diretório
echo -e "Procurando arquivos de tarefas...\n"

for file in "$TODOS_DIR"/*.json; do
  # Verifica se o padrão expandiu para arquivos reais
  if [ ! -f "$file" ]; then
    continue
  fi
  
  filename=$(basename "$file")
  
  # Verifica se é um arquivo vazio
  if [ ! -s "$file" ]; then
    echo -e "${YELLOW}Removendo arquivo vazio:${NC} $filename"
    rm "$file"
    ((removed_count++))
    continue
  fi
  
  # Verifica se é um array vazio
  if is_empty_array "$file"; then
    echo -e "${YELLOW}Removendo arquivo com array vazio:${NC} $filename"
    rm "$file"
    ((empty_array_count++))
    continue
  fi
  
  # Verifica se tem tarefas válidas
  if has_valid_tasks "$file"; then
    echo -e "${GREEN}Preservando arquivo com tarefas válidas:${NC} $filename"
    ((preserved_count++))
  else
    echo -e "${YELLOW}Removendo arquivo sem tarefas válidas:${NC} $filename"
    rm "$file"
    ((removed_count++))
  fi
done

# Lida com o arquivo todos.md separadamente
if [ -f "$TODOS_DIR/todos.md" ]; then
  echo -e "\n${GREEN}Preservando arquivo de documentação:${NC} todos.md"
fi

# Resumo da operação
echo -e "\n${CYAN}=== Resumo da Limpeza ===${NC}"
echo -e "${GREEN}Arquivos preservados:${NC} $preserved_count"
echo -e "${YELLOW}Arquivos vazios removidos:${NC} $removed_count"
echo -e "${YELLOW}Arquivos com array vazio removidos:${NC} $empty_array_count"
echo -e "${YELLOW}Total de arquivos removidos:${NC} $((removed_count + empty_array_count))"

# Criação de hook para execução automática
HOOKS_DIR="${HOME}/.claude/hooks"
mkdir -p "$HOOKS_DIR"

cat > "${HOOKS_DIR}/post_cleanup.sh" << EOF
#!/bin/bash
# Hook executado periodicamente para limpeza
${HOME}/.claude/clean_todos.sh
EOF

chmod +x "${HOOKS_DIR}/post_cleanup.sh"

# Adicionar entrada de cron para execução periódica (semanal)
CRON_JOB="0 0 * * 0 ${HOME}/.claude/clean_todos.sh > ${HOME}/.claude/clean_todos.log 2>&1"

# Verifica se o cron job já existe
(crontab -l 2>/dev/null | grep -q "clean_todos.sh") || {
  # Adiciona o cron job apenas se não existir
  (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
  echo -e "\n${GREEN}Limpeza automática semanal configurada.${NC}"
}

echo -e "\n${GREEN}Para executar a limpeza manualmente:${NC}"
echo -e "${CYAN}~/.claude/clean_todos.sh${NC}"

# Adicionar ao CLAUDE.md
if ! grep -q "## Limpeza Automática de Todos" "${HOME}/.claude/CLAUDE.md"; then
  cat >> "${HOME}/.claude/CLAUDE.md" << EOF

## Limpeza Automática de Todos

O sistema agora realiza limpeza automática semanal dos arquivos de tarefas (todos), removendo:
- Arquivos vazios
- Arquivos contendo apenas um array vazio "[]"
- Arquivos sem tarefas válidas

Para limpar manualmente a qualquer momento:
\`\`\`bash
~/.claude/clean_todos.sh
\`\`\`

A limpeza preserva todos os arquivos com tarefas válidas e o arquivo de documentação todos.md.
EOF
fi