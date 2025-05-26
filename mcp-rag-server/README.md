# MCP-RAG Server

Servidor MCP customizado que unifica RAG local com captura de documentações web.

## Funcionalidades

### 🔍 Busca Vetorial Real
- Indexação com TF-IDF e busca por similaridade
- Persistência local em cache
- Múltiplos modos de busca

### 🌐 WebFetch Integration
- Captura automática de documentações web
- Indexação de subpáginas
- Suporte para múltiplos domínios

### 📋 Claude Sessions
- Integração com sistema de tarefas
- Indexação automática de sessões
- Busca em histórico de conversas

## Instalação

```bash
cd /Users/agents/.claude/mcp-rag-server
pip install -r requirements.txt
```

## Configuração no Claude

Adicione ao seu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-rag": {
      "command": "python",
      "args": ["/Users/agents/.claude/mcp-rag-server/server.py"]
    }
  }
}
```

## Uso

### Criar Knowledge Base de Documentações

```python
# Indexar documentação do MCP
mcp_rag.rag_webfetch({
  url: "https://modelcontextprotocol.io/docs",
  max_depth: 2
})

# Criar knowledge base completo
mcp_rag.rag_create_knowledge_base({
  urls: [
    "https://modelcontextprotocol.io/docs",
    "https://docs.anthropic.com/claude/docs",
    "https://langchain.com/docs"
  ]
})
```

### Buscar Informações

```python
# Busca simples
mcp_rag.rag_search({
  query: "como criar ferramentas MCP",
  mode: "hybrid"
})

# Busca com mais resultados
mcp_rag.rag_search({
  query: "Claude Sessions integration", 
  limit: 10
})
```

### Indexar Sessões Claude

```python
# Indexar todas as sessões
mcp_rag.rag_index_all_sessions()

# Indexar sessão específica
mcp_rag.rag_index_session({
  session_id: "uuid-da-sessao"
})
```

## Fluxo de Dados

```
[WebFetch URLs] → [BeautifulSoup Parser] → [TF-IDF Vectorizer] → [Cache Local]
                                                ↓
[Claude Sessions] → [JSON Parser] →  [Índice Unificado] ← [Busca Vetorial]
                                                ↓
                                         [Resultados Rankeados]
```

## Estrutura do Cache

```
~/.claude/mcp-rag-cache/
├── documents.json    # Documentos indexados
├── index.pkl        # Vetorizador TF-IDF
└── vectors.npy      # Vetores de documentos
```