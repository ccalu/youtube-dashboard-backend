# SISTEMA DE UPLOAD AUTOMÁTICO - INSTRUÇÕES COMPLETAS

## STATUS: 100% FUNCIONAL ✅

### CORREÇÕES APLICADAS (03/02/2026)
1. **Wizard v2 corrigido** - salva tudo atomicamente no final
2. **SERVICE_ROLE_KEY configurada** - bypass RLS funcionando
3. **Canal coreano deletado** - pronto para readicionar
4. **Proteção contra duplicatas** - funcionando

---

## 🎯 COMO ADICIONAR UM NOVO CANAL

### Passo 1: Execute o Wizard
```bash
python add_canal_wizard_v2.py
```

### Passo 2: Responda as Perguntas (Nova Ordem)
1. **Channel ID do YouTube** (ex: UCxxxxxxxxxxxxxx)
2. **Nome do Canal** (aparece no dashboard)
3. **Língua** (13 opções disponíveis)
4. **Subnicho** (6 opções: seus subnichos reais)
5. **Canal Monetizado?** (s/n)
6. **ID da Playlist** (pegar do YouTube Studio)
7. **ID da Planilha** (Google Sheets com vídeos)

### Passo 3: Faça o OAuth
- Wizard abre navegador automaticamente
- Faça login com a conta do canal
- Autorize acesso
- Cole o código de autorização

### Passo 4: Verificação
```bash
python verificar_canal_salvo.py
```

**Deve mostrar:**
- ✓ Canal salvo
- ✓ Credenciais encontradas
- ✓ Tokens encontrados
- ✓ Token válido por X minutos

---

## 📊 DASHBOARD DE MONITORAMENTO

### Para Ver Uploads do Dia
```bash
python dashboard_daily_uploads.py
```
- Acesse: http://localhost:5001
- Mostra todos os canais
- Status em tempo real
- Botão para forçar upload

### Para Executar Upload Manual
```bash
python daily_uploader.py
```
- Processa todos os canais com upload_automatico=True
- Verifica planilha de cada canal
- Faz upload de 1 vídeo/canal

---

## 📋 CONFIGURAR VÍDEOS NA PLANILHA

### Colunas Obrigatórias:
- **Coluna J:** Status (marque como "done" quando pronto)
- **Coluna K:** Título do vídeo
- **Coluna L:** Descrição
- **Coluna M:** Tags (separadas por vírgula)
- **Coluna O:** Path do vídeo no Google Drive

### Exemplo:
| J | K | L | M | O |
|---|---|---|---|---|
| done | Título Incrível | Descrição completa... | tag1, tag2, tag3 | /Videos/video123.mp4 |

---

## 🔄 FLUXO AUTOMÁTICO DIÁRIO

### Horários:
- **~5:30 AM:** Sistema de coleta roda (collector.py)
- **~6:00 AM:** Upload automático roda (daily_uploader.py)
- **Resultado:** 1 vídeo/canal/dia

### Logs:
- Salvos em: `yt_upload_daily_logs`
- Consultar: Dashboard ou banco de dados

---

## 🛠️ RESOLUÇÃO DE PROBLEMAS

### Se o Wizard Fechar Inesperadamente:
1. Verifique se tem SERVICE_ROLE_KEY no .env
2. Execute: `python test_rls_bypass.py`
3. Delete canal incompleto: `python delete_canal_incompleto.py`
4. Tente novamente

### Se Upload Falhar:
1. Verifique token: `python verificar_canal_salvo.py`
2. Verifique planilha (coluna J = "done")
3. Verifique path do vídeo (coluna O)
4. Consulte logs no dashboard

### Se Token Expirar:
- Sistema renova automaticamente com refresh_token
- Se falhar, refaça OAuth com wizard

---

## 📁 ARQUIVOS DO SISTEMA

### Scripts Principais:
- `add_canal_wizard_v2.py` - Adicionar novos canais
- `daily_uploader.py` - Executor de uploads
- `dashboard_daily_uploads.py` - Dashboard web
- `verificar_canal_salvo.py` - Verificar configuração

### Scripts de Manutenção:
- `delete_canal_incompleto.py` - Deletar canal problemático
- `test_wizard_flow.py` - Testar proteção duplicatas
- `test_rls_bypass.py` - Testar SERVICE_ROLE_KEY

### Documentação:
- `SISTEMA_UPLOAD_AUTOMATICO.md` - Documentação técnica
- `INSTRUCOES_UPLOAD_AUTOMATICO.md` - Este arquivo

---

## ✅ PRÓXIMOS PASSOS

1. **Adicione o canal coreano novamente:**
   ```bash
   python add_canal_wizard_v2.py
   ```

2. **Configure vídeos na planilha**
   - Marque coluna J como "done"
   - Preencha título, descrição, tags
   - Confirme path no Drive

3. **Acompanhe no dashboard:**
   ```bash
   python dashboard_daily_uploads.py
   ```

4. **Aguarde upload automático**
   - Ou force manualmente pelo dashboard
   - Ou execute: `python daily_uploader.py`

---

## 📞 SUPORTE

Se tiver problemas:
1. Verifique este documento
2. Consulte logs no dashboard
3. Execute scripts de verificação
4. Entre em contato com suporte técnico

**Sistema desenvolvido e testado com sucesso!** 🚀