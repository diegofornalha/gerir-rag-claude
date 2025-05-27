# Troubleshooting: Erro de Tela Branca - Duplicação de Declaração

## Problema Encontrado

A aplicação estava apresentando uma tela branca ao carregar, sem nenhum conteúdo visível, mesmo com os serviços (backend e frontend) rodando corretamente.

## Causa Raiz

O problema foi causado por uma **duplicação de declaração** do hook `useDebouncedValue` no arquivo `useRAGSearch.ts`.

### Detalhes do Erro

```
Error: Identifier 'useDebouncedValue' has already been declared
```

O arquivo `/src/hooks/useRAGSearch.ts` estava:
1. **Importando** o hook na linha 2:
   ```typescript
   import { useDebouncedValue } from './useDebouncedValue'
   ```

2. **Declarando localmente** o mesmo hook nas linhas 108-122:
   ```typescript
   function useDebouncedValue<T>(value: T, delay: number): T {
     // implementação...
   }
   ```

## Solução Aplicada

1. **Identificação do problema**: Utilizamos o console do navegador através do Puppeteer para capturar o erro específico
2. **Localização**: Usamos `grep` para encontrar todas as ocorrências de `useDebouncedValue`
3. **Correção**: Removemos a declaração duplicada do hook, mantendo apenas o import

### Comando para correção:
```bash
# Removemos a função duplicada do arquivo
Edit /src/hooks/useRAGSearch.ts
# Deletamos as linhas 108-122 que continham a declaração duplicada
```

## Como Prevenir

Para evitar este tipo de problema no futuro:

1. **Sempre verificar imports**: Antes de declarar uma função, verifique se ela já não está sendo importada
2. **Use TypeScript**: O TypeScript geralmente captura esses erros em tempo de compilação
3. **Linting**: Configure ESLint para detectar declarações duplicadas
4. **Convenção de nomes**: Use nomes únicos e descritivos para evitar conflitos

## Diagnóstico Rápido

Se encontrar uma tela branca novamente:

1. Abra o console do navegador (F12)
2. Procure por erros de JavaScript/React
3. Verifique especialmente por:
   - Erros de importação
   - Declarações duplicadas
   - Módulos não encontrados
   - Erros de sintaxe

## Comandos Úteis

```bash
# Verificar logs do frontend
./dev.sh logs

# Verificar erros de TypeScript
cd frontend && pnpm tsc --noEmit

# Limpar cache e reiniciar
./dev.sh clean-start

# Buscar declarações duplicadas
grep -r "function nomeDaFuncao" src/
```

## Nota Adicional

Também encontramos um problema secundário onde o arquivo estava nomeado como `app.tsx` (minúsculo) mas o import esperava `App.tsx` (maiúsculo). Isso foi corrigido renomeando o arquivo:

```bash
mv src/app.tsx src/App.tsx
```

---

**Data da resolução**: 27/01/2025  
**Tempo de resolução**: ~15 minutos  
**Impacto**: Aplicação completamente inacessível (tela branca)