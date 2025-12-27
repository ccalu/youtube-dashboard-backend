# Scanner Automático de Planilhas Google Sheets

## 📊 O QUE FAZ

Sistema que varre automaticamente todas as planilhas Google Sheets dos 35 canais a cada 5 minutos, detecta vídeos prontos para upload e adiciona na fila automaticamente.

**Benefícios:**
- ✅ Zero intervenção manual
- ✅ Detecção instantânea (máximo 5 min de atraso)
- ✅ Prevenção de duplicatas
- ✅ Logs detalhados para debug
- ✅ Proteção contra erros (circuit breaker)

---

## 🏗️ ARQUITETURA

### Componentes:

1. **spreadsheet_scanner.py** (400+ linhas)
   - Classe `SpreadsheetScanner`
   - Lógica de varredura, validação e inserção na fila
   - Rate limiting, timeouts, circuit breaker

2. **main.py** (scheduler)
   - Task assíncrona `schedule_spreadsheet_scanner()`
   - Roda em background desde o startup do Railway

3. **populate_spreadsheet_ids.py** (script auxiliar)
   - Para popular os 35 spreadsheet_ids no banco
   - Uso único (configuração inicial)

4. **migrations/add_spreadsheet_id_column.sql**
   - Adiciona coluna `spreadsheet_id` na tabela `yt_channels`

---

## 🔍 COMO FUNCIONA

### Fluxo Completo:

```
RAILWAY STARTUP
    ↓
schedule_spreadsheet_scanner() inicia
    ↓
A cada 5 minutos:
    ↓
1. Busca canais ativos com spreadsheet_id
    ↓
2. Processa em batches de 5 planilhas
    ↓
3. Para cada planilha:
    - Lê aba "Página1"
    - Filtra linhas prontas (J="done", K vazio, O vazio)
    - Verifica duplicatas no banco
    - Adiciona na fila (yt_upload_queue)
    - Marca planilha como "⏳ processing..."
    ↓
4. Logs detalhados de tudo
    ↓
5. Aguarda 5 minutos e repete
```

### Validação de Vídeo Pronto:

**Todas as condições devem ser TRUE:**

| Coluna | Nome     | Condição                  | Razão                           |
|--------|----------|---------------------------|---------------------------------|
| J      | Status   | == "done"                 | Vídeo renderizado               |
| K      | Post     | Vazio (sem data)          | Ainda não publicado             |
| O      | Upload   | Vazio                     | Ainda não processado            |
| A      | Name     | Preenchido                | Tem título                      |
| M      | Drive    | Preenchido (URL)          | Tem vídeo no Drive              |

**Se QUALQUER condição falhar → vídeo é skipado (não entra na fila)**

---

## ⚙️ CONFIGURAÇÃO

### Variáveis de Ambiente (Railway):

| Variável                      | Padrão | Descrição                                    |
|-------------------------------|--------|----------------------------------------------|
| `SCANNER_ENABLED`             | true   | Ativa/desativa scanner                       |
| `SCANNER_INTERVAL_MINUTES`    | 5      | Intervalo entre varreduras (minutos)         |
| `SCANNER_BATCH_SIZE`          | 5      | Planilhas processadas em paralelo            |
| `SCANNER_TIMEOUT_SECONDS`     | 15     | Timeout máximo por planilha                  |
| `SCANNER_MAX_ERRORS`          | 3      | Erros consecutivos antes de desligar         |
| `GOOGLE_SHEETS_CREDENTIALS_2` | -      | JSON da Service Account (obrigatório)        |

**Para desabilitar temporariamente:**
```bash
# No Railway → Variables
SCANNER_ENABLED=false
```

---

## 🚀 SETUP INICIAL

### PASSO 1: Executar Migration SQL

No Supabase SQL Editor:

```sql
-- Copia e cola o conteúdo de:
-- migrations/add_spreadsheet_id_column.sql
```

Ou via psql:
```bash
psql $SUPABASE_URL -f migrations/add_spreadsheet_id_column.sql
```

Verifica se coluna foi criada:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'yt_channels'
  AND column_name = 'spreadsheet_id';
```

---

### PASSO 2: Popular Spreadsheet IDs

1. **Abra:** `populate_spreadsheet_ids.py`

2. **Preencha o dicionário:**
```python
SPREADSHEET_IDS = {
    'UCQWjUcLU3CUuidv9BJ4VMNg': '1abc...xyz',  # Asche der Imperien
    'UCxxxxxxxxxxxxx': '1def...123',            # Canal 2
    # ... adicionar todos os 35 canais
}
```

3. **Rode o script:**
```bash
python populate_spreadsheet_ids.py
```

4. **Confere os resultados:**
```
==========================================================================
RESUMO
==========================================================================
✅ Sucessos: 35
❌ Erros: 0
📊 Total: 35

==========================================================================
CANAIS ATIVOS SEM SPREADSHEET_ID
==========================================================================
✅ Todos os canais ativos têm spreadsheet_id configurado!
```

---

### PASSO 3: Deploy no Railway

```bash
# 1. Commit das mudanças
git add .
git commit -m "feat: Adicionar scanner automático de planilhas"
git push origin main

# 2. Railway faz deploy automático
# 3. Verifica logs (deve aparecer):
#    📊 Scanner de planilhas AGENDADO (a cada 5 min)
```

---

## 📋 COMO ADICIONAR NOVOS CANAIS

### Opção 1: Via Script (recomendado)

1. Edita `populate_spreadsheet_ids.py`:
```python
SPREADSHEET_IDS = {
    # ... canais existentes
    'UCnovoCanal123': '1xyz...abc',  # Novo Canal
}
```

2. Roda novamente:
```bash
python populate_spreadsheet_ids.py
```

### Opção 2: Via SQL Direto

```sql
UPDATE yt_channels
SET spreadsheet_id = '1xyz...abc'
WHERE channel_id = 'UCnovoCanal123';
```

### Opção 3: Via Python/Supabase

```python
from supabase import create_client
import os

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

sb.table('yt_channels').update({
    'spreadsheet_id': '1xyz...abc'
}).eq('channel_id', 'UCnovoCanal123').execute()
```

**IMPORTANTE:** Scanner detecta automaticamente canais novos (próxima varredura em até 5 min).

---

## 🔍 LOGS E MONITORAMENTO

### Logs Normais (Railway):

```
=================================================================================
🔍 SCANNER INICIADO
⏰ Timestamp: 2025-12-27T14:35:00.123456
📊 Canais para varrer: 35
=================================================================================
📦 Batch 1/7 (canais 1-5)
  📊 Canal: Asche der Imperien (UCQWjUcLU3CUuidv9BJ4VMNg)
     Planilha: 1abc...xyz
     ✅ Linhas lidas: 47
     📹 Vídeos encontrados: 2
     ✅ Vídeos adicionados: 2
        ✅ Row 15: "Título do vídeo..." → Fila (ID 12345)
        ✅ Row 28: "Outro vídeo..." → Fila (ID 12346)
  📊 Canal: El Legado Eterno (UCxxxxx...)
     Planilha: 1def...123
     ✅ Linhas lidas: 32
     📹 Vídeos encontrados: 0
=================================================================================
✅ SCANNER CONCLUÍDO
⏱️  Tempo total: 8.2s
📹 Vídeos encontrados: 7
✅ Vídeos adicionados: 7
⏭️  Vídeos skipados: 0
❌ Erros: 0
=================================================================================
```

### Logs de Duplicata:

```
        ⏭️  Row 15: Já em processamento (ID 12340)
```

### Logs de Timeout:

```
     ⏰ Timeout (15s) - skipando
```

### Logs de Erro:

```
     ❌ Erro: [Errno 2] No such file or directory
```

---

## 🚨 TROUBLESHOOTING

### Problema: "SCANNER DESATIVADO após 3 erros consecutivos"

**Causa:** Circuit breaker ativado (proteção).

**Solução:**
1. Verifica logs para ver qual erro causou
2. Corrige problema raiz (ex: credenciais, permissões)
3. Reinicia Railway:
   ```bash
   # Railway Dashboard → Deployments → Redeploy
   ```

**OU** define variável temporária:
```bash
SCANNER_ENABLED=true
```

---

### Problema: "Nenhum canal ativo com spreadsheet_id encontrado"

**Causa:** Canais não têm `spreadsheet_id` ou `is_active=false`.

**Solução:**
```bash
python populate_spreadsheet_ids.py
```

Ou verifica no Supabase:
```sql
SELECT channel_id, channel_name, spreadsheet_id, is_active
FROM yt_channels
WHERE is_active = true;
```

---

### Problema: "Vídeos não estão sendo detectados"

**Checklist de validação:**
- [ ] Coluna J (Status) = "done" (case-sensitive!)
- [ ] Coluna K (Post) = vazio (sem espaços)
- [ ] Coluna O (Upload) = vazio
- [ ] Coluna A (Name) preenchido
- [ ] Coluna M (Drive URL) preenchido

**Teste manual:**
```python
from yt_uploader.spreadsheet_scanner import SpreadsheetScanner

scanner = SpreadsheetScanner()

# Testa validação de uma linha
row_data = ['Título', 'Desc', '', '', '', '', '', '', '', 'done', '', '', 'https://drive...', '', '']
print(scanner._is_video_ready(row_data))  # True se válido
```

---

### Problema: "Scanner não está rodando no Railway"

**Verifica logs do startup:**
```bash
# Deve aparecer:
📊 Scanner de planilhas AGENDADO (a cada 5 min)
✅ Schedulers started (Railway environment + Scanner)
```

**Se não aparecer:**
1. Verifica se está no Railway:
   ```python
   is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
   ```

2. Verifica se `SCANNER_ENABLED != false`

3. Reinicia deployment

---

### Problema: "ENOSPC: no space left on device"

**Causa:** Disco do Railway cheio (raro).

**Solução:**
1. Limpa arquivos temporários:
   ```bash
   rm -rf /tmp/videos/*
   ```

2. Aumenta storage plan no Railway (se necessário)

---

### Problema: "Erro ao ler planilha: WorksheetNotFound"

**Causa:** Aba "Página1" não existe na planilha.

**Solução:**
- Garante que TODAS as planilhas têm aba chamada **exatamente** "Página1" (sem espaço)
- Não aceita: "Página 1", "Pagina1", "página1"

---

### Problema: "Erro ao autenticar Google Sheets"

**Causa:** `GOOGLE_SHEETS_CREDENTIALS_2` não configurado ou inválido.

**Solução:**
1. Verifica no Railway → Variables:
   ```json
   GOOGLE_SHEETS_CREDENTIALS_2={
     "type": "service_account",
     "project_id": "...",
     "private_key": "...",
     ...
   }
   ```

2. Testa credenciais localmente:
   ```python
   import os
   import json

   creds = json.loads(os.getenv('GOOGLE_SHEETS_CREDENTIALS_2'))
   print(creds.get('client_email'))  # Deve mostrar email da SA
   ```

3. Verifica se Service Account tem acesso às planilhas (compartilhadas com email da SA)

---

## 📊 PERFORMANCE

### Recursos Utilizados:

**Por varredura (35 canais):**
- ⏱️ Tempo: ~8-12 segundos
- 💾 RAM: ~50 MB (pico)
- 🌐 Requisições Google: ~35 reads (bem abaixo do limite de 500/100s)

**Total por hora:**
- 12 varreduras/hora (a cada 5 min)
- ~420 requisições Google/hora
- ~10% dos recursos do Railway

**CONCLUSÃO:** Impacto mínimo, Railway aguenta tranquilamente.

---

## 🔐 SEGURANÇA

### Rate Limiting:
- ✅ Batch size de 5 planilhas em paralelo
- ✅ Pausa de 1s entre batches
- ✅ Timeout de 15s por planilha

### Prevenção de Duplicatas:
- ✅ Query no banco antes de inserir
- ✅ Chave única: (spreadsheet_id + sheets_row_number)
- ✅ Filtra status: pending, downloading, uploading

### Circuit Breaker:
- ✅ Conta erros consecutivos
- ✅ Desliga após 3 erros
- ✅ Log crítico para alertar

### Logs Sensíveis:
- ✅ Nunca loga credenciais
- ✅ Nunca loga conteúdo de descrição (pode ter info sensível)
- ✅ Loga apenas: títulos (primeiros 40 chars), IDs, status

---

## 🎯 ROADMAP FUTURO

**Melhorias planejadas:**

- [ ] Métricas Prometheus (tempo médio por varredura, vídeos detectados/hora)
- [ ] Webhook Discord/Slack quando vídeo é adicionado na fila
- [ ] Dashboard web para ver status do scanner em tempo real
- [ ] Auto-scaling: aumenta frequência se detectar muitos vídeos
- [ ] Histórico de varreduras (tabela no banco)
- [ ] Retry inteligente (backoff exponencial)
- [ ] Suporte a múltiplas abas por planilha

---

## ❓ FAQ

### P: Posso mudar o intervalo para 1 minuto?
R: Sim, mas não é necessário. 5 minutos é mais que suficiente e economiza recursos.

### P: E se uma planilha ficar temporariamente inacessível?
R: Scanner skipará com timeout (15s) e tentará novamente na próxima varredura (5 min).

### P: Preciso reiniciar Railway após adicionar novo canal?
R: Não! Basta popular o spreadsheet_id. Scanner detecta automaticamente em até 5 min.

### P: Scanner funciona no ambiente local?
R: Sim, desde que tenha `GOOGLE_SHEETS_CREDENTIALS_2` configurado no .env.

### P: Como sei se um vídeo foi adicionado na fila?
R: Logs do Railway mostram:
```
✅ Row 15: "Título do vídeo..." → Fila (ID 12345)
```

### P: Posso desabilitar temporariamente sem fazer deploy?
R: Sim:
```bash
# Railway → Variables
SCANNER_ENABLED=false
# Salva → Deploy automático em ~2 min
```

---

## 📞 SUPORTE

**Documentação relacionada:**
- `README.md` - Setup geral do projeto
- `.claude/DASHBOARD_MINERACAO.md` - Documentação do dashboard
- `yt_uploader/README.md` - Sistema de upload

**Logs úteis:**
- Railway Logs (tempo real)
- Supabase Logs (queries)
- Google Cloud Console (API usage)

**Em caso de dúvida:**
1. Leia esta documentação completa
2. Verifica logs do Railway
3. Testa validação manual (código Python acima)
4. Verifica configuração do banco (spreadsheet_ids)
