# API Documentation - Node Local DB

## Visão Geral

Esta é a documentação completa da API REST para o sistema de gerenciamento de issues. A API foi construída com Fastify, PostgreSQL e Drizzle ORM, oferecendo endpoints type-safe com validação automática via Zod.

## Base URL

```
http://localhost:3333
```

## Autenticação

⚠️ **Nota**: Atualmente a API não implementa autenticação. Esta funcionalidade está planejada para versões futuras.

## Headers Padrão

### Request Headers
```http
Content-Type: application/json
Accept: application/json
```

### Response Headers
```http
Content-Type: application/json
X-Cache: HIT|MISS (indica se a resposta veio do cache)
```

## Recursos da API

### 1. Issues

#### 1.1 Criar Issue

Cria uma nova issue no sistema.

**Endpoint**: `POST /issues`

**Body Parameters**:
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| title | string | Sim | Título da issue (1-255 caracteres) |
| description | string | Não | Descrição detalhada da issue |
| userId | number | Sim | ID do usuário criador |

**Exemplo de Request**:
```bash
curl -X POST http://localhost:3333/issues \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bug no formulário de login",
    "description": "O botão de submit não está funcionando no Firefox",
    "userId": 1
  }'
```

**Response (201 Created)**:
```json
{
  "id": 42,
  "title": "Bug no formulário de login",
  "userId": 1,
  "createdAt": "2024-01-24T10:30:00Z"
}
```

#### 1.2 Listar Issues

Retorna uma lista paginada de issues.

**Endpoint**: `GET /issues`

**Query Parameters**:
| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| page | number | 1 | Número da página |
| limit | number | 20 | Itens por página (máx: 100) |
| userId | number | - | Filtrar por usuário |

**Exemplo de Request**:
```bash
curl "http://localhost:3333/issues?page=1&limit=10&userId=1"
```

**Response (200 OK)**:
```json
{
  "data": [
    {
      "id": 42,
      "title": "Bug no formulário de login",
      "description": "O botão de submit não está funcionando no Firefox",
      "userId": 1,
      "createdAt": "2024-01-24T10:30:00Z"
    },
    {
      "id": 41,
      "title": "Adicionar dark mode",
      "description": null,
      "userId": 1,
      "createdAt": "2024-01-23T15:20:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 42,
    "totalPages": 5
  }
}
```

#### 1.3 Buscar Issue por ID

Retorna uma issue específica com dados do usuário.

**Endpoint**: `GET /issues/:id`

**Path Parameters**:
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| id | number | ID da issue |

**Exemplo de Request**:
```bash
curl http://localhost:3333/issues/42
```

**Response (200 OK)**:
```json
{
  "id": 42,
  "title": "Bug no formulário de login",
  "description": "O botão de submit não está funcionando no Firefox",
  "userId": 1,
  "createdAt": "2024-01-24T10:30:00Z",
  "user": {
    "id": 1,
    "name": "João Silva"
  }
}
```

**Response (404 Not Found)**:
```json
{
  "error": "Issue not found"
}
```

#### 1.4 Atualizar Issue

Atualiza uma issue existente.

**Endpoint**: `PUT /issues/:id`

**Path Parameters**:
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| id | number | ID da issue |

**Body Parameters**:
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| title | string | Não | Novo título (1-255 caracteres) |
| description | string | Não | Nova descrição |
| userId | number | Não | Novo ID do usuário |

**Exemplo de Request**:
```bash
curl -X PUT http://localhost:3333/issues/42 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bug crítico no formulário de login",
    "description": "URGENTE: O botão não funciona em nenhum navegador"
  }'
```

**Response (200 OK)**:
```json
{
  "id": 42,
  "title": "Bug crítico no formulário de login",
  "description": "URGENTE: O botão não funciona em nenhum navegador",
  "userId": 1,
  "createdAt": "2024-01-24T10:30:00Z",
  "updatedAt": "2024-01-24T14:45:00Z"
}
```

#### 1.5 Deletar Issue

Remove uma issue do sistema.

**Endpoint**: `DELETE /issues/:id`

**Path Parameters**:
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| id | number | ID da issue |

**Exemplo de Request**:
```bash
curl -X DELETE http://localhost:3333/issues/42
```

**Response (204 No Content)**: Sem corpo de resposta

**Response (404 Not Found)**:
```json
{
  "error": "Issue not found"
}
```

### 2. Users

#### 2.1 Criar Usuário

Cria um novo usuário no sistema.

**Endpoint**: `POST /users`

**Body Parameters**:
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| name | string | Sim | Nome do usuário (1-255 caracteres) |

**Exemplo de Request**:
```bash
curl -X POST http://localhost:3333/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Maria Santos"
  }'
```

**Response (201 Created)**:
```json
{
  "id": 5,
  "name": "Maria Santos",
  "createdAt": "2024-01-24T10:30:00Z"
}
```

#### 2.2 Listar Usuários

Retorna uma lista paginada de usuários.

**Endpoint**: `GET /users`

**Query Parameters**:
| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| page | number | 1 | Número da página |
| limit | number | 20 | Itens por página (máx: 100) |

**Exemplo de Request**:
```bash
curl "http://localhost:3333/users?page=1&limit=10"
```

**Response (200 OK)**:
```json
{
  "data": [
    {
      "id": 5,
      "name": "Maria Santos",
      "createdAt": "2024-01-24T10:30:00Z"
    },
    {
      "id": 4,
      "name": "Pedro Oliveira",
      "createdAt": "2024-01-23T15:20:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25,
    "totalPages": 3
  }
}
```

#### 2.3 Buscar Usuário por ID

Retorna um usuário específico com contagem de issues.

**Endpoint**: `GET /users/:id`

**Path Parameters**:
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| id | number | ID do usuário |

**Exemplo de Request**:
```bash
curl http://localhost:3333/users/5
```

**Response (200 OK)**:
```json
{
  "id": 5,
  "name": "Maria Santos",
  "createdAt": "2024-01-24T10:30:00Z",
  "issuesCount": 15
}
```

**Response (404 Not Found)**:
```json
{
  "error": "User not found"
}
```

### 3. Health Check

#### 3.1 Verificar Status da API

Retorna o status de saúde da API.

**Endpoint**: `GET /health`

**Exemplo de Request**:
```bash
curl http://localhost:3333/health
```

**Response (200 OK)**:
```json
{
  "status": "ok",
  "timestamp": "2024-01-24T10:30:00Z",
  "uptime": 3600.5
}
```

## Tratamento de Erros

A API retorna erros em formato JSON padronizado:

### Erro de Validação (400)
```json
{
  "error": "Validation Error",
  "message": "Invalid request data",
  "details": [
    {
      "field": "title",
      "message": "String must contain at least 1 character(s)"
    }
  ]
}
```

### Recurso Não Encontrado (404)
```json
{
  "error": "Issue not found"
}
```

### Rate Limit Excedido (429)
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Please try again later."
}
```

### Erro Interno do Servidor (500)
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

## Cache

A API implementa cache em memória para endpoints GET:

- **TTL (Time To Live)**: 60 segundos
- **Header X-Cache**: Indica se a resposta veio do cache
  - `HIT`: Resposta servida do cache
  - `MISS`: Resposta gerada e armazenada no cache
- **Invalidação**: Cache é limpo em operações de escrita (POST, PUT, DELETE)

## Limites e Restrições

- **Paginação**: Máximo de 100 itens por página
- **Tamanho de String**: 
  - Títulos: 1-255 caracteres
  - Nomes: 1-255 caracteres
  - Descrições: Sem limite definido
- **IDs**: Devem ser inteiros positivos

## Segurança

### Headers de Segurança (via Helmet)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (em produção)

### CORS
- Desenvolvimento: Aceita todas as origens
- Produção: Configurar domínio específico em `CORS_ORIGIN`

### Compressão
- Gzip/Brotli habilitado para todas as respostas

## Exemplos de Uso com JavaScript

### Criar uma Issue
```javascript
const response = await fetch('http://localhost:3333/issues', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    title: 'Nova feature request',
    description: 'Implementar sistema de notificações',
    userId: 1
  })
});

const issue = await response.json();
console.log('Issue criada:', issue);
```

### Listar Issues com Filtro
```javascript
const userId = 1;
const page = 1;
const limit = 20;

const response = await fetch(
  `http://localhost:3333/issues?userId=${userId}&page=${page}&limit=${limit}`
);

const { data, pagination } = await response.json();
console.log(`Mostrando ${data.length} de ${pagination.total} issues`);
```

### Atualizar uma Issue
```javascript
const issueId = 42;
const response = await fetch(`http://localhost:3333/issues/${issueId}`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    title: 'Título atualizado',
    description: 'Descrição atualizada com mais detalhes'
  })
});

if (response.ok) {
  const updatedIssue = await response.json();
  console.log('Issue atualizada:', updatedIssue);
} else {
  console.error('Erro ao atualizar issue');
}
```

## Versionamento

A API atualmente não implementa versionamento. Futuras versões podem incluir versionamento via:
- Path (`/v1/issues`)
- Header (`Accept: application/vnd.api+json;version=1`)

## Status de Desenvolvimento

### Implementado ✅
- CRUD completo para Issues
- CRUD parcial para Users
- Paginação
- Cache em memória
- Validação com Zod
- Tratamento de erros
- Headers de segurança
- Compressão
- Health check

### Planejado 🚧
- Autenticação JWT
- Rate limiting
- WebSockets para updates em tempo real
- Busca e filtros avançados
- Documentação Swagger/OpenAPI
- Testes automatizados
- Métricas e monitoramento

## Suporte

Para reportar bugs ou solicitar features, abra uma issue no repositório do projeto.