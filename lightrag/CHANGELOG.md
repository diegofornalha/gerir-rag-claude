# Changelog LightRAG

## [Melhorias 2025-05-21 - Parte 2]

### Reorganização de Scripts
- Consolidado scripts de detecção e remoção de duplicatas em `tools/duplicate_manager.py`
- Movido scripts de utilidade para diretórios apropriados
  - `remover_duplicatas_auto.py` e `correct_duplicate_ids.py` → `tools/duplicate_manager.py`
  - `query_project.py`, `query_claude_docs.py` → `api/`
  - `extract_jsonl.py` → `api/`
- Mantido sistema de symlinks para compatibilidade com versões anteriores

### Unificação de Scripts de Manutenção
- Criado script unificado `tools/maintenance.sh` com todas as funções de manutenção
- Consolidado funcionalidades de `clean_pids.sh`, `cleanup.sh` e `limpar_banco.sh`
- Implementado menu interativo para operações de manutenção
- Adicionadas novas funcionalidades:
  - Verificação de integridade do sistema
  - Backup automático do banco de dados
  - Gerenciamento de processos
  - Limpeza de arquivos temporários

### Organização do Código
- Criado diretório `obsolete/` para arquivos obsoletos
- Movidos scripts originais para diretório `obsolete/` preservando compatibilidade
- Organizado scripts de API no diretório `api/`
- Mantido sistema de symlinks para preservar compatibilidade

## [Melhorias 2025-05-21 - Parte 1]

### Correções no Gerenciamento de Processos
- Corrigido o sistema de detecção de processos legados no `process_manager.py`
- Removido `ui/app.py`, `lightrag_ui.py` e `ui.py` dos padrões de detecção de processos legados
- Feito padrões de detecção de monitores legados mais específicos para evitar falsos positivos
- Atualizada a lógica para diferenciar corretamente entre monitores atuais e obsoletos

### Documentação
- Criado arquivo `README.md` com documentação completa do sistema
- Documentado o sistema de gerenciamento de processos
- Documentado o sistema de monitoramento unificado
- Adicionadas instruções sobre compatibilidade e processos legados

### Organização
- Verificado o funcionamento correto do sistema com os padrões atualizados
- Confirmado que a interface Streamlit não é mais erroneamente detectada como processo legado
- Verificada a integridade do sistema com as correções aplicadas

## [Melhorias Anteriores]

### Gerenciamento de PIDs
- Centralizado todos os arquivos PID no diretório `.pids/`
- Criado script `clean_pids.sh` para organizar e limpar arquivos PID

### Consolidação de Scripts
- Unificado monitores em `unified_monitor.py`
- Consolidado ferramentas de migração em `tools/migration_tools.py`
- Implementado sistema de symlinks para compatibilidade