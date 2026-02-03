# ✅ CHECKLIST FINAL - Sistema de Upload Automático

## ⚠️ IMPORTANTE - VERIFICAÇÃO DE TOKENS
**Para verificar tokens OAuth:** Use `python check_oauth_definitivo.py`
- ❌ NÃO use scripts com SUPABASE_KEY (não mostra tokens por causa do RLS)
- ✅ USE scripts com SERVICE_ROLE_KEY (bypassa RLS e mostra tudo)

## 📊 STATUS ATUAL (03/02/2026 - 16:45)

### Canal Coreano (UCiMgKMWsYH8a8EFp94TClIQ):
- ✅ Canal configurado no banco (ID: 90)
- ✅ Upload automático ATIVO
- ✅ Playlist configurada: PLe-V17oPwzExLhmRHSL9MITHkeaLadY-x
- ✅ Spreadsheet configurado: 16VWyE0zuAvJOeiGtXVP...
- ✅ Credenciais OAuth salvas (Client ID + Secret)
- ✅ Tokens OAuth CONFIRMADOS (Access: 253 chars, Refresh: 103 chars)
- ✅ Tokens criados: 03/02/2026 às 15:29
- ✅ **Upload E Playlist testados e funcionando 100%!**
- ✅ **Último teste bem-sucedido:** 15:51 (Video ID: yYncJBqxBzg)

---

## 🔧 CORREÇÃO APLICADA (03/02/2026)

### Bug Resolvido: Playlist não funcionava
- **Problema:** Upload funcionava mas vídeos não eram adicionados à playlist (erro 403)
- **Causa:** Falta do scope `youtube.force-ssl` na autorização OAuth
- **Solução:** Todos os wizards e oauth_manager.py atualizados com os 4 scopes obrigatórios

### OAuth Scopes Obrigatórios (TODOS necessários):
1. `https://www.googleapis.com/auth/youtube.upload` - Upload de vídeos
2. `https://www.googleapis.com/auth/youtube` - Leitura do canal
3. `https://www.googleapis.com/auth/youtube.force-ssl` - **Gerenciar playlists** (CRÍTICO!)
4. `https://www.googleapis.com/auth/spreadsheets` - Google Sheets

---

## 🎯 PASSO 1: ADICIONAR NOVOS CANAIS

Execute o comando:
```bash
python add_canal_wizard_v3.py
```

### Instruções:
1. **Channel ID:** Digite `UCiMgKMWsYH8a8EFp94TClIQ`
2. **OAuth:** Quando abrir o navegador, faça login com a conta do canal
3. **IMPORTANTE:** Aceite TODAS as permissões:
   - ✅ Gerenciar conta do YouTube
   - ✅ Fazer upload de vídeos
   - ✅ Ver planilhas do Google
4. **Código:** Copie e cole o código de autorização

---

## 🧪 PASSO 2: VERIFICAR QUE FUNCIONOU

### 2.1. Verificar configuração:
```bash
python verify_after_reauth.py
```
Deve mostrar tudo como "OK"

### 2.2. Testar upload:
```bash
python daily_uploader.py --test
```
Se não tiver vídeos na planilha, vai mostrar "Sem vídeo" (normal)

---

## ➕ PASSO 3: ADICIONAR NOVO CANAL

Execute o mesmo wizard:
```bash
python add_canal_wizard_v3.py
```

### Instruções:
1. Digite o Channel ID do novo canal
2. Configure todos os dados pedidos
3. Faça o OAuth completo
4. **IMPORTANTE:** Aceite TODAS as permissões

---

## ✔️ VERIFICAÇÕES FINAIS

### Sistema está garantido para:
- ✅ Upload automático funcionar
- ✅ Vídeos serem adicionados às playlists
- ✅ Refresh automático de tokens
- ✅ Logs claros de erro se falhar algo
- ✅ SERVICE_ROLE_KEY funcionando (sem RLS)

### O que NÃO foi alterado (continua funcionando):
- ✅ Sistema de upload (daily_uploader.py)
- ✅ Integração com Google Sheets
- ✅ Download do Google Drive
- ✅ Estrutura do banco de dados
- ✅ Deploy no Railway

---

## 📝 COMANDOS ÚTEIS

### Verificar tokens OAuth (USAR ESTE!):
```bash
python check_oauth_definitivo.py
```
**IMPORTANTE:** Este script usa SERVICE_ROLE_KEY e mostra os tokens reais!

### Verificar status de qualquer canal:
```bash
python check_upload_status.py
```

### Testar upload manual:
```bash
python daily_uploader.py --test
```

### Ver tokens salvos:
```bash
python test_oauth_fix.py
```

### Limpar registro de upload de hoje (para testar novamente):
```bash
python clear_upload_today.py
```

---

## ⚠️ PROBLEMAS COMUNS

### "Sem vídeo disponível"
- Normal se a planilha não tem vídeos
- Adicione vídeos na planilha do Google Sheets

### "Upload funciona mas playlist não adiciona"
- **Erro 403:** "insufficientPermissions" ao adicionar à playlist
- **Causa:** Falta o scope `youtube.force-ssl` na autorização
- **Solução:** Refazer OAuth com wizard v3 (já corrigido)
- **Prevenção:** Sempre aceitar TODAS as permissões no OAuth

### "Token expirado"
- Normal, o sistema renova automaticamente
- Se falhar, refaça OAuth com wizard

---

## 🚀 SISTEMA 100% PRONTO E CONFIRMADO!

### ✅ STATUS FINAL (03/02/2026 - 16:45):
- **Canal coreano:** Tokens OAuth CONFIRMADOS com SERVICE_ROLE_KEY
- **Upload automático:** TESTADO e funcionando
- **Railway:** Deploy successful + DAILY_UPLOAD_ENABLED=true
- **Integração main.py:** Código deployado e ativo

### 🎯 CONFIRMAÇÃO DEFINITIVA:
```
[SUCESSO TOTAL] Canal 100% configurado!
- Tokens OAuth salvos (253 + 103 chars)
- Credenciais salvas (72 + 35 chars)
- Sistema pronto para upload automático!
```

**AMANHÃ ÀS 5:30 AM:** Sistema vai rodar automaticamente e fazer upload de 1 vídeo!