  1. Prefere ser chamado de Diego
  2. Usa sistema operacional MacOS
  3. Prefere comunicação em português do Brasil
  4. sempre que constatar e dizer agora você pode acessar que a aplicação funciona tente em seguida tirar um print ou navegar com puppeteer para confirmar.
  5.sim não precisa me perguntar apenas execute as tarefas até o fim, a não ser
│   que seja ao critico que vai precisar de uma decisão estrategica.  

# Configuração do Desktop Commander

O serviço Desktop Commander MCP permite acesso ao sistema de arquivos e execução de comandos. Abaixo estão exemplos de uso e comandos disponíveis:

## Comandos Principais

### Sistema de Arquivos
- `desktop_commander.list_directory(path="/caminho/diretorio")` - Lista arquivos e diretórios
- `desktop_commander.read_file(path="/caminho/arquivo.txt")` - Lê conteúdo de arquivos
- `desktop_commander.write_file(path="/caminho/arquivo.txt", content="conteúdo", mode="rewrite")` - Escreve em arquivos
- `desktop_commander.search_files(path="/caminho/base", pattern="nome_arquivo")` - Busca arquivos por nome
- `desktop_commander.search_code(path="/caminho/base", pattern="texto")` - Busca conteúdo em arquivos de código

### Manipulação de Arquivos
- `desktop_commander.create_directory(path="/caminho/novo_diretorio")` - Cria diretórios
- `desktop_commander.move_file(source="/origem", destination="/destino")` - Move/renomeia arquivos
- `desktop_commander.get_file_info(path="/caminho/arquivo")` - Obtém informações de arquivos
- `desktop_commander.edit_block(file_path="/caminho", old_string="texto", new_string="novo")` - Edita partes de arquivos

### Execução de Comandos
- `desktop_commander.execute_command(command="comando shell")` - Executa comandos no terminal
- `desktop_commander.list_processes()` - Lista processos em execução
- `desktop_commander.kill_process(pid=1234)` - Termina um processo específico

# Configuração do Memory MCP

O serviço Memory MCP permite armazenar e gerenciar conhecimento estruturado em forma de grafo. Abaixo estão exemplos de uso e comandos disponíveis:

## Operações Principais

### Manipulação de Entidades e Relações
- `create_entities` - Cria novas entidades no grafo de conhecimento, com tipo e observações associadas
- `create_relations` - Estabelece conexões entre entidades existentes com um tipo de relação específico
- `add_observations` - Adiciona novas informações/observações a entidades já existentes
- `delete_entities` - Remove entidades completas do grafo, incluindo suas relações associadas
- `delete_observations` - Remove observações específicas de entidades sem excluir a entidade
- `delete_relations` - Remove conexões específicas entre entidades sem excluir as entidades

### Consultas
- `read_graph` - Recupera todo o grafo de conhecimento com entidades e relações
- `search_nodes` - Pesquisa entidades por nome, tipo ou conteúdo das observações
- `open_nodes` - Recupera entidades específicas pelo nome, mostrando detalhes completos

# Configuração do Puppeteer

O serviço Puppeteer MCP permite automação e controle de navegador web. Abaixo estão exemplos de uso e comandos disponíveis:

## Comandos Principais

### Navegação
- `puppeteer_navigate(url: string, launchOptions?: object)` - Navega para uma URL
  ```javascript
  puppeteer_navigate({ url: "https://example.com" })
  ```

### Captura de Tela
- `puppeteer_screenshot(name: string, width?: number, height?: number, selector?: string)` - Tira screenshot
  ```javascript
  puppeteer_screenshot({ 
    name: "dashboard", 
    width: 1280, 
    height: 720,
    selector: "#main-content"  // opcional: captura elemento específico
  })
  ```

### Interação com Elementos
- `puppeteer_click(selector: string)` - Clica em um elemento
  ```javascript
  puppeteer_click({ selector: "button.submit" })
  ```

- `puppeteer_fill(selector: string, value: string)` - Preenche campo de formulário
  ```javascript
  puppeteer_fill({ selector: "#email", value: "user@example.com" })
  ```

- `puppeteer_select(selector: string, value: string)` - Seleciona opção em dropdown
  ```javascript
  puppeteer_select({ selector: "#country", value: "BR" })
  ```

- `puppeteer_hover(selector: string)` - Passa mouse sobre elemento
  ```javascript
  puppeteer_hover({ selector: ".menu-item" })
  ```

### Execução de JavaScript
- `puppeteer_evaluate(script: string)` - Executa JavaScript no contexto da página
  ```javascript
  puppeteer_evaluate({ script: "document.title" })
  puppeteer_evaluate({ script: "document.querySelectorAll('a').length" })
  ```

## Casos de Uso

1. **Testes Automatizados**: Verificar funcionalidade de aplicações web
2. **Screenshots para Documentação**: Capturar telas de sistemas
3. **Automação de Tarefas**: Login automático, preenchimento de formulários
4. **Extração de Dados**: Coletar informações de páginas (com permissão)
5. **Monitoramento**: Verificar disponibilidade de serviços

# Configuração do Terminal

O serviço Terminal MCP permite execução de comandos no sistema. Abaixo estão exemplos de uso:

## Comando Principal

- `terminal.run_command(command: string, workdir?: string, stdin?: string)` - Executa comandos
  ```bash
  terminal.run_command({ command: "ls -la" })
  terminal.run_command({ 
    command: "python3 script.py",
    workdir: "/path/to/project" 
  })
  ```

## Casos de Uso

1. **Executar scripts**: Python, Node.js, Shell scripts
2. **Operações git**: commit, push, pull
3. **Gerenciar processos**: iniciar/parar serviços
4. **Análise de logs**: grep, tail, awk
5. **Operações de sistema**: verificar espaço, processos

# Configuração do LightRAG

O serviço LightRAG MCP permite indexação e busca em documentos. Abaixo estão exemplos de uso:

## Comandos Principais

### Consultas
- `rag_query(query: string, mode?: string)` - Busca informações na base de conhecimento
  ```python
  rag_query({ query: "como configurar docker", mode: "hybrid" })
  ```

### Inserção de Dados
- `rag_insert_text(text: string)` - Insere texto na base
  ```python
  rag_insert_text({ text: "Conteúdo do documento..." })
  ```

- `rag_insert_file(file_path: string)` - Insere arquivo na base
  ```python
  rag_insert_file({ file_path: "/path/to/document.txt" })
  ```

## Modos de Busca
- `naive`: Busca simples por palavras-chave
- `local`: Busca em contexto local
- `global`: Busca em todo o conhecimento
- `hybrid`: Combinação de local e global (padrão)

## Limpeza Automática de Todos

O sistema agora realiza limpeza automática semanal dos arquivos de tarefas (todos), removendo:
- Arquivos vazios
- Arquivos contendo apenas um array vazio "[]"
- Arquivos sem tarefas válidas

Para limpar manualmente a qualquer momento:
```bash
~/.claude/clean_todos.sh
```

A limpeza preserva todos os arquivos com tarefas válidas e o arquivo de documentação todos.md.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.