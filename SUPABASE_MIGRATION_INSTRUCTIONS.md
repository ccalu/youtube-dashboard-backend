# 📋 INSTRUÇÕES PARA APLICAR MIGRATION NO SUPABASE

## ⚡ PASSOS RÁPIDOS:

1. **Abra o arquivo SQL:**
   ```
   D:\ContentFactory\youtube-dashboard-backend\database\migrations\006_comments_gpt_optimized.sql
   ```

2. **Copie TODO o conteúdo** (Ctrl+A, Ctrl+C)

3. **Acesse o Supabase:**
   - Entre no seu dashboard Supabase
   - Clique em **SQL Editor** (menu lateral)

4. **Execute a migration:**
   - Cole o SQL (Ctrl+V)
   - Clique em **RUN** (botão verde)

5. **Verifique o resultado:**
   - Deve aparecer mensagens de sucesso:
     ```
     ✅ Tabela video_comments criada com sucesso
     ✅ Campo gpt_analysis (JSONB) configurado
     ✅ Tabela video_comments_summary criada
     ✅ Tabela gpt_analysis_metrics criada
     ✅ Migration 006_comments_gpt_optimized aplicada com sucesso!
     ```

## 📊 O QUE FOI CRIADO:

### Tabelas:
- `video_comments` - Comentários com análise GPT
- `video_comments_summary` - Resumo por vídeo
- `gpt_analysis_metrics` - Métricas de uso da API

### Campos principais:
- `gpt_analysis` (JSONB) - Análise completa da IA
- `priority_score` (0-100) - Priorização inteligente
- `suggested_response` - Resposta sugerida
- `sentiment_confidence` - Confiança da análise

### Views:
- `priority_comments_view` - Comentários prioritários
- `pending_response_view` - Pendentes de resposta

## ⚠️ IMPORTANTE:

- **CUIDADO:** A migration dropa tabelas antigas se existirem
- Só execute se não tiver dados importantes nas tabelas de comentários
- Após aplicar, NÃO execute novamente (duplicaria)

## ✅ PRÓXIMOS PASSOS:

Após aplicar a migration com sucesso:
1. Volte aqui e confirme que aplicou
2. Vamos atualizar o database.py
3. Criar o analisador GPT
4. Testar tudo funcionando

---

**STATUS:** Aguardando aplicação no Supabase...