# Model Context Protocol (MCP) no LightRAG

## O que é o Model Context Protocol?

O Model Context Protocol (MCP) é um protocolo aberto projetado para padronizar como aplicações fornecem contexto aos Modelos de Linguagem de Grande Escala (LLMs). Seu objetivo principal é criar uma espécie de "porta USB-C universal para aplicações de IA" que permite integração perfeita entre modelos de IA e várias fontes de dados e ferramentas.

## Componentes Principais do MCP

- **MCP Hosts**: Aplicações como Claude Desktop que desejam acessar dados
- **MCP Clients**: Clientes do protocolo que mantêm conexões com servidores
- **MCP Servers**: Programas leves que expõem capacidades específicas
- **Fontes de Dados Locais**: Arquivos de computador, bancos de dados, serviços
- **Serviços Remotos**: Sistemas externos acessíveis via APIs

## Integração com o LightRAG

No sistema LightRAG, o MCP é utilizado para conectar o serviço RAG (Retrieval Augmented Generation) com clientes como o Claude, permitindo consultas e inserções de documentos de maneira padronizada. O arquivo `/Users/agents/.claude/app_mcp.py` é responsável por registrar e expor as funcionalidades do LightRAG como um serviço MCP.

### Funcionalidades Expostas pelo LightRAG via MCP

O LightRAG expõe as seguintes funcionalidades via MCP:

1. **rag_query**: Consulta documentos na base de conhecimento
   ```python
   # Exemplo de uso
   result = lightrag_service.rag_query(query="Como usar o LightRAG?", mode="hybrid")
   ```

2. **rag_insert_text**: Insere texto na base de conhecimento
   ```python
   # Exemplo de uso
   result = lightrag_service.rag_insert_text(text="Conteúdo a ser inserido", source="manual")
   ```

3. **rag_insert_file**: Insere o conteúdo de um arquivo na base
   ```python
   # Exemplo de uso
   result = lightrag_service.rag_insert_file(file_path="/caminho/para/arquivo.txt")
   ```

4. **rag_status**: Verifica o status do serviço LightRAG
   ```python
   # Exemplo de uso
   status = lightrag_service.rag_status()
   ```

5. **rag_clear**: Limpa a base de conhecimento (requer confirmação)
   ```python
   # Exemplo de uso
   result = lightrag_service.rag_clear(confirm=True)
   ```

## Como o LightRAG se integra ao MCP

O arquivo `/Users/agents/.claude/app_mcp.py` registra o serviço LightRAG como um servidor MCP, permitindo que aplicações como o Claude possam se conectar a ele de forma padronizada.

```python
# Trecho simplificado do app_mcp.py
from claude_mcp import MCPServer
from lightrag.core.mcp import rag_query, rag_insert_text, rag_insert_file, rag_status, rag_clear

# Criar servidor MCP
server = MCPServer("lightrag")

# Registrar funções do LightRAG
server.register_function("rag_query", rag_query)
server.register_function("rag_insert_text", rag_insert_text)
server.register_function("rag_insert_file", rag_insert_file)
server.register_function("rag_status", rag_status)
server.register_function("rag_clear", rag_clear)

# Iniciar servidor
server.start()
```

## Benefícios do uso do MCP no LightRAG

1. **Padronização**: Interface consistente para interação com o sistema RAG
2. **Flexibilidade**: Facilita a integração com diferentes clientes e LLMs
3. **Segurança**: Segue as melhores práticas para segurança de dados
4. **Extensibilidade**: Permite adicionar novas funcionalidades facilmente

## Como usar o LightRAG via MCP

Para utilizar o LightRAG via MCP em seus próprios scripts:

```python
# Exemplo de uso em scripts Python
from claude import MCP  # Model Context Protocol

# Conectar ao serviço LightRAG
lightrag_service = MCP.connect_to_service('lightrag')

# Consultar a base de conhecimento
result = lightrag_service.rag_query(query="Como implementar um sistema RAG?")

# Exibir o resultado
print(result["response"])
```

## Recursos Adicionais

- Documentação oficial do MCP: [Model Context Protocol](https://modelcontextprotocol.io/introduction)
- Repositório do LightRAG: [GitHub](https://github.com/seu-usuario/lightrag)

---

Criado em: 21/05/2024