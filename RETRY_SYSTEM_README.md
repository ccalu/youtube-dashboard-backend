# Sistema de Retry Automático - Vídeos com Erro

## 📋 Resumo

Sistema implementado para re-tentar automaticamente uploads de vídeos que falharam, com limite de 3 tentativas totais.

## 🎯 Problema Resolvido

**Antes:**
- Vídeos com erro (coluna O = "❌ Erro") eram ignorados permanentemente pelo scanner
- Não havia retry automático
- Usuário precisava intervir manualmente para re-tentar uploads

**Depois:**
- Scanner detecta vídeos com erro automaticamente
- Re-adiciona à fila de upload
- Máximo de 3 tentativas totais
- Após 3 falhas → marca "❌ Erro Final" (para de tentar)

## 🔄 Fluxo Completo

### Primeira Tentativa (retry_count = 0)
1. Vídeo com Status = "done", Upload = vazio
2. Scanner adiciona à fila
3. Upload falha → Planilha = "❌ Erro", retry_count = 1

### Segunda Tentativa (retry_count = 1)
4. Scanner detecta Upload = "❌ Erro" + retry_count < 3
5. Re-adiciona à fila
6. Upload falha → Planilha = "❌ Erro", retry_count = 2

### Terceira Tentativa (retry_count = 2)
7. Scanner detecta Upload = "❌ Erro" + retry_count < 3
8. Re-adiciona à fila
9. Upload falha → Planilha = "❌ Erro Final", retry_count = 3

### Tentativas Bloqueadas (retry_count = 3)
10. Scanner detecta Upload = "❌ Erro Final"
11. **IGNORA** (não adiciona à fila)

## 📊 Estados da Coluna O (Upload)

| Estado | Scanner Processa? | Descrição |
|--------|-------------------|-----------|
| `vazio` | ✅ Sim | Primeira tentativa |
| `❌ Erro` | ✅ Sim | Retry (< 3 tentativas) |
| `❌ Erro Final` | ❌ Não | Limite atingido (3 tentativas) |
| `✅` | ❌ Não | Upload bem-sucedido |
| `✅ done` | ❌ Não | Upload bem-sucedido |

## 🛠️ Arquivos Modificados

### 1. `yt_uploader/spreadsheet_scanner.py`

**Mudanças:**
- `_is_video_ready()` (linha 372-382): Aceita Upload = "❌ Erro"
- `_add_to_queue()` (linha 417-444): Verifica retry_count antes de adicionar à fila

**Lógica:**
```python
# Aceita vazio OU "❌ Erro" (para retry)
if upload and upload.strip():
    upload_clean = upload.strip()
    if upload_clean in ["❌ Erro", "❌ erro", "erro", "Erro"]:
        # Permite retry
        pass
    else:
        # Ignora (sucesso ou erro final)
        return False

# Verifica limite de 3 tentativas
if retry_count >= 3:
    logger.info(f"Limite de 3 tentativas atingido")
    return False
```

### 2. `main.py`

**Mudanças:**
- `process_upload_task()` (linha 2233-2269): Marca "❌ Erro Final" após 3ª falha

**Lógica:**
```python
# Busca retry_count atual do banco
total_retry_count = current_upload.get('retry_count', 0)

# Após falha:
if total_retry_count >= 2:
    # 3ª tentativa (0, 1, 2)
    status = "❌ Erro Final"
else:
    # 1ª ou 2ª tentativa
    status = "❌ Erro"
```

## ✅ Testes

Execute o script de teste:

```bash
python test_retry_system.py
```

**Resultados esperados:**
- ✅ Scanner detecta vídeos corretos para retry
- ✅ Marcação correta após falhas
- ✅ Fluxo completo (3 tentativas + bloqueio)

## 📝 Observações

1. **Contador de tentativas:**
   - Armazenado em `yt_upload_queue.retry_count`
   - Incrementado após cada falha
   - Persiste entre scans do scanner

2. **Intervalos de scan:**
   - Scanner roda a cada 5 minutos (Railway)
   - Vídeo com erro será tentado novamente no próximo scan

3. **Limite de 3 tentativas:**
   - Total: 3 tentativas (incluindo primeira)
   - retry_count = 0 (primeira), 1 (segunda), 2 (terceira)
   - retry_count >= 3 = bloqueado

4. **Reset manual:**
   - Para resetar vídeo com "❌ Erro Final":
     1. Mudar coluna O para "❌ Erro" (ou vazio)
     2. Atualizar retry_count no banco para 0
     3. Scanner vai processar novamente
