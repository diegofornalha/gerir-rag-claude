# Ferramentas de Análise JSONL para LightRAG

Este conjunto de ferramentas foi desenvolvido para análise completa de arquivos JSONL do Claude Code, extraindo TODOS os campos documentados e fornecendo insights práticos.

## 🚀 Novos Scripts

### 1. `extract_jsonl.py` (Aprimorado)
Extrai TODOS os campos documentados dos arquivos JSONL, incluindo:
- Métricas de custo (costUSD)
- Duração (durationMs)
- Uso de tokens detalhado (input, output, cache)
- Uso de ferramentas (tool_use)
- Resultados de ferramentas (tool_result)
- Modelos utilizados
- Stop reasons
- Eficiência de cache

**Uso:**
```bash
# Análise completa com relatório
python extract_jsonl.py /path/to/conversation.jsonl

# Apenas análise (sem inserir no RAG)
python extract_jsonl.py /path/to/conversation.jsonl --analyze-only

# Saída em JSON
python extract_jsonl.py /path/to/conversation.jsonl --format json
```

### 2. `analyze_costs.py`
Script especializado para análise de custos e métricas financeiras.

**Características:**
- Análise de custos por modelo
- Estatísticas de uso de tokens
- Eficiência de cache
- Economia estimada
- Exportação de resultados

**Uso:**
```bash
# Analisar um arquivo
python analyze_costs.py /path/to/conversation.jsonl

# Analisar diretório completo
python analyze_costs.py /Users/agents/.claude/projects/ --directory

# Exportar resultados
python analyze_costs.py /path/to/dir/ -d --export results.json
```

### 3. `track_tools.py`
Rastreamento detalhado de uso de ferramentas.

**Características:**
- Correlação entre tool_use e tool_result
- Taxa de sucesso por ferramenta
- Sequências de ferramentas mais comuns
- Análise de erros
- Tamanhos médios de input/output

**Uso:**
```bash
# Analisar um arquivo
python track_tools.py conversation.jsonl

# Múltiplos arquivos
python track_tools.py file1.jsonl file2.jsonl file3.jsonl

# Exportar análise detalhada
python track_tools.py file.jsonl --export tools_analysis.json
```

### 4. `practical_analysis.py`
Análises práticas com visualizações e recomendações.

**Características:**
- Gráficos de custos diários
- Distribuição de uso por modelo
- Padrões de atividade por hora
- Recomendações automáticas
- Relatório Markdown

**Uso:**
```bash
# Análise com visualizações
python practical_analysis.py /path/to/conversation.jsonl

# Analisar diretório completo
python practical_analysis.py /Users/agents/.claude/projects/ -d

# Gerar relatório completo
python practical_analysis.py /path/to/dir/ -d --report analysis.md

# Especificar diretório de saída
python practical_analysis.py file.jsonl -o ./reports/
```

### 5. `load_claude_projects.py` (Atualizado)
Agora exibe métricas adicionais na interface:
- Custo total por conversa
- Modelos utilizados
- Contagem de ferramentas
- Total de tokens processados

## 📊 Exemplos de Saída

### Relatório de Métricas
```
📋 RELATÓRIO DE MÉTRICAS - Exemplo de Conversa
============================================================

📊 RESUMO GERAL:
  • Session ID: 463cef43-5459-4767-ba08-cc01cd6aa433
  • Total de mensagens: 42
  • Mensagens do usuário: 21
  • Mensagens do assistente: 21
  • Duração da sessão: 1h 23m 45s

💰 CUSTOS:
  • Custo total: $0.4512
  • Custo por modelo:
    - claude-opus-4-20250514: $0.3200
    - claude-3-5-sonnet-20241022: $0.1312

🔢 USO DE TOKENS:
  • Tokens de entrada: 45,231
  • Tokens de saída: 3,456
  • Tokens para criar cache: 23,107
  • Tokens lidos do cache: 12,543
  • Eficiência do cache: 54.3%

🔧 USO DE FERRAMENTAS:
  • Read: 15 vezes
  • MultiEdit: 8 vezes
  • TodoWrite: 5 vezes
  • Bash: 3 vezes
```

### Visualizações Geradas
1. **daily_costs.png**: Gráfico de linha mostrando evolução dos custos
2. **usage_distribution.png**: Pizza de modelos e barras de ferramentas
3. **hourly_activity.png**: Histograma de atividade por hora

## 🔧 Instalação de Dependências

Para usar todas as funcionalidades:

```bash
# Instalar matplotlib para visualizações (opcional)
pip install matplotlib

# As outras ferramentas usam apenas bibliotecas padrão do Python
```

## 💡 Casos de Uso Práticos

### 1. Auditoria de Custos Mensais
```bash
# Analisar todos os projetos do mês
python analyze_costs.py /Users/agents/.claude/projects/ -d --export custos_novembro.json
```

### 2. Otimização de Performance
```bash
# Identificar ferramentas com problemas
python track_tools.py /Users/agents/.claude/projects/*.jsonl -v
```

### 3. Relatório Executivo
```bash
# Gerar relatório completo com visualizações
python practical_analysis.py /Users/agents/.claude/projects/ -d \
  --report relatorio_executivo.md \
  --output-dir ./relatorios/
```

### 4. Integração com LightRAG
```bash
# Processar e inserir conversas importantes
for file in /Users/agents/.claude/projects/*.jsonl; do
    python extract_jsonl.py "$file"
done
```

## 📈 Métricas Rastreadas

### Financeiras
- Custo total e por modelo
- Custo médio por sessão/mensagem
- Economia com cache
- Tendências de gastos

### Performance
- Tempo de resposta médio
- Duração das sessões
- Tokens processados
- Taxa de cache hit

### Uso
- Modelos mais utilizados
- Ferramentas mais comuns
- Padrões de atividade
- Sequências de trabalho

### Qualidade
- Taxa de sucesso de ferramentas
- Tipos de erros comuns
- Eficiência de operações

## 🚨 Notas Importantes

1. **Performance**: Scripts otimizados para processar arquivos grandes incrementalmente
2. **Privacidade**: Cuidado ao compartilhar relatórios - podem conter informações sensíveis
3. **Armazenamento**: Considere arquivar conversas antigas para manter performance
4. **Monitoramento**: Use cron para gerar relatórios automáticos periodicamente

## 🔄 Próximos Passos

1. Integrar métricas no dashboard do LightRAG
2. Criar alertas para custos anormais
3. Implementar comparação entre períodos
4. Adicionar export para ferramentas de BI

---

*Ferramentas desenvolvidas com base na documentação oficial do formato JSONL do Claude Code*