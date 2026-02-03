# CONFIGURAÇÃO OPENAI_API_KEY NO RAILWAY

## ⚠️ PROBLEMA IDENTIFICADO

O endpoint `/api/comentarios/{id}/gerar-resposta` está falhando porque a variável de ambiente `OPENAI_API_KEY` não está configurada no Railway.

## 🔧 SOLUÇÃO

### 1. Acesse o Railway
1. Entre em https://railway.app/dashboard
2. Selecione o projeto `youtube-dashboard-backend`
3. Clique na aba "Variables"

### 2. Adicione a OPENAI_API_KEY
```
Nome: OPENAI_API_KEY
Valor: [sua chave da OpenAI]
```

### 3. Como obter a chave (se não tiver)
1. Acesse https://platform.openai.com/api-keys
2. Clique em "Create new secret key"
3. Copie a chave gerada

### 4. Deploy será automático
Após adicionar a variável, o Railway fará redeploy automático.

## 📝 VARIÁVEIS NECESSÁRIAS NO RAILWAY

Verifique se TODAS estas variáveis estão configuradas:

```env
# Supabase (obrigatório)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# OpenAI (obrigatório para respostas de comentários)
OPENAI_API_KEY=sk-...

# YouTube API Keys (obrigatório para coleta)
YOUTUBE_API_KEY_3=AIza...
YOUTUBE_API_KEY_4=AIza...
# ... adicione todas as keys que você tem

# Opcional
OPENAI_MODEL=gpt-4o-mini
PORT=8000
```

## 🐛 DEBUG - Como verificar o erro

Se o erro persistir após adicionar a chave:

1. Verifique os logs do Railway:
   - Aba "Deployments"
   - Clique no último deploy
   - Veja os logs de erro

2. O erro esperado se a chave estiver faltando:
```
ValueError: OPENAI_API_KEY não configurada no .env
```

3. Se a chave estiver configurada mas ainda houver erro, pode ser:
   - Chave inválida ou expirada
   - Limite de quota da OpenAI excedido
   - Problema de rede/CORS

## ✅ TESTE RÁPIDO

Após configurar, teste no dashboard:
1. Abra a aba de comentários
2. Clique em "Gerar Resposta" em qualquer comentário
3. Deve funcionar imediatamente