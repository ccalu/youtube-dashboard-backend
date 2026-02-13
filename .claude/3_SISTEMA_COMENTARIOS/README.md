# Sistema de Comentários - Dashboard YouTube

## 📊 Visão Geral

Sistema completo de gestão de comentários para canais YouTube, com foco em **responder comentários de canais monetizados**.

### Números Atuais (13/02/2026)
- **43 canais** monitorados (tipo="nosso")
- **6 canais monetizados** (subnicho="Monetizados") - foco para respostas
- **37 canais de análise** - apenas mineração/insights
- **15.074 comentários** coletados no total (coleta histórica completa)
- **1.860 comentários** com sugestão de resposta pronta
- **100% traduzidos** para PT-BR (com canais PT otimizados)
- **Coleta completa** de TODOS os vídeos de cada canal (sem limite)

## 🎯 Propósito

O sistema foi criado para:
1. **Coletar** comentários de TODOS os 43 canais nossos (todos os vídeos)
2. **Traduzir** comentários em outras línguas para PT-BR (pulando canais PT)
3. **Gerar sugestões de resposta** personalizadas via GPT (não análises)
4. **Gerenciar respostas** apenas para os 6 canais monetizados
5. **Analisar sentimento** e categorizar comentários

## 🔄 Fluxo do Sistema

```
1. COLETA
   └─> YouTube API coleta comentários de vídeos

2. PROCESSAMENTO
   ├─> Tradução automática (se não PT)
   └─> Análise de sentimento

3. SUGESTÃO DE RESPOSTA
   └─> GPT gera sugestão de resposta personalizada (gpt_response_suggester.py)

4. GESTÃO
   ├─> Dashboard mostra comentários dos monetizados
   ├─> Copiar sugestão de resposta
   └─> Marcar como respondido
```

## 📁 Estrutura de Arquivos

### Backend
- `database.py` - 6 novas funções para comentários
- `main.py` - 6 novos endpoints da API
- `collector.py` - Coleta comentários via YouTube API

### Frontend
- `docs/LOVABLE_COMMENTS_COMPLETE.md` - Componente React completo
- `frontend-code/CommentsTab.tsx` - Interface usuário

### Scripts
- `scripts/comentarios/` - Scripts de automação e processamento

## 🚀 Como Usar

### 1. Aba de Comentários no Dashboard
- Mostra apenas comentários dos 6 canais monetizados
- Cards com resumo: total, novos hoje, aguardando resposta
- Navegação: Canal → Vídeos → Comentários

### 2. Respondendo Comentários
1. Clicar no canal monetizado
2. Escolher vídeo com comentários
3. Ver sugestão de resposta
4. Copiar e personalizar
5. Marcar como respondido

### 3. Coleta Manual
- Botão "Coletar" por canal
- Busca últimos 100 comentários
- Processa automaticamente

## 🔗 Documentação Relacionada

- [ENDPOINTS.md](./ENDPOINTS.md) - Detalhes dos 6 endpoints
- [BANCO_DADOS.md](./BANCO_DADOS.md) - Estrutura da tabela
- [IMPLEMENTACAO.md](./IMPLEMENTACAO.md) - Timeline do desenvolvimento
- [FRONTEND.md](./FRONTEND.md) - Componente React

## ⚙️ Configurações

### Canais Monetizados (6 total - atualizado em 13/02/2026)
Subnicho="Monetizados" no banco de dados

Estes são os únicos que aparecem na aba de comentários para gestão de respostas.

## 📈 Status Atual (13/02/2026)

✅ **Sistema 100% funcional com coleta histórica completa**
- 15.074 comentários coletados de 43 canais
- Coleta histórica completa (TODOS os vídeos, sem limite)
- Coleta automática funcionando às 5h AM diariamente
- Traduções processadas (100% - 0 pendentes)
- Sugestões geradas (1.860 total)
- Canais PT não gastam tokens GPT (11 canais otimizados)
- Pronto e rodando em produção no Railway

### 🔧 6 Fixes Aplicados (13/02/2026)
1. Campo `comment_text_original` - coleta salva no campo correto
2. Campo `response_generated_at` - atualizado ao gerar sugestões GPT
3. Campo `comentarios_sem_resposta` - endpoint retorna campo correto
4. `videos_to_collect` sem limite - coleta TODOS os vídeos (não mais TOP 20)
5. `total_coletados` no response - endpoint retorna total real
6. Coleta histórica completa - 15.074 comentários de 43 canais

### 🔧 Bugs Anteriores Corrigidos (02/02/2026)
- Bug collector.py: variável `recent_videos` → corrigido
- Bug engagement_preprocessor.py: campo `all_comments` → corrigido

## 🔮 Próximos Passos

1. Integrar componente no Lovable
2. Começar a responder comentários com sugestões
3. Automação de respostas para comentários positivos

---

**Última atualização:** 13/02/2026
**Desenvolvido por:** Cellibs com Claude