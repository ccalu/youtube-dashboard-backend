# 🔐 VERIFICAÇÃO DE TOKENS OAUTH - GUIA DEFINITIVO

**Última atualização:** 03/02/2026 - 16:45
**Status:** ✅ Sistema configurado e funcionando

---

## ⚠️ DESCOBERTA CRÍTICA - LEIA PRIMEIRO!

### Por que verificações falham mas o sistema funciona?

**PROBLEMA:** Tokens OAuth existem mas parecem "não estar lá" quando verificamos.

**CAUSA:** Supabase tem duas chaves com comportamentos diferentes:

1. **SUPABASE_KEY (anon)**
   - ❌ RLS (Row Level Security) ATIVO
   - ❌ NÃO mostra tokens OAuth
   - ❌ NÃO mostra credenciais
   - ✅ Mostra dados públicos (canais, etc)

2. **SUPABASE_SERVICE_ROLE_KEY**
   - ✅ Bypass RLS completo
   - ✅ MOSTRA tokens OAuth
   - ✅ MOSTRA credenciais
   - ✅ Acesso total ao banco

**SOLUÇÃO:** SEMPRE use SERVICE_ROLE_KEY para verificar tokens!

---

## 📊 Como o Sistema Funciona

### daily_uploader.py usa SERVICE_ROLE_KEY
```python
# Linha 32-33 do daily_uploader.py
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # <-- BYPASS RLS!
)
```

Por isso o upload funciona mesmo quando verificações normais dizem "sem tokens".

### database.py usa SUPABASE_KEY (anon)
```python
# database.py usa chave normal com RLS
self.supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")  # <-- RLS ATIVO!
)
```

Por isso verificações com database.py não mostram tokens.

---

## ✅ VERIFICAÇÃO CORRETA DE TOKENS

### Script Definitivo: check_oauth_definitivo.py

```bash
python check_oauth_definitivo.py
```

Este script:
- Usa SERVICE_ROLE_KEY (bypass RLS)
- Mostra TODOS os tokens e credenciais
- Confirma se sistema está pronto

### Resultado Esperado:
```
[SUCESSO TOTAL] Canal 100% configurado!
- Canal existe no banco
- Tokens OAuth salvos
- Credenciais salvas

SISTEMA PRONTO PARA UPLOAD AUTOMATICO!
```

---

## 📋 STATUS ATUAL (03/02/2026)

### Canal Coreano: UCiMgKMWsYH8a8EFp94TClIQ

| Componente | Status | Detalhes |
|------------|--------|----------|
| **Canal** | ✅ CONFIGURADO | ID: 90 no banco |
| **Tokens OAuth** | ✅ SALVOS | Access (253 chars) + Refresh (103 chars) |
| **Credenciais** | ✅ SALVAS | Client ID + Secret |
| **Criado em** | ✅ | 03/02/2026 às 15:29 |
| **Último upload** | ✅ | Video ID: yYncJBqxBzg |
| **Playlist** | ✅ | PLe-V17oPwzExLhmRHSL9MITHkeaLadY-x |

---

## 🔍 Comandos de Verificação

### 1. Verificação Completa (RECOMENDADO)
```bash
python check_oauth_definitivo.py
```
Usa SERVICE_ROLE_KEY - Mostra TUDO

### 2. Teste de Upload
```bash
python daily_uploader.py --test
```
Faz upload real para confirmar que funciona

### 3. Dashboard de Status
```bash
python dashboard_daily_uploads.py
# Acessar: http://localhost:5002
```
Interface web para monitorar uploads

---

## ⚠️ TROUBLESHOOTING

### "Canal sem OAuth configurado"
**Causa:** Usando SUPABASE_KEY em vez de SERVICE_ROLE_KEY
**Solução:** Use check_oauth_definitivo.py

### "Token expirado"
**Normal:** Sistema renova automaticamente
**Verificar:** Token tem refresh_token para renovação

### "403 Insufficient Permissions"
**Causa:** Falta scope youtube.force-ssl
**Solução:** Refazer OAuth com wizard v3

---

## 🚀 CHECKLIST PARA NOVO CANAL

1. **Adicionar canal:**
```bash
python add_canal_wizard_v2.py
```

2. **Verificar tokens foram salvos:**
```bash
python check_oauth_definitivo.py
```

3. **Testar upload:**
```bash
python daily_uploader.py --test
```

4. **Confirmar no Railway:**
- Variável DAILY_UPLOAD_ENABLED=true
- SERVICE_ROLE_KEY configurada

---

## 📝 NOTAS IMPORTANTES

### Sempre que verificar tokens:
1. Use SERVICE_ROLE_KEY, não SUPABASE_KEY
2. Se não encontrar com chave normal, não significa que não existem
3. O que importa é se daily_uploader.py consegue acessar

### RLS (Row Level Security):
- Protege dados sensíveis (tokens, credenciais)
- Só SERVICE_ROLE_KEY pode ver tudo
- É uma feature de segurança, não um bug

### Variáveis de Ambiente Necessárias:
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJxxxxx  # Chave anon (com RLS)
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx  # Chave service (bypass RLS)
```

---

## 🎯 RESUMO

**Sistema está 100% funcional quando:**
1. check_oauth_definitivo.py mostra tokens salvos
2. daily_uploader.py --test funciona
3. Railway tem DAILY_UPLOAD_ENABLED=true

**Não se preocupe se:**
- Verificações normais dizem "sem tokens"
- Scripts com SUPABASE_KEY não veem tokens
- RLS está bloqueando acesso

**O que importa:**
- daily_uploader.py usa SERVICE_ROLE_KEY
- Sistema funciona às 5:30 AM diariamente
- Uploads são realizados com sucesso

---

**Documento criado para evitar confusões futuras sobre tokens OAuth "invisíveis".**