# 🔗 Conectando Marag ao MCP A2A Gateway

## 📋 O que é o MCP A2A Gateway?

O **MCP A2A Gateway** é um gateway que permite que agentes se comuniquem através do protocolo **MCP (Model Context Protocol)** usando o padrão **A2A (Agent-to-Agent)**.

### **🎯 Funcionalidades:**
- ✅ Comunicação entre agentes via MCP
- ✅ Protocolo padronizado A2A
- ✅ Integração com outros agentes
- ✅ Comunicação via stdio ou HTTP

## 🔧 Configuração MCP para Marag

### **1. Arquivo de Configuração MCP**

Criar arquivo `~/.cursor/mcp.json` (se não existir):

```json
{
  "mcpServers": {
    "marag": {
      "command": "python3",
      "args": ["/Users/agents/.claude/marag/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/Users/agents/.claude"
      }
    }
  }
}
```

### **2. Servidor MCP para Marag**

O servidor MCP implementa os métodos necessários para comunicação A2A.

## 🚀 Implementação

### **📁 Arquivos Necessários:**

1. **`mcp_server.py`** - Servidor MCP principal
2. **`mcp_config.json`** - Configuração MCP
3. **`test_mcp_connection.py`** - Teste de conexão
4. **`a2a_gateway_client.py`** - Cliente para A2A Gateway

## 🔄 Fluxo de Comunicação

```
Marag Agent → MCP Server → A2A Gateway → Outros Agentes
     ↓              ↓              ↓              ↓
  Extração    Protocolo MCP   Gateway      Comunicação
  de Dados    JSON-RPC        A2A          Multi-Agent
```

## 📊 Métodos MCP Implementados

### **✅ Métodos Suportados:**

1. **`initialize`** - Inicialização do servidor
2. **`tools/list`** - Lista ferramentas disponíveis
3. **`tools/call`** - Executa ferramentas
4. **`extract_contact`** - Extrai informações de contato
5. **`save_to_rag`** - Salva no RAG
6. **`search_rag`** - Busca no RAG

## 🎯 Benefícios da Integração

### **✅ Comunicação Padronizada:**
- Protocolo MCP padronizado
- Integração com outros agentes
- Comunicação via stdio/HTTP

### **✅ Funcionalidades Expandidas:**
- Extração de dados via MCP
- Salvamento automático no RAG
- Busca semântica integrada
- Comunicação multi-agente

### **✅ Escalabilidade:**
- Fácil adição de novos agentes
- Protocolo extensível
- Arquitetura modular

## 🔧 Como Implementar

### **1. Criar Servidor MCP:**

```python
# mcp_server.py
import json
import sys
from pathlib import Path

class MaragMCPServer:
    def __init__(self):
        self.tools = {
            "extract_contact": {
                "name": "extract_contact",
                "description": "Extrai informações de contato do texto",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"}
                    }
                }
            }
        }
    
    def handle_request(self, request):
        # Implementar lógica MCP
        pass
```

### **2. Configurar Gateway:**

```json
{
  "gateway": {
    "host": "localhost",
    "port": 8080,
    "agents": {
      "marag": {
        "type": "mcp",
        "config": "marag_config.json"
      }
    }
  }
}
```

### **3. Testar Conexão:**

```bash
# Testar servidor MCP
python3 test_mcp_connection.py

# Testar gateway
python3 a2a_gateway_client.py
```

## 📝 Exemplos de Uso

### **🔍 Extração via MCP:**

```python
# Cliente MCP
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "extract_contact",
        "arguments": {
            "text": "Meu nome é João, email: joao@exemplo.com"
        }
    }
}
```

### **💾 Salvamento no RAG:**

```python
# Salvar via MCP
request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "save_to_rag",
        "arguments": {
            "title": "Contato João",
            "content": "João - joao@exemplo.com"
        }
    }
}
```

## 🚀 Próximos Passos

### **1. Implementação Completa:**
- ✅ Criar servidor MCP
- ✅ Configurar A2A Gateway
- ✅ Implementar métodos
- ✅ Testar integração

### **2. Funcionalidades Avançadas:**
- 🔄 Comunicação em tempo real
- 🔄 Sincronização de dados
- 🔄 Monitoramento de agentes
- 🔄 Logs detalhados

### **3. Integração com Outros Agentes:**
- 🤖 marag Agent
- 🤖 Claude Agent
- 🤖 Outros agentes MCP

---

**🎯 Marag conectado ao MCP A2A Gateway para comunicação multi-agente!** 🚀 