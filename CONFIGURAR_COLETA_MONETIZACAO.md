# CONFIGURAÇÃO DA COLETA DE MONETIZAÇÃO

## PROBLEMA IDENTIFICADO
A coleta de dados REAIS de monetização **PAROU no dia 10/12/2025**.

## SOLUÇÃO NECESSÁRIA

### 1. Configurar no Agendador de Tarefas do Windows

Execute como Administrador:
```cmd
taskschd.msc
```

### 2. Criar Nova Tarefa

**Nome:** Coleta Monetização YouTube
**Executar com privilégios mais altos:** ✅

### 3. Configurar Gatilho (Trigger)

- **Tipo:** Diariamente
- **Horário:** 08:00 AM
- **Repetir a cada:** 1 dia

### 4. Configurar Ação

**Programa/Script:**
```
C:\Users\User-OEM\AppData\Local\Programs\Python\Python310\python.exe
```

**Argumentos:**
```
coleta_diaria.py
```

**Iniciar em:**
```
D:\ContentFactory\youtube-dashboard-backend\monetization_dashboard
```

### 5. ALTERNATIVA: Executar Manualmente

Para executar a coleta agora:
```cmd
cd D:\ContentFactory\youtube-dashboard-backend\monetization_dashboard
python coleta_diaria.py
```

## DADOS COLETADOS

O script `coleta_diaria.py` coleta via OAuth2:
- ✅ **Revenue real** (estimatedRevenue)
- ✅ **Views**
- ✅ **Likes, Comments, Shares**
- ✅ **Subscribers gained/lost**
- ✅ **Minutes watched**

## MÉTRICAS NÃO COLETADAS (mas disponíveis)

Para adicionar retenção e CTR, modifique a linha 122:
```python
"metrics": "estimatedRevenue,views,likes,comments,shares,subscribersGained,subscribersLost,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,cardClickRate",
```

## VERIFICAÇÃO DE STATUS

Para verificar se está funcionando:
```python
from database import SupabaseClient
from datetime import datetime

db = SupabaseClient()

# Ver últimos dados reais
metrics = db.supabase.table('yt_daily_metrics')\
    .select('date')\
    .eq('is_estimate', False)\
    .order('date', desc=True)\
    .limit(1)\
    .execute()

print(f"Último dado real: {metrics.data[0]['date']}")
```

## LOGS

Verificar logs em:
```
D:\ContentFactory\youtube-dashboard-backend\monetization_dashboard\logs\coleta.log
```

## IMPORTANTE

- O script usa OAuth2 (não usa as 20 API keys)
- Cada canal precisa ter tokens OAuth configurados
- Os dados aparecem com 2-3 dias de atraso (normal do YouTube)