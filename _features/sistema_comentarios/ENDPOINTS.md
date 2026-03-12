# Endpoints da API - Sistema de Comentários

## 📍 Base URL
- **Local:** `http://localhost:8000`
- **Produção:** `https://youtube-dashboard-backend-production.up.railway.app`

**Última Atualização:** 13/02/2026 - Atualizado após 6 fixes e coleta histórica completa

---

## 1️⃣ GET /api/comentarios/resumo

**Descrição:** Retorna resumo dos comentários dos canais monetizados

**Localização no código:**
- `main.py` linha 1157
- `database.py` linha 2480-2516 (função `get_comments_summary`)

**Resposta:**
```json
{
  "canais_monetizados": 6,
  "total_comentarios": 1937,
  "novos_hoje": 26,
  "aguardando_resposta": 1014
}
```

**Filtros aplicados:**
- Apenas canais com `tipo="nosso"` e `subnicho="Monetizados"`
- Total de comentários dos últimos 30 dias (filtro: `collected_at >= 30 dias atrás`)
- Novos hoje: filtro por `collected_at >= hoje 00:00`
- Aguardando resposta: comentários com `suggested_response IS NOT NULL` e `is_responded = false`

---

## 2️⃣ GET /api/comentarios/monetizados

**Descrição:** Lista canais monetizados com estatísticas de comentários

**Localização no código:**
- `main.py` linha 1075
- `database.py` linha 2295-2347 (função `get_monetized_channels_with_comments`)

**Resposta:**
```json
[
  {
    "id": 672,
    "nome_canal": "Mistérios Arquivados",
    "total_comentarios": 1095,
    "total_videos": 61,
    "comentarios_sem_resposta": 600,
    "comentarios_pendentes": 526,
    "url_canal": "https://youtube.com/@misterios_arquivados",
    "thumbnail": "https://yt3.ggpht.com/..."
  }
]
```

**Campos adicionados (02/02/2026):**
- `total_videos`: Número de vídeos únicos com comentários

---

## 3️⃣ GET /api/canais/{canal_id}/videos-com-comentarios

**Descrição:** Lista TOP 10 vídeos de um canal ordenados por quantidade de comentários

**Localização no código:**
- `main.py` linha 1089
- `database.py` linha 2349-2419 (função `get_videos_with_comments_count`)

### ⚠️ REESCRITA COMPLETA (02/02/2026)

**ANTES (até commit d3db5ba):**
- Buscava de `videos_historico` (tabela com histórico temporal)
- Causava duplicatas (mesmo vídeo aparecia múltiplas vezes)
- Ordenava por views
- Retornava apenas 2 vídeos devido a duplicatas

**DEPOIS (commit 6239352):**
- Busca diretamente de `video_comments`
- Usa `Counter` do Python para agrupar vídeos únicos
- Ordena por quantidade de comentários
- Retorna TOP 10 vídeos mais comentados
- Zero duplicatas

**Implementação atual:**
```python
# 1. Busca TODOS comentários do canal
comments_data = self.supabase.table('video_comments').select(
    'video_id, video_title'
).eq('canal_id', canal_id).execute()

# 2. Agrupa por video_id usando Counter (elimina duplicatas)
from collections import Counter
video_counts = Counter([c['video_id'] for c in comments_data.data])

# 3. Ordena por quantidade de comentários
top_videos = video_counts.most_common(limit)

# 4. Busca dados adicionais apenas para views/data
```

**Resposta:**
```json
[
  {
    "video_id": "Tj1HkeXJobo",
    "titulo": "DNA de indígenas brasileiros revela origem que ninguém esperava",
    "views": 61167,
    "data_publicacao": "2025-12-27T12:00:00Z",
    "total_comentarios": 283,
    "comentarios_pendentes": 150,
    "thumbnail": "https://i.ytimg.com/vi/Tj1HkeXJobo/mqdefault.jpg"
  }
]
```

**Parâmetros:**
- `limit`: Número de vídeos (padrão: 10)

---

## 4️⃣ GET /api/videos/{video_id}/comentarios-paginados

**Descrição:** Retorna comentários paginados de um vídeo

**Localização no código:**
- `main.py` linha 1104
- `database.py` linha 2421-2478 (função `get_video_comments_paginated`)

### 🔧 Helper Function: _safe_date_format()

**Nova função criada (02/02/2026):**
- Localização: `database.py` linha 2423-2448
- Propósito: Tratamento robusto de datas para evitar RangeError no frontend
- Trata: datas NULL, vazias, mal formatadas
- Garante: sempre retorna ISO 8601 válido com timezone

**Resposta:**
```json
{
  "comments": [
    {
      "id": "abc123",
      "author_name": "João Silva",
      "author_channel_id": "@joao",
      "comment_text": "Excelente vídeo!",
      "comment_text_pt": "Excelente vídeo!",
      "suggested_response": "Obrigado pelo feedback!",
      "is_responded": false,
      "published_at": "2025-12-27T20:23:37Z",
      "collected_at": "2026-01-21T15:59:27Z",
      "likes": 5,
      "reply_count": 2
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 283,
    "total_pages": 15
  }
}
```

**⚠️ MUDANÇA IMPORTANTE (02/02/2026):**
- **ANTES:** Retornava chave `comentarios`
- **AGORA:** Retorna chave `comments` (compatível com frontend)

**Parâmetros:**
- `page`: Página atual (padrão: 1)
- `limit`: Comentários por página (padrão: 20)

---

## 5️⃣ PATCH /api/comentarios/{comment_id}/marcar-respondido

**Descrição:** Marca um comentário como respondido

**Localização no código:**
- `main.py` linha 1121
- `database.py` linha 2518-2536 (função `mark_comment_as_responded`)

**Request:**
```json
{
  "response_text": "Texto da resposta enviada"
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Comentário marcado como respondido"
}
```

**Campos atualizados:**
- `is_responded`: true
- `response_text`: Texto da resposta
- `responded_at`: Timestamp atual

---

## 6️⃣ POST /api/collect-comments/{canal_id}

**Descrição:** Força coleta manual de comentários de um canal

**Localização no código:**
- `main.py` linha 1136
- `collector.py` linha 949-1024 (função `collect_comments_for_channel`)

**Filtros aplicados:**
- Apenas canais com `tipo="nosso"`
- Coleta TODOS os vídeos do canal (sem limite)
- Até 100 comentários por vídeo

**Resposta:**
```json
{
  "status": "success",
  "canal": "Mistérios Arquivados",
  "comentarios_coletados": 245,
  "videos_processados": 10
}
```

---

## 📊 Estatísticas do Sistema

### Números Atualizados (13/02/2026):
- **43 canais** tipo="nosso"
- **6 canais monetizados** (subnicho="Monetizados")
- **15.074 comentários** totais (coleta histórica completa)
- **11 canais em português** (não gastam tokens GPT)
- **100% traduzidos** para PT-BR (0 pendentes)

### Performance:
- **Coleta completa** de TODOS os vídeos (sem limite de TOP 20)
- **28% economia** em tokens GPT (pula canais PT)
- **Coleta automática** às 5h AM diariamente
- **Tradução automática** após coleta

---

## 🔧 Mudanças Técnicas Importantes

### Reescrita Completa (02/02/2026 - commit 6239352)

**Função:** `get_videos_with_comments_count()`

**Problema raiz:** Função buscava de `videos_historico` que contém registros temporais (múltiplas entradas por vídeo ao longo do tempo), causando:
- Duplicatas nos resultados
- Apenas 2 vídeos aparecendo quando deveria mostrar 10
- Títulos NULL em alguns casos

**Solução implementada:**
1. Busca diretamente de `video_comments` (fonte única)
2. Agrupa usando `Counter` do Python
3. Ordena por quantidade de comentários (não por views)
4. Busca dados complementares de `videos_historico` apenas para views/data
5. Tratamento de títulos com fallback

**Helper function:** `_safe_date_format()`
- Trata datas NULL, vazias, mal formatadas
- Sempre retorna ISO 8601 válido
- Evita RangeError no frontend

---

## 📝 Logs e Monitoramento

Todos os endpoints incluem logs detalhados:
- `logger.info()` para operações bem-sucedidas
- `logger.error()` para erros com stack trace
- `logger.warning()` para situações anômalas

Arquivo de logs: `comments_logs.py` gerencia todo o sistema de logging.

---

*Documentação atualizada em 13/02/2026 após 6 fixes e coleta histórica completa (15.074 comentários, 43 canais)*