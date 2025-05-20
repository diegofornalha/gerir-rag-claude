# LightRAG

Sistema leve de RAG (Retrieval Augmented Generation) para uso com Claude via MCP.

## Instalação

```bash
cd ~/.claude/lightrag
./setup_lightrag.sh
```

## Uso

### No código Python ou no Claude

```python
from claude import MCP

# Conectar ao serviço
lightrag = MCP.connect_to_service('lightrag')

# Adicionar informações à base de conhecimento
lightrag.rag_insert_text(text="LightRAG é um sistema de RAG leve para Claude.")

# Consultar informações
resultado = lightrag.rag_query(query="O que é LightRAG?")
print(resultado)
```

### Usando o demo interativo

```bash
cd ~/.claude/lightrag
python3 demo.py
```

### Testando via cURL

```bash
# Consulta
curl -X POST -H "Content-Type: application/json" \
     -d '{"query":"O que é LightRAG?"}' \
     http://127.0.0.1:5000/query

# Inserção
curl -X POST -H "Content-Type: application/json" \
     -d '{"text":"LightRAG é um sistema de RAG leve."}' \
     http://127.0.0.1:5000/insert

# Status
curl http://127.0.0.1:5000/status
```

## Documentação

Para documentação completa, abra o arquivo `docs.html` em um navegador.

```bash
open ~/.claude/lightrag/docs.html
```