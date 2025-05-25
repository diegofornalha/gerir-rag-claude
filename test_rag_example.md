# Exemplo de Teste do LightRAG MCP

## Como o LightRAG funciona:

### 1. Inserir Texto
```python
# Inserir conhecimento sobre o projeto
mcp__lightrag__rag_insert_text({
  text: "O sistema Claude Sessions integra conversas e todos através de UUIDs únicos. Cada sessão tem um arquivo JSONL com a conversa e um arquivo JSON com os todos."
})
```

### 2. Inserir Arquivo
```python
# Inserir documentação
mcp__lightrag__rag_insert_file({
  file_path: "/Users/agents/.claude/BACKUP_GDRIVE_SUCESSO.md"
})
```

### 3. Consultar Base de Conhecimento
```python
# Buscar informações
mcp__lightrag__rag_query({
  query: "como fazer backup do claude",
  mode: "hybrid"
})
```

## Modos de Busca:

- **naive**: Busca simples por palavras-chave
- **local**: Busca em contexto próximo
- **global**: Busca em toda a base
- **hybrid**: Combina local e global (melhor resultado)

## Casos de Uso Práticos:

1. **Documentação de Projetos**
   - Inserir READMEs e documentação
   - Buscar soluções para problemas

2. **Base de Conhecimento Pessoal**
   - Armazenar aprendizados
   - Recuperar informações rapidamente

3. **Histórico de Conversas**
   - Indexar conversas importantes
   - Buscar discussões anteriores

## Status Atual

⚠️ O serviço LightRAG precisa estar rodando na porta 8020 para funcionar.

Para iniciar:
```bash
cd /Users/agents/.claude/lightrag
python3 api/server.py
```

Ou usar o script:
```bash
/Users/agents/.claude/lightrag/start_lightrag.sh
```