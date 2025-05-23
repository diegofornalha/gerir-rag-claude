# Formato JSONL - Explicação Detalhada

## O que é JSONL?

JSONL (JSON Lines) é um formato de arquivo de texto onde cada linha contém um objeto JSON válido e completo. É diferente de um arquivo JSON tradicional que contém um único objeto ou array.

### Características do JSONL:
- **Uma linha = Um objeto JSON**
- **Sem vírgulas entre objetos**
- **Cada linha é independente**
- **Facilita processamento linha por linha**
- **Ideal para logs e streaming de dados**

## Estrutura do Arquivo de Projeto Claude

O arquivo `/Users/agents/.claude/projects/-Users-agents--claude/eaa82ead-c3be-416b-8d01-5e4a62b83390.jsonl` contém o histórico de uma conversa com o Claude. Vamos analisar os principais tipos de objetos:

### 1. Summary (Resumo)
```json
{
  "type": "summary",
  "summary": "LightRAG App Deployment and Server Activation",
  "leafUuid": "303a2eab-2e4f-4fc0-8d68-89e2dd1efaaf"
}
```
- **type**: Identifica o tipo de registro (summary)
- **summary**: Descrição concisa da conversa
- **leafUuid**: Identificador único da folha/nó

### 2. User Message (Mensagem do Usuário)
```json
{
  "parentUuid": null,
  "isSidechain": false,
  "userType": "external",
  "cwd": "/Users/agents/.claude",
  "sessionId": "eaa82ead-c3be-416b-8d01-5e4a62b83390",
  "version": "1.0.2",
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "crie um .md sobre \"WebFetch(domain:lojaintegrada.docs.apiary.io)\","
      }
    ]
  },
  "uuid": "213232a5-59da-4aab-87cc-7a8a9f7847f9",
  "timestamp": "2025-05-23T12:43:54.026Z"
}
```

#### Campos Principais:
- **parentUuid**: UUID da mensagem pai (null se for primeira)
- **isSidechain**: Se é uma cadeia lateral de conversa
- **userType**: Tipo de usuário ("external" para humano)
- **cwd**: Diretório de trabalho atual
- **sessionId**: ID único da sessão (nome do arquivo)
- **version**: Versão do formato
- **type**: Tipo de mensagem ("user", "assistant")
- **message**: Conteúdo da mensagem
  - **role**: Papel do remetente
  - **content**: Array com o conteúdo (texto, imagens, etc.)
- **uuid**: Identificador único da mensagem
- **timestamp**: Momento da mensagem

### 3. Assistant Message (Resposta do Claude)
```json
{
  "parentUuid": "213232a5-59da-4aab-87cc-7a8a9f7847f9",
  "type": "assistant",
  "message": {
    "id": "msg_01FwjGFqBtcNvUj6pHKXvDTj",
    "type": "message",
    "role": "assistant",
    "model": "claude-3-7-sonnet-20250219",
    "content": [...],
    "stop_reason": "tool_use",
    "usage": {
      "input_tokens": 4,
      "cache_creation_input_tokens": 22634,
      "cache_read_input_tokens": 0,
      "output_tokens": 164
    }
  },
  "costUSD": 0.043674750000000005,
  "durationMs": 8959,
  "uuid": "7c18e874-070d-42c2-8c17-cadcb03d54cd"
}
```

#### Campos Adicionais do Assistant:
- **model**: Modelo específico do Claude usado
- **stop_reason**: Por que a resposta parou ("end_turn", "tool_use")
- **usage**: Detalhamento de tokens utilizados
  - **input_tokens**: Tokens de entrada
  - **cache_creation_input_tokens**: Tokens para criar cache
  - **cache_read_input_tokens**: Tokens lidos do cache
  - **output_tokens**: Tokens de saída
- **costUSD**: Custo estimado em dólares
- **durationMs**: Duração em milissegundos

### 4. Tool Use (Uso de Ferramenta)
```json
{
  "type": "assistant",
  "message": {
    "content": [
      {
        "type": "tool_use",
        "id": "toolu_019i25FiHjTVfu5zAVgseRRB",
        "name": "WebFetch",
        "input": {
          "url": "https://lojaintegrada.docs.apiary.io",
          "prompt": "Extraia informações sobre a API..."
        }
      }
    ]
  }
}
```

### 5. Tool Result (Resultado de Ferramenta)
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "tool_use_id": "toolu_019i25FiHjTVfu5zAVgseRRB",
        "type": "tool_result",
        "content": "Based on the provided content..."
      }
    ]
  },
  "toolUseResult": {
    "bytes": 5728,
    "code": 200,
    "codeText": "OK",
    "result": "...",
    "durationMs": 5213,
    "url": "https://lojaintegrada.docs.apiary.io"
  }
}
```

## Fluxo de Conversa

O arquivo JSONL registra todo o fluxo de uma conversa:

1. **Usuário faz pergunta** → Registro tipo "user"
2. **Claude processa** → Registro tipo "assistant" 
3. **Claude usa ferramenta** → Registro com "tool_use"
4. **Sistema retorna resultado** → Registro com "tool_result"
5. **Claude responde final** → Novo registro tipo "assistant"

## Vantagens do Formato JSONL

1. **Streaming**: Pode processar linha por linha sem carregar tudo
2. **Append-only**: Fácil adicionar novas mensagens
3. **Recuperação**: Se corromper, perde apenas linhas afetadas
4. **Análise**: Facilita análise de conversas e métricas
5. **Compatibilidade**: Suportado por muitas ferramentas

## Uso Prático

```python
# Lendo arquivo JSONL
import json

with open('conversa.jsonl', 'r') as f:
    for linha in f:
        objeto = json.loads(linha)
        if objeto['type'] == 'user':
            print(f"Usuário: {objeto['message']['content'][0]['text']}")
        elif objeto['type'] == 'assistant':
            print(f"Claude: {objeto['message']['content'][0]['text']}")
```

## Estrutura de Diretórios Claude

- `/projects/`: Armazena conversas JSONL
- `/todos/`: Armazena listas de tarefas
- Cada conversa tem um UUID único como nome de arquivo

---

*Este formato permite rastreabilidade completa de conversas, análise de custos, e replay de interações com o Claude.*