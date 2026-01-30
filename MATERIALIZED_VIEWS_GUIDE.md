# GUIA COMPLETO: MATERIALIZED VIEWS DO DASHBOARD

## O que são as Materialized Views (MVs)?

Materialized Views são "tabelas pré-calculadas" que armazenam resultados de queries complexas. No nosso sistema, elas transformam queries de 3000ms em 100ms (30x mais rápido).

## MVs no Sistema

### 1. mv_canal_video_stats
- **O que faz:** Pré-calcula total de vídeos e views por canal
- **Atualização:** Após cada coleta diária
- **Uso:** Dashboard principal

### 2. mv_dashboard_completo
- **O que faz:** Consolida TODOS os dados do dashboard
- **Atualização:** Após cada coleta diária
- **Uso:** Endpoints `/api/canais` e `/api/canais-tabela`

## Como Funciona o Sistema

```
[Coleta Diária 5h] → [Salva Dados] → [Refresh MVs] → [Limpa Cache]
                                           ↓
                                    [Dashboard Rápido]
```

## Sistema de Cache

### Duração
- **Atual:** 6 horas (pode ser ajustado)
- **Localização:** Memória RAM do servidor
- **Tamanho:** ~50KB para 232 canais

### Como funciona
1. Primeiro acesso: Busca da MV (~100ms) e cria cache
2. Próximos acessos: Direto do cache (<1ms)
3. Cache expira: Busca nova da MV

## Como Atualizar MVs Manualmente

### Opção 1: Botão no Dashboard (RECOMENDADO)
1. Abra o dashboard
2. Clique no botão "Atualizar" (ícone de refresh)
3. Aguarde ~3 segundos
4. Dashboard atualizado!

### Opção 2: Via API
```bash
curl -X POST https://youtube-dashboard-backend-production.up.railway.app/api/cache/clear
```

### Opção 3: Script Python
```bash
python update_materialized_views.py
```

## Troubleshooting

### Problema: Dashboard mostra dados antigos
**Solução:**
1. Clique no botão "Atualizar" no dashboard
2. Se não resolver, execute o script `update_materialized_views.py`
3. Último recurso: Reinicie o servidor no Railway

### Problema: MVs com timeout
**Causa:** Muitos dados para processar
**Solução:**
1. Aguarde 5 minutos e tente novamente
2. Se persistir, execute direto no Supabase:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_completo;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_canal_video_stats;
```

### Problema: Canais fantasma após deletar
**Causa:** MV não foi atualizada
**Solução:**
1. Delete o canal
2. Clique imediatamente no botão "Atualizar"
3. Dashboard mostrará dados corretos

## Endpoint /api/cache/clear

### O que faz:
1. Limpa cache do Dashboard
2. Limpa cache da Tabela
3. Atualiza ambas MVs
4. Retorna status da operação

### Resposta esperada:
```json
{
  "message": "Cache limpo com sucesso",
  "cache_cleared": true,
  "mv_refreshed": true,
  "timestamp": "2026-01-30T15:45:00Z"
}
```

## Performance

| Operação | Sem MV | Com MV | Ganho |
|----------|--------|--------|-------|
| Dashboard inicial | 3000ms | 100ms | 30x |
| Dashboard (cache) | 3000ms | <1ms | 3000x |
| Após atualização | 3000ms | 100ms | 30x |

## Manutenção

### Diária (Automática)
- Coleta às 5h (horário de SP)
- Refresh das MVs
- Limpeza de cache

### Manual (Quando necessário)
- Após deletar/adicionar canais
- Após reorganizações grandes
- Se dados parecerem desatualizados

## Scripts Disponíveis

| Script | Uso | Tempo |
|--------|-----|-------|
| `update_materialized_views.py` | Atualiza MVs e mostra status | ~30s |
| `force_refresh_mv.py` | Força refresh simples | ~10s |
| `check_mv_sync.py` | Verifica sincronização | ~5s |

## Boas Práticas

1. **Após mudanças grandes:** Sempre clique no botão "Atualizar"
2. **Desenvolvimento:** Use o botão frequentemente
3. **Produção:** Confie na atualização diária
4. **Performance:** Não desabilite as MVs (dashboard fica lento)

## FAQ

### Por que usar MVs?
- Dashboard 30x mais rápido
- Menos carga no banco
- Melhor experiência do usuário

### Quando NÃO usar MVs?
- Durante debug intenso (use queries diretas)
- Se precisar dados em tempo real absoluto
- Para relatórios únicos/especiais

### MVs são obrigatórias?
Não, mas sem elas o dashboard fica muito lento (3+ segundos)

### Posso criar novas MVs?
Sim, no Supabase SQL Editor. Lembre de adicionar refresh no código.

## Contato

Para problemas com MVs, verificar:
1. Logs no Railway
2. SQL Editor no Supabase
3. Scripts de manutenção local