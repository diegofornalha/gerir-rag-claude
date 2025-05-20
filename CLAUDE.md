  1. Prefere ser chamado de Diego
  2. Usa sistema operacional MacOS
  3. Prefere comunicação em português do Brasil
  4. Tem interesse em sistemas de agentes de IA integrados
  5. Está desenvolvendo um sistema pessoal de agentes

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
