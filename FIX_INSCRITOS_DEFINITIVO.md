# 🚨 FIX DEFINITIVO - INSCRITOS_DIFF NÃO ATUALIZA

**Data:** 26/01/2026
**Problema:** Dashboard mostra "--" para ganho/perda de inscritos há 3 dias
**Causa:** Materialized View criada sem o campo `inscritos_diff`
**Solução:** Recriar MV com cálculo correto

⚠️ **ATUALIZAÇÃO IMPORTANTE:** Correções aplicadas para usar `status = 'ativo'` ao invés de `ativo = true` (campo não existe)

---

## ⚡ RESOLUÇÃO RÁPIDA (5 MINUTOS)

### 📋 Passo 1: Acesse o Supabase
1. Entre em: https://supabase.com/dashboard
2. Selecione seu projeto
3. Clique em **SQL Editor** no menu lateral

### 📋 Passo 2: Execute as Validações ANTES (Opcional mas Recomendado)
Cole e execute o conteúdo do arquivo `validate_before.sql` para verificar a estrutura atual.

**Principais verificações:**
- Estrutura das tabelas
- Se há dados de hoje e ontem
- Preview do cálculo manual

### 📋 Passo 3: Execute o Fix Principal
Cole TODO o conteúdo do arquivo `fix_mv_corrected.sql` e execute.

**O que este SQL faz:**
1. Remove a MV antiga (que está quebrada)
2. Recria com o cálculo `inscritos_diff = hoje - ontem`
3. Cria índices para performance
4. Mostra resultados de verificação

**Tempo de execução:** 30-60 segundos

### 📋 Passo 4: Valide o Sucesso
Execute o conteúdo do arquivo `validate_after.sql` para confirmar que funcionou.

**Você deve ver:**
- ✅ Campo `inscritos_diff` criado
- ✅ Valores calculados (positivos, negativos, zeros)
- ✅ Compatibilidade com Python confirmada

### 📋 Passo 5: Limpe o Cache (Local)
Se estiver testando localmente:
```bash
python clear_cache.py
```

**Output esperado:**
```
✅ FIX APLICADO COM SUCESSO!
📈 Ganharam: X canais
📉 Perderam: Y canais
```

### 📋 Passo 6: Verifique no Dashboard
1. Abra o dashboard
2. Vá na aba **Tabela** ou **Canais**
3. Confirme que mostra valores como: +150, -23, 0 (não mais "--")

---

## 🔍 DETALHES TÉCNICOS

### Problema Identificado
A MV `mv_dashboard_completo` foi criada em 23/01 durante otimização de performance, mas:
- ❌ Não incluía cálculo de `inscritos_diff`
- ❌ Tinha campos inexistentes (username, nome ao invés de nome_canal)
- ❌ Cache 24h perpetuava o problema

### Como Funcionava Antes
```python
# database.py linha 434-441 (FUNCIONAVA)
data_ontem = (datetime.now() - timedelta(days=1)).isoformat()
inscritos_diff = hoje - ontem
```

### O Que Mudou
- 23/01: Criada MV para performance (3000ms → 0.109ms)
- MV tinha prioridade sobre cálculo manual
- MV retornava NULL → Dashboard mostrava "--"

### Solução Aplicada
```sql
-- Cálculo correto adicionado na MV
CASE
    WHEN hoje.inscritos IS NOT NULL AND ontem.inscritos IS NOT NULL
    THEN hoje.inscritos - ontem.inscritos
    ELSE NULL
END as inscritos_diff
```

---

## ⚠️ TROUBLESHOOTING

### Se ainda mostrar "--" após aplicar:

1. **Verifique se há dados de hoje:**
```sql
SELECT COUNT(*) FROM dados_canais_historico
WHERE data_coleta = CURRENT_DATE;
```

2. **Verifique se há dados de ontem:**
```sql
SELECT COUNT(*) FROM dados_canais_historico
WHERE data_coleta = CURRENT_DATE - 1;
```

3. **Force refresh da MV:**
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;
```

4. **Limpe cache forçadamente:**
- No Railway: Restart do serviço
- Local: Pare e inicie o servidor novamente

### Se der erro ao executar o SQL:

**Erro: "column ativo does not exist"**
- ✅ **JÁ CORRIGIDO!** Os SQLs agora usam `status = 'ativo'` ao invés de `ativo = true`

**Erro: "column nome_canal does not exist"**
- Verifique a estrutura real com query 1 do `validate_before.sql`
- Ajuste o SQL para usar os nomes corretos

**Erro: "mv_canal_video_stats does not exist"**
- Comente as linhas relacionadas a video_stats no SQL
- A MV funcionará sem essas estatísticas

---

## 📊 RESULTADO ESPERADO

### Antes do Fix:
```
Canal A: 10.5K inscritos | --
Canal B: 25.3K inscritos | --
Canal C: 8.2K inscritos  | --
```

### Depois do Fix:
```
Canal A: 10.5K inscritos | +150
Canal B: 25.3K inscritos | -23
Canal C: 8.2K inscritos  | 0
```

---

## 🔄 ROLLBACK (Se Necessário)

Se algo der errado e precisar reverter:

```sql
-- Volta para versão anterior (sem inscritos_diff)
DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_completo;

CREATE MATERIALIZED VIEW mv_dashboard_completo AS
SELECT
    c.id,
    c.nome_canal,
    c.url_canal,
    c.tipo,
    c.subnicho,
    c.inscritos,
    NULL::INTEGER as inscritos_diff,  -- Temporário
    c.views_30d,
    c.ultima_coleta
FROM canais_monitorados c
WHERE c.ativo = true;
```

Depois disso, o sistema voltará a usar o cálculo manual do Python (mais lento mas funcional).

---

## ✅ CHECKLIST FINAL

- [ ] Executei `validate_before.sql` e vi a estrutura
- [ ] Executei `fix_mv_corrected.sql` sem erros
- [ ] Executei `validate_after.sql` e confirmei sucesso
- [ ] Limpei o cache com `clear_cache.py`
- [ ] Dashboard mostra valores corretos (não mais "--")
- [ ] Aba Tabela ordena corretamente por ganho/perda

---

## 📞 SUPORTE

Se ainda tiver problemas após seguir todos os passos:

1. Verifique os logs do Railway
2. Execute as queries de troubleshooting
3. Confirme que a coleta diária está funcionando
4. Verifique se há dados dos últimos 2 dias no histórico

**Arquivos criados para este fix:**
- `fix_mv_corrected.sql` - SQL principal do fix
- `validate_before.sql` - Validações pré-execução
- `validate_after.sql` - Validações pós-execução
- `clear_cache.py` - Script melhorado de limpeza
- `FIX_INSCRITOS_DEFINITIVO.md` - Esta documentação

---

**FIM DO DOCUMENTO**