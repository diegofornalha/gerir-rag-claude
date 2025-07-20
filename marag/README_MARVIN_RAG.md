# 🤖 marag Agent com Integração RAG

## 📋 Visão Geral

O **marag Agent** foi modificado para integrar com o **MCP RAG Server**, permitindo que todas as informações extraídas das conversas sejam automaticamente salvas no sistema RAG para busca e referência futura.

## 🎯 Funcionalidades

### **✅ Extração de Informações**
- Extrai informações de contato estruturadas
- Identifica nome, email, telefone, organização e cargo
- Processa texto natural e converte para dados estruturados

### **✅ Salvamento Automático no RAG**
- Salva automaticamente todas as conversas no RAG
- Mantém histórico persistente de extrações
- Organiza informações por sessão e data

### **✅ Busca Semântica**
- Busca informações salvas anteriormente
- Permite encontrar contatos por nome, empresa, etc.
- Histórico completo de conversas

## 🚀 Como Usar

### **1. Iniciar o Servidor marag com RAG**

```bash
cd /Users/agents/.claude/marag
python3 start_marag_with_rag.py
```

**Resultado:**
```
🚀 Iniciando servidor marag com RAG em localhost:10030...
📊 Funcionalidades:
  ✅ Extração de informações de contato
  ✅ Salvamento automático no RAG
  ✅ Memória persistente de conversas
  ✅ Busca semântica em histórico

✅ Servidor configurado com RAG, iniciando...
🌐 Acesse: http://localhost:10030
📝 Use o agente para extrair informações e elas serão salvas automaticamente no RAG!
```

### **2. Testar a Integração**

```bash
python3 test_rag_integration.py
```

**Testes incluídos:**
- ✅ Query com informações completas
- ✅ Query incompleta (pede mais informações)
- ✅ Verificação de salvamento no RAG

### **3. Buscar Informações Salvas**

```bash
python3 search_marag_rag.py
```

**Funcionalidades:**
- 🔍 Lista todos os documentos do marag
- 🔍 Busca interativa por palavra-chave
- 🔍 Exibe informações estruturadas

## 📊 Estrutura dos Dados

### **Formato do Documento Salvo:**

```json
{
  "id": "doc_marag_1752993197832",
  "title": "Extração de Contato - Sessão test_session_1",
  "content": "CONVERSAÇÃO marag AGENT\n========================\n\nSessão: test_session_1\nData: 2025-07-20 03:33:17\n\nQUERY DO USUÁRIO:\nMeu nome é João Silva, email: joao.silva@exemplo.com...\n\nINFORMAÇÕES EXTRAÍDAS:\n{\n  \"name\": \"João Silva\",\n  \"email\": \"joao.silva@exemplo.com\",\n  \"phone\": \"(11) 99999-9999\",\n  \"organization\": \"TechCorp\",\n  \"role\": \"desenvolvedor senior\"\n}\n\nRESUMO:\nExtraído contato completo de João Silva...\n\nTIPO: Extração de informações de contato\nFONTE: marag Agent A2A",
  "type": "contact_extraction",
  "source": "marag_session_test_session_1",
  "created_at": "2025-07-20T03:33:17Z",
  "metadata": {
    "extracted_by": "marag_agent",
    "session_id": "marag_session"
  }
}
```

## 🔧 Arquitetura

### **📁 Arquivos Modificados:**

1. **`agent.py`** - Agente principal com integração RAG
2. **`start_marag_with_rag.py`** - Servidor com RAG
3. **`test_rag_integration.py`** - Testes da integração
4. **`search_marag_rag.py`** - Buscador de documentos

### **🔄 Fluxo de Dados:**

```
Usuário → marag Agent → Extração → RAG → Busca Futura
   ↓           ↓           ↓        ↓         ↓
  Query    Processa    Estrutura  Salva    Consulta
```

## 🎯 Exemplos de Uso

### **Exemplo 1: Extração Completa**

**Input:**
```
"Meu nome é Ana Costa, email: ana.costa@empresa.com, 
telefone: (21) 98888-7777, trabalho na TechSolutions 
como gerente de projetos"
```

**Output no RAG:**
- ✅ Nome: Ana Costa
- ✅ Email: ana.costa@empresa.com
- ✅ Telefone: (21) 98888-7777
- ✅ Empresa: TechSolutions
- ✅ Cargo: gerente de projetos

### **Exemplo 2: Busca Posterior**

**Buscar por:** "Ana Costa"

**Resultado:**
```
📄 Extração de Contato - Sessão session_123
   🆔 ID: doc_marag_1752993197832
   📅 Criado: 2025-07-20T03:33:17Z
   🏷️  Tipo: contact_extraction
   📍 Fonte: marag_session_session_123
   📝 Conteúdo: CONVERSAÇÃO marag AGENT...
```

## 🔍 Comandos Úteis

### **Verificar Status do RAG:**
```bash
# Verificar documentos do marag
python3 search_marag_rag.py

# Verificar cache RAG
ls -la /Users/agents/.claude/mcp-rag-cache/
```

### **Limpar Cache (se necessário):**
```bash
# Backup
cp /Users/agents/.claude/mcp-rag-cache/documents.json /Users/agents/.claude/mcp-rag-cache/documents.json.backup

# Limpar apenas documentos do marag
python3 -c "
import json
from pathlib import Path
rag_path = Path.home() / '.claude' / 'mcp-rag-cache' / 'documents.json'
if rag_path.exists():
    with open(rag_path, 'r') as f:
        data = json.load(f)
    docs = [d for d in data['documents'] if not d.get('source', '').startswith('marag_session_')]
    data['documents'] = docs
    with open(rag_path, 'w') as f:
        json.dump(data, f, indent=2)
print('✅ Documentos do marag removidos')
"
```

## 🎉 Benefícios

### **✅ Memória Persistente**
- Todas as conversas ficam salvas
- Busca por informações anteriores
- Histórico completo de extrações

### **✅ Organização Automática**
- Dados estruturados automaticamente
- Metadados ricos (sessão, data, tipo)
- Fácil busca e filtragem

### **✅ Integração Offline-First**
- Funciona sem internet
- Dados locais seguros
- Performance otimizada

### **✅ Escalabilidade**
- Suporta múltiplas sessões
- Crescimento automático do cache
- Backup e recuperação simples

## 🚀 Próximos Passos

1. **Adicionar mais tipos de extração** (eventos, tarefas, etc.)
2. **Implementar busca semântica avançada** no RAG
3. **Criar interface web** para visualização
4. **Adicionar exportação** de dados estruturados
5. **Implementar sincronização** com outros sistemas

---

**🎯 marag Agent com RAG - Memória Persistente para Conversas Inteligentes!** 🚀 